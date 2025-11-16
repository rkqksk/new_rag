"""
Cloud Integration Services for Phase 7
Google Drive, S3, and automated data pipeline
"""

from .automated_pipeline import AutomatedDataPipeline, PipelineConfig, PipelineResult
from .google_drive_integration import DownloadResult, DriveFile, GoogleDriveIntegration
from .s3_integration import S3DownloadResult, S3Integration, S3Object

__all__ = [
    # Google Drive
    "GoogleDriveIntegration",
    "DriveFile",
    "DownloadResult",
    # S3
    "S3Integration",
    "S3Object",
    "S3DownloadResult",
    # Automated Pipeline
    "AutomatedDataPipeline",
    "PipelineConfig",
    "PipelineResult",
]
