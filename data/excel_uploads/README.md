# Excel Upload Folder

## 업로드 방법 (How to Upload)

이 폴더에 공식 Excel 파일을 업로드하세요.

### 폴더 구조:
```
excel_uploads/
├── raw/          ← 여기에 Excel 파일 업로드 (.xlsx)
├── processed/    ← 처리된 JSON 파일 (자동 생성)
├── images/       ← 추출된 이미지 (자동 생성)
└── README.md     ← 이 파일
```

### Excel 파일 예상 구조:
- **Code**: 제품 코드 (예: BT050-G001)
- **Spec**: 사양 (예: 50ml, 41x77mm)
- **포장**: 포장 정보
- **금형**: 금형 정보
- **원가**: 원가
- **판매**: 판매가
- **생산량**: 생산량
- **비고**: 비고
- **Images**: Excel에 포함된 이미지 (자동 추출)

### 사용 방법:
1. `raw/` 폴더에 Excel 파일 복사
2. API 호출: `POST /api/v1/admin/excel/analyze`
3. 비교 리포트 확인
4. 필요시 데이터 업데이트

### 현재 상태:
- ✅ 폴더 준비 완료
- ⏳ Excel 파일 대기 중
- ⏳ API 엔드포인트 생성 중
