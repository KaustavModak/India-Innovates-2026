"""
PKI (Public Key Infrastructure) service for digital signatures.

Signs hash records with the official's private key so that the origin
of every hash submission can be cryptographically verified.
"""

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
import base64


class PKIService:
    """Digital signature service using RSA-2048 + SHA-256."""

    @staticmethod
    def generate_key_pair() -> dict:
        """
        Generate a new RSA-2048 key pair.
        
        Returns:
            dict with 'private_key' and 'public_key' as PEM strings.
        """
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return {
            "private_key": private_pem,
            "public_key": public_pem,
        }

    @staticmethod
    def sign_data(data: str, private_key_pem: str) -> str:
        """
        Sign data using RSA private key with PKCS1v15 + SHA-256.
        
        Args:
            data: The string data to sign (e.g., a hash value).
            private_key_pem: PEM-encoded RSA private key.
            
        Returns:
            Base64-encoded digital signature.
        """
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode("utf-8"),
            password=None,
            backend=default_backend(),
        )

        signature = private_key.sign(
            data.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )

        return base64.b64encode(signature).decode("utf-8")

    @staticmethod
    def verify_signature(data: str, signature_b64: str, public_key_pem: str) -> bool:
        """
        Verify a digital signature using RSA public key.
        
        Args:
            data: The original data that was signed.
            signature_b64: Base64-encoded signature.
            public_key_pem: PEM-encoded RSA public key.
            
        Returns:
            True if the signature is valid, False otherwise.
        """
        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8"),
                backend=default_backend(),
            )

            signature = base64.b64decode(signature_b64)

            public_key.verify(
                signature,
                data.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            return True
        except Exception:
            return False


pki_service = PKIService()
