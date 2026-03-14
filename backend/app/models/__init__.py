"""
SQLAlchemy ORM models mapping to the PostgreSQL schema.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Integer, BigInteger, Text, Date,
    ForeignKey, Enum, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# --- Enum Types ---

class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ELECTION_OFFICIAL = "election_official"
    AUDITOR = "auditor"
    VIEWER = "viewer"


class FileStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    HASHING = "hashing"
    HASHED = "hashed"
    SUBMITTED_TO_BLOCKCHAIN = "submitted_to_blockchain"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    TAMPERED = "tampered"
    ERROR = "error"


class AuditAction(str, enum.Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    UPLOAD_FILE = "upload_file"
    GENERATE_HASH = "generate_hash"
    SUBMIT_HASH = "submit_hash"
    VERIFY_RESULT = "verify_result"
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    MFA_ENABLED = "mfa_enabled"
    MFA_VERIFIED = "mfa_verified"
    ACCESS_DENIED = "access_denied"


# --- ORM Models ---

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    organization = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(255))
    public_key = Column(Text)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    uploaded_files = relationship("ResultFile", back_populates="uploader")
    audit_logs = relationship("AuditLog", back_populates="user")


class Constituency(Base):
    __tablename__ = "constituencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    state = Column(String(255), nullable=False, index=True)
    district = Column(String(255))
    country = Column(String(100), nullable=False, default="India")
    total_registered_voters = Column(Integer)
    metadata_ = Column("metadata", JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    result_files = relationship("ResultFile", back_populates="constituency")


class ResultFile(Base):
    __tablename__ = "result_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    constituency_id = Column(UUID(as_uuid=True), ForeignKey("constituencies.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_filename = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(100), nullable=False)
    status = Column(Enum(FileStatus), nullable=False, default=FileStatus.UPLOADED)
    election_date = Column(Date, nullable=False)
    election_type = Column(String(100), nullable=False)
    description = Column(Text)
    metadata_ = Column("metadata", JSON, default={})
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    constituency = relationship("Constituency", back_populates="result_files")
    uploader = relationship("User", back_populates="uploaded_files")
    hash_record = relationship("HashRecord", back_populates="result_file", uselist=False)


class HashRecord(Base):
    __tablename__ = "hash_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_file_id = Column(UUID(as_uuid=True), ForeignKey("result_files.id"), nullable=False)
    sha256_hash = Column(String(64), nullable=False, unique=True)
    hash_algorithm = Column(String(20), nullable=False, default="SHA-256")
    file_size_bytes = Column(BigInteger, nullable=False)
    digital_signature = Column(Text)
    signed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    blockchain_tx_id = Column(String(255))
    blockchain_block_number = Column(BigInteger)
    blockchain_timestamp = Column(DateTime(timezone=True))
    blockchain_network = Column(String(100), default="hyperledger-fabric")
    is_on_blockchain = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    result_file = relationship("ResultFile", back_populates="hash_record")
    signer = relationship("User", foreign_keys=[signed_by])


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    action = Column(Enum(AuditAction), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(UUID(as_uuid=True))
    ip_address = Column(String(45))  # IPv6 max length
    user_agent = Column(Text)
    details = Column(JSON, default={})
    success = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submitted_hash = Column(String(64), nullable=False, index=True)
    submitted_filename = Column(String(500))
    submitted_file_size = Column(BigInteger)
    matched_hash_record_id = Column(UUID(as_uuid=True), ForeignKey("hash_records.id"))
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.PENDING)
    requester_ip = Column(String(45))
    blockchain_verified = Column(Boolean, default=False)
    blockchain_query_tx_id = Column(String(255))
    result_details = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    matched_record = relationship("HashRecord")
