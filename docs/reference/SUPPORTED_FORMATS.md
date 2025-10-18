# 📄 지원되는 문서 형식

## 전체 지원 형식 목록

Document Ingestion Service는 다음의 **15가지 이상의 형식**을 지원합니다:

### 📊 데이터 형식

| 형식 | 확장자 | 라이브러리 | 설명 |
|------|--------|----------|------|
| **CSV** | .csv | pandas | 행/열 기반 구조화 데이터 |
| **Excel** | .xlsx, .xls | pandas, openpyxl | 스프레드시트 (다중 시트 지원) |
| **JSON** | .json | json | 구조화된 객체 형식 |
| **XML** | .xml | xml.etree | 계층적 데이터 구조 |

### 📄 문서 형식

| 형식 | 확장자 | 라이브러리 | 설명 |
|------|--------|----------|------|
| **PDF** | .pdf | unstructured, pdfminer | 텍스트 및 테이블 추출 |
| **Word** | .docx, .doc | python-docx | Microsoft Word 문서 |
| **PowerPoint** | .pptx, .ppt | python-pptx | 슬라이드별 텍스트 추출 |
| **HTML** | .html, .htm | BeautifulSoup | 웹 페이지 콘텐츠 |
| **Text** | .txt, .md, .rst, .log | 내장 | 평문 텍스트 파일 |

### 🖼️ 이미지 형식

| 형식 | 확장자 | 라이브러리 | 설명 |
|------|--------|----------|------|
| **JPEG** | .jpg, .jpeg | unstructured, EasyOCR, Tesseract | OCR 기반 텍스트 추출 |
| **PNG** | .png | unstructured, EasyOCR, Tesseract | 투명도 지원 이미지 |
| **GIF** | .gif | unstructured, PIL | 애니메이션 첫 프레임 처리 |
| **BMP** | .bmp | unstructured, PIL | 비트맵 형식 |
| **TIFF** | .tiff | unstructured, PIL | 고해상도 이미지 |
| **WebP** | .webp | unstructured, PIL | 현대식 압축 형식 |

### 📦 압축 형식

| 형식 | 확장자 | 설명 |
|------|--------|------|
| **ZIP** | .zip | 내부 파일 자동 추출 후 처리 |
| **TAR** | .tar | 내부 파일 자동 추출 후 처리 |
| **GZIP** | .gz, .tar.gz | 내부 파일 자동 추출 후 처리 |

---

## 📋 형식별 처리 방식

### 1. **CSV 파일**

```python
# 처리 방식
1. Pandas로 데이터프레임 로드
2. 헤더 행을 별도 청크로 생성
3. 각 데이터 행을 별도 청크로 변환
4. 메타데이터: row_index, chunk_type

# 결과 예시
헤더 청크: "CSV Headers: Product | Price | Stock"
데이터 청크: "Product: 50mm Container | Price: 1000 | Stock: 500"
```

### 2. **XML 파일**

```python
# 처리 방식
1. XML 파서로 구조 분석
2. 계층적 태그를 들여쓰기로 표현
3. 텍스트 콘텐츠 추출
4. 512 토큰 단위로 청킹

# 결과 예시
"<product>
  <name>50mm Container</name>
  <price>1000</price>
  <stock>500</stock>
</product>"
```

### 3. **JSON 파일**

```python
# 처리 방식
1. JSON 파서로 객체 로드
2. 포맷팅된 JSON 문자열 생성
3. 줄 단위로 토큰 계산
4. 512 토큰 단위로 청킹

# 결과 예시
"  \"product\": {
    \"name\": \"50mm Container\",
    \"price\": 1000,
    \"stock\": 500
  }"
```

### 4. **이미지 파일 (JPEG, PNG)**

```python
# 처리 방식
1. Unstructured 라이브러리로 초기 처리
2. EasyOCR 또는 Tesseract로 OCR 실행
3. 추출된 텍스트를 단일 청크로 생성
4. 메타데이터: image_format, ocr_confidence

# 결과 예시
"Product label text: 50mm PET Container, Made in Korea, ..."
```

### 5. **Word 문서**

```python
# 처리 방식
1. python-docx로 문서 로드
2. 각 단락을 수집
3. 512 토큰 단위로 청킹
4. 메타데이터: paragraph_index

# 결과 예시
"Introduction: This document describes our product line..."
```

### 6. **PowerPoint 프레젠테이션**

```python
# 처리 방식
1. python-pptx로 프레젠테이션 로드
2. 슬라이드별로 모든 텍스트 수집
3. 각 슬라이드를 별도 청크로 생성
4. 메타데이터: slide_number

# 결과 예시
"=== Slide 1 ===
Title: Product Overview
Content: We are introducing..."
```

### 7. **압축 파일 (ZIP, TAR)**

```python
# 처리 방식
1. 임시 디렉토리에 압축 해제
2. 각 내부 파일의 형식 감지
3. 형식에 따라 재귀적 처리
4. 모든 청크 통합
5. 임시 디렉토리 정리

# 결과 예시
catalog.zip
├─ product_list.csv (행별 처리)
├─ manual.pdf (PDF 처리)
├─ images/
│  ├─ product1.jpg (OCR)
│  └─ product2.png (OCR)
└─ data.json (JSON 처리)
→ 모든 청크 통합 저장
```

---

## 🔧 사용 예시

### CLI 예시

