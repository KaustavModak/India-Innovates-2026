"""
Application configuration via Pydantic Settings.
Loads from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Election Audit API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://audit_user:audit_pass@localhost:5432/election_audit"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300

    # JWT
    JWT_SECRET_KEY: str = "CHANGE-THIS-TO-A-SECURE-SECRET-KEY-IN-PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: str = "pdf,csv,xlsx,json,xml"

    # Blockchain (Hyperledger Fabric)
    HLF_PEER_ENDPOINT: str = "localhost:7051"
    HLF_ORDERER_ENDPOINT: str = "localhost:7050"
    HLF_CHANNEL_NAME: str = "electionchannel"
    HLF_CHAINCODE_NAME: str = "election_audit"
    HLF_MSP_ID: str = "Org1MSP"
    HLF_CERT_PATH: str = "./crypto/cert.pem"
    HLF_KEY_PATH: str = "./crypto/key.pem"
    HLF_TLS_CERT_PATH: str = "./crypto/tls-cert.pem"

    # Security
    CORS_ORIGINS: str = "http://localhost:3000,https://audit.election.gov"
    RATE_LIMIT_PER_MINUTE: int = 60

    # MFA
    MFA_ISSUER_NAME: str = "ElectionAudit"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
