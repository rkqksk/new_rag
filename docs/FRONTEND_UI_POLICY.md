# Frontend UI/UX Design Policy

## 📋 현재 프로덕션 UI/UX (고정)

### ✅ 승인된 디자인 시스템

#### 디자인 컨셉
```yaml
Name: 스마트 제품 추천 (Smart Product Recommendation)
Version: 1.0.0
Style: Minimal & Clean
Mode: Light Mode Only (No Dark Mode)
Status: ✅ Production Ready
Tested: 2025-11-04

Design Philosophy:
  - Minimalism: 군더더기 없는 깔끔한 인터페이스
  - Clarity: 제품 중심의 명확한 정보 전달
  - Consistency: 데스크탑/모바일 동일한 경험
  - Accessibility: 누구나 쉽게 사용 가능
```

---

## 🎨 디자인 상수 (FIXED - 변경 금지)

### 색상 팔레트

```css
/* Primary Colors (Purple Gradient) */
--color-primary-start: #667eea    /* 보라색 시작 */
--color-primary-end: #764ba2      /* 보라색 끝 */

/* Background Colors */
--color-bg-main: #f5f5f5          /* 메인 배경 (연한 회색) */
--color-bg-card: #ffffff          /* 카드 배경 (흰색) */
--color-bg-image: #f9fafb         /* 이미지 배경 */

/* Text Colors */
--color-text-primary: #333        /* 주요 텍스트 (진한 회색) */
--color-text-secondary: #555      /* 보조 텍스트 */
--color-text-tertiary: #666       /* 3차 텍스트 */
--color-text-light: #999          /* 연한 텍스트 */

/* Accent Colors */
--color-accent-red: #e74c3c       /* 강조 빨강 (추천제품 위치) */

/* Border Colors */
--color-border: #d1d5db           /* 기본 테두리 */
--color-border-light: #e5e7eb     /* 연한 테두리 */
```

### 타이포그래피

```css
/* Font Family (System Fonts) */
--font-family: -apple-system, BlinkMacSystemFont,
               'Segoe UI', 'Roboto',
               'Helvetica', 'Arial', sans-serif

/* Font Sizes */
--font-size-header: 18px          /* 헤더 */
--font-size-large: 16px           /* 큰 텍스트 */
--font-size-base: 15px            /* 기본 텍스트 */
--font-size-medium: 14px          /* 중간 텍스트 */
--font-size-small: 12px           /* 작은 텍스트 */
--font-size-tiny: 11px            /* 아주 작은 텍스트 */

/* Font Weights */
--font-weight-semibold: 600       /* 세미볼드 */

/* Line Heights */
--line-height-base: 1.6           /* 기본 줄간격 */
```

### 레이아웃

```css
/* Max Widths */
--max-width-content: 1200px       /* 콘텐츠 최대 너비 */
--max-width-recommendations: 1000px /* 추천 영역 최대 너비 */

/* Component Sizes */
--slot-width: 280px               /* 추천제품 슬롯 너비 */
--slot-height: 320px              /* 추천제품 슬롯 높이 */
--card-width: 280px               /* 제품 카드 너비 */
--card-image-height: 220px        /* 제품 이미지 높이 (데스크톱) */
--card-image-height-mobile: 180px /* 제품 이미지 높이 (모바일) */

/* Avatar */
--avatar-size: 28px               /* 아바타 크기 */
```

### 간격 (Spacing)

```css
--spacing-xs: 8px                 /* 아주 작은 간격 */
--spacing-sm: 12px                /* 작은 간격 */
--spacing-md: 16px                /* 중간 간격 */
--spacing-lg: 20px                /* 큰 간격 */
--spacing-xl: 24px                /* 아주 큰 간격 */
--spacing-2xl: 40px               /* 2배 큰 간격 */
--spacing-3xl: 60px               /* 3배 큰 간격 */
```

### 테두리 반경 (Border Radius)

```css
--radius-sm: 8px                  /* 작은 반경 (입력창, 버튼) */
--radius-md: 12px                 /* 중간 반경 (카드) */
--radius-full: 50%                /* 완전 원형 (아바타) */
```

### 그림자 (Shadows)

```css
--shadow-sm: 0 2px 12px rgba(0,0,0,0.08)        /* 작은 그림자 */
--shadow-md: 0 4px 20px rgba(0,0,0,0.12)        /* 중간 그림자 */
--shadow-lg: 0 4px 20px rgba(0,0,0,0.15)        /* 큰 그림자 */
--shadow-input: 0 0 0 3px rgba(102,126,234,0.1) /* 입력 포커스 */
--shadow-button: 0 4px 12px rgba(102,126,234,0.4) /* 버튼 호버 */
--shadow-top: 0 -2px 12px rgba(0,0,0,0.08)      /* 상단 그림자 */
```

### 트랜지션 (Transitions)

```css
--transition-fast: 0.2s           /* 빠른 애니메이션 */
--transition-base: 0.3s           /* 기본 애니메이션 */
--transition-slow: 1.4s           /* 느린 애니메이션 (로딩) */
```

