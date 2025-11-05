"""
JSON/JSONL Parser for RAG Pipeline

Handles JSON and JSONL (newline-delimited JSON) document parsing.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from .base_parser import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class JSONParser(BaseParser):
    """Parser for JSON and JSONL (newline-delimited JSON) files"""

    SUPPORTED_FORMATS = ['json', 'jsonl']

    def supports_format(self, file_extension: str) -> bool:
        """Check if parser supports given file format"""
        return file_extension.lower() in self.SUPPORTED_FORMATS

    def parse(self, file_path: str, options: Optional[Dict[str, Any]] = None) -> ParseResult:
        """
        Parse JSON/JSONL file and return structured content.

        Args:
            file_path: Path to JSON/JSONL file
            options: Parsing options
                - flatten: bool = True - Flatten nested structures
                - max_depth: int = 5 - Maximum nesting depth for flattening
                - include_keys: bool = True - Include JSON keys in text content
                - array_as_text: bool = True - Convert arrays to readable text

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
        flatten = options.get('flatten', True)
        max_depth = options.get('max_depth', 5)
        include_keys = options.get('include_keys', True)
        array_as_text = options.get('array_as_text', True)

        try:
            file_extension = Path(file_path).suffix.lstrip('.').lower()

            if file_extension == 'jsonl':
                return self._parse_jsonl(file_path, flatten, max_depth, include_keys, array_as_text)
            else:
                return self._parse_json(file_path, flatten, max_depth, include_keys, array_as_text)

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parse error in {file_path}: {e}")
            return ParseResult(
                content="",
                metadata=self.extract_metadata(file_path),
                success=False,
                error=f"JSON decode error: {str(e)}"
            )
        except Exception as e:
            self.logger.error(f"Error parsing JSON file {file_path}: {e}")
            return ParseResult(
                content="",
                metadata=self.extract_metadata(file_path),
                success=False,
                error=f"Parse error: {str(e)}"
            )

    def _parse_json(
        self,
        file_path: str,
        flatten: bool,
        max_depth: int,
        include_keys: bool,
        array_as_text: bool
    ) -> ParseResult:
        """Parse standard JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert to text content
        content = self._json_to_text(data, flatten, max_depth, include_keys, array_as_text)

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['record_count'] = self._count_records(data)
        metadata['json_type'] = self._detect_json_type(data)
        metadata['keys'] = list(data.keys()) if isinstance(data, dict) else []

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )

    def _parse_jsonl(
        self,
        file_path: str,
        flatten: bool,
        max_depth: int,
        include_keys: bool,
        array_as_text: bool
    ) -> ParseResult:
        """Parse JSONL (newline-delimited JSON) file"""
        records = []
        content_parts = []

        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    record = json.loads(line)
                    records.append(record)

                    # Convert record to text
                    record_text = self._json_to_text(record, flatten, max_depth, include_keys, array_as_text)
                    content_parts.append(f"Record {line_num}:\n{record_text}")

                except json.JSONDecodeError as e:
                    self.logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                    continue

        # Combine all records
        content = "\n\n".join(content_parts)

        # Extract metadata
        metadata = self.extract_metadata(file_path)
        metadata['record_count'] = len(records)
        metadata['json_type'] = 'jsonl'

        # Get common keys across records
        if records and isinstance(records[0], dict):
            all_keys = set()
            for record in records:
                if isinstance(record, dict):
                    all_keys.update(record.keys())
            metadata['keys'] = sorted(list(all_keys))

        return ParseResult(
            content=content,
            metadata=metadata,
            success=True
        )

    def _json_to_text(
        self,
        data: Any,
        flatten: bool,
        max_depth: int,
        include_keys: bool,
        array_as_text: bool,
        current_depth: int = 0
    ) -> str:
        """Convert JSON data to readable text"""
        if current_depth > max_depth:
            return "[Max depth reached]"

        if isinstance(data, dict):
            parts = []
            for key, value in data.items():
                value_text = self._json_to_text(value, flatten, max_depth, include_keys, array_as_text, current_depth + 1)

                if include_keys:
                    parts.append(f"{key}: {value_text}")
                else:
                    parts.append(value_text)

            separator = "\n" if flatten else ", "
            return separator.join(parts)

        elif isinstance(data, list):
            if array_as_text:
                items = [self._json_to_text(item, flatten, max_depth, include_keys, array_as_text, current_depth + 1)
                         for item in data]
                return ", ".join(str(item) for item in items)
            else:
                return str(data)

        elif isinstance(data, (str, int, float, bool)):
            return str(data)

        elif data is None:
            return "null"

        else:
            return str(data)

    def _detect_json_type(self, data: Any) -> str:
        """Detect type of JSON structure"""
        if isinstance(data, dict):
            return "object"
        elif isinstance(data, list):
            if data and isinstance(data[0], dict):
                return "array_of_objects"
            else:
                return "array"
        else:
            return "primitive"

    def _count_records(self, data: Any) -> int:
        """Count number of records in JSON structure"""
        if isinstance(data, dict):
            return 1
        elif isinstance(data, list):
            return len(data)
        else:
            return 1
