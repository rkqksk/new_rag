# Frontend - 제품 검색 인터페이스

## 🎨 디자인 컨셉

**ChatGPT 스타일의 깔끔한 대화형 제품 검색**

- 라이트 모드 (다크 모드 없음)
- 단일 컬럼 레이아웃
- 제품 그리드 디스플레이

---

## 📂 파일 구조

```
frontend/
├── chat.html           # 메인 UI (현재 버전)
├── chat.html.backup    # 이전 버전 백업
├── TEST_GUIDE.md       # 테스트 가이드
└── README.md           # 이 파일
```

---

## 🚀 실행 방법

### 1. 백엔드 시작

```bash
cd /Users/oypnus/Project/rag-enterprise
python run_chat_server.py
# Backend: http://localhost:8001
```

### 2. 프론트엔드 시작

```bash
cd frontend
python3 -m http.server 8080
# Frontend: http://localhost:8080/chat.html
```

### 3. 브라우저 열기

```bash
open http://localhost:8080/chat.html
```

---

## 🎯 주요 기능

### 1. 초기 화면

- **제목**: "어떤 제품을 찾으세요?"
- **안내**: 용량, 재질, 제품명으로 검색 가능
- **입력창**: 하단 고정

### 2. 검색 결과

- **사용자 메시지**: 오른쪽 정렬, 녹색 아바타
- **시스템 응답**: 왼쪽 정렬, 보라색 아바타
- **제품 그리드**: 이미지 + 간단한 스펙

### 3. 제품 카드

```
┌─────────────────┐
│                 │
│     이미지      │  (180px 높이)
│                 │
├─────────────────┤
│ 제품명          │
│ 재질: PET       │
│ 용량: 50ml      │
│ 네크: Ø24      │
│ 제품코드        │
└─────────────────┘
```

---

## 🎨 디자인 사양

### 색상

```css
/* 배경 */
background: #ffffff (흰색)

/* 텍스트 */
primary: #2e3338 (진한 회색)
secondary: #6e6e80 (중간 회색)
tertiary: #acacbe (연한 회색)

/* 액센트 */
user-avatar: #19c37d (녹색)
assistant-avatar: #ab68ff (보라색)
primary-button: #10a37f (청록색)
border: #e5e7eb (연한 회색)
```

### 타이포그래피

```css
font-family: -apple-system, BlinkMacSystemFont,
             'Segoe UI', 'Roboto',
             'Helvetica', 'Arial', sans-serif

/* 크기 */
제목: 32px (bold)
안내: 16px
메시지: 15px
제품명: 13px (bold)
제품스펙: 11px
제품코드: 10px
```

### 레이아웃

```css
/* 반응형 그리드 */
desktop: repeat(auto-fill, minmax(200px, 1fr))
mobile: repeat(auto-fill, minmax(150px, 1fr))

/* 여백 */
gap: 16px (desktop), 12px (mobile)
padding: 24px (container)
```

---

## 🔌 API 연동

### 엔드포인트

```javascript
const API_BASE = 'http://localhost:8001';

// 1. 세션 생성
POST /chat/create_session
Body: {}
Response: { session_id, created_at }

// 2. 제품 검색
POST /chat/query
Body: { session_id, query }
Response: { products: [...], ... }
```

### 제품 데이터 구조

```javascript
{
  "idx": "123",
  "product_name": "50ml PET 병",
  "product_code": "PET-50-001",
  "images": [
    { "url": "http://..." }
  ],
  "specifications": {
    "재질(원료)": "PET",
    "capacity": "50ml",
    "neck_size": "Ø24"
  }
}
```

---

## 🧪 테스트 케이스

### 검색 테스트

```
1. "50ml bottle"       → 세럼/화장품 용기
2. "PET 병"            → PET 재질 필터링
3. "100ml 화장품 용기" → 용량 + 용도 매칭
4. "펌프"              → 펌프 카테고리
```

### UI 테스트

- [ ] 초기 화면 정상 표시
- [ ] 입력창 포커스 시 테두리 색상 변경
- [ ] Enter 키로 전송
- [ ] 전송 버튼 활성화/비활성화
- [ ] 로딩 애니메이션 표시
- [ ] 제품 그리드 정상 렌더링
- [ ] 제품 카드 호버 효과
- [ ] 이미지 로드 실패 시 placeholder 표시
- [ ] 반응형 레이아웃 (모바일/태블릿/데스크톱)

---

## 📱 반응형 대응

### 데스크톱 (> 768px)

- 제품 카드: 200px 최소 너비
- 이미지 높이: 180px
- 그리드 갭: 16px

### 모바일 (≤ 768px)

- 제품 카드: 150px 최소 너비
- 이미지 높이: 140px
- 그리드 갭: 12px
- 제목 크기 축소: 24px

---

## 🚧 향후 개선사항

### Phase 2
- [ ] 제품 상세 모달
- [ ] 필터 UI (재질, 용량, 네크사이즈)
- [ ] 정렬 옵션 (인기순, 최신순)

### Phase 3
- [ ] 이미지 확대 보기
- [ ] 제품 비교 기능
- [ ] 즐겨찾기/북마크

### Phase 4
- [ ] 검색 히스토리
- [ ] 자동완성
- [ ] 추천 검색어

---

## 📊 성능 목표

```yaml
초기 로드: < 1s
API 응답: < 500ms
이미지 로드: lazy loading
메모리 사용: < 100MB
```

---

## 🔗 관련 문서

- **테스트 가이드**: `TEST_GUIDE.md`
- **백엔드 API**: `src/api/chat.py`
- **아키텍처**: `docs/ARCHITECTURE.md`

---

**Last Updated**: 2025-11-04
**Version**: 2.0 (ChatGPT-style redesign)
**Status**: ✅ Production Ready
