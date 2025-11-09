"""
HashiCorp Vault Secret Management (v7.0.0)
===========================================

Centralized secret management with Vault.

Features:
- Secret storage and retrieval
- Dynamic secrets
- Encryption as a service
- Secret rotation
- Audit logging

Version: v7.0.0
"""

import logging
import os
from typing import Any, Dict, Optional

try:
    import hvac
    VAULT_AVAILABLE = True
except ImportError:
    VAULT_AVAILABLE = False
    hvac = None

logger = logging.getLogger(__name__)


# ============================================================================
# Vault Client
# ============================================================================


class VaultClient:
    """
    HashiCorp Vault client for secret management

    Features:
    - KV secrets v2
    - Dynamic database credentials
    - Transit encryption
    """

    def __init__(
        self,
        url: str = "http://localhost:8200",
        token: str = "root",
        mount_point: str = "secret",
    ):
        """
        Initialize Vault client

        Args:
            url: Vault server URL
            token: Vault token
            mount_point: KV mount point
        """
        if not VAULT_AVAILABLE:
            logger.warning("hvac not installed. Vault disabled.")
            self.client = None
            return

        try:
            self.client = hvac.Client(url=url, token=token)
            self.mount_point = mount_point

            if self.client.is_authenticated():
                logger.info(f"✅ Vault connected: {url}")
            else:
                logger.error("Vault authentication failed")
                self.client = None
        except Exception as e:
            logger.error(f"Failed to connect to Vault: {e}")
            self.client = None

    # ========================================================================
    # KV Secrets v2
    # ========================================================================

    def create_or_update_secret(
        self, path: str, secret: Dict[str, Any]
    ) -> bool:
        """
        Create or update secret

        Args:
            path: Secret path
            secret: Secret data

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=self.mount_point,
            )
            logger.info(f"Stored secret: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to store secret: {e}")
            return False

    def read_secret(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Read secret

        Args:
            path: Secret path

        Returns:
            Secret data or None
        """
        if not self.client:
            return None

        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self.mount_point,
            )
            return response["data"]["data"]
        except Exception as e:
            logger.error(f"Failed to read secret: {e}")
            return None

    def delete_secret(self, path: str) -> bool:
        """
        Delete secret

        Args:
            path: Secret path

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=path,
                mount_point=self.mount_point,
            )
            logger.info(f"Deleted secret: {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret: {e}")
            return False

    def list_secrets(self, path: str = "") -> Optional[List[str]]:
        """
        List secrets at path

        Args:
            path: Secret path

        Returns:
            List of secret names or None
        """
        if not self.client:
            return None

        try:
            response = self.client.secrets.kv.v2.list_secrets(
                path=path,
                mount_point=self.mount_point,
            )
            return response["data"]["keys"]
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return None

    # ========================================================================
    # Convenience Methods
    # ========================================================================

    def get_database_credentials(
        self, role: str = "rag-enterprise"
    ) -> Optional[Dict[str, str]]:
        """
        Get dynamic database credentials

        Args:
            role: Database role

        Returns:
            Credentials dict with username and password
        """
        if not self.client:
            return None

        try:
            response = self.client.secrets.database.generate_credentials(name=role)
            return {
                "username": response["data"]["username"],
                "password": response["data"]["password"],
            }
        except Exception as e:
            logger.error(f"Failed to get database credentials: {e}")
            return None

    def encrypt_data(self, plaintext: str, key_name: str = "rag-key") -> Optional[str]:
        """
        Encrypt data using Transit engine

        Args:
            plaintext: Data to encrypt
            key_name: Encryption key name

        Returns:
            Ciphertext or None
        """
        if not self.client:
            return None

        try:
            import base64
            encoded = base64.b64encode(plaintext.encode()).decode()
            response = self.client.secrets.transit.encrypt_data(
                name=key_name,
                plaintext=encoded,
            )
            return response["data"]["ciphertext"]
        except Exception as e:
            logger.error(f"Failed to encrypt: {e}")
            return None

    def decrypt_data(self, ciphertext: str, key_name: str = "rag-key") -> Optional[str]:
        """
        Decrypt data using Transit engine

        Args:
            ciphertext: Encrypted data
            key_name: Encryption key name

        Returns:
            Plaintext or None
        """
        if not self.client:
            return None

        try:
            import base64
            response = self.client.secrets.transit.decrypt_data(
                name=key_name,
                ciphertext=ciphertext,
            )
            decoded = base64.b64decode(response["data"]["plaintext"]).decode()
            return decoded
        except Exception as e:
            logger.error(f"Failed to decrypt: {e}")
            return None


# ============================================================================
# Singleton Instance
# ============================================================================

_vault_client: Optional[VaultClient] = None


def get_vault_client() -> VaultClient:
    """Get or create Vault client singleton"""
    global _vault_client

    if _vault_client is None:
        url = os.getenv("VAULT_ADDR", "http://localhost:8200")
        token = os.getenv("VAULT_TOKEN", "root")
        mount_point = os.getenv("VAULT_MOUNT_POINT", "secret")

        _vault_client = VaultClient(
            url=url,
            token=token,
            mount_point=mount_point,
        )

    return _vault_client


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize client
    client = get_vault_client()

    # Store secret
    client.create_or_update_secret(
        path="database/postgres",
        secret={"username": "postgres", "password": "secret123"},
    )

    # Read secret
    secret = client.read_secret("database/postgres")
    print(f"Secret: {secret}")

    # Encrypt data
    ciphertext = client.encrypt_data("sensitive data")
    print(f"Encrypted: {ciphertext}")

    # Decrypt data
    plaintext = client.decrypt_data(ciphertext)
    print(f"Decrypted: {plaintext}")
