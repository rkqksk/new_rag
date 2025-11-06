"""Excel and CSV Parser with OCR Support"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import pandas as pd
from PIL import Image
import io

logger = logging.getLogger(__name__)


class ExcelParser:
    """
    Parse Excel and CSV files.
    
    Features:
    - Read Excel/CSV directly
    - Convert Excel screenshots to data via OCR
    - Handle multiple sheets
    - Auto-detect headers
    """
    
    def __init__(self, ocr_engine=None, preprocessor=None):
        """
        Initialize Excel parser.
        
        Args:
            ocr_engine: OCR engine instance
            preprocessor: Image preprocessor instance
        """
        self.ocr_engine = ocr_engine
        self.preprocessor = preprocessor
    
    def parse_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Parse Excel file.
        
        Args:
            file_path: Path to Excel file
            sheet_name: Specific sheet name (None = all sheets)
            
        Returns:
            List of dictionaries (one per row)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        try:
            # Read Excel
            if sheet_name:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                dfs = {sheet_name: df}
            else:
                dfs = pd.read_excel(file_path, sheet_name=None)
            
            # Convert to list of dicts
            all_records = []
            for sheet, df in dfs.items():
                records = df.to_dict('records')
                for record in records:
                    record['_sheet_name'] = sheet
                    all_records.append(record)
            
            logger.info(f"Excel parsed: {len(all_records)} rows from {len(dfs)} sheet(s)")
            return all_records
        
        except Exception as e:
            logger.error(f"Failed to parse Excel: {e}")
            return []
    
    def parse_csv(
        self,
        file_path: str,
        encoding: str = 'utf-8',
        delimiter: str = ','
    ) -> List[Dict[str, Any]]:
        """
        Parse CSV file.
        
        Args:
            file_path: Path to CSV file
            encoding: File encoding
            delimiter: CSV delimiter
            
        Returns:
            List of dictionaries (one per row)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        try:
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            records = df.to_dict('records')
            
            logger.info(f"CSV parsed: {len(records)} rows")
            return records
        
        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            return []
    
    def parse_excel_screenshot(
        self,
        image_path: str
    ) -> List[Dict[str, Any]]:
        """
        Parse Excel screenshot using OCR.
        
        Args:
            image_path: Path to Excel screenshot
            
        Returns:
            Parsed data (best effort)
        """
        if not self.ocr_engine:
            logger.error("OCR engine required for screenshot parsing")
            return []
        
        image_path = Path(image_path)
        if not image_path.exists():
            logger.error(f"Image not found: {image_path}")
            return []
        
        # Load image
        image = Image.open(image_path)
        
        # Preprocess
        if self.preprocessor:
            image = self.preprocessor.optimize_for_ocr(image)
        
        # Run OCR
        ocr_result = self.ocr_engine.extract_text(image)
        
        if not ocr_result.text_boxes:
            logger.warning("No text detected in screenshot")
            return []
        
        # Parse table structure from text boxes
        # Group by Y-coordinate (rows)
        rows = self._group_into_rows(ocr_result.text_boxes)
        
        if not rows:
            return []
        
        # First row is likely headers
        headers = [box.text for box in rows[0]]
        
        # Rest are data rows
        records = []
        for row in rows[1:]:
            record = {}
            for i, box in enumerate(row):
                header = headers[i] if i < len(headers) else f'column_{i}'
                record[header] = box.text
            records.append(record)
        
        logger.info(f"Screenshot parsed: {len(records)} rows, {len(headers)} columns")
        return records
    
    def _group_into_rows(self, text_boxes, y_tolerance: int = 10) -> List[List]:
        """
        Group text boxes into rows based on Y-coordinate.
        
        Args:
            text_boxes: List of TextBox objects
            y_tolerance: Y-coordinate tolerance for same row
            
        Returns:
            List of rows (each row is list of TextBox)
        """
        if not text_boxes:
            return []
        
        # Sort by Y-coordinate
        sorted_boxes = sorted(text_boxes, key=lambda box: box.bbox[1])
        
        # Group into rows
        rows = []
        current_row = [sorted_boxes[0]]
        current_y = sorted_boxes[0].bbox[1]
        
        for box in sorted_boxes[1:]:
            box_y = box.bbox[1]
            
            if abs(box_y - current_y) <= y_tolerance:
                # Same row
                current_row.append(box)
            else:
                # New row
                # Sort current row by X-coordinate
                current_row.sort(key=lambda b: b.bbox[0])
                rows.append(current_row)
                
                current_row = [box]
                current_y = box_y
        
        # Add last row
        if current_row:
            current_row.sort(key=lambda b: b.bbox[0])
            rows.append(current_row)
        
        return rows
    
    def auto_detect_format(self, file_path: str) -> str:
        """
        Auto-detect file format.
        
        Args:
            file_path: Path to file
            
        Returns:
            Format: 'excel', 'csv', 'image', or 'unknown'
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        
        if ext in ['.xlsx', '.xls', '.xlsm']:
            return 'excel'
        elif ext in ['.csv', '.tsv']:
            return 'csv'
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']:
            return 'image'
        else:
            return 'unknown'
    
    def parse_auto(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Auto-detect format and parse.
        
        Args:
            file_path: Path to file
            
        Returns:
            Parsed records
        """
        format_type = self.auto_detect_format(file_path)
        
        if format_type == 'excel':
            return self.parse_excel(file_path)
        elif format_type == 'csv':
            return self.parse_csv(file_path)
        elif format_type == 'image':
            return self.parse_excel_screenshot(file_path)
        else:
            logger.error(f"Unknown file format: {file_path}")
            return []
