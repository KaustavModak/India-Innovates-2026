"""
SHA-256 Cryptographic Hash Engine.

Generates and verifies cryptographic fingerprints for election result files.
"""

import hashlib
import os
from pathlib import Path
from typing import BinaryIO


class HashService:
    """
    Generates SHA-256 hashes of files for tamper detection.
    
    Uses streaming reads (8KB chunks) to handle arbitrarily large files
    without loading them entirely into memory.
    """

    ALGORITHM = "SHA-256"
    CHUNK_SIZE = 8192  # 8KB chunks for memory-efficient reading

    @staticmethod
    def hash_file(file_path: str) -> dict:
        """
        Generate SHA-256 hash of a file on disk.
        
        Args:
            file_path: Absolute path to the file.
            
        Returns:
            dict with hash, algorithm, and file_size_bytes.
            
        Raises:
            FileNotFoundError: If the file does not exist.
            PermissionError: If the file is not readable.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        sha256 = hashlib.sha256()
        file_size = 0

        with open(path, "rb") as f:
            while True:
                chunk = f.read(HashService.CHUNK_SIZE)
                if not chunk:
                    break
                sha256.update(chunk)
                file_size += len(chunk)

        return {
            "sha256_hash": sha256.hexdigest(),
            "hash_algorithm": HashService.ALGORITHM,
            "file_size_bytes": file_size,
        }

    @staticmethod
    def hash_bytes(data: bytes) -> dict:
        """
        Generate SHA-256 hash from raw bytes (used for uploaded file content).
        
        Args:
            data: Raw file bytes.
            
        Returns:
            dict with hash, algorithm, and file_size_bytes.
        """
        sha256 = hashlib.sha256(data)
        return {
            "sha256_hash": sha256.hexdigest(),
            "hash_algorithm": HashService.ALGORITHM,
            "file_size_bytes": len(data),
        }

    @staticmethod
    def hash_stream(file_obj: BinaryIO) -> dict:
        """
        Generate SHA-256 hash from a file-like stream object.
        
        Args:
            file_obj: A file-like object with read() method.
            
        Returns:
            dict with hash, algorithm, and file_size_bytes.
        """
        sha256 = hashlib.sha256()
        file_size = 0

        while True:
            chunk = file_obj.read(HashService.CHUNK_SIZE)
            if not chunk:
                break
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            sha256.update(chunk)
            file_size += len(chunk)

        return {
            "sha256_hash": sha256.hexdigest(),
            "hash_algorithm": HashService.ALGORITHM,
            "file_size_bytes": file_size,
        }

    @staticmethod
    def verify_file(file_path: str, expected_hash: str) -> dict:
        """
        Verify file integrity by comparing its current hash against an expected hash.
        
        Args:
            file_path: Path to the file to verify.
            expected_hash: The SHA-256 hash to compare against.
            
        Returns:
            dict with is_valid, computed_hash, expected_hash.
        """
        result = HashService.hash_file(file_path)
        computed = result["sha256_hash"]

        return {
            "is_valid": computed == expected_hash.lower(),
            "computed_hash": computed,
            "expected_hash": expected_hash.lower(),
            "file_size_bytes": result["file_size_bytes"],
            "algorithm": HashService.ALGORITHM,
        }

    @staticmethod
    def verify_bytes(data: bytes, expected_hash: str) -> dict:
        """
        Verify byte data integrity against an expected hash.
        
        Args:
            data: Raw bytes to verify.
            expected_hash: The SHA-256 hash to compare against.
            
        Returns:
            dict with is_valid, computed_hash, expected_hash.
        """
        result = HashService.hash_bytes(data)
        computed = result["sha256_hash"]

        return {
            "is_valid": computed == expected_hash.lower(),
            "computed_hash": computed,
            "expected_hash": expected_hash.lower(),
            "file_size_bytes": result["file_size_bytes"],
            "algorithm": HashService.ALGORITHM,
        }


hash_service = HashService()
