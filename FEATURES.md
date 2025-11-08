# RAG Enterprise - Feature Documentation

> **Version**: v5.1.0 | **Last Updated**: 2025-11-08
> **Feature Flag System**: ✅ Enabled | **Total Features**: 30+

---

## 📚 Table of Contents

1. [Feature Flag System](#feature-flag-system)
2. [Quick Wins Features](#quick-wins-features)
3. [Priority Features](#priority-features)
4. [Usage Guide](#usage-guide)
5. [Configuration](#configuration)

---

## 🎛️ Feature Flag System

### Overview

모든 기능을 대시보드에서 on/off할 수 있는 중앙 관리 시스템입니다.

### Access

```
URL: /admin/settings
권한: Super-user, Admin, Manager
```

### Features

- ✅ **전체 활성화/비활성화**: 모든 기능을 한 번에 on/off
- ✅ **기본값 복원**: 초기 설정으로 되돌리기
- ✅ **검색 기능**: 기능 이름/설명으로 검색
- ✅ **카테고리 필터**: UI/UX, 기능, 접근성, 개발자 도구, 데이터 관리
- ✅ **실시간 적용**: 토글 즉시 반영
- ✅ **LocalStorage 저장**: 브라우저 종료 후에도 유지

### Statistics Display

- 전체 기능 수
- 활성화된 기능 수
- 비활성화된 기능 수
- 활성화율 (%)

---

## ⚡ Quick Wins Features

### 1. Toast Notifications 🍞

**Status**: ✅ Implemented
**Category**: UI/UX
**Impact**: High

성공/실패/정보 메시지를 화면 우측 상단에 표시합니다.

**Usage**:
```typescript
import { toast } from "sonner"

// Success
toast.success("크롤링이 시작되었습니다!")

// Error
toast.error("소스 추가에 실패했습니다")

// Info
toast.info("데이터 로딩 중...")

// Warning
toast.warning("Rate limit에 근접했습니다")
```

**Features**:
- 자동 사라짐 (3초)
- 색상 구분 (Success=초록, Error=빨강, Info=파랑, Warning=노랑)
- 스택 지원 (여러 알림 동시 표시)
- 위치: 화면 우측 상단

---

### 2. Copy to Clipboard 📋

**Status**: ✅ Implemented
**Category**: Functionality
**Impact**: Low

텍스트/JSON을 클립보드에 복사하는 유틸리티 함수입니다.

**Usage**:
```typescript
import { copyToClipboard, copyJSON } from "@/lib/utils/copy"

// Copy plain text
await copyToClipboard("https://example.com")

// Copy JSON (auto-formatted)
await copyJSON({ id: 1, name: "Test" })

// Custom success message
await copyToClipboard(text, "URL이 복사되었습니다!")
```

**Features**:
- Toast 알림 포함
- JSON 자동 포맷팅 (2-space indent)
- 에러 처리
- 비동기 지원

---

### 3. Data Export (CSV/JSON) 📥

**Status**: ✅ Implemented
**Category**: Functionality
**Impact**: High

크롤링 결과 및 기타 데이터를 파일로 다운로드합니다.

**Usage**:
```typescript
import { exportJSON, exportCSV } from "@/lib/utils/export"

// Export as JSON
exportJSON(data, "crawl_results.json")

// Export as CSV
exportCSV(arrayData, "products.csv")
```

**Features**:
- ✅ JSON Export: Formatted with 2-space indent
- ✅ CSV Export: Automatic header generation
- ✅ Nested object flattening (for CSV)
- ✅ Array serialization
- ✅ Quote escaping
- ✅ Toast notification on completion

**Integrated In**:
- JsonViewer component (CSV/JSON/Copy buttons)
- Crawling results page

---

### 4. Empty State Component 📭

**Status**: ✅ Implemented
**Category**: UI/UX
**Impact**: Medium

데이터가 없을 때 표시되는 친절한 빈 상태 화면입니다.

**Usage**:
```tsx
import { EmptyState } from "@/components/dashboard/EmptyState"

{sources.length === 0 ? (
  <EmptyState
    icon="📭"
    title="등록된 소스가 없습니다"
    description="새 크롤링 소스를 추가해보세요"
    action={{
      label: "소스 추가하기",
      onClick: () => setTab('add')
    }}
  />
) : (
  <Table>...</Table>
)}
```

**Props**:
- `icon`: Emoji icon (default: "📭")
- `title`: Main message (required)
- `description`: Optional description
- `action`: Optional button action
- `className`: Custom styling

---

### 5. Loading Skeleton 💀

**Status**: ⏳ Planned
**Category**: UI/UX
**Impact**: Medium

**Feature Description**:
데이터 로딩 중 스켈레톤 UI를 표시하여 체감 속도를 향상시킵니다.

**Usage** (Planned):
```tsx
import { Skeleton } from "@/components/ui/skeleton"

{isLoading ? (
  <Skeleton className="h-20 w-full" />
) : (
  <StatCard {...props} />
)}
```

---

### 6. Theme Toggle 🌓

**Status**: ⏳ Planned
**Category**: UI/UX
**Impact**: Low

**Feature Description**:
Dark/Light 모드 전환 기능입니다.

**Usage** (Planned):
```tsx
const [theme, setTheme] = useState('dark')

<Button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
  {theme === 'dark' ? <Sun /> : <Moon />}
</Button>
```

---

### 7. Confirmation Modal ⚠️

**Status**: ⏳ Planned
**Category**: UI/UX
**Impact**: High

**Feature Description**:
삭제 등 중요한 작업 전 확인 다이얼로그를 표시합니다.

**Usage** (Planned):
```tsx
<AlertDialog>
  <AlertDialogTrigger>삭제</AlertDialogTrigger>
  <AlertDialogContent>
    <AlertDialogTitle>정말 삭제하시겠습니까?</AlertDialogTitle>
    <AlertDialogDescription>
      이 작업은 되돌릴 수 없습니다.
    </AlertDialogDescription>
    <AlertDialogAction onClick={handleDelete}>확인</AlertDialogAction>
  </AlertDialogContent>
</AlertDialog>
```

---

## 🚀 Priority Features

### 1. Crawling Scheduler 🕐

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 3-4 hours

**Feature Description**:
크롤링 작업을 자동으로 스케줄링합니다.

**Planned Features**:
- Daily/Weekly/Monthly 스케줄
- Cron expression 지원
- Timezone 설정
- 다음 실행 시간 표시
- 스케줄 활성화/비활성화
- 스케줄 히스토리

**API Endpoints** (Planned):
```
POST /api/v1/scheduler/add
GET  /api/v1/scheduler/list
PUT  /api/v1/scheduler/{id}/toggle
DELETE /api/v1/scheduler/{id}
```

---

### 2. Webhook System 🔔

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 2-3 hours

**Feature Description**:
크롤링 완료 시 자동으로 외부 URL로 알림을 전송합니다.

**Planned Features**:
- Slack/Discord/Custom endpoint 지원
- Retry logic (최대 3회)
- Webhook 로그 저장
- 테스트 전송 기능
- Payload 템플릿 커스터마이징

**Payload Example** (Planned):
```json
{
  "event": "crawl_completed",
  "source_id": "product_catalog",
  "source_name": "Product Catalog",
  "status": "success",
  "items_count": 150,
  "crawled_at": "2025-11-08T10:30:00Z",
  "duration_ms": 5430
}
```

---

### 3. Audit Log / Activity Trail 📜

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 4-5 hours

**Feature Description**:
모든 사용자 액션을 기록하고 추적합니다.

**Planned Features**:
- 모든 API 호출 기록
- 사용자별 액션 히스토리
- IP 주소, User-Agent 기록
- 필터링 (날짜, 사용자, 액션 타입)
- Export to CSV

**Tracked Actions** (Planned):
- 크롤링 시작/중지
- 소스 추가/수정/삭제
- 사용자 생성/권한 변경
- 로그인/로그아웃
- 설정 변경

---

### 4. Usage Dashboard 📊

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 6-8 hours

**Feature Description**:
API 사용량을 시각화합니다.

**Planned Features**:
- API 호출 수 (일별/월별 그래프)
- Endpoint별 사용 통계
- 응답 시간 분포 (histogram)
- 에러율 추이
- Top users (가장 많이 사용하는 사용자)
- Rate limit 근접 경고

**Charts** (Planned):
- Line Chart: API calls over time
- Bar Chart: Top endpoints
- Pie Chart: Success vs. Error rate
- Histogram: Response time distribution

---

### 5. Team Management 👥

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 8-10 hours

**Feature Description**:
팀 협업 기능을 제공합니다.

**Planned Features**:
- 팀원 초대 (이메일)
- 역할 할당 (Admin, Manager, Viewer)
- 초대 링크 생성 (7일 만료)
- 팀원 권한 수정/삭제
- 팀원별 활동 통계

**Roles** (Planned):
- Super-user: 모든 권한
- Admin: 사용자 관리, 설정 변경
- Manager: 읽기 + 크롤링 시작
- Viewer: 읽기만 가능

---

### 6. Notification Center 🔔

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: High
**Implementation Time**: 6-8 hours

**Feature Description**:
인앱 알림 센터입니다.

**Planned Features**:
- 크롤링 완료 알림
- 시스템 공지사항
- 청구서 발행 알림
- Rate limit 경고
- 읽음/안 읽음 상태
- 알림 설정 (켜기/끄기)
- WebSocket 실시간 알림

---

### 7. Advanced Search & Filtering 🔍

**Status**: ⏳ Planned
**Category**: Functionality
**Impact**: Medium
**Implementation Time**: 4-5 hours

**Feature Description**:
크롤링 결과에 대한 고급 검색 및 필터링 기능입니다.

**Planned Features**:
- 키워드 검색 (title, content)
- 날짜 범위 필터
- 카테고리 필터
- 소스별 필터
- 정렬 (날짜, 이름, 아이템 수)
- 페이지네이션

---

## 📖 Usage Guide

### 1. Enable/Disable Features

1. Navigate to `/admin/settings`
2. Search for feature or browse by category
3. Toggle switch to enable/disable
4. Changes apply immediately

### 2. Export Data

**From Crawling Results**:
1. Go to `/admin/crawling`
2. Click "크롤링 결과" tab
3. Select a source
4. Click CSV or JSON button in JsonViewer

**Programmatically**:
```typescript
import { exportCSV, exportJSON } from "@/lib/utils/export"

// Export crawl results
exportJSON(results, "crawl_results_2025-11-08.json")
exportCSV(results, "crawl_results_2025-11-08.csv")
```

### 3. Use Empty States

```tsx
import { EmptyState } from "@/components/dashboard/EmptyState"

function MyComponent() {
  const data = []

  if (data.length === 0) {
    return (
      <EmptyState
        icon="🔍"
        title="검색 결과가 없습니다"
        description="다른 키워드로 검색해보세요"
      />
    )
  }

  return <DataTable data={data} />
}
```

### 4. Show Toast Notifications

```typescript
import { toast } from "sonner"

// On success
const handleSubmit = async () => {
  try {
    await api.createSource(data)
    toast.success("소스가 추가되었습니다!")
  } catch (error) {
    toast.error("소스 추가에 실패했습니다")
  }
}
```

---

## ⚙️ Configuration

### Feature Flags Storage

Features are stored in `localStorage`:
```
Key: rag-enterprise-features
Format: JSON
```

### Reset to Defaults

Settings 페이지에서 "기본값 복원" 버튼 클릭

### Programmatic Access

```typescript
import { useFeatures, useFeature } from "@/contexts/FeatureContext"

// Check if feature is enabled
const isEnabled = useFeature('toast-notifications')

// Get all features
const { features, toggle, enable, disable } = useFeatures()
```

---

## 📊 Feature Matrix

| Feature | Status | Impact | Time | Category |
|---------|--------|--------|------|----------|
| Feature Flag System | ✅ | High | 2h | Functionality |
| Toast Notifications | ✅ | High | 15min | UI/UX |
| Copy to Clipboard | ✅ | Low | 10min | Functionality |
| Data Export (CSV/JSON) | ✅ | High | 2h | Functionality |
| Empty State | ✅ | Medium | 15min | UI/UX |
| Settings Page | ✅ | High | 3h | Functionality |
| Crawling Scheduler | ⏳ | High | 3-4h | Functionality |
| Webhook System | ⏳ | High | 2-3h | Functionality |
| Audit Log | ⏳ | High | 4-5h | Functionality |
| Usage Dashboard | ⏳ | High | 6-8h | Functionality |
| Team Management | ⏳ | High | 8-10h | Functionality |
| Notification Center | ⏳ | High | 6-8h | Functionality |
| Advanced Search | ⏳ | Medium | 4-5h | Functionality |

**Legend**:
- ✅ Implemented
- ⏳ Planned
- ❌ Disabled

---

## 🔮 Roadmap

### Phase 1 (Current) - Core Features ✅
- Feature Flag System
- Toast Notifications
- Copy Utilities
- Data Export
- Empty States
- Settings Page

### Phase 2 (Next) - Automation
- Crawling Scheduler
- Webhook System
- Auto-Refresh

### Phase 3 - Monitoring
- Audit Log
- Usage Dashboard
- Error Monitoring

### Phase 4 - Collaboration
- Team Management
- Notification Center
- Advanced Permissions

---

## 📝 Notes

### Browser Compatibility

- Chrome: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Edge: ✅ Full support

### Performance

- Feature checks: < 1ms (in-memory)
- Toast rendering: < 10ms
- Export operations: < 100ms for 1000 items

### Security

- Feature flags are client-side only (UI control)
- Server-side permissions still enforced
- No sensitive data in localStorage

---

**Version**: v5.1.0
**Last Updated**: 2025-11-08
**Documentation**: FEATURES.md
**License**: MIT