---

## 🔒 UI/UX 고정 정책

### 원칙

1. **프로덕션 디자인은 함부로 변경하지 않음**
2. **새로운 컴포넌트는 기존 디자인 상수 사용**
3. **디자인 변경은 반드시 테스트 후 승인**
4. **변경 시 반드시 롤백 계획 수립**

### 금지 사항

```css
/* ❌ 금지: CSS 변수를 하드코딩으로 덮어쓰기 */
.my-component {
    color: #667eea;  /* ❌ 잘못됨 */
}

/* ❌ 금지: 새로운 색상 체계 도입 */
:root {
    --my-new-color: #ff0000;  /* ❌ 승인 없이 추가 금지 */
}

/* ❌ 금지: 반응형 브레이크포인트 변경 */
@media (max-width: 600px) {  /* ❌ 768px 고정 */
    /* ... */
}

/* ❌ 금지: 다크 모드 추가 */
@media (prefers-color-scheme: dark) {  /* ❌ 다크 모드 없음 */
    /* ... */
}
```

### 허용 사항

```css
/* ✅ 허용: CSS 변수 사용 */
.my-component {
    color: var(--color-primary-start);  /* ✅ 올바름 */
    padding: var(--spacing-md);         /* ✅ 올바름 */
}

/* ✅ 허용: 기존 변수 조합 */
.my-button {
    background: linear-gradient(135deg,
                var(--color-primary-start) 0%,
                var(--color-primary-end) 100%);  /* ✅ 올바름 */
}

/* ✅ 허용: 컴포넌트별 미세 조정 (승인 후) */
.special-card {
    padding: calc(var(--spacing-md) * 1.5);  /* ✅ 필요 시 계산 */
}
```

---

## 📱 반응형 디자인 정책

### 브레이크포인트 (FIXED)

```css
/* Desktop First (기본) */
/* 768px 이상: 데스크톱 레이아웃 */

/* Mobile (768px 이하만 허용) */
@media (max-width: 768px) {
    /* 모바일 최적화 */
}

/* ⚠️ 주의: 다른 브레이크포인트 추가 금지 */
/* 예: 1024px, 1440px 등 추가 금지 */
```

### 반응형 규칙

#### 데스크톱 (> 768px)
```yaml
추천제품 슬롯:
  - 가로 정렬
  - 슬롯 크기: 280px × 320px
  - 간격: 20px

제품 그리드:
  - grid-template-columns: repeat(auto-fill, minmax(280px, 1fr))
  - 이미지 높이: 220px
  - 간격: 20px

최대 너비:
  - 콘텐츠: 1200px
  - 추천 영역: 1000px
```

#### 모바일 (≤ 768px)
```yaml
추천제품 슬롯:
  - 세로 정렬
  - 슬롯 크기: 100% (max-width: 320px)

제품 그리드:
  - grid-template-columns: repeat(auto-fill, minmax(200px, 1fr))
  - 이미지 높이: 180px
  - 간격: 16px

최대 너비:
  - 콘텐츠: 100%
```

---

## 🏗️ 컴포넌트 구조 (FIXED)

### 1. 헤더

```html
<div class="header">
    <div class="header-title">🏠 스마트 제품 추천</div>
</div>
```

**변경 금지 사항:**
- 배경: Purple gradient (667eea → 764ba2)
- 텍스트: "🏠 스마트 제품 추천"
- 패딩: 20px 24px
- 이모지: 🏠 (집 아이콘)

### 2. 초기 화면

```html
<div id="initialView">
    <div class="guide-text">
        인생제품이 완벽하는 쉬기를 검색해보세요.<br>
        예: "화장품", "플라스틱 용기", "세럼병"
    </div>

    <div class="recommendations">
        <div class="recommendation-slot">추천제품 위치</div>
        <div class="recommendation-slot">추천제품 위치</div>
        <div class="recommendation-slot">추천제품 위치</div>
    </div>
</div>
```

**변경 금지 사항:**
- 슬롯 개수: 3개 고정
- 슬롯 텍스트: "추천제품 위치" (빨간색)
- 안내 문구: 현재 텍스트 유지

### 3. 입력 영역

```html
<div class="input-container">
    <div class="input-hint">
        <span>진술 버스도로 화면으로 이동하기</span>
        <span class="hint-arrow">↘</span>
    </div>
    <div class="input-wrapper">
        <textarea placeholder="여자사를 입력하세요..."></textarea>
        <button class="send-btn">전송</button>
    </div>
</div>
```

**변경 금지 사항:**
- Placeholder: "여자사를 입력하세요..."
- 버튼 텍스트: "전송"
- 힌트 텍스트: "진술 버스도로 화면으로 이동하기"
- 힌트 화살표: ↘

### 4. 제품 카드

```html
<div class="product-card">
    <img src="..." class="product-image">
    <div class="product-info">
        <div class="product-name">제품명</div>
        <div class="product-spec">재질: PET</div>
        <div class="product-spec">용량: 50ml</div>
        <div class="product-spec">네크: Ø24</div>
        <div class="product-code">제품코드</div>
    </div>
</div>
```

