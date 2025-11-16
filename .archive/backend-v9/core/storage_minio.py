"""
MinIO Object Storage Client (v7.0.0)
=====================================

S3-compatible object storage with MinIO.

Features:
- File upload/download
- Bucket management
- Presigned URLs
- Object metadata
- Versioning support

Version: v7.0.0
"""

import logging
import os
from datetime import timedelta
from io import BytesIO
from typing import BinaryIO, Dict, List, Optional, Union

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    Minio = None
    S3Error = Exception

logger = logging.getLogger(__name__)


# ============================================================================
# MinIO Client
# ============================================================================


class MinIOClient:
    """
    MinIO S3-compatible object storage client

    Features:
    - Bucket operations
    - Object upload/download
    - Presigned URLs
    - Metadata management
    """

    def __init__(
        self,
        endpoint: str = "localhost:9001",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False,
    ):
        """
        Initialize MinIO client

        Args:
            endpoint: MinIO server endpoint
            access_key: Access key
            secret_key: Secret key
            secure: Use HTTPS
        """
        if not MINIO_AVAILABLE:
            logger.warning("minio not installed. Object storage disabled.")
            self.client = None
            return

        try:
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            logger.info(f"✅ MinIO client connected: {endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to MinIO: {e}")
            self.client = None

    # ========================================================================
    # Bucket Operations
    # ========================================================================

    def create_bucket(self, bucket_name: str) -> bool:
        """
        Create bucket if not exists

        Args:
            bucket_name: Bucket name

        Returns:
            True if created or already exists
        """
        if not self.client:
            return False

        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False

    def list_buckets(self) -> List[str]:
        """List all buckets"""
        if not self.client:
            return []

        try:
            buckets = self.client.list_buckets()
            return [bucket.name for bucket in buckets]
        except S3Error as e:
            logger.error(f"Failed to list buckets: {e}")
            return []

    def delete_bucket(self, bucket_name: str) -> bool:
        """Delete empty bucket"""
        if not self.client:
            return False

        try:
            self.client.remove_bucket(bucket_name)
            logger.info(f"Deleted bucket: {bucket_name}")
            return True
        except S3Error as e:
            logger.error(f"Failed to delete bucket {bucket_name}: {e}")
            return False

    # ========================================================================
    # Object Operations
    # ========================================================================

    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Upload file to bucket

        Args:
            bucket_name: Bucket name
            object_name: Object name (path in bucket)
            file_path: Local file path
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.create_bucket(bucket_name)
            self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                content_type=content_type,
                metadata=metadata or {},
            )
            logger.info(f"Uploaded: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            return False

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Upload bytes to bucket

        Args:
            bucket_name: Bucket name
            object_name: Object name
            data: Bytes data
            content_type: MIME type
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.create_bucket(bucket_name)
            data_stream = BytesIO(data)
            self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata=metadata or {},
            )
            logger.info(f"Uploaded bytes: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            return False

    def download_file(
        self, bucket_name: str, object_name: str, file_path: str
    ) -> bool:
        """
        Download file from bucket

        Args:
            bucket_name: Bucket name
            object_name: Object name
            file_path: Local file path

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            logger.info(f"Downloaded: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Download failed: {e}")
            return False

    def download_bytes(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """
        Download object as bytes

        Args:
            bucket_name: Bucket name
            object_name: Object name

        Returns:
            Bytes data or None
        """
        if not self.client:
            return None

        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Download failed: {e}")
            return None

    def list_objects(self, bucket_name: str, prefix: str = "") -> List[str]:
        """
        List objects in bucket

        Args:
            bucket_name: Bucket name
            prefix: Object prefix filter

        Returns:
            List of object names
        """
        if not self.client:
            return []

        try:
            objects = self.client.list_objects(bucket_name, prefix=prefix)
            return [obj.object_name for obj in objects]
        except S3Error as e:
            logger.error(f"List failed: {e}")
            return []

    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete object

        Args:
            bucket_name: Bucket name
            object_name: Object name

        Returns:
            True if successful
        """
        if not self.client:
            return False

        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted: {bucket_name}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Delete failed: {e}")
            return False

    # ========================================================================
    # Presigned URLs
    # ========================================================================

    def get_presigned_url(
        self, bucket_name: str, object_name: str, expires: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for object download

        Args:
            bucket_name: Bucket name
            object_name: Object name
            expires: Expiration time in seconds

        Returns:
            Presigned URL or None
        """
        if not self.client:
            return None

        try:
            url = self.client.presigned_get_object(
                bucket_name, object_name, expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Presigned URL failed: {e}")
            return None

    def get_presigned_upload_url(
        self, bucket_name: str, object_name: str, expires: int = 3600
    ) -> Optional[str]:
        """
        Generate presigned URL for object upload

        Args:
            bucket_name: Bucket name
            object_name: Object name
            expires: Expiration time in seconds

        Returns:
            Presigned URL or None
        """
        if not self.client:
            return None

        try:
            url = self.client.presigned_put_object(
                bucket_name, object_name, expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Presigned upload URL failed: {e}")
            return None

    # ========================================================================
    # Metadata
    # ========================================================================

    def get_object_metadata(self, bucket_name: str, object_name: str) -> Optional[Dict]:
        """
        Get object metadata

        Args:
            bucket_name: Bucket name
            object_name: Object name

        Returns:
            Metadata dict or None
        """
        if not self.client:
            return None

        try:
            stat = self.client.stat_object(bucket_name, object_name)
            return {
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified,
                "metadata": stat.metadata,
            }
        except S3Error as e:
            logger.error(f"Stat failed: {e}")
            return None


# ============================================================================
# Singleton Instance
# ============================================================================

_minio_client: Optional[MinIOClient] = None


def get_minio_client() -> MinIOClient:
    """Get or create MinIO client singleton"""
    global _minio_client

    if _minio_client is None:
        endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9001")
        access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
        secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
        secure = os.getenv("MINIO_SECURE", "false").lower() == "true"

        _minio_client = MinIOClient(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    return _minio_client


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Initialize client
    client = get_minio_client()

    # Create bucket
    client.create_bucket("test-bucket")

    # Upload file
    client.upload_bytes("test-bucket", "test.txt", b"Hello, MinIO!")

    # Download file
    data = client.download_bytes("test-bucket", "test.txt")
    print(f"Downloaded: {data}")

    # Get presigned URL
    url = client.get_presigned_url("test-bucket", "test.txt")
    print(f"Presigned URL: {url}")

    # List objects
    objects = client.list_objects("test-bucket")
    print(f"Objects: {objects}")
