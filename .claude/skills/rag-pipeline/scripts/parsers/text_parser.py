"""
Text Parser for RAG Pipeline

Handles TXT and CSV file parsing.
"""

import csv
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """Parser for TXT and CSV files"""

    SUPPORTED_FORMATS = ['txt', 'csv']

    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports given file format"""
        return file_extension.lower() in self.SUPPORTED_FORMATS

    def parse(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse text/CSV file and return structured content.

        Args:
            file_path: Path to text/CSV file
            options: Parsing options
                - encoding: str = 'utf-8' - File encoding
                - csv_delimiter: str = ',' - CSV delimiter character
                - csv_has_header: bool = True - CSV has header row
                - preserve_structure: bool = False - Keep line breaks

        Returns:
            ParseResult with extracted content and metadata
        """
        if not self.validate_file(file_path):
            return ParseResult(
                content="",
                metadata={},
                success=False,
                error=f"File validation failed: {file_path}"
            )

        options = options or {}
        encoding = options.get('encoding', 'utf-8')
        file_extension = Path(file_path).suffix.lstrip('.').lower()

        try:
            if file_extension == 'csv':
                return self._parse_csv(file_path, options, encoding)
            else:
                return self._parse_txt(file_path, options, encoding)

        except UnicodeDecodeError as e:
            logger.warning(f"UTF-8 decode failed, trying latin-1: {e}")
            try:
                return self.parse(file_path, {**options, 'encoding': 'latin-1'})
            except Exception as e2:
                logger.error(f"Failed to parse with alternative encoding: {e2}")
                return ParseResult(
                    content="",
                    metadata=self.extract_metadata(file_path),
                    success=False,
                    error=f"Encoding error: {str(e)}"
                )
        except Exception as e:
            logger.error(f"Error parsing text file {file_path}: {e}")
            return ParseResult(
                content="",
                metadata=self.extract_metadata(file_path),
                success=False,
                error=f"Parse error: {str(e)}"
            )

    def _parse_txt(self, file_path: str, options: Dict[str, Any], encoding: str) -> ParseResult:
        """Parse plain text file"""
        preserve_structure = options.get('preserve_structure', False)

        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()

        if not preserve_structure:
            # Normalize whitespace
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            content = '\n'.join(lines)

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['line_count'] = content.count('\n') + 1
        metadata['char_count'] = len(content)
        metadata['encoding'] = encoding

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )

    def _parse_csv(self, file_path: str, options: Dict[str, Any], encoding: str) -> ParseResult:
        """Parse CSV file"""
        delimiter = options.get('csv_delimiter', ',')
        has_header = options.get('csv_has_header', True)

        rows = []
        headers = []

        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.reader(f, delimiter=delimiter)

            if has_header:
                headers = next(reader, [])

            for row in reader:
                rows.append(row)

        # Convert to text content
        content_parts = []

        if has_header:
            content_parts.append(f"Headers: {', '.join(headers)}")
            content_parts.append("")

        for i, row in enumerate(rows, 1):
            if has_header and headers:
                row_text = []
                for j, value in enumerate(row):
                    if j < len(headers):
                        row_text.append(f"{headers[j]}: {value}")
                    else:
                        row_text.append(value)
                content_parts.append(f"Row {i}: " + ", ".join(row_text))
            else:
                content_parts.append(f"Row {i}: " + ", ".join(row))

        content = "\n".join(content_parts)

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['row_count'] = len(rows)
        metadata['column_count'] = len(headers) if headers else (len(rows[0]) if rows else 0)
        metadata['headers'] = headers
        metadata['csv_delimiter'] = delimiter
        metadata['encoding'] = encoding

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )
