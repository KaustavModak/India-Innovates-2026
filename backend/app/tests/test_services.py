"""
Tests for the hash generation and verification service.
"""

import os
import tempfile
import pytest
from app.services.hash_service import HashService


class TestHashService:
    """Test suite for the SHA-256 cryptographic hash engine."""

    def test_hash_known_string(self):
        """Verify SHA-256 produces correct hash for known input."""
        data = b"Hello, Election Audit!"
        result = HashService.hash_bytes(data)
        assert result["hash_algorithm"] == "SHA-256"
        assert len(result["sha256_hash"]) == 64
        assert result["file_size_bytes"] == len(data)

    def test_hash_empty_bytes(self):
        """SHA-256 of empty content should match known empty hash."""
        result = HashService.hash_bytes(b"")
        # SHA-256 of empty string
        assert result["sha256_hash"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert result["file_size_bytes"] == 0

    def test_hash_file(self):
        """Test hashing an actual file on disk."""
        content = b"Official Election Results for Constituency ABC-001\nCandidate A: 15000\nCandidate B: 12000"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as f:
            f.write(content)
            f.flush()
            filepath = f.name

        try:
            result = HashService.hash_file(filepath)
            assert result["hash_algorithm"] == "SHA-256"
            assert len(result["sha256_hash"]) == 64
            assert result["file_size_bytes"] == len(content)

            # Verify the file hash matches the bytes hash
            bytes_result = HashService.hash_bytes(content)
            assert result["sha256_hash"] == bytes_result["sha256_hash"]
        finally:
            os.unlink(filepath)

    def test_hash_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            HashService.hash_file("/nonexistent/path/file.csv")

    def test_verify_bytes_valid(self):
        """Verification should pass with correct hash."""
        data = b"Test election data"
        hash_result = HashService.hash_bytes(data)
        
        verify = HashService.verify_bytes(data, hash_result["sha256_hash"])
        assert verify["is_valid"] is True
        assert verify["computed_hash"] == verify["expected_hash"]

    def test_verify_bytes_tampered(self):
        """Verification should fail if data has been modified."""
        original = b"Original election data"
        tampered = b"Tampered election data"

        hash_result = HashService.hash_bytes(original)
        verify = HashService.verify_bytes(tampered, hash_result["sha256_hash"])

        assert verify["is_valid"] is False
        assert verify["computed_hash"] != verify["expected_hash"]

    def test_verify_file(self):
        """Test file verification on disk."""
        content = b"Verified election results"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(content)
            f.flush()
            filepath = f.name

        try:
            hash_result = HashService.hash_file(filepath)
            verify = HashService.verify_file(filepath, hash_result["sha256_hash"])
            assert verify["is_valid"] is True

            # Tamper the file
            with open(filepath, "wb") as f:
                f.write(b"Modified content")

            verify_tampered = HashService.verify_file(filepath, hash_result["sha256_hash"])
            assert verify_tampered["is_valid"] is False
        finally:
            os.unlink(filepath)

    def test_deterministic_hashing(self):
        """Same input always produces same hash."""
        data = b"Deterministic test"
        h1 = HashService.hash_bytes(data)
        h2 = HashService.hash_bytes(data)
        assert h1["sha256_hash"] == h2["sha256_hash"]

    def test_different_inputs_different_hashes(self):
        """Different inputs produce different hashes (collision resistance)."""
        h1 = HashService.hash_bytes(b"Input A")
        h2 = HashService.hash_bytes(b"Input B")
        assert h1["sha256_hash"] != h2["sha256_hash"]


class TestBlockchainService:
    """Test suite for the mock blockchain service."""

    @pytest.mark.asyncio
    async def test_store_and_query_hash(self):
        """Test storing and querying a hash on the mock blockchain."""
        from app.services.blockchain import HyperledgerFabricService

        service = HyperledgerFabricService()
        test_hash = "a" * 64

        record = await service.store_hash(
            file_hash=test_hash,
            file_id="test-file-id",
            constituency_code="TEST-001",
            election_date="2024-01-01",
            election_type="General",
            uploader_id="test-user-id",
        )

        assert record.tx_id is not None
        assert record.block_number > 0
        assert record.data["file_hash"] == test_hash

        # Query it back
        queried = await service.query_hash(test_hash)
        assert queried is not None
        assert queried.tx_id == record.tx_id

    @pytest.mark.asyncio
    async def test_query_nonexistent_hash(self):
        """Querying a non-existent hash should return None."""
        from app.services.blockchain import HyperledgerFabricService

        service = HyperledgerFabricService()
        result = await service.query_hash("b" * 64)
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_hash(self):
        """Test the verification method."""
        from app.services.blockchain import HyperledgerFabricService

        service = HyperledgerFabricService()
        test_hash = "c" * 64

        await service.store_hash(
            file_hash=test_hash,
            file_id="file-1",
            constituency_code="C-001",
            election_date="2024-06-15",
            election_type="State",
            uploader_id="user-1",
        )

        result = await service.verify_hash(test_hash)
        assert result["exists_on_blockchain"] is True
        assert result["verified"] is True

        result_missing = await service.verify_hash("d" * 64)
        assert result_missing["exists_on_blockchain"] is False
        assert result_missing["verified"] is False


class TestPKIService:
    """Test suite for the PKI digital signature service."""

    def test_generate_key_pair(self):
        from app.services.pki_service import PKIService

        keys = PKIService.generate_key_pair()
        assert "-----BEGIN PRIVATE KEY-----" in keys["private_key"]
        assert "-----BEGIN PUBLIC KEY-----" in keys["public_key"]

    def test_sign_and_verify(self):
        from app.services.pki_service import PKIService

        keys = PKIService.generate_key_pair()
        data = "a1b2c3d4e5f6" * 5  # Simulating a hash value

        signature = PKIService.sign_data(data, keys["private_key"])
        assert signature is not None

        is_valid = PKIService.verify_signature(data, signature, keys["public_key"])
        assert is_valid is True

    def test_verify_tampered_data(self):
        from app.services.pki_service import PKIService

        keys = PKIService.generate_key_pair()
        data = "original_hash_value"
        tampered = "tampered_hash_value"

        signature = PKIService.sign_data(data, keys["private_key"])
        is_valid = PKIService.verify_signature(tampered, signature, keys["public_key"])
        assert is_valid is False
