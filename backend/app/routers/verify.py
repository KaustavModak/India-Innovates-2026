"""
Verification router: public endpoints for citizens to verify results.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import Optional, List

from app.database import get_db
from app.models import (
    HashRecord, ResultFile, Constituency, VerificationRequest as VerReqModel,
    VerificationStatus, AuditLog, AuditAction,
)
from app.schemas import (
    VerificationResponse, VerificationStatusSchema,
    ConstituencyResponse, AuditLogResponse, AuditLogListResponse,
    HashRecordResponse,
)
from app.services.blockchain import blockchain_service
from app.services.hash_service import hash_service
from app.redis_client import cache_service

router = APIRouter(prefix="/verify", tags=["Verification"])


@router.get("/result/{file_hash}", response_model=VerificationResponse)
async def verify_result(
    file_hash: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    PUBLIC ENDPOINT: Verify an election result file hash.
    
    Citizens can submit a SHA-256 hash and the system will:
    1. Check the database for a matching hash record
    2. Verify the hash exists on the blockchain
    3. Return verification status
    
    Results are cached in Redis for performance.
    """
    # Normalize hash
    file_hash = file_hash.lower().strip()

    if len(file_hash) != 64:
        raise HTTPException(status_code=400, detail="Invalid SHA-256 hash format (must be 64 hex characters)")

    # Check Redis cache first
    cached = await cache_service.get_cached_verification(file_hash)
    if cached:
        return cached

    # Query database for hash record
    result = await db.execute(
        select(HashRecord)
        .options(
            selectinload(HashRecord.result_file)
            .selectinload(ResultFile.constituency)
        )
        .where(HashRecord.sha256_hash == file_hash)
    )
    hash_record = result.scalar_one_or_none()

    # Verify on blockchain
    bc_result = await blockchain_service.verify_hash(file_hash)

    if not hash_record:
        # Hash not found in our system
        ver_request = VerReqModel(
            submitted_hash=file_hash,
            status=VerificationStatus.TAMPERED,
            requester_ip=request.client.host if request.client else None,
            blockchain_verified=False,
            result_details={"message": "Hash not found in official records"},
        )
        db.add(ver_request)
        await db.flush()

        response_data = VerificationResponse(
            id=ver_request.id,
            submitted_hash=file_hash,
            status=VerificationStatusSchema.tampered,
            is_verified=False,
            blockchain_verified=False,
            blockchain_tx_id=None,
            matched_record=None,
            result_details={"message": "Hash not found in official records. The file may have been tampered with."},
            verified_at=datetime.utcnow(),
        )
    else:
        # Hash found — verify against blockchain
        is_blockchain_verified = bc_result.get("exists_on_blockchain", False)

        ver_request = VerReqModel(
            submitted_hash=file_hash,
            matched_hash_record_id=hash_record.id,
            status=VerificationStatus.VERIFIED if is_blockchain_verified else VerificationStatus.PENDING,
            requester_ip=request.client.host if request.client else None,
            blockchain_verified=is_blockchain_verified,
            blockchain_query_tx_id=bc_result.get("tx_id"),
            result_details={
                "constituency": hash_record.result_file.constituency.name if hash_record.result_file.constituency else None,
                "election_date": str(hash_record.result_file.election_date),
                "election_type": hash_record.result_file.election_type,
                "original_filename": hash_record.result_file.original_filename,
                "blockchain": bc_result,
            },
        )
        db.add(ver_request)
        await db.flush()

        response_data = VerificationResponse(
            id=ver_request.id,
            submitted_hash=file_hash,
            status=VerificationStatusSchema.verified if is_blockchain_verified else VerificationStatusSchema.pending,
            is_verified=is_blockchain_verified,
            blockchain_verified=is_blockchain_verified,
            blockchain_tx_id=hash_record.blockchain_tx_id,
            matched_record=HashRecordResponse.model_validate(hash_record),
            result_details=ver_request.result_details,
            verified_at=datetime.utcnow(),
        )

    # Audit log
    audit = AuditLog(
        action=AuditAction.VERIFY_RESULT,
        ip_address=request.client.host if request.client else None,
        resource_type="verification",
        resource_id=ver_request.id,
        details={"hash": file_hash, "verified": response_data.is_verified},
        success=True,
    )
    db.add(audit)

    # Cache the result
    await cache_service.cache_verification(file_hash, response_data.model_dump(mode="json"))

    return response_data


@router.get("/constituencies", response_model=List[ConstituencyResponse])
async def list_constituencies(
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """PUBLIC ENDPOINT: List all constituencies with optional state filter."""
    # Check cache
    cached = await cache_service.get_cached_constituencies()
    if cached and not state:
        return cached

    query = select(Constituency).order_by(Constituency.state, Constituency.name)
    if state:
        query = query.where(Constituency.state == state)

    result = await db.execute(query)
    constituencies = result.scalars().all()
    data = [ConstituencyResponse.model_validate(c) for c in constituencies]

    if not state:
        await cache_service.cache_constituency_list([d.model_dump(mode="json") for d in data])

    return data


@router.get("/audit-logs", response_model=AuditLogListResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """PUBLIC ENDPOINT: View audit logs for transparency."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)

    # Count total
    count_query = select(func.count()).select_from(AuditLog)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    total = (await db.execute(count_query)).scalar()

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    result = await db.execute(query)
    logs = result.scalars().all()

    return AuditLogListResponse(
        total=total,
        page=page,
        per_page=per_page,
        logs=[AuditLogResponse.model_validate(log) for log in logs],
    )
