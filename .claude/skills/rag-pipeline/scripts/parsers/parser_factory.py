"""
Parser Factory for RAG Pipeline

Provides automatic parser selection and document processing coordination.
"""

import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_parser import BaseParser, ParseResult
from .pdf_parser import PDFParser
from .text_parser import TextParser
from .json_parser import JSONParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating appropriate parsers based on file type"""

    def __init__(self):
        """Initialize factory with available parsers"""
        self._parsers: Dict[str, BaseParser] = {}
        self._register_default_parsers()

    def _register_default_parsers(self):
        """Register default parsers"""
        # PDF parser
        pdf_parser = PDFParser()
        for fmt in pdf_parser.SUPPORTED_FORMATS:
            self._parsers[fmt] = pdf_parser

        # Text/CSV parser
        text_parser = TextParser()
        for fmt in text_parser.SUPPORTED_FORMATS:
            self._parsers[fmt] = text_parser

        # JSON/JSONL parser
        json_parser = JSONParser()
        for fmt in json_parser.SUPPORTED_FORMATS:
            self._parsers[fmt] = json_parser

        logger.info(f"Registered parsers for formats: {list(self._parsers.keys())}")

    def register_parser(self, parser: BaseParser, formats: List[str]):
        """
        Register a custom parser for specific formats.

        Args:
            parser: Parser instance
            formats: List of file extensions this parser handles
        """
        for fmt in formats:
            self._parsers[fmt.lower()] = parser
            logger.info(f"Registered custom parser for format: {fmt}")

    def get_parser(self, file_path: str) -> Optional[BaseParser]:
        """
        Get appropriate parser for file.

        Args:
            file_path: Path to file

        Returns:
            Parser instance or None if no parser available
        """
        extension = Path(file_path).suffix.lstrip('.').lower()

        if extension not in self._parsers:
            logger.warning(f"No parser available for format: {extension}")
            return None

        return self._parsers[extension]

    def parse(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse document using appropriate parser.

        Args:
            file_path: Path to document
            options: Parser-specific options

        Returns:
            ParseResult with content and metadata
        """
        parser = self.get_parser(file_path)

        if not parser:
            extension = Path(file_path).suffix.lstrip('.').lower()
            return ParseResult(
                content="",
                metadata={'file_path': file_path, 'file_extension': extension},
                success=False,
                error=f"No parser available for {extension} files"
            )

        try:
            return parser.parse(file_path, options)
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return ParseResult(
                content="",
                metadata={'file_path': file_path},
                success=False,
                error=f"Parser error: {str(e)}"
            )

    def supported_formats(self) -> List[str]:
        """
        Get list of supported file formats.

        Returns:
            List of file extensions
        """
        return list(self._parsers.keys())


# Global parser factory instance
_parser_factory = None


def get_parser_factory() -> ParserFactory:
    """Get global parser factory instance"""
    global _parser_factory
    if _parser_factory is None:
        _parser_factory = ParserFactory()
    return _parser_factory


def parse_document(file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
    """
    Convenience function to parse document.

    Args:
        file_path: Path to document
        options: Parser options

    Returns:
        ParseResult with content and metadata
    """
    factory = get_parser_factory()
    return factory.parse(file_path, options)