**변경 금지 사항:**
- 스펙 순서: 재질 → 용량 → 네크
- 카드 크기: 280px 너비
- 이미지 높이: 220px (데스크톱), 180px (모바일)

---

## 🔄 디자인 변경 절차

### Phase 1: 제안 (1일)
```yaml
Required:
  - 변경 이유 및 목적
  - Before/After 스크린샷
  - 영향 범위 분석
  - 사용자 피드백 (필요 시)
```

### Phase 2: 설계 (1-2일)
```yaml
Deliverables:
  - 디자인 목업 (Figma, Sketch)
  - CSS 변수 변경 목록
  - 반응형 대응 계획
  - 호환성 체크리스트
```

### Phase 3: 검증 (2-3일)
```yaml
Tests:
  - 브라우저 호환성 (Chrome, Safari, Firefox, Edge)
  - 반응형 테스트 (Desktop, Tablet, Mobile)
  - 접근성 테스트 (WCAG 2.1 AA)
  - 성능 테스트 (LCP, CLS, FID)
  - A/B 테스트 (선택적)
```

### Phase 4: 승인 (1일)
```yaml
Required:
  - 테스트 보고서
  - 디자인 팀 승인
  - 개발 팀 승인
  - 롤백 계획
```

### Phase 5: 배포 (0.5일)
```bash
# 1. 현재 버전 백업
cp frontend/chat.html frontend/chat.html.backup_$(date +%Y%m%d)

# 2. 변경사항 적용
# (CSS 변수 또는 HTML 수정)

# 3. Git 커밋
git add frontend/
git commit -m "feat(ui): [변경 내용 설명]"

# 4. 배포 후 모니터링 (1주일)
```

### Phase 6: 모니터링 (1주일)
```yaml
Metrics:
  - 사용자 피드백
  - 이탈률 변화
  - 성능 지표 (LCP, CLS, FID)
  - 에러율

Alert Conditions:
  - 이탈률 > 10% 증가
  - LCP > 2.5s
  - CLS > 0.1
  - 에러율 > 5%
```

---

## 🚨 긴급 롤백 절차

### Trigger Conditions
- 치명적 UI 버그 발견
- 성능 저하 (LCP > 3s)
- 사용자 이탈률 급증 (> 20%)
- 접근성 문제 발견

### Rollback Steps

```bash
# 1. 즉시 이전 버전으로 복원
cp frontend/chat.html.backup_YYYYMMDD frontend/chat.html

# 2. 캐시 무효화
# (CDN 또는 브라우저 캐시 클리어)

# 3. Git 복원
git checkout HEAD~1 -- frontend/chat.html
git commit -m "revert(ui): Rollback to previous UI version"

# 4. 인시던트 보고서 작성
# - 문제 설명
# - 영향 범위
# - 근본 원인
# - 재발 방지 대책
```

---

## 📊 디자인 시스템 메트릭스

### 성능 목표

```yaml
Core Web Vitals:
  LCP (Largest Contentful Paint): < 2.5s
  FID (First Input Delay): < 100ms
  CLS (Cumulative Layout Shift): < 0.1

Page Load:
  초기 로드: < 1s
  이미지 로드: lazy loading
  API 응답: < 500ms

Bundle Size:
  HTML + CSS: < 50KB (uncompressed)
  Images: WebP, < 100KB each
```

### 접근성 목표

```yaml
WCAG 2.1 Level AA:
  - 색상 대비: 4.5:1 이상 (텍스트)
  - 색상 대비: 3:1 이상 (UI 컴포넌트)
  - 키보드 네비게이션: 모든 인터랙티브 요소
  - 스크린 리더: ARIA 레이블 적용
  - 포커스 표시: 명확한 outline

Browser Support:
  - Chrome: 최신 2개 버전
  - Safari: 최신 2개 버전
  - Firefox: 최신 2개 버전
  - Edge: 최신 2개 버전
```

---

## 🔗 관련 파일

### 프론트엔드 파일
```
frontend/
├── chat.html              # 메인 UI (프로덕션)
├── chat.html.backup       # 이전 버전 백업
├── README.md             # 프론트엔드 문서
└── TEST_GUIDE.md         # 테스트 가이드
```

### 설정 파일
```
config/
├── ui_constants.yaml     # UI 상수 설정 (YAML)
└── ollama_models.yaml    # Ollama 모델 설정
```

### 문서
```
docs/
├── FRONTEND_UI_POLICY.md     # 이 문서
├── OLLAMA_MODEL_POLICY.md    # Ollama 정책
├── ARCHITECTURE.md           # 시스템 아키텍처
└── README.md                 # 문서 인덱스
```

---

## 📞 문의

UI/UX 변경 또는 개선 관련 문의:
1. 이슈 생성: `GitHub Issues`
2. 디자인 리뷰 요청: `#design-team` 채널
3. 긴급 문의: `ui-team@company.com`

---

**Last Updated**: 2025-11-04
**Policy Version**: 1.0.0
**Status**: Active
**Design System Version**: 1.0.0
