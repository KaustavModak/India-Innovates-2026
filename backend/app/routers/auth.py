"""
Authentication router: login, MFA, user management.
"""

from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, UserRole, AuditLog, AuditAction
from app.schemas import (
    LoginRequest, LoginResponse, MFAVerifyRequest, MFASetupResponse,
    UserCreate, UserResponse, MessageResponse,
)
from app.services.auth_service import (
    hash_password, verify_password,
    create_access_token, create_mfa_session_token,
    decode_token, get_current_user, require_roles,
    generate_mfa_secret, get_mfa_uri, verify_mfa_code,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user with email/password. Returns JWT or MFA challenge."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        # Log failed attempt
        audit = AuditLog(
            action=AuditAction.LOGIN,
            ip_address=request.client.host if request.client else None,
            details={"email": body.email, "reason": "invalid_credentials"},
            success=False,
        )
        db.add(audit)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    # If MFA is enabled, return a session token for the MFA step
    if user.mfa_enabled:
        session_token = create_mfa_session_token(user.id)
        return LoginResponse(
            access_token="",
            requires_mfa=True,
            mfa_session_token=session_token,
        )

    # No MFA — issue access token directly
    access_token = create_access_token(user.id, user.email, user.role.value)
    user.last_login = datetime.utcnow()
    db.add(user)

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.LOGIN,
        ip_address=request.client.host if request.client else None,
        success=True,
    )
    db.add(audit)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/mfa-verify", response_model=LoginResponse)
async def mfa_verify(
    body: MFAVerifyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Verify MFA TOTP code and issue access token."""
    payload = decode_token(body.session_token)
    if payload.get("type") != "mfa_session":
        raise HTTPException(status_code=400, detail="Invalid MFA session token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not configured")

    if not verify_mfa_code(user.mfa_secret, body.mfa_code):
        raise HTTPException(status_code=401, detail="Invalid MFA code")

    access_token = create_access_token(user.id, user.email, user.role.value)
    user.last_login = datetime.utcnow()
    db.add(user)

    audit = AuditLog(
        user_id=user.id,
        action=AuditAction.MFA_VERIFIED,
        success=True,
    )
    db.add(audit)

    return LoginResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/mfa-setup", response_model=MFASetupResponse)
async def mfa_setup(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Enable MFA for the current user. Returns secret + QR code URI."""
    secret = generate_mfa_secret()
    uri = get_mfa_uri(secret, current_user.email)

    current_user.mfa_secret = secret
    current_user.mfa_enabled = True
    db.add(current_user)

    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.MFA_ENABLED,
        success=True,
    )
    db.add(audit)

    return MFASetupResponse(
        secret=secret,
        qr_code_uri=uri,
        backup_codes=[],  # Production: generate and store backup codes
    )


@router.post("/register", response_model=UserResponse)
async def register_user(
    body: UserCreate,
    current_user: User = Depends(require_roles([UserRole.SUPER_ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    """Register a new user (admin only)."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role=UserRole(body.role.value),
        organization=body.organization,
    )
    db.add(user)
    await db.flush()

    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.CREATE_USER,
        resource_type="user",
        resource_id=user.id,
        success=True,
    )
    db.add(audit)

    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the current authenticated user's profile."""
    return UserResponse.model_validate(current_user)
