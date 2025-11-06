"""
Unified File Processor
Excel/CSV 파일을 처리하여 RAG 시스템에 통합

목적: 파일 업로드 → 파싱 → 청킹 → 임베딩 → Qdrant 업로드
전략:
- Excel/CSV 자동 감지 및 파싱
- enhanced_field_extractor.py 통합
- advanced_chunk_generator.py로 청킹
- Qdrant 자동 업로드
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from src.core.structured_processors.excel_parser import ExcelParser
from src.core.structured_processors.csv_parser import CSVParser
from src.core.enhanced_field_extractor import EnhancedFieldExtractor
from src.core.advanced_chunk_generator import AdvancedChunkGenerator

logger = logging.getLogger(__name__)


class FileProcessor:
    """통합 파일 프로세서"""

    def __init__(self):
        self.excel_parser = ExcelParser()
        self.csv_parser = CSVParser()
        self.field_extractor = EnhancedFieldExtractor()
        self.chunk_generator = AdvancedChunkGenerator()

    def process_file(
        self,
        file_path: str,
        upload_to_qdrant: bool = False
    ) -> Dict[str, Any]:
        """
        파일 처리 (전체 파이프라인)

        Args:
            file_path: 파일 경로 (.xlsx, .xls, .csv)
            upload_to_qdrant: Qdrant 업로드 여부

        Returns:
            {
                'products': List[Dict],  # 원본 제품 데이터
                'chunks': List[Dict],    # 생성된 청크
                'stats': {
                    'total_products': int,
                    'total_chunks': int,
                    'avg_chunks_per_product': float
                }
            }
        """
        file_path = Path(file_path)
        logger.info(f"Processing file: {file_path}")

        # Step 1: 파일 타입 감지 및 파싱
        products = self._parse_file(file_path)
        logger.info(f"Step 1: Parsed {len(products)} products")

        if not products:
            logger.warning("No products extracted from file")
            return {
                'products': [],
                'chunks': [],
                'stats': {'total_products': 0, 'total_chunks': 0, 'avg_chunks_per_product': 0}
            }

        # Step 2: 필드 강화 (enhanced_field_extractor)
        enhanced_products = self._enhance_products(products)
        logger.info(f"Step 2: Enhanced {len(enhanced_products)} products")

        # Step 3: 청킹 (advanced_chunk_generator)
        chunks = self._generate_chunks(enhanced_products)
        logger.info(f"Step 3: Generated {len(chunks)} chunks")

        # Step 4: Qdrant 업로드 (optional)
        if upload_to_qdrant:
            self._upload_to_qdrant(chunks)
            logger.info(f"Step 4: Uploaded {len(chunks)} chunks to Qdrant")

        # 통계
        stats = {
            'total_products': len(products),
            'total_chunks': len(chunks),
            'avg_chunks_per_product': len(chunks) / len(products) if products else 0
        }

        return {
            'products': products,
            'chunks': chunks,
            'stats': stats
        }

    def _parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """파일 파싱 (Excel 또는 CSV)"""
        suffix = file_path.suffix.lower()

        if suffix in ['.xlsx', '.xls']:
            logger.info(f"Detected Excel file: {suffix}")
            return self.excel_parser.parse_file(str(file_path))

        elif suffix == '.csv':
            logger.info("Detected CSV file")
            return self.csv_parser.parse_file(str(file_path))

        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _enhance_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        제품 데이터 강화

        Args:
            products: 원본 제품 데이터 (parser 결과)

        Returns:
            강화된 제품 데이터 (복합 필드 추가)
        """
        enhanced = []

        for product in products:
            # EnhancedFieldExtractor 사용
            fields = self.field_extractor.extract_fields(product)

            # 복합 필드 생성
            composite_fields = self.field_extractor.create_composite_fields(fields)
            fields.update(composite_fields)

            # FieldType.value → str로 변환
            enhanced_product = {
                field_type.value: value
                for field_type, value in fields.items()
            }

            enhanced.append(enhanced_product)

        return enhanced

    def _generate_chunks(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        청크 생성

        Args:
            products: 강화된 제품 데이터

        Returns:
            청크 리스트
        """
        all_chunks = []

        for i, product in enumerate(products):
            # product_id 생성 (없으면)
            if 'product_id' not in product:
                product['product_id'] = f"uploaded_{i+1:04d}"

            # 청크 생성 (AtomicChunk 객체)
            chunks = self.chunk_generator.generate_chunks(product)

            # AtomicChunk → dict 변환
            for chunk in chunks:
                chunk_dict = {
                    'chunk_id': chunk.chunk_id,
                    'product_id': product.get('product_id', f"uploaded_{i+1:04d}"),
                    'field_type': chunk.field_type.value,
                    'chunk_text': chunk.text,
                    'priority': chunk.priority,
                    'metadata': chunk.metadata,
                    'search_keywords': chunk.search_keywords
                }
                all_chunks.append(chunk_dict)

        return all_chunks

    def _upload_to_qdrant(self, chunks: List[Dict[str, Any]]):
        """
        Qdrant 업로드

        Args:
            chunks: 청크 리스트
        """
        # TODO: Qdrant 클라이언트 통합
        # 현재는 placeholder
        logger.info(f"TODO: Upload {len(chunks)} chunks to Qdrant")
        pass

    def get_processing_report(self, result: Dict[str, Any]) -> str:
        """
        처리 결과 리포트 생성

        Args:
            result: process_file() 결과

        Returns:
            사람이 읽기 쉬운 리포트
        """
        stats = result['stats']

        report = [
            "File Processing Report",
            "=" * 50,
            f"Total Products:  {stats['total_products']}",
            f"Total Chunks:    {stats['total_chunks']}",
            f"Avg Chunks/Product: {stats['avg_chunks_per_product']:.1f}",
            "=" * 50
        ]

        # 샘플 제품 (최대 3개)
        products = result['products'][:3]
        if products:
            report.append("\nSample Products:")
            for i, product in enumerate(products, 1):
                name = product.get('product_name', product.get('description', 'N/A'))
                report.append(f"  {i}. {name}")

        # 청크 타입 분포
        chunks = result['chunks']
        if chunks:
            field_counts = {}
            for chunk in chunks:
                field_type = chunk.get('field_type', 'unknown')
                field_counts[field_type] = field_counts.get(field_type, 0) + 1

            report.append("\nChunk Distribution:")
            for field_type, count in sorted(field_counts.items(), key=lambda x: -x[1])[:5]:
                report.append(f"  {field_type:20s}: {count:4d}")

        return "\n".join(report)


if __name__ == "__main__":
    # Test file processor
    import tempfile
    import openpyxl

    print("=" * 80)
    print("FILE PROCESSOR TEST")
    print("=" * 80)

    # Create test Excel file
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False, mode='wb') as f:
        temp_path = f.name

    wb = openpyxl.Workbook()
    ws = wb.active

    # Header
    ws.append(["제품명", "제품코드", "용량(ml)", "재질", "가격(원)", "최소주문수량", "제조사"])

    # Sample data
    ws.append(["100ml PE 보틀", "BE100-001", "100", "PE", "1,200", "5,000개", "금양실업"])
    ws.append(["200ml PET 보틀", "BE200-002", "200", "PET", "1,500", "3,000ea", "청진코리아"])

    wb.save(temp_path)

    print(f"\n[Test] Processing Excel file: {temp_path}")

    # Process
    processor = FileProcessor()
    result = processor.process_file(temp_path, upload_to_qdrant=False)

    print("\n" + processor.get_processing_report(result))

    # Cleanup
    import os
    os.unlink(temp_path)

    print("\n" + "=" * 80)
    print("✅ TEST COMPLETED")
    print("=" * 80)
