"""
Hash generation and blockchain submission router.
"""

import os
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.config import get_settings
from app.models import (
    User, UserRole, ResultFile, FileStatus,
    HashRecord, AuditLog, AuditAction,
)
from app.schemas import (
    HashGenerateRequest, HashRecordResponse,
    StoreHashRequest, StoreHashResponse, MessageResponse,
)
from app.services.auth_service import get_current_user, require_roles
from app.services.hash_service import hash_service
from app.services.blockchain import blockchain_service
from app.services.pki_service import pki_service

settings = get_settings()
router = APIRouter(prefix="/hash", tags=["Hash & Blockchain"])


@router.post("/generate", response_model=HashRecordResponse)
async def generate_hash(
    request: Request,
    body: HashGenerateRequest,
    current_user: User = Depends(
        require_roles([UserRole.SUPER_ADMIN, UserRole.ELECTION_OFFICIAL])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate SHA-256 hash for an uploaded result file.
    
    Reads the file from disk, computes SHA-256, optionally signs it
    with the user's PKI key, and stores the hash record in the database.
    """
    # Get the result file
    result = await db.execute(
        select(ResultFile).where(ResultFile.id == body.result_file_id)
    )
    result_file = result.scalar_one_or_none()

    if not result_file:
        raise HTTPException(status_code=404, detail="Result file not found")

    if result_file.status not in (FileStatus.UPLOADED, FileStatus.FAILED):
        raise HTTPException(status_code=400, detail="File has already been hashed")

    # Update status to hashing
    result_file.status = FileStatus.HASHING
    db.add(result_file)
    await db.flush()

    # Read file and compute hash
    file_path = os.path.join(os.path.abspath(settings.UPLOAD_DIR), result_file.stored_filename)
    if not os.path.exists(file_path):
        result_file.status = FileStatus.FAILED
        db.add(result_file)
        raise HTTPException(status_code=500, detail="Stored file not found on disk")

    hash_result = hash_service.hash_file(file_path)

    # Optional: digitally sign the hash with user's private key
    digital_signature = None
    if current_user.public_key:
        # In production, the private key would be in a secure enclave
        # For now we skip actual signing if no key is available
        pass

    # Create hash record
    hash_record = HashRecord(
        result_file_id=result_file.id,
        sha256_hash=hash_result["sha256_hash"],
        hash_algorithm=hash_result["hash_algorithm"],
        file_size_bytes=hash_result["file_size_bytes"],
        digital_signature=digital_signature,
        signed_by=current_user.id if digital_signature else None,
    )
    db.add(hash_record)

    # Update file status
    result_file.status = FileStatus.HASHED
    db.add(result_file)
    await db.flush()

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.GENERATE_HASH,
        resource_type="hash_record",
        resource_id=hash_record.id,
        ip_address=request.client.host if request.client else None,
        details={
            "sha256_hash": hash_result["sha256_hash"],
            "file_id": str(result_file.id),
        },
        success=True,
    )
    db.add(audit)

    return HashRecordResponse.model_validate(hash_record)


@router.post("/store", response_model=StoreHashResponse)
async def store_hash_on_blockchain(
    request: Request,
    body: StoreHashRequest,
    current_user: User = Depends(
        require_roles([UserRole.SUPER_ADMIN, UserRole.ELECTION_OFFICIAL])
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a hash record to the Hyperledger Fabric blockchain.
    
    Makes the hash immutable by storing it on the distributed ledger.
    """
    # Get the hash record with its result file
    result = await db.execute(
        select(HashRecord)
        .options(selectinload(HashRecord.result_file).selectinload(ResultFile.constituency))
        .where(HashRecord.id == body.hash_record_id)
    )
    hash_record = result.scalar_one_or_none()

    if not hash_record:
        raise HTTPException(status_code=404, detail="Hash record not found")

    if hash_record.is_on_blockchain:
        raise HTTPException(status_code=400, detail="Hash already stored on blockchain")

    result_file = hash_record.result_file
    constituency = result_file.constituency

    # Submit to blockchain
    try:
        bc_record = await blockchain_service.store_hash(
            file_hash=hash_record.sha256_hash,
            file_id=str(result_file.id),
            constituency_code=constituency.code if constituency else "unknown",
            election_date=str(result_file.election_date),
            election_type=result_file.election_type,
            uploader_id=str(current_user.id),
        )
    except Exception as e:
        result_file.status = FileStatus.FAILED
        db.add(result_file)
        raise HTTPException(status_code=500, detail=f"Blockchain submission failed: {str(e)}")

    # Update hash record with blockchain details
    hash_record.blockchain_tx_id = bc_record.tx_id
    hash_record.blockchain_block_number = bc_record.block_number
    hash_record.blockchain_timestamp = bc_record.timestamp
    hash_record.is_on_blockchain = True
    db.add(hash_record)

    # Update file status
    result_file.status = FileStatus.CONFIRMED
    db.add(result_file)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action=AuditAction.SUBMIT_HASH,
        resource_type="hash_record",
        resource_id=hash_record.id,
        ip_address=request.client.host if request.client else None,
        details={
            "tx_id": bc_record.tx_id,
            "block_number": bc_record.block_number,
        },
        success=True,
    )
    db.add(audit)

    return StoreHashResponse(
        hash_record_id=hash_record.id,
        blockchain_tx_id=bc_record.tx_id,
        blockchain_block_number=bc_record.block_number,
        message="Hash successfully stored on blockchain",
    )
