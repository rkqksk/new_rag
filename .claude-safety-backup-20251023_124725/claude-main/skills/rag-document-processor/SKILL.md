---
name: rag-document-processor
description: RAG Enterprise 시스템을 위한 고급 문서 처리 스킬. PDF, DOCX, XLSX 등 다양한 형식의 문서를 파싱하고 벡터 DB에 저장하기 위한 전처리를 수행합니다.
license: MIT
allowed-tools:
  - filesystem
  - python
  - bash
metadata:
  version: "2.0.0"
  category: "document-processing"
  author: "RAG Enterprise Team"
  dependencies: ["docling", "pandas", "qdrant-client"]
---

# RAG Document Processor Skill

RAG 파이프라인을 위한 전문 문서 처리 스킬입니다. 이 스킬은 다양한 문서 형식을 자동으로 감지하고 최적화된 파싱 전략을 적용합니다.

## 활성화 조건

다음 상황에서 자동으로 활성화됩니다:
- "문서를 RAG 시스템에 추가" 요청
- PDF, DOCX, XLSX 파일 처리 필요 시
- "벡터 DB에 문서 인덱싱" 작업
- "청킹 및 임베딩" 작업

## 주요 기능

### 1. 지능형 문서 파싱

상황에 따라 적절한 파서를 선택합니다:

```python
from pathlib import Path
import mimetypes

def select_parser(file_path: str):
    """파일 형식에 따른 최적 파서 선택"""
    file_type = mimetypes.guess_type(file_path)[0]
    
    parsers = {
        'application/pdf': 'parse_pdf_advanced',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'parse_docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'parse_excel',
        'text/plain': 'parse_text',
        'text/csv': 'parse_csv'
    }
    
    return parsers.get(file_type, 'parse_generic')
```

### 2. PDF 처리 (Docling 기반)

한국어 문서와 복잡한 표 구조를 위한 최적화:

```python
from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import PdfPipelineOptions
import os

def parse_pdf_advanced(file_path: str) -> dict:
    """Docling을 사용한 고급 PDF 파싱"""
    
    # 파이프라인 옵션 설정
    options = PdfPipelineOptions()
    options.do_ocr = True
    options.ocr_lang = "kor+eng"  # 한국어 + 영어
    options.do_table_structure = True
    options.table_structure_options.do_cell_matching = True
    
    converter = DocumentConverter()
    result = converter.convert(
        file_path,
        pipeline_options=options
    )
    
    # 구조화된 데이터 추출
    return {
        "text": result.text,
        "tables": extract_tables(result),
        "metadata": {
            "page_count": result.page_count,
            "language": detect_language(result.text),
            "extracted_at": datetime.now().isoformat()
        },
        "sections": split_into_sections(result)
    }
```

### 3. 의미 기반 청킹

문서 구조와 의미를 보존하는 청킹 전략:

```python
def semantic_chunking(text: str, max_chunk_size: int = 512) -> list:
    """의미 단위로 텍스트 분할"""
    
    # 문단 경계 찾기
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) < max_chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks
```

### 4. 메타데이터 보강

검색 품질 향상을 위한 메타데이터 추가:

```python
def enrich_metadata(doc_data: dict, file_path: str) -> dict:
    """문서 메타데이터 보강"""
    
    doc_data['metadata'].update({
        'file_name': Path(file_path).name,
        'file_size': os.path.getsize(file_path),
        'doc_type': classify_document(doc_data['text']),
        'key_entities': extract_entities(doc_data['text']),
        'summary': generate_summary(doc_data['text'][:2000])
    })
    
    return doc_data
```

## 고급 기능

### 표 데이터 처리

복잡한 표를 구조화된 데이터로 변환:

