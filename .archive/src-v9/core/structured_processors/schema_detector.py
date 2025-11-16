"""
Schema Detector
컬럼명 자동 인식 시스템

목적: Excel/CSV 파일의 컬럼명을 분석하여 FieldType으로 자동 매핑
전략:
- 패턴 매칭 (정규식 + 키워드)
- 유사도 기반 매칭 (difflib)
- 신뢰도 점수 (Confidence scoring)
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from src.core.chunk_templates import FieldType


class SchemaDetector:
    """컬럼명 자동 인식기"""

    # 컬럼명 → FieldType 매핑 사전
    COLUMN_PATTERNS = {
        FieldType.PRODUCT_NAME: [
            "제품명",
            "product name",
            "품명",
            "상품명",
            "제품이름",
            "name",
            "product",
            "item name",
            "description",
            "제품",
            "상품",
            "품목",
        ],
        FieldType.PRODUCT_CODE: [
            "제품코드",
            "product code",
            "품번",
            "모델번호",
            "model",
            "code",
            "item code",
            "sku",
            "part number",
            "코드",
            "번호",
            "모델",
        ],
        FieldType.MANUFACTURER: [
            "제조사",
            "manufacturer",
            "공급사",
            "vendor",
            "supplier",
            "maker",
            "brand",
            "브랜드",
            "업체",
            "제조업체",
        ],
        FieldType.CAPACITY: [
            "용량",
            "capacity",
            "ml",
            "내용량",
            "volume",
            "size",
            "cc",
            "리터",
            "사이즈",
        ],
        FieldType.MATERIAL: [
            "재질",
            "material",
            "소재",
            "원료",
            "plastic",
            "pp",
            "pe",
            "pet",
            "petg",
        ],
        FieldType.NECK: ["neck", "넥", "파이", "직경", "diameter", "Ø", "phi", "mouth", "opening"],
        FieldType.MOQ: [
            "moq",
            "최소주문",
            "minimum order",
            "min qty",
            "최소수량",
            "주문단위",
            "포장단위",
            "package",
        ],
        FieldType.PRICE: [
            "가격",
            "price",
            "단가",
            "공급가",
            "supply price",
            "selling price",
            "cost",
            "금액",
            "판매가",
        ],
        FieldType.ORIGIN: ["원산지", "origin", "제조국", "country", "made in", "생산국", "국가"],
        FieldType.WEIGHT: ["무게", "weight", "중량", "g", "kg"],
        FieldType.SIZE: ["크기", "size", "사이즈", "dimensions", "치수"],
        FieldType.USE_CASE: ["용도", "use case", "application", "사용처", "쓰임새", "활용"],
        FieldType.KEYWORD: ["키워드", "keyword", "tag", "태그"],
        FieldType.DESCRIPTION: [
            "설명",
            "description",
            "상세설명",
            "비고",
            "note",
            "remark",
            "메모",
            "detail",
        ],
    }

    @classmethod
    def detect_schema(cls, columns: List[str]) -> Dict[str, Tuple[FieldType, float]]:
        """
        컬럼 리스트를 분석하여 FieldType 매핑

        Args:
            columns: 컬럼명 리스트

        Returns:
            {column_name: (FieldType, confidence_score)}
        """
        schema = {}

        for column in columns:
            field_type, confidence = cls._match_column(column)
            if field_type and confidence > 0.5:  # 50% 이상 신뢰도
                schema[column] = (field_type, confidence)

        return schema

    @classmethod
    def _match_column(cls, column_name: str) -> Tuple[Optional[FieldType], float]:
        """
        단일 컬럼명 매칭

        Args:
            column_name: 컬럼명

        Returns:
            (FieldType, confidence_score)
        """
        if not column_name:
            return None, 0.0

        # 정규화 (소문자, 공백/특수문자 제거)
        normalized = cls._normalize(column_name)

        best_match = None
        best_score = 0.0

        # 각 FieldType에 대해 패턴 매칭
        for field_type, patterns in cls.COLUMN_PATTERNS.items():
            for pattern in patterns:
                normalized_pattern = cls._normalize(pattern)

                # 1. 정확한 매칭
                if normalized == normalized_pattern:
                    return field_type, 1.0

                # 2. 포함 여부 (부분 문자열)
                if normalized_pattern in normalized or normalized in normalized_pattern:
                    score = 0.9
                    if score > best_score:
                        best_match = field_type
                        best_score = score

                # 3. 유사도 매칭 (difflib)
                similarity = SequenceMatcher(None, normalized, normalized_pattern).ratio()
                if similarity > 0.8:  # 80% 이상 유사
                    score = similarity * 0.85  # 약간 낮은 신뢰도
                    if score > best_score:
                        best_match = field_type
                        best_score = score

        return best_match, best_score

    @classmethod
    def _normalize(cls, text: str) -> str:
        """텍스트 정규화 (소문자, 공백/특수문자 제거)"""
        # 소문자 변환
        text = text.lower()
        # 공백, 밑줄, 하이픈 제거
        text = re.sub(r"[\s_\-]", "", text)
        # 괄호 제거
        text = re.sub(r"[\(\)\[\]]", "", text)
        return text

    @classmethod
    def detect_header_row(cls, df) -> int:
        """
        DataFrame에서 헤더 행 자동 탐지

        Args:
            df: pandas DataFrame

        Returns:
            헤더 행 번호 (0-indexed)
        """
        # 전략: 각 행을 스캔하여 가장 많은 필드 매칭이 발생하는 행 찾기
        max_matches = 0
        header_row = 0

        for i in range(min(10, len(df))):  # 첫 10행만 검사
            row = df.iloc[i]
            matches = 0

            for cell in row:
                if isinstance(cell, str):
                    field_type, confidence = cls._match_column(cell)
                    if field_type and confidence > 0.5:
                        matches += 1

            if matches > max_matches:
                max_matches = matches
                header_row = i

        return header_row

    @classmethod
    def validate_schema(cls, schema: Dict[str, Tuple[FieldType, float]]) -> bool:
        """
        스키마 유효성 검증

        Args:
            schema: detect_schema() 결과

        Returns:
            True if valid (필수 필드 포함)
        """
        detected_types = {field_type for _, (field_type, _) in schema.items()}

        # 필수 필드: PRODUCT_NAME 또는 PRODUCT_CODE 중 하나 이상
        required_fields = {FieldType.PRODUCT_NAME, FieldType.PRODUCT_CODE}

        return bool(detected_types & required_fields)

    @classmethod
    def get_mapping_report(cls, schema: Dict[str, Tuple[FieldType, float]]) -> str:
        """
        스키마 매핑 리포트 생성

        Args:
            schema: detect_schema() 결과

        Returns:
            사람이 읽기 쉬운 리포트
        """
        if not schema:
            return "No schema detected."

        report = ["Schema Detection Report", "=" * 50]

        for column, (field_type, confidence) in sorted(schema.items()):
            confidence_pct = confidence * 100
            report.append(f"{column:30s} → {field_type.value:20s} ({confidence_pct:5.1f}%)")

        report.append("=" * 50)
        report.append(f"Total columns mapped: {len(schema)}")

        # 유효성 검증
        is_valid = cls.validate_schema(schema)
        report.append(
            f"Schema valid: {'✅ Yes' if is_valid else '❌ No (missing required fields)'}"
        )

        return "\n".join(report)


if __name__ == "__main__":
    # Test schema detection
    print("=" * 80)
    print("SCHEMA DETECTOR TEST")
    print("=" * 80)

    # Test 1: Korean column names
    columns_kr = [
        "제품명",
        "제품코드",
        "용량(ml)",
        "재질",
        "가격(원)",
        "최소주문수량",
        "제조사",
        "원산지",
        "비고",
    ]

    print("\n[Test 1] Korean Column Names")
    print(f"Columns: {columns_kr}")

    detector = SchemaDetector()
    schema = detector.detect_schema(columns_kr)

    print("\n" + detector.get_mapping_report(schema))

    # Test 2: English column names
    columns_en = [
        "Product Name",
        "SKU",
        "Capacity (ml)",
        "Material",
        "Price ($)",
        "MOQ",
        "Manufacturer",
        "Country of Origin",
        "Description",
    ]

    print("\n" + "─" * 80)
    print("[Test 2] English Column Names")
    print(f"Columns: {columns_en}")

    schema2 = detector.detect_schema(columns_en)
    print("\n" + detector.get_mapping_report(schema2))

    # Test 3: Mixed/Partial names
    columns_mixed = [
        "품명",
        "Model No.",
        "ml",
        "PP/PE",
        "공급가",
        "Package Unit",
        "Vendor",
        "Made in",
        "Note",
    ]

    print("\n" + "─" * 80)
    print("[Test 3] Mixed/Partial Column Names")
    print(f"Columns: {columns_mixed}")

    schema3 = detector.detect_schema(columns_mixed)
    print("\n" + detector.get_mapping_report(schema3))

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