```bash
# CSV 파일 업로드
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@products.csv" \
  -F "doc_type=csv"

# 이미지 파일 업로드 (자동 OCR)
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@product_label.png" \
  -F "doc_type=image"

# XML 파일 업로드
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@supplier_data.xml"

# 압축 파일 업로드 (자동 추출 및 처리)
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@documents.zip"

# 형식 자동 감지 (확장자 기반)
curl -X POST http://localhost:8000/api/v1/ingestion/documents/upload \
  -F "file=@report.docx"
```

### Python 예시

```python
from app.services.document_ingestion_service import DocumentIngestionService
from qdrant_client import QdrantClient

# 초기화
qdrant_client = QdrantClient(host="172.28.0.2", port=6333)
service = DocumentIngestionService(qdrant_client)

# 다양한 형식 처리
async def process_files():
    # CSV 처리
    result1 = await service.ingest_file(
        "products.csv",
        doc_type="csv",
        metadata={"source": "supplier_a"}
    )

    # 이미지 OCR
    result2 = await service.ingest_file(
        "label.jpg",
        doc_type="image",
        metadata={"source": "quality_check"}
    )

    # 압축 파일 처리
    result3 = await service.ingest_file(
        "documents.zip",
        doc_type="archive",
        metadata={"batch": "monthly_update"}
    )

    # 검색
    results = await service.search_documents(
        query="50mm container",
        top_k=5
    )

    return results
```

---

## 📊 형식별 청킹 전략

### 구조화 형식 (CSV, JSON, XML)
```
장점:
- 행/열/엘리먼트 구조 보존
- 의미 단위로 자연스럽게 분할
- 메타데이터 풍부 (행 번호, 키 등)

결과:
- CSV: 각 행 = 1 청크
- JSON: 객체 경계 존중
- XML: 엘리먼트 단위 처리
```

### 비구조화 형식 (PDF, Word, Text)
```
전략:
- 512 토큰 단위 (약 1,000-1,500 문자)
- 50 토큰 오버랩 (컨텍스트 보존)
- 문장/문단 경계 존중

결과:
- 각 청크는 완전한 의미 유지
- 검색 시 높은 정확도
```

### 이미지 형식 (JPEG, PNG)
```
방식:
- OCR로 텍스트 추출
- 전체 이미지 = 1 청크 (일반)
- 여러 텍스트 영역 감지 시 분할

결과:
- 라벨, 문서 스캔 등 자동 처리
```

### 압축 형식 (ZIP, TAR)
```
프로세스:
1. 임시 디렉토리에 추출
2. 각 파일 형식 감지
3. 재귀적 처리
4. 모든 청크 통합

결과:
- 단일 doc_id로 통합
- 파일 정보 메타데이터 추가
```

---

## 🎯 최적화 팁

### 대용량 파일 처리
```python
# CSV: 청크 단위로 처리 권장
# 1000행 이상 → 배치 처리
# 메모리 효율: pandas의 chunksize 파라미터 사용

# PDF: 첫 100페이지만 처리
# 매우 큰 PDF → 분할 후 업로드
```

### 이미지 품질
```python
# 해상도 400 DPI 이상 권장
# OCR 정확도: 95%+ (명확한 텍스트)
# 복잡한 레이아웃 → Word/PDF 형식 사용
```

### 아카이브 크기
```python
# ZIP 파일: 100MB 이하 권장
# 내부 파일 수: 1000개 이하 권장
# 깊은 폴더 구조: 5단계 이하 권장
```

---

## 🔐 지원되는 문자 인코딩

| 인코딩 | 지원 | 비고 |
|--------|------|------|
| UTF-8 | ✅ | 기본 인코딩 |
| EUC-KR | ✅ | 한글 텍스트 |
| GB2312 | ✅ | 중국어 텍스트 |
| Big5 | ✅ | 번체 중국어 |
| Shift-JIS | ✅ | 일본어 텍스트 |
| ISO-8859-1 | ✅ | 라틴 문자 |

---

## 📈 지원 확장 계획

### 향후 추가 형식
- [ ] ProtoBuf (.proto)
- [ ] YAML (.yaml, .yml)
- [ ] TOML (.toml)
- [ ] SQL Scripts (.sql)
- [ ] SVG 이미지 (.svg)
- [ ] Markdown tables (.md)
- [ ] Jupyter Notebooks (.ipynb)
- [ ] Parquet 데이터셋 (.parquet)

### 성능 최적화
- [ ] 병렬 청킹 (멀티스레드)
- [ ] 스트리밍 처리 (대용량 파일)
- [ ] 캐싱 (반복 처리)
- [ ] GPU 기반 OCR (이미지)

---

## 📝 API 응답 메타데이터

각 청크는 다음 메타데이터를 포함합니다:

```json
{
  "chunk": {
    "text": "청크 본문",
    "doc_id": "문서 ID",
    "chunk_index": 0,
    "metadata": {
      "source": "csv|json|image|...",
      "file_path": "/path/to/file",
      "chunk_type": "headers|data_row|slide|...",
      "encoding": "utf-8",
      "language": "ko|en|...",
      "row_index": 42,  // CSV의 경우
      "slide_number": 1,  // PPT의 경우
      "page_number": 3,  // PDF의 경우
      "custom": {...}  // 사용자 정의 메타데이터
    },
    "created_at": "2025-10-17T08:30:00"
  }
}
```

---

**Last Updated**: 2025-10-17
**Status**: ✅ 완벽 지원 (15+ 형식)
**Version**: 2.0 (확장)
