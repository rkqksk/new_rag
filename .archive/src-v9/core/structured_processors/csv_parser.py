"""
CSV Parser
CSV 파일 자동 파싱 및 제품 데이터 추출

목적: CSV 파일을 읽어 제품 데이터로 변환
전략:
- pandas로 파일 읽기
- chardet로 인코딩 자동 감지
- SchemaDetector로 컬럼 자동 인식
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import chardet
import pandas as pd

from src.core.structured_processors.excel_parser import ExcelParser

logger = logging.getLogger(__name__)


class CSVParser(ExcelParser):
    """
    CSV 파일 파서 (Excel Parser 상속)

    ExcelParser의 기능을 재사용하면서 CSV 특화 기능 추가
    """

    def parse_file(
        self,
        file_path: str,
        encoding: Optional[str] = None,
        delimiter: str = ",",
        auto_detect_header: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        CSV 파일 파싱

        Args:
            file_path: CSV 파일 경로
            encoding: 인코딩 (None이면 자동 감지)
            delimiter: 구분자 (기본: ',')
            auto_detect_header: 헤더 행 자동 탐지

        Returns:
            List[Dict]: 제품 데이터 리스트
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Parsing CSV file: {file_path}")

        # 인코딩 자동 감지
        if encoding is None:
            encoding = self._detect_encoding(file_path)
            logger.info(f"Detected encoding: {encoding}")

        # CSV 읽기 (헤더 없이)
        try:
            df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, header=None)
        except Exception as e:
            raise ValueError(f"Failed to read CSV file: {e}")

        if df.empty:
            logger.warning("CSV file is empty")
            return []

        # 헤더 행 탐지
        if auto_detect_header:
            header_row = self.detector.detect_header_row(df)
            logger.info(f"Detected header row: {header_row}")
        else:
            header_row = 0

        # 헤더를 사용하여 다시 읽기
        df = pd.read_csv(file_path, encoding=encoding, delimiter=delimiter, header=header_row)

        # 스키마 탐지
        schema = self.detector.detect_schema(df.columns.tolist())
        logger.info(f"Schema detection: {len(schema)} columns mapped")

        # 스키마 유효성 검증
        if not self.detector.validate_schema(schema):
            logger.warning("Invalid schema (missing required fields)")
            logger.warning(f"Detected: {[ft.value for _, (ft, _) in schema.items()]}")
            return []

        # DataFrame → 제품 데이터 변환
        products = self._dataframe_to_products(df, schema)
        logger.info(f"Total products extracted: {len(products)}")

        return products

    def _detect_encoding(self, file_path: Path) -> str:
        """
        파일 인코딩 자동 감지

        Args:
            file_path: 파일 경로

        Returns:
            인코딩 (예: 'utf-8', 'euc-kr', 'cp949')
        """
        with open(file_path, "rb") as f:
            raw_data = f.read(10000)  # 처음 10KB 읽기

        result = chardet.detect(raw_data)
        encoding = result["encoding"]
        confidence = result["confidence"]

        logger.info(f"Encoding detection: {encoding} (confidence: {confidence:.2f})")

        # 한글 인코딩 처리
        if encoding and encoding.lower() in ["euc-kr", "euckr"]:
            encoding = "cp949"  # EUC-KR 대신 CP949 사용 (호환성)

        return encoding or "utf-8"


if __name__ == "__main__":
    # Test CSV parser
    import tempfile

    print("=" * 80)
    print("CSV PARSER TEST")
    print("=" * 80)

    # Create test CSV file (UTF-8)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        temp_path_utf8 = f.name
        f.write("제품명,제품코드,용량(ml),재질,가격(원),최소주문수량,제조사,원산지\n")
        f.write('100ml PE 보틀,BE100-001,100,PE,"1,200","5,000개",금양실업,한국\n')
        f.write('200ml PET 보틀,BE200-002,200,PET,"1,500","3,000ea",청진코리아,중국\n')
        f.write('24파이 캡,CA024-001,,PP,150,"10,000",금양실업,한국\n')

    print(f"\n[Test 1] UTF-8 CSV file: {temp_path_utf8}")

    # Parse
    parser = CSVParser()
    products = parser.parse_file(temp_path_utf8)

    print(f"\nExtracted {len(products)} products:")
    print("-" * 80)

    for i, product in enumerate(products, 1):
        print(f"\n{i}. {product.get('product_name', 'N/A')}")
        for key, value in product.items():
            print(f"   {key:20s}: {value}")

    # Create test CSV file (EUC-KR for Korean compatibility)
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="cp949") as f:
        temp_path_euckr = f.name
        f.write("Product Name,SKU,Capacity (ml),Material,Price ($),MOQ\n")
        f.write("100ml PE Bottle,BE100-001,100,PE,12.00,5000\n")
        f.write("200ml PET Bottle,BE200-002,200,PET,15.00,3000\n")

    print("\n" + "─" * 80)
    print(f"[Test 2] CP949 CSV file: {temp_path_euckr}")

    products2 = parser.parse_file(temp_path_euckr)

    print(f"\nExtracted {len(products2)} products:")
    print("-" * 80)

    for i, product in enumerate(products2, 1):
        print(f"\n{i}. {product.get('product_name', 'N/A')}")
        for key, value in product.items():
            print(f"   {key:20s}: {value}")

    # Cleanup
    import os

    os.unlink(temp_path_utf8)
    os.unlink(temp_path_euckr)

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