```python
def process_tables(tables: list) -> list:
    """표 데이터를 검색 가능한 형태로 변환"""
    processed = []
    
    for table in tables:
        # DataFrame으로 변환
        df = table_to_dataframe(table)
        
        # 통계 정보 추가
        stats = {
            'row_count': len(df),
            'col_count': len(df.columns),
            'numeric_cols': df.select_dtypes(include='number').columns.tolist()
        }
        
        # 검색용 텍스트 생성
        search_text = generate_table_description(df)
        
        processed.append({
            'data': df.to_dict('records'),
            'stats': stats,
            'search_text': search_text
        })
    
    return processed
```

### 이미지 텍스트 추출

문서 내 이미지에서 텍스트 추출:

```python
from easyocr import Reader

def extract_image_text(image_path: str) -> str:
    """이미지에서 텍스트 추출 (OCR)"""
    
    reader = Reader(['ko', 'en'])
    results = reader.readtext(image_path)
    
    # 결과 정리
    text = ' '.join([text for _, text, _ in results])
    return text
```

## 벡터 DB 통합

처리된 문서를 Qdrant에 저장:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

def index_to_qdrant(chunks: list, metadata: dict):
    """처리된 청크를 Qdrant에 인덱싱"""
    
    client = QdrantClient(url="http://localhost:6333")
    
    # 임베딩 생성
    embeddings = generate_embeddings(chunks)
    
    # 포인트 생성
    points = [
        PointStruct(
            id=i,
            vector=emb,
            payload={
                "text": chunk,
                "metadata": metadata,
                "chunk_index": i
            }
        )
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
    ]
    
    # 업로드
    client.upsert(
        collection_name="documents",
        points=points
    )
```

## 성능 최적화

### 배치 처리

대량 문서 처리를 위한 최적화:

```python
async def batch_process_documents(file_paths: list, batch_size: int = 10):
    """비동기 배치 처리"""
    
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    executor = ThreadPoolExecutor(max_workers=4)
    
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        
        tasks = [
            asyncio.create_task(
                process_document_async(fp, executor)
            )
            for fp in batch
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 결과 저장
        for result in results:
            if result:
                save_to_cache(result)
```

## 에러 처리

견고한 에러 처리와 복구:

```python
def process_with_fallback(file_path: str):
    """폴백 전략을 포함한 처리"""
    
    strategies = [
        parse_pdf_advanced,    # Docling
        parse_pdf_fallback,    # PyPDF2
        parse_pdf_ocr_only,    # OCR only
        extract_text_basic     # 기본 텍스트 추출
    ]
    
    for strategy in strategies:
        try:
            result = strategy(file_path)
            if result and len(result.get('text', '')) > 100:
                return result
        except Exception as e:
            logger.warning(f"Strategy {strategy.__name__} failed: {e}")
            continue
    
    raise ProcessingError(f"모든 전략 실패: {file_path}")
```

## 추가 리소스 참조

특정 작업에 대한 상세 가이드:
- `resources/pdf-guide.md` - PDF 처리 상세 가이드
- `resources/table-extraction.md` - 표 추출 고급 기법
- `scripts/benchmark.py` - 성능 벤치마크 도구
- `templates/` - 문서 형식별 템플릿

## 사용 예제

```bash
# 단일 문서 처리
python -c "
from skills.rag_document_processor import process_document
result = process_document('path/to/document.pdf')
print(f'처리 완료: {len(result['chunks'])} 청크 생성')
"

# 디렉토리 일괄 처리
python scripts/batch_process.py --input-dir ./documents --output-dir ./processed
```

## 설정 옵션

환경 변수로 동작 커스터마이징:

```bash
export RAG_CHUNK_SIZE=512
export RAG_CHUNK_OVERLAP=50
export RAG_OCR_LANG="kor+eng"
export RAG_EMBEDDING_MODEL="gte-Qwen2-7B-instruct"
export QDRANT_URL="http://localhost:6333"
```

## 주의사항

- 대용량 PDF (>100MB)는 메모리 사용량 주의
- OCR 처리 시 GPU 사용 권장
- 민감 정보가 포함된 문서는 암호화 저장
- 배치 처리 시 rate limiting 고려
