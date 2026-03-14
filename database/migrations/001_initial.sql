-- ============================================================
-- Post-Count Cryptographic Audit Layer
-- Database Migration 001: Initial Schema
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- ENUM TYPES
-- ============================================================

CREATE TYPE user_role AS ENUM (
    'super_admin',
    'election_official',
    'auditor',
    'viewer'
);

CREATE TYPE file_status AS ENUM (
    'uploaded',
    'hashing',
    'hashed',
    'submitted_to_blockchain',
    'confirmed',
    'failed'
);

CREATE TYPE verification_status AS ENUM (
    'pending',
    'verified',
    'tampered',
    'error'
);

CREATE TYPE audit_action AS ENUM (
    'login',
    'logout',
    'upload_file',
    'generate_hash',
    'submit_hash',
    'verify_result',
    'create_user',
    'update_user',
    'delete_user',
    'mfa_enabled',
    'mfa_verified',
    'access_denied'
);

-- ============================================================
-- TABLE: users
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'viewer',
    organization VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mfa_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    public_key TEXT,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================
-- TABLE: constituencies
-- ============================================================

CREATE TABLE constituencies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    state VARCHAR(255) NOT NULL,
    district VARCHAR(255),
    country VARCHAR(100) NOT NULL DEFAULT 'India',
    total_registered_voters INTEGER,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_constituencies_code ON constituencies(code);
CREATE INDEX idx_constituencies_state ON constituencies(state);

-- ============================================================
-- TABLE: result_files
-- ============================================================

CREATE TABLE result_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    constituency_id UUID NOT NULL REFERENCES constituencies(id) ON DELETE RESTRICT,
    uploaded_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    original_filename VARCHAR(500) NOT NULL,
    stored_filename VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    status file_status NOT NULL DEFAULT 'uploaded',
    election_date DATE NOT NULL,
    election_type VARCHAR(100) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}',
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_result_files_constituency ON result_files(constituency_id);
CREATE INDEX idx_result_files_uploaded_by ON result_files(uploaded_by);
CREATE INDEX idx_result_files_status ON result_files(status);
CREATE INDEX idx_result_files_election_date ON result_files(election_date);

-- ============================================================
-- TABLE: hash_records
-- ============================================================

CREATE TABLE hash_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    result_file_id UUID NOT NULL REFERENCES result_files(id) ON DELETE RESTRICT,
    sha256_hash VARCHAR(64) NOT NULL,
    hash_algorithm VARCHAR(20) NOT NULL DEFAULT 'SHA-256',
    file_size_bytes BIGINT NOT NULL,
    digital_signature TEXT,
    signed_by UUID REFERENCES users(id),
    blockchain_tx_id VARCHAR(255),
    blockchain_block_number BIGINT,
    blockchain_timestamp TIMESTAMPTZ,
    blockchain_network VARCHAR(100) DEFAULT 'hyperledger-fabric',
    is_on_blockchain BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_hash_records_sha256 ON hash_records(sha256_hash);
CREATE INDEX idx_hash_records_result_file ON hash_records(result_file_id);
CREATE INDEX idx_hash_records_blockchain_tx ON hash_records(blockchain_tx_id);

-- ============================================================
-- TABLE: audit_logs
-- ============================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action audit_action NOT NULL,
    resource_type VARCHAR(100),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    details JSONB DEFAULT '{}',
    success BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- ============================================================
-- TABLE: verification_requests
-- ============================================================

CREATE TABLE verification_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    submitted_hash VARCHAR(64) NOT NULL,
    submitted_filename VARCHAR(500),
    submitted_file_size BIGINT,
    matched_hash_record_id UUID REFERENCES hash_records(id),
    status verification_status NOT NULL DEFAULT 'pending',
    requester_ip INET,
    blockchain_verified BOOLEAN DEFAULT FALSE,
    blockchain_query_tx_id VARCHAR(255),
    result_details JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_verification_requests_hash ON verification_requests(submitted_hash);
CREATE INDEX idx_verification_requests_status ON verification_requests(status);
CREATE INDEX idx_verification_requests_created ON verification_requests(created_at);

-- ============================================================
-- TRIGGER: auto-update updated_at columns
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_constituencies_updated_at
    BEFORE UPDATE ON constituencies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_result_files_updated_at
    BEFORE UPDATE ON result_files
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- SEED DATA: Default admin user (password: change-me-immediately)
-- ============================================================

INSERT INTO users (email, password_hash, full_name, role, organization)
VALUES (
    'admin@election-audit.gov',
    -- bcrypt hash of 'change-me-immediately'
    '$2b$12$LJ3m4ys1GnHyMXbGOpW9PeRNsEMOG1GZmPqXJVJBbHDHSqN0MxNSW',
    'System Administrator',
    'super_admin',
    'Election Commission'
);
