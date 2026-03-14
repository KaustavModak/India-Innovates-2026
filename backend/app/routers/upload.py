"""
File upload router: handles election result file uploads.
"""

import os
import uuid
import aiofiles
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import get_settings
from app.models import User, UserRole, ResultFile, FileStatus, Constituency, AuditLog, AuditAction
from app.schemas import ResultFileResponse, MessageResponse
from app.services.auth_service import get_current_user, require_roles

settings = get_settings()
router = APIRouter(prefix="/upload", tags=["File Upload"])

ALLOWED_EXTENSIONS = set(settings.ALLOWED_EXTENSIONS.split(","))


def validate_file_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in ALLOWED_EXTENSIONS


@router.post("/result", response_model=ResultFileResponse)
async def upload_result(
    request: Request,
    file: UploadFile = File(...),
    constituency_id: str = Form(...),
    election_date: str = Form(...),
    election_type: str = Form(...),
    description: str = Form(None),
    current_user: User = Depends(
        require_roles([UserRole.SUPER_ADMIN, UserRole.ELECTION_OFFICIAL])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an official election result file.
    
    Only election officials and admins can upload files.
    The file is stored locally and a database record is created.
    """
    # Validate file extension
    if not validate_file_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Validate constituency exists
    const_result = await db.execute(
        select(Constituency).where(Constituency.id == uuid.UUID(constituency_id))
    )
    constituency = const_result.scalar_one_or_none()
    if not constituency:
        raise HTTPException(status_code=404, detail="Constituency not found")

    # Generate unique stored filename
    file_ext = file.filename.rsplit(".", 1)[-1].lower()
    stored_filename = f"{uuid.uuid4()}.{file_ext}"

    # Ensure upload directory exists
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, stored_filename)

    # Save file to disk
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Create database record
    from datetime import date as date_type
    result_file = ResultFile(
        constituency_id=uuid.UUID(constituency_id),
        uploaded_by=current_user.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_size_bytes=file_size,
        mime_type=file.content_type or "application/octet-stream",
        status=FileStatus.UPLOADED,
        election_date=datetime.strptime(election_date, "%Y-%m-%d").date(),
        election_type=election_type,
        description=description,
    )
    db.add(result_file)
    await db.flush()

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.UPLOAD_FILE,
        resource_type="result_file",
        resource_id=result_file.id,
        ip_address=request.client.host if request.client else None,
        details={
            "filename": file.filename,
            "file_size": file_size,
            "constituency": constituency.code,
        },
        success=True,
    )
    db.add(audit)

    return ResultFileResponse.model_validate(result_file)
