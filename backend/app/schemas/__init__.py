"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID
from enum import Enum


# --- Enums ---

class UserRoleSchema(str, Enum):
    super_admin = "super_admin"
    election_official = "election_official"
    auditor = "auditor"
    viewer = "viewer"


class FileStatusSchema(str, Enum):
    uploaded = "uploaded"
    hashing = "hashing"
    hashed = "hashed"
    submitted_to_blockchain = "submitted_to_blockchain"
    confirmed = "confirmed"
    failed = "failed"


class VerificationStatusSchema(str, Enum):
    pending = "pending"
    verified = "verified"
    tampered = "tampered"
    error = "error"


# --- Auth Schemas ---

class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_mfa: bool = False
    mfa_session_token: Optional[str] = None
    user: Optional["UserResponse"] = None


class MFAVerifyRequest(BaseModel):
    session_token: str
    mfa_code: str = Field(..., min_length=6, max_length=6)


class MFASetupResponse(BaseModel):
    secret: str
    qr_code_uri: str
    backup_codes: List[str]


class TokenData(BaseModel):
    user_id: UUID
    email: str
    role: UserRoleSchema


# --- User Schemas ---

class UserCreate(BaseModel):
    email: str
    password: str = Field(..., min_length=8)
    full_name: str
    role: UserRoleSchema = UserRoleSchema.viewer
    organization: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: UserRoleSchema
    organization: Optional[str]
    is_active: bool
    mfa_enabled: bool
    last_login: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Constituency Schemas ---

class ConstituencyCreate(BaseModel):
    name: str
    code: str
    state: str
    district: Optional[str] = None
    country: str = "India"
    total_registered_voters: Optional[int] = None


class ConstituencyResponse(BaseModel):
    id: UUID
    name: str
    code: str
    state: str
    district: Optional[str]
    country: str
    total_registered_voters: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Result File Schemas ---

class ResultFileUploadRequest(BaseModel):
    constituency_id: UUID
    election_date: date
    election_type: str
    description: Optional[str] = None


class ResultFileResponse(BaseModel):
    id: UUID
    constituency_id: UUID
    uploaded_by: UUID
    original_filename: str
    file_size_bytes: int
    mime_type: str
    status: FileStatusSchema
    election_date: date
    election_type: str
    description: Optional[str]
    uploaded_at: datetime

    class Config:
        from_attributes = True


# --- Hash Schemas ---

class HashGenerateRequest(BaseModel):
    result_file_id: UUID


class HashRecordResponse(BaseModel):
    id: UUID
    result_file_id: UUID
    sha256_hash: str
    hash_algorithm: str
    file_size_bytes: int
    digital_signature: Optional[str]
    blockchain_tx_id: Optional[str]
    blockchain_block_number: Optional[int]
    blockchain_timestamp: Optional[datetime]
    is_on_blockchain: bool
    created_at: datetime

    class Config:
        from_attributes = True


class StoreHashRequest(BaseModel):
    hash_record_id: UUID


class StoreHashResponse(BaseModel):
    hash_record_id: UUID
    blockchain_tx_id: str
    blockchain_block_number: int
    message: str


# --- Verification Schemas ---

class VerificationRequest(BaseModel):
    file_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash to verify")


class VerificationResponse(BaseModel):
    id: UUID
    submitted_hash: str
    status: VerificationStatusSchema
    is_verified: bool
    blockchain_verified: bool
    blockchain_tx_id: Optional[str]
    matched_record: Optional[HashRecordResponse]
    result_details: dict
    verified_at: datetime

    class Config:
        from_attributes = True


# --- Audit Log Schemas ---

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    action: str
    resource_type: Optional[str]
    resource_id: Optional[UUID]
    ip_address: Optional[str]
    details: dict
    success: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    logs: List[AuditLogResponse]


# --- Generic Schemas ---

class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
