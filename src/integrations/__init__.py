"""
Cloud Integration Services for Phase 7
Google Drive, S3, and automated data pipeline
"""

from .google_drive_integration import (
    GoogleDriveIntegration,
    DriveFile,
    DownloadResult
)
from .s3_integration import (
    S3Integration,
    S3Object,
    S3DownloadResult
)
from .automated_pipeline import (
    AutomatedDataPipeline,
    PipelineConfig,
    PipelineResult
)

__all__ = [
    # Google Drive
    'GoogleDriveIntegration',
    'DriveFile',
    'DownloadResult',

    # S3
    'S3Integration',
    'S3Object',
    'S3DownloadResult',

    # Automated Pipeline
    'AutomatedDataPipeline',
    'PipelineConfig',
    'PipelineResult',
]
