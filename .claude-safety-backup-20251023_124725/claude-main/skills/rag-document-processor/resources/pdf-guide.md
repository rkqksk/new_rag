# PDF 처리 고급 가이드

## Docling 파이프라인 옵션

### OCR 설정
```python
options.do_ocr = True
options.ocr_lang = "kor+eng"  # 한국어와 영어
options.ocr_dpi = 300  # 고품질 OCR
options.ocr_engine = "tesseract"  # or "easyocr"
```

### 표 추출 설정
```python
options.do_table_structure = True
options.table_structure_options.do_cell_matching = True
options.table_structure_options.mode = "ml"  # ML 기반 추출
options.table_structure_options.min_confidence = 0.8
```

### 이미지 처리
```python
options.extract_images = True
options.image_export_format = "png"
options.image_resolution_dpi = 150
```

## 문제 해결

### 한국어 문서 깨짐
- 폰트 임베딩 확인
- UTF-8 인코딩 강제
- 대체 폰트 매핑 설정

### 스캔 PDF 처리
1. 이미지 품질 개선 (OpenCV)
2. OCR 전처리 (노이즈 제거, 회전 보정)
3. 다중 OCR 엔진 사용 (Tesseract + EasyOCR)

### 암호화된 PDF
```python
# 비밀번호 처리
options.pdf_password = os.getenv('PDF_PASSWORD')
# 또는 대화형 입력
if is_encrypted(file_path):
    password = getpass.getpass("PDF 비밀번호: ")
```

## 성능 최적화

### 메모리 효율
- 스트리밍 파싱 사용
- 페이지 단위 처리
- 임시 파일 즉시 정리

### 속도 개선
- 병렬 처리 (multiprocessing)
- GPU 가속 OCR
- 캐싱 전략

## 품질 검증

### 추출 품질 체크
```python
def validate_extraction(result):
    checks = {
        'text_length': len(result['text']) > 100,
        'language_detected': result['metadata']['language'] is not None,
        'tables_valid': all(t['data'] for t in result['tables']),
        'encoding_valid': 'utf-8' in result['metadata'].get('encoding', '')
    }
    return all(checks.values())
```
