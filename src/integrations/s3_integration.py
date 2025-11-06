"""
S3 Integration for Phase 7.2
Automated data ingestion from AWS S3 and S3-compatible storage
"""

import logging
import os
from typing import List, Dict, Any, Optional, BinaryIO
from dataclasses import dataclass
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class S3Object:
    """S3 object metadata"""
    key: str
    bucket: str
    size: int
    last_modified: str
    etag: str
    storage_class: str = "STANDARD"
    metadata: Optional[Dict[str, str]] = None


@dataclass
class S3DownloadResult:
    """S3 download result"""
    s3_object: S3Object
    local_path: str
    success: bool
    error: Optional[str] = None


class S3Integration:
    """
    S3 Integration Service

    Features:
    - AWS S3 and S3-compatible storage (MinIO, Wasabi, etc.)
    - List objects with prefix filtering
    - Download files (single and batch)
    - Upload processed results
    - Bucket synchronization
    - Presigned URLs for secure access

    Example:
        >>> s3 = S3Integration(
        ...     aws_access_key_id="YOUR_KEY",
        ...     aws_secret_access_key="YOUR_SECRET",
        ...     region="us-east-1"
        ... )
        >>>
        >>> # List objects
        >>> objects = await s3.list_objects(bucket="my-bucket", prefix="products/")
        >>>
        >>> # Download files
        >>> results = await s3.download_objects(objects, output_dir="/data/downloads")
        >>>
        >>> # Upload results
        >>> await s3.upload_file("processed.json", bucket="my-bucket", key="results/processed.json")
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
        use_ssl: bool = True
    ):
        """
        Initialize S3 Integration

        Args:
            aws_access_key_id: AWS access key (or env AWS_ACCESS_KEY_ID)
            aws_secret_access_key: AWS secret key (or env AWS_SECRET_ACCESS_KEY)
            region: AWS region
            endpoint_url: Optional custom endpoint (for S3-compatible storage)
            use_ssl: Use HTTPS
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region = region
        self.endpoint_url = endpoint_url
        self.use_ssl = use_ssl

        self.client = None

        logger.info(
            f"✅ S3Integration initialized "
            f"(region={region}, endpoint={endpoint_url or 'default'})"
        )

    def _get_client(self):
        """Get or create boto3 client"""
        if self.client is None:
            import boto3

            self.client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region,
                endpoint_url=self.endpoint_url,
                use_ssl=self.use_ssl
            )

        return self.client

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        max_keys: int = 1000,
        suffix: Optional[str] = None
    ) -> List[S3Object]:
        """
        List objects in S3 bucket

        Args:
            bucket: Bucket name
            prefix: Key prefix filter (e.g., "products/")
            max_keys: Maximum number of keys to return
            suffix: Optional suffix filter (e.g., ".pdf")

        Returns:
            List of S3Object

        Example:
            >>> # List all PDFs in products folder
            >>> objects = await s3.list_objects(
            ...     bucket="my-bucket",
            ...     prefix="products/",
            ...     suffix=".pdf"
            ... )
        """
        client = self._get_client()

        try:
            # List objects
            response = client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            objects = []

            if 'Contents' in response:
                for item in response['Contents']:
                    # Apply suffix filter if provided
                    if suffix and not item['Key'].endswith(suffix):
                        continue

                    obj = S3Object(
                        key=item['Key'],
                        bucket=bucket,
                        size=item['Size'],
                        last_modified=item['LastModified'].isoformat(),
                        etag=item['ETag'].strip('"'),
                        storage_class=item.get('StorageClass', 'STANDARD')
                    )
                    objects.append(obj)

            logger.info(f"Found {len(objects)} objects in s3://{bucket}/{prefix}")
            return objects

        except Exception as e:
            logger.error(f"❌ Failed to list objects: {e}")
            return []

    async def download_object(
        self,
        s3_object: S3Object,
        output_path: str
    ) -> S3DownloadResult:
        """
        Download an object from S3

        Args:
            s3_object: S3Object to download
            output_path: Local path to save file

        Returns:
            S3DownloadResult

        Example:
            >>> obj = objects[0]
            >>> result = await s3.download_object(obj, "/data/product.pdf")
        """
        client = self._get_client()

        try:
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Download
            client.download_file(
                s3_object.bucket,
                s3_object.key,
                output_path
            )

            logger.info(f"✅ Downloaded: s3://{s3_object.bucket}/{s3_object.key} → {output_path}")

            return S3DownloadResult(
                s3_object=s3_object,
                local_path=output_path,
                success=True
            )

        except Exception as e:
            logger.error(f"❌ Failed to download {s3_object.key}: {e}")
            return S3DownloadResult(
                s3_object=s3_object,
                local_path=output_path,
                success=False,
                error=str(e)
            )

    async def download_objects(
        self,
        s3_objects: List[S3Object],
        output_dir: str,
        preserve_structure: bool = True
    ) -> List[S3DownloadResult]:
        """
        Download multiple objects

        Args:
            s3_objects: List of S3Object to download
            output_dir: Output directory
            preserve_structure: Preserve S3 key structure in local paths

        Returns:
            List of S3DownloadResult

        Example:
            >>> results = await s3.download_objects(objects, "/data/downloads")
            >>> success_count = sum(1 for r in results if r.success)
        """
        results = []

        for s3_object in s3_objects:
            # Determine output path
            if preserve_structure:
                # Keep S3 key structure
                output_path = os.path.join(output_dir, s3_object.key)
            else:
                # Flatten to single directory
                filename = os.path.basename(s3_object.key)
                output_path = os.path.join(output_dir, filename)

            # Download
            result = await self.download_object(s3_object, output_path)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ Downloaded {success_count}/{len(s3_objects)} objects")

        return results

    async def upload_file(
        self,
        file_path: str,
        bucket: str,
        key: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Upload a file to S3

        Args:
            file_path: Local file path
            bucket: Target bucket
            key: S3 key (default: filename)
            metadata: Optional metadata dict
            content_type: Optional content type

        Returns:
            True if successful

        Example:
            >>> success = await s3.upload_file(
            ...     "processed_data.json",
            ...     bucket="my-bucket",
            ...     key="results/processed.json"
            ... )
        """
        client = self._get_client()

        try:
            # Determine key
            if key is None:
                key = os.path.basename(file_path)

            # Determine content type
            if content_type is None:
                import mimetypes
                content_type, _ = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'

            # Build extra args
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata

            # Upload
            client.upload_file(
                file_path,
                bucket,
                key,
                ExtraArgs=extra_args
            )

            logger.info(f"✅ Uploaded: {file_path} → s3://{bucket}/{key}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to upload {file_path}: {e}")
            return False

    async def sync_bucket(
        self,
        bucket: str,
        prefix: str,
        local_dir: str,
        suffix: Optional[str] = None,
        incremental: bool = True
    ) -> Dict[str, Any]:
        """
        Synchronize S3 bucket/prefix to local directory

        Args:
            bucket: Bucket name
            prefix: Key prefix
            local_dir: Local directory
            suffix: Optional suffix filter
            incremental: Only download new/updated files

        Returns:
            Sync statistics

        Example:
            >>> stats = await s3.sync_bucket(
            ...     bucket="my-bucket",
            ...     prefix="products/",
            ...     local_dir="/data/products",
            ...     suffix=".pdf"
            ... )
        """
        os.makedirs(local_dir, exist_ok=True)

        # List remote objects
        s3_objects = await self.list_objects(bucket, prefix, suffix=suffix)

        # Incremental sync: check existing files
        if incremental:
            to_download = []

            for obj in s3_objects:
                local_path = os.path.join(local_dir, obj.key.replace(prefix, '', 1))
                if not os.path.exists(local_path):
                    to_download.append(obj)
                else:
                    # Check size (simplified)
                    local_size = os.path.getsize(local_path)
                    if local_size != obj.size:
                        to_download.append(obj)

            objects_to_download = to_download
        else:
            objects_to_download = s3_objects

        # Download
        results = await self.download_objects(
            objects_to_download,
            local_dir,
            preserve_structure=True
        )

        # Statistics
        stats = {
            'total_remote_objects': len(s3_objects),
            'downloaded': len(objects_to_download),
            'success': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'skipped': len(s3_objects) - len(objects_to_download)
        }

        logger.info(
            f"✅ Bucket sync complete: "
            f"{stats['success']} downloaded, "
            f"{stats['skipped']} skipped, "
            f"{stats['failed']} failed"
        )

        return stats

    async def generate_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
        method: str = "get_object"
    ) -> Optional[str]:
        """
        Generate presigned URL for secure access

        Args:
            bucket: Bucket name
            key: Object key
            expiration: URL expiration in seconds (default: 1 hour)
            method: S3 method (get_object, put_object)

        Returns:
            Presigned URL if successful

        Example:
            >>> url = await s3.generate_presigned_url(
            ...     bucket="my-bucket",
            ...     key="products/product1.pdf",
            ...     expiration=3600
            ... )
        """
        client = self._get_client()

        try:
            url = client.generate_presigned_url(
                method,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )

            logger.debug(f"Generated presigned URL for s3://{bucket}/{key}")
            return url

        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return {
            'region': self.region,
            'endpoint': self.endpoint_url or 'default',
            'use_ssl': self.use_ssl,
            'configured': self.aws_access_key_id is not None
        }

    def __repr__(self):
        endpoint = self.endpoint_url or "AWS S3"
        return f"S3Integration(region={self.region}, endpoint={endpoint})"
