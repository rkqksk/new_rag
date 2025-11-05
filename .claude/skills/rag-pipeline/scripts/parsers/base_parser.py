"""
Base Parser Module for RAG Pipeline

Provides abstract base class for document parsers with standardized interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ParseResult:
    """Standardized parsing result container"""

    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunks: Optional[List[Dict[str, Any]]] = None,
        success: bool = True,
        error: Optional[str] = None
    ):
        self.content = content
        self.metadata = metadata
        self.chunks = chunks or []
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'chunks': self.chunks,
            'success': self.success,
            'error': self.error
        }


class BaseParser(ABC):
    """Abstract base class for document parsers"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser with configuration.

        Args:
            config: Parser-specific configuration options
        """
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def parse(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse document and return structured content.

        Args:
            file_path: Path to document file
            options: Parsing options (OCR, tables, etc.)

        Returns:
            ParseResult with content and metadata
        """
        pass

    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if parser supports given file format.

        Args:
            file_extension: File extension (e.g., 'pdf', 'docx')

        Returns:
            True if format is supported
        """
        pass

    def validate_file(self, file_path: str) -> bool:
        """
        Validate file exists and is readable.

        Args:
            file_path: Path to file

        Returns:
            True if file is valid
        """
        path = Path(file_path)
        if not path.exists():
            self.logger.error(f"File not found: {file_path}")
            return False

        if not path.is_file():
            self.logger.error(f"Not a file: {file_path}")
            return False

        if not path.stat().st_size > 0:
            self.logger.warning(f"File is empty: {file_path}")
            return False

        return True

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic file metadata.

        Args:
            file_path: Path to file

        Returns:
            Dictionary with file metadata
        """
        path = Path(file_path)
        stat = path.stat()

        return {
            'file_name': path.name,
            'file_path': str(path.absolute()),
            'file_extension': path.suffix.lstrip('.'),
            'file_size_bytes': stat.st_size,
            'file_modified': stat.st_mtime,
            'parser': self.__class__.__name__
        }
