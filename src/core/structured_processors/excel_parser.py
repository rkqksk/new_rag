"""
Excel Parser
Excel 파일 자동 파싱 및 제품 데이터 추출

목적: Excel 파일(.xlsx, .xls)을 읽어 제품 데이터로 변환
전략:
- pandas + openpyxl로 파일 읽기
- SchemaDetector로 컬럼 자동 인식
- Multi-sheet 처리
- 데이터 검증 및 정제
"""

import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

from src.core.structured_processors.schema_detector import SchemaDetector
from src.core.chunk_templates import FieldType

logger = logging.getLogger(__name__)


class ExcelParser:
    """Excel 파일 파서"""

    def __init__(self):
        self.detector = SchemaDetector()

    def parse_file(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        auto_detect_header: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Excel 파일 파싱

        Args:
            file_path: Excel 파일 경로
            sheet_name: 시트 이름 (None이면 모든 시트)
            auto_detect_header: 헤더 행 자동 탐지

        Returns:
            List[Dict]: 제품 데이터 리스트
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing Excel file: {file_path}")

        # Excel 파일 읽기
        try:
            excel_file = pd.ExcelFile(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {e}")

        # 시트 목록
        sheet_names = [sheet_name] if sheet_name else excel_file.sheet_names
        logger.info(f"Found {len(sheet_names)} sheet(s): {sheet_names}")

        all_products = []

        for sheet in sheet_names:
            logger.info(f"Processing sheet: {sheet}")
            products = self._parse_sheet(excel_file, sheet, auto_detect_header)
            all_products.extend(products)
            logger.info(f"  → Extracted {len(products)} products")

        logger.info(f"Total products extracted: {len(all_products)}")
        return all_products

    def _parse_sheet(
        self,
        excel_file: pd.ExcelFile,
        sheet_name: str,
        auto_detect_header: bool
    ) -> List[Dict[str, Any]]:
        """
        단일 시트 파싱

        Args:
            excel_file: pd.ExcelFile 객체
            sheet_name: 시트 이름
            auto_detect_header: 헤더 자동 탐지

        Returns:
            제품 데이터 리스트
        """
        # 시트 읽기 (헤더 없이)
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

        if df.empty:
            logger.warning(f"Sheet '{sheet_name}' is empty")
            return []

        # 헤더 행 탐지
        if auto_detect_header:
            header_row = self.detector.detect_header_row(df)
            logger.info(f"  Detected header row: {header_row}")
        else:
            header_row = 0

        # 헤더를 사용하여 다시 읽기
        df = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)

        # 스키마 탐지
        schema = self.detector.detect_schema(df.columns.tolist())
        logger.info(f"  Schema detection: {len(schema)} columns mapped")

        # 스키마 유효성 검증
        if not self.detector.validate_schema(schema):
            logger.warning(f"  Invalid schema (missing required fields)")
            logger.warning(f"  Detected: {[ft.value for _, (ft, _) in schema.items()]}")
            return []

        # DataFrame → 제품 데이터 변환
        products = self._dataframe_to_products(df, schema)

        return products

    def _dataframe_to_products(
        self,
        df: pd.DataFrame,
        schema: Dict[str, Tuple[FieldType, float]]
    ) -> List[Dict[str, Any]]:
        """
        DataFrame을 제품 데이터 리스트로 변환

        Args:
            df: pandas DataFrame
            schema: 컬럼 → (FieldType, confidence) 매핑

        Returns:
            제품 데이터 리스트
        """
        products = []

        # 컬럼명 → FieldType 매핑
        column_to_field = {col: field_type for col, (field_type, _) in schema.items()}

        for index, row in df.iterrows():
            product = {}

            for column, field_type in column_to_field.items():
                value = row[column]

                # NaN/None 처리
                if pd.isna(value):
                    continue

                # 데이터 타입 변환 및 정제
                cleaned_value = self._clean_value(value, field_type)

                if cleaned_value is not None:
                    # FieldType.value를 키로 사용
                    product[field_type.value] = cleaned_value

            # 빈 제품 스킵
            if product:
                products.append(product)

        return products

    def _clean_value(self, value: Any, field_type: FieldType) -> Optional[Any]:
        """
        값 정제 (데이터 타입 변환, 공백 제거 등)

        Args:
            value: 원본 값
            field_type: 필드 타입

        Returns:
            정제된 값
        """
        # 문자열 변환
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None

        # 숫자 필드
        if field_type in [FieldType.MOQ, FieldType.WEIGHT]:
            try:
                if isinstance(value, str):
                    # 숫자 추출 (쉼표 제거)
                    value = value.replace(',', '').replace(' ', '')
                    # 단위 제거 (ea, 개, pcs 등)
                    import re
                    match = re.search(r'([\d.]+)', value)
                    if match:
                        value = match.group(1)
                return int(float(value))
            except (ValueError, AttributeError):
                logger.debug(f"Failed to convert '{value}' to int for {field_type.value}")
                return None

        # 가격 필드
        if field_type in [FieldType.PRICE, FieldType.SUPPLY_PRICE, FieldType.SELLING_PRICE]:
            try:
                if isinstance(value, str):
                    # 숫자 추출
                    value = value.replace(',', '').replace(' ', '').replace('원', '').replace('$', '')
                    import re
                    match = re.search(r'([\d.]+)', value)
                    if match:
                        value = match.group(1)
                return float(value)
            except (ValueError, AttributeError):
                logger.debug(f"Failed to convert '{value}' to float for {field_type.value}")
                return None

        # 문자열 필드 (기본)
        return str(value)

    def get_sheet_names(self, file_path: str) -> List[str]:
        """
        Excel 파일의 시트 목록 반환

        Args:
            file_path: Excel 파일 경로

        Returns:
            시트 이름 리스트
        """
        excel_file = pd.ExcelFile(file_path)
        return excel_file.sheet_names


if __name__ == "__main__":
    # Test Excel parser
    import tempfile
    import openpyxl

    print("=" * 80)
    print("EXCEL PARSER TEST")
    print("=" * 80)

    # Create test Excel file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False, mode='wb') as f:
        temp_path = f.name

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"

    # Header
    ws.append(["제품명", "제품코드", "용량(ml)", "재질", "가격(원)", "최소주문수량", "제조사", "원산지"])

    # Sample data
    ws.append(["100ml PE 보틀", "BE100-001", "100", "PE", "1,200", "5,000개", "금양실업", "한국"])
    ws.append(["200ml PET 보틀", "BE200-002", "200", "PET", "1,500", "3,000ea", "청진코리아", "중국"])
    ws.append(["24파이 캡", "CA024-001", "", "PP", "150", "10,000", "금양실업", "한국"])

    wb.save(temp_path)

    print(f"\n[Test] Created test Excel file: {temp_path}")

    # Parse
    parser = ExcelParser()
    products = parser.parse_file(temp_path, auto_detect_header=True)

    print(f"\nExtracted {len(products)} products:")
    print("-" * 80)

    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.get('product_name', 'N/A')}")
        for key, value in product.items():
            print(f"   {key:20s}: {value}")

    # Cleanup
    import os
    os.unlink(temp_path)

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
