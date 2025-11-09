"""
Google Drive Integration for Phase 7.1
Automated data ingestion from Google Drive
"""

import io
import logging
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class DriveFile:
    """Google Drive file metadata"""

    id: str
    name: str
    mime_type: str
    size: int
    created_time: str
    modified_time: str
    web_view_link: Optional[str] = None
    parents: Optional[List[str]] = None


@dataclass
class DownloadResult:
    """Download result"""

    file: DriveFile
    local_path: str
    success: bool
    error: Optional[str] = None


class GoogleDriveIntegration:
    """
    Google Drive Integration Service

    Features:
    - OAuth2 authentication
    - List files and folders
    - Download files (PDFs, images, Excel, etc.)
    - Upload processed results
    - Folder synchronization
    - Incremental updates

    Example:
        >>> drive = GoogleDriveIntegration(credentials_path="credentials.json")
        >>> await drive.authenticate()
        >>>
        >>> # List files in folder
        >>> files = await drive.list_files(folder_id="abc123", mime_type="application/pdf")
        >>>
        >>> # Download files
        >>> results = await drive.download_files(files, output_dir="/data/downloads")
        >>>
        >>> # Upload results
        >>> await drive.upload_file("processed.json", folder_id="abc123")
    """

    def __init__(
        self,
        credentials_path: str = "credentials.json",
        token_path: str = "token.json",
        scopes: Optional[List[str]] = None,
    ):
        """
        Initialize Google Drive Integration

        Args:
            credentials_path: Path to Google OAuth2 credentials JSON
            token_path: Path to store access token
            scopes: OAuth2 scopes (default: drive.readonly)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path

        if scopes is None:
            self.scopes = [
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/drive.file",
            ]
        else:
            self.scopes = scopes

        self.service = None
        self.credentials = None

        logger.info("✅ GoogleDriveIntegration initialized")

    async def authenticate(self) -> bool:
        """
        Authenticate with Google Drive API

        Returns:
            True if authentication successful

        Example:
            >>> success = await drive.authenticate()
            >>> if success:
            ...     print("Authenticated!")
        """
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None

            # Load existing token
            if os.path.exists(self.token_path):
                creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)

            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.scopes
                    )
                    creds = flow.run_local_server(port=0)

                # Save token
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())

            # Build service
            self.service = build("drive", "v3", credentials=creds)
            self.credentials = creds

            logger.info("✅ Google Drive authentication successful")
            return True

        except Exception as e:
            logger.error(f"❌ Google Drive authentication failed: {e}")
            return False

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None,
        name_contains: Optional[str] = None,
        page_size: int = 100,
    ) -> List[DriveFile]:
        """
        List files in Google Drive

        Args:
            folder_id: Optional folder ID to list from
            mime_type: Optional MIME type filter (e.g., "application/pdf")
            name_contains: Optional name filter
            page_size: Results per page (max 1000)

        Returns:
            List of DriveFile objects

        Example:
            >>> # List all PDFs in folder
            >>> files = await drive.list_files(
            ...     folder_id="abc123",
            ...     mime_type="application/pdf"
            ... )
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        # Build query
        query_parts = []

        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")

        if mime_type:
            query_parts.append(f"mimeType='{mime_type}'")

        if name_contains:
            query_parts.append(f"name contains '{name_contains}'")

        # Add not trashed
        query_parts.append("trashed=false")

        query = " and ".join(query_parts)

        # Execute request
        try:
            results = (
                self.service.files()
                .list(
                    q=query,
                    pageSize=page_size,
                    fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents)",
                )
                .execute()
            )

            items = results.get("files", [])

            # Convert to DriveFile objects
            files = [
                DriveFile(
                    id=item["id"],
                    name=item["name"],
                    mime_type=item["mimeType"],
                    size=int(item.get("size", 0)),
                    created_time=item["createdTime"],
                    modified_time=item["modifiedTime"],
                    web_view_link=item.get("webViewLink"),
                    parents=item.get("parents"),
                )
                for item in items
            ]

            logger.info(f"Found {len(files)} files in Google Drive")
            return files

        except Exception as e:
            logger.error(f"❌ Failed to list files: {e}")
            return []

    async def download_file(self, file: DriveFile, output_path: str) -> DownloadResult:
        """
        Download a file from Google Drive

        Args:
            file: DriveFile object
            output_path: Local path to save file

        Returns:
            DownloadResult

        Example:
            >>> file = files[0]
            >>> result = await drive.download_file(file, "/data/product.pdf")
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            from googleapiclient.http import MediaIoBaseDownload

            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Request file
            request = self.service.files().get_media(fileId=file.id)

            # Download
            fh = io.FileIO(output_path, "wb")
            downloader = MediaIoBaseDownload(fh, request)

            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download progress: {int(status.progress() * 100)}%")

            fh.close()

            logger.info(f"✅ Downloaded: {file.name} → {output_path}")

            return DownloadResult(file=file, local_path=output_path, success=True)

        except Exception as e:
            logger.error(f"❌ Failed to download {file.name}: {e}")
            return DownloadResult(file=file, local_path=output_path, success=False, error=str(e))

    async def download_files(
        self, files: List[DriveFile], output_dir: str, create_subfolder: bool = False
    ) -> List[DownloadResult]:
        """
        Download multiple files

        Args:
            files: List of DriveFile objects
            output_dir: Output directory
            create_subfolder: Create subfolder per file type

        Returns:
            List of DownloadResult

        Example:
            >>> results = await drive.download_files(files, "/data/downloads")
            >>> success_count = sum(1 for r in results if r.success)
        """
        results = []

        for file in files:
            # Determine output path
            if create_subfolder:
                # Group by MIME type
                subdir = file.mime_type.replace("/", "_")
                output_path = os.path.join(output_dir, subdir, file.name)
            else:
                output_path = os.path.join(output_dir, file.name)

            # Download
            result = await self.download_file(file, output_path)
            results.append(result)

        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ Downloaded {success_count}/{len(files)} files")

        return results

    async def upload_file(
        self, file_path: str, folder_id: Optional[str] = None, name: Optional[str] = None
    ) -> Optional[DriveFile]:
        """
        Upload a file to Google Drive

        Args:
            file_path: Local file path
            folder_id: Optional target folder ID
            name: Optional custom name (default: filename)

        Returns:
            DriveFile object if successful, None otherwise

        Example:
            >>> uploaded = await drive.upload_file(
            ...     "processed_data.json",
            ...     folder_id="abc123"
            ... )
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            from googleapiclient.http import MediaFileUpload

            # Determine file name
            if name is None:
                name = os.path.basename(file_path)

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Build metadata
            file_metadata = {"name": name}
            if folder_id:
                file_metadata["parents"] = [folder_id]

            # Upload
            media = MediaFileUpload(file_path, mimetype=mime_type)

            file = (
                self.service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name, mimeType, size, createdTime, modifiedTime, webViewLink",
                )
                .execute()
            )

            logger.info(f"✅ Uploaded: {name} (ID: {file['id']})")

            return DriveFile(
                id=file["id"],
                name=file["name"],
                mime_type=file["mimeType"],
                size=int(file.get("size", 0)),
                created_time=file["createdTime"],
                modified_time=file["modifiedTime"],
                web_view_link=file.get("webViewLink"),
            )

        except Exception as e:
            logger.error(f"❌ Failed to upload {file_path}: {e}")
            return None

    async def sync_folder(
        self,
        folder_id: str,
        local_dir: str,
        mime_types: Optional[List[str]] = None,
        incremental: bool = True,
    ) -> Dict[str, Any]:
        """
        Synchronize a Google Drive folder to local directory

        Args:
            folder_id: Google Drive folder ID
            local_dir: Local directory path
            mime_types: Optional MIME type filters
            incremental: Only download new/updated files

        Returns:
            Sync statistics

        Example:
            >>> stats = await drive.sync_folder(
            ...     folder_id="abc123",
            ...     local_dir="/data/products",
            ...     mime_types=["application/pdf", "image/jpeg"]
            ... )
        """
        os.makedirs(local_dir, exist_ok=True)

        # List remote files
        all_files = []
        if mime_types:
            for mime_type in mime_types:
                files = await self.list_files(folder_id=folder_id, mime_type=mime_type)
                all_files.extend(files)
        else:
            all_files = await self.list_files(folder_id=folder_id)

        # Incremental sync: check existing files
        if incremental:
            existing_files = {f.name: f for f in all_files}
            to_download = []

            for file in all_files:
                local_path = os.path.join(local_dir, file.name)
                if not os.path.exists(local_path):
                    to_download.append(file)
                else:
                    # Check modification time
                    # (simplified: could compare timestamps)
                    pass

            files_to_download = to_download
        else:
            files_to_download = all_files

        # Download
        results = await self.download_files(files_to_download, local_dir)

        # Statistics
        stats = {
            "total_remote_files": len(all_files),
            "downloaded": len(files_to_download),
            "success": sum(1 for r in results if r.success),
            "failed": sum(1 for r in results if not r.success),
            "skipped": len(all_files) - len(files_to_download),
        }

        logger.info(
            f"✅ Folder sync complete: "
            f"{stats['success']} downloaded, "
            f"{stats['skipped']} skipped, "
            f"{stats['failed']} failed"
        )

        return stats

    def get_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        return {
            "authenticated": self.service is not None,
            "credentials_path": self.credentials_path,
            "scopes": self.scopes,
        }

    def __repr__(self):
        auth_status = "authenticated" if self.service else "not authenticated"
        return f"GoogleDriveIntegration({auth_status})"
