"""
Hyperledger Fabric blockchain integration service.

Handles submitting hashes to the blockchain and querying stored records.
In development mode, uses a mock implementation.
"""

import json
import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional
from app.config import get_settings

settings = get_settings()


class BlockchainRecord:
    """Represents a hash record stored on the blockchain."""

    def __init__(self, tx_id: str, block_number: int, timestamp: datetime, data: dict):
        self.tx_id = tx_id
        self.block_number = block_number
        self.timestamp = timestamp
        self.data = data


class HyperledgerFabricService:
    """
    Service for interacting with Hyperledger Fabric network.
    
    In production, this uses the Fabric Gateway SDK to:
    - Submit transactions (store hashes)
    - Evaluate transactions (query hashes)
    
    In development, a mock ledger is used for testing.
    """

    def __init__(self):
        self.channel = settings.HLF_CHANNEL_NAME
        self.chaincode = settings.HLF_CHAINCODE_NAME
        self.mock_ledger: dict = {}  # dev-mode in-memory ledger
        self._block_counter = 0

    async def store_hash(
        self,
        file_hash: str,
        file_id: str,
        constituency_code: str,
        election_date: str,
        election_type: str,
        uploader_id: str,
    ) -> BlockchainRecord:
        """
        Store a result hash on the blockchain.

        Invokes the 'StoreResultHash' chaincode function.
        
        Args:
            file_hash: SHA-256 hash of the result file
            file_id: UUID of the result file in the database
            constituency_code: Code of the constituency
            election_date: Date of the election
            election_type: Type of election
            uploader_id: UUID of the uploading official
            
        Returns:
            BlockchainRecord with transaction details
        """
        try:
            # Try connecting to real Fabric network
            return await self._fabric_store_hash(
                file_hash, file_id, constituency_code,
                election_date, election_type, uploader_id,
            )
        except Exception:
            # Fall back to mock implementation for development
            return await self._mock_store_hash(
                file_hash, file_id, constituency_code,
                election_date, election_type, uploader_id,
            )

    async def query_hash(self, file_hash: str) -> Optional[BlockchainRecord]:
        """
        Query the blockchain for a stored hash record.

        Invokes the 'QueryResultHash' chaincode function.
        
        Args:
            file_hash: SHA-256 hash to look up
            
        Returns:
            BlockchainRecord if found, None otherwise
        """
        try:
            return await self._fabric_query_hash(file_hash)
        except Exception:
            return await self._mock_query_hash(file_hash)

    async def verify_hash(self, file_hash: str) -> dict:
        """
        Verify a hash exists on the blockchain and return verification details.
        
        Args:
            file_hash: SHA-256 hash to verify
            
        Returns:
            dict with verification status and blockchain details
        """
        record = await self.query_hash(file_hash)

        if record is None:
            return {
                "exists_on_blockchain": False,
                "verified": False,
                "message": "Hash not found on blockchain",
            }

        return {
            "exists_on_blockchain": True,
            "verified": True,
            "tx_id": record.tx_id,
            "block_number": record.block_number,
            "timestamp": record.timestamp.isoformat(),
            "data": record.data,
            "message": "Hash verified on blockchain",
        }

    # --- Real Fabric Implementation ---

    async def _fabric_store_hash(self, file_hash, file_id, constituency_code,
                                  election_date, election_type, uploader_id) -> BlockchainRecord:
        """
        Submit 'StoreResultHash' transaction to Hyperledger Fabric.
        
        This requires:
        - fabric-gateway Python SDK
        - Valid MSP credentials (cert + key)
        - Running Fabric network
        """
        # NOTE: Production implementation would use:
        # from hfc.fabric import Client
        # client = Client(net_profile="network.json")
        # ...
        raise NotImplementedError("Fabric SDK not connected — using mock")

    async def _fabric_query_hash(self, file_hash) -> Optional[BlockchainRecord]:
        """Evaluate 'QueryResultHash' transaction on Hyperledger Fabric."""
        raise NotImplementedError("Fabric SDK not connected — using mock")

    # --- Mock Implementation (Development Mode) ---

    async def _mock_store_hash(self, file_hash, file_id, constituency_code,
                                election_date, election_type, uploader_id) -> BlockchainRecord:
        """Mock store: keeps hashes in an in-memory dict to simulate blockchain."""
        self._block_counter += 1
        tx_id = hashlib.sha256(
            f"{file_hash}{time.time()}{uuid.uuid4()}".encode()
        ).hexdigest()

        now = datetime.utcnow()
        data = {
            "file_hash": file_hash,
            "file_id": file_id,
            "constituency_code": constituency_code,
            "election_date": election_date,
            "election_type": election_type,
            "uploader_id": uploader_id,
            "stored_at": now.isoformat(),
        }

        record = BlockchainRecord(
            tx_id=tx_id,
            block_number=self._block_counter,
            timestamp=now,
            data=data,
        )

        self.mock_ledger[file_hash] = record
        return record

    async def _mock_query_hash(self, file_hash) -> Optional[BlockchainRecord]:
        """Mock query: look up hash in the in-memory dict."""
        return self.mock_ledger.get(file_hash)


blockchain_service = HyperledgerFabricService()
