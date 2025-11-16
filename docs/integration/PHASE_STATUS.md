# Frontend Migration Phase Status

**Plan**: FRONTEND_FILE_STRUCTURE_PLAN.md
**Version**: v1.0.0
**Last Updated**: 2025-11-15
**Status**: Ready to Start

---

## Phase Overview

| Phase | Description | Duration | Status | Start Date | End Date |
|-------|-------------|----------|--------|------------|----------|
| **Phase 1** | Archive deprecated code | 1 day | 🔴 Not Started | - | - |
| **Phase 2** | Move components to packages/ui | 1 week | 🔴 Not Started | - | - |
| **Phase 3** | Migrate HTML → React (6 features) | 4 weeks | 🔴 Not Started | - | - |
| **Phase 4** | Extract services | 2 weeks | 🔴 Not Started | - | - |
| **Phase 5** | Consolidate mobile | 2 weeks | 🔴 Not Started | - | - |
| **Phase 6** | Claude Code optimization | 1 week | 🔴 Not Started | - | - |
| **Phase 7** | Testing & validation | 1 week | 🔴 Not Started | - | - |

**Total**: 12 weeks | **Status Legend**: 🔴 Not Started | 🟡 In Progress | 🟢 Complete

---

## Phase 1: Archive Deprecated Code

**Status**: 🔴 Not Started
**Duration**: 1 day
**Script**: `pnpm migration:archive`

### Checklist

- [ ] Create `.archived/` directory
- [ ] Move `frontend-v2/` to `.archived/`
- [ ] Move `frontend-next/` to `.archived/`
- [ ] Move `mobile/` to `.archived/mobile-standalone/`
- [ ] Create `.archived/README.md` with documentation
- [ ] Update `.gitignore` to exclude `.archived/`
- [ ] Update `.claudeignore` to exclude `.archived/`
- [ ] Validate: Check for broken imports
- [ ] Validate: Ensure git status clean

### Success Criteria

- ✅ 3 directories archived
- ✅ `.archived/README.md` exists
- ✅ `.gitignore` updated
- ✅ `.claudeignore` updated
- ✅ No broken imports

### Notes

_Add notes during execution..._

---

## Phase 2: Move Dashboard Components

**Status**: 🔴 Not Started
**Duration**: 1 week
**Script**: `pnpm migration:components`

### Checklist

**Week 1 (Setup)**
- [ ] Create `packages/ui/src/dashboard/` directory
- [ ] Create `packages/ui/src/dashboard/__tests__/` directory
- [ ] Create barrel export `packages/ui/src/dashboard/index.ts`

**Component Migration**
- [ ] Move and parameterize `Sidebar` component
- [ ] Move and parameterize `Navbar` component
- [ ] Move and parameterize `StatsCard` component
- [ ] Move and parameterize `CollectionCard` component
- [ ] Move and parameterize `ProductCard` component
- [ ] Move and parameterize `SearchBar` component
- [ ] Move and parameterize `Filters` component

**Update Imports**
- [ ] Update all imports in `apps/web`
- [ ] Update `packages/ui/src/index.ts` to export dashboard

**Testing**
- [ ] Write unit tests for each component
- [ ] All component tests passing
- [ ] Visual regression tests (optional)

**Documentation**
- [ ] Generate component documentation
- [ ] Update Storybook (if exists)

### Success Criteria

- ✅ 7 components in `packages/ui/src/dashboard/`
- ✅ All components parameterized (brand-agnostic)
- ✅ All imports updated in `apps/web`
- ✅ All tests passing
- ✅ No hardcoded brand names

### Notes

_Add notes during execution..._

---

## Phase 3: Migrate HTML → React

**Status**: 🔴 Not Started
**Duration**: 4 weeks

### 3.1: chat.html → SearchPage (Week 3-4)

**Status**: 🔴 Not Started
**Script**: `pnpm migration:chat`

#### Checklist

**Week 3 (Components)**
- [ ] Create directory structure `apps/web/(customer)/search/`
- [ ] Create `page.tsx` main component
- [ ] Create `SearchHeader` component
- [ ] Create `SearchFilters` component
- [ ] Create `ProductGrid` component
- [ ] Reuse `ProductCard` from `@rag/ui`

**Week 4 (Features)**
- [ ] Create `ImageGallery` component
- [ ] Create `RecommendationsSidebar` component
- [ ] Create `EmptyState` component
- [ ] Create `useSearch` hook
- [ ] Create `useInfiniteScroll` hook
- [ ] Create `useImageGallery` hook

**Styling**
- [ ] Remove all emojis from UI
- [ ] Apply design-system.css
- [ ] Ensure neutral color scheme
- [ ] Remove gradient backgrounds

**Testing**
- [ ] Write unit tests for all components
- [ ] Write integration tests
- [ ] Write E2E tests (Playwright)
- [ ] Performance test: <500ms load time

#### Success Criteria

- ✅ All chat.html features migrated
- ✅ 0 emojis in UI
- ✅ Progressive loading works
- ✅ Image gallery functional
- ✅ Offline support works
- ✅ i18n works (Korean/English)
- ✅ Tests passing (80%+ coverage)
- ✅ Performance: <500ms initial render

#### Notes

_Add notes during execution..._

---

### 3.2: realtime-demo.html → RealtimePage (Week 5)

**Status**: 🔴 Not Started
**Script**: `pnpm migration:realtime`

#### Checklist

- [ ] Create directory structure `apps/web/(super-admin)/realtime/`
- [ ] Create `page.tsx` main component
- [ ] Create `RealtimeStatus` component
- [ ] Create `QueryExecutor` component
- [ ] Create `EventLog` component
- [ ] Create `ConnectionControls` component
- [ ] Enhance `useWebSocket` hook in `@rag/core`
- [ ] Remove dark theme (neutral light theme)
- [ ] Write tests
- [ ] Validate WebSocket connection

#### Success Criteria

- ✅ WebSocket connection functional
- ✅ Real-time query execution works
- ✅ Event log displays correctly
- ✅ Auto-reconnect functional
- ✅ No emojis
- ✅ Tests passing

#### Notes

_Add notes during execution..._

---

### 3.3-3.6: Remaining Features (Week 6)

**Status**: 🔴 Not Started

#### 3.3: profile.html → ProfilePage

- [ ] Create `apps/web/(customer)/profile/`
- [ ] Create ProfilePage components
- [ ] Remove avatar gradient
- [ ] Implement password change form
- [ ] Write tests

#### 3.4: rag_dashboard.html → RAGDashboardPage

- [ ] Create `apps/web/(admin)/rag/`
- [ ] Create file upload component
- [ ] Create collection manager
- [ ] Create embedding progress display
- [ ] Create log display
- [ ] Write tests

#### 3.5: dashboard.html → Enhanced Dashboard

- [ ] Enhance existing dashboard
- [ ] Add collection cards with badges
- [ ] Add stats display (neutral)
- [ ] Add recent activity
- [ ] Write tests

#### 3.6: streaming-demo.html → StreamingPage

- [ ] Create `apps/web/(super-admin)/streaming/`
- [ ] Create mode selector
- [ ] Create event stream display
- [ ] Create `useSSE` hook
- [ ] Write tests

#### Success Criteria

- ✅ All 4 features migrated
- ✅ All tests passing
- ✅ No emojis
- ✅ Design system applied

#### Notes

_Add notes during execution..._

---

## Phase 4: Extract Services

**Status**: 🔴 Not Started
**Duration**: 2 weeks
**Script**: `pnpm migration:services`

### Checklist

**Week 7 (Primary Services)**
- [ ] Create `packages/core/src/services/offline.service.ts`
  - [ ] Convert to TypeScript
  - [ ] Use IndexedDB instead of localStorage
  - [ ] Add async/await
  - [ ] Add proper error handling
  - [ ] Write unit tests
- [ ] Create `packages/core/src/services/i18n.service.ts`
  - [ ] Convert to TypeScript
  - [ ] Add type-safe translations
  - [ ] Support Korean/English
  - [ ] Write unit tests
- [ ] Create `packages/core/src/services/recommendations.service.ts`
  - [ ] Convert to TypeScript
  - [ ] Add API integration
  - [ ] Add caching
  - [ ] Write unit tests

**Week 8 (Secondary Services + Integration)**
- [ ] Create `packages/core/src/services/notifications.service.ts`
  - [ ] Convert to TypeScript
  - [ ] Add push notification support
  - [ ] Add browser notification API
  - [ ] Write unit tests
- [ ] Enhance `packages/core/src/services/auth.service.ts`
  - [ ] Add helpers from `frontend/js/auth.js`
  - [ ] Write additional tests

**Update Apps**
- [ ] Update `apps/web` to use new services
- [ ] Update `apps/mobile` to use new services
- [ ] Update `apps/pwa` to use new services

**Deprecate Legacy**
- [ ] Move `frontend/js/` to `.archived/`
- [ ] Update documentation

### Success Criteria

- ✅ 4 services created in `packages/core`
- ✅ All services TypeScript with type safety
- ✅ All services tested (80%+ coverage)
- ✅ Apps using new services
- ✅ `frontend/js/` archived

### Notes

_Add notes during execution..._

---

## Phase 5: Mobile Consolidation

**Status**: 🔴 Not Started
**Duration**: 2 weeks
**Script**: `pnpm migration:mobile`

### Checklist

**Week 9 (Consolidation)**
- [ ] Archive standalone `mobile/` to `.archived/mobile-standalone/`
- [ ] Copy missing screens from standalone to `apps/mobile/`
- [ ] Update `apps/mobile/` to use `@rag/mobile-ui`
- [ ] Update `apps/mobile/` to use `@rag/core`
- [ ] Configure Expo (`app.json`)
- [ ] Update all imports

**Week 10 (Testing)**
- [ ] Write mobile-specific tests
- [ ] Build iOS app (successful)
- [ ] Build Android app (successful)
- [ ] Test on physical devices
- [ ] Validate PWA functionality (`apps/pwa`)

### Success Criteria

- ✅ Single mobile app (`apps/mobile`)
- ✅ Uses `@rag/mobile-ui` components
- ✅ Uses `@rag/core` services
- ✅ Expo configured
- ✅ iOS build successful
- ✅ Android build successful
- ✅ All tests passing

### Notes

_Add notes during execution..._

---

## Phase 6: Claude Code Optimization

**Status**: 🔴 Not Started
**Duration**: 1 week

### Checklist

**Slash Commands**
- [ ] Create `/migrate-html` command
- [ ] Create `/test-rag` command
- [ ] Create `/validate-mobile` command
- [ ] Create `/new-component` command
- [ ] Create `/new-service` command
- [ ] Create `/analyze-bundle` command
- [ ] Update `.claude/commands/README.md`

**MCP Configuration**
- [ ] Optimize `.claude/mcp.json`
- [ ] Configure filesystem server with allowed directories
- [ ] Configure GitHub server
- [ ] Configure Serena server for TypeScript + Python

**Custom Agents (Optional)**
- [ ] Create frontend migration agent
- [ ] Create component extractor agent

**Symbol System**
- [ ] Update `docs/reference/SYMBOLS.md`
- [ ] Add v10.0.0 symbols

**Documentation**
- [ ] Update `CLAUDE.md`
- [ ] Update Claude Code workflows

### Success Criteria

- ✅ 6+ new slash commands
- ✅ MCP configuration optimized
- ✅ Symbol system updated
- ✅ Documentation complete

### Notes

_Add notes during execution..._

---

## Phase 7: Testing & Validation

**Status**: 🔴 Not Started
**Duration**: 1 week
**Script**: `pnpm migration:validate`

### Checklist

**Code Quality**
- [ ] All migration scripts executed successfully
- [ ] 0 HTML files in production
- [ ] 90%+ component reuse from `@rag/ui`
- [ ] 80%+ test coverage
- [ ] All tests passing (unit, integration, E2E)
- [ ] Visual regression tests passing
- [ ] No emojis in UI
- [ ] Design system applied consistently

**Performance**
- [ ] Build time <5 min
- [ ] Web bundle size <1MB
- [ ] Search page load <500ms
- [ ] Mobile build <3 min
- [ ] Lighthouse score >90

**Architecture**
- [ ] Backend migration complete (`app/` + `src/` → `backend/`)
- [ ] Frontend consolidation complete
- [ ] Mobile consolidation complete
- [ ] Shared packages functional (`@rag/ui`, `@rag/core`, `@rag/mobile-ui`)
- [ ] Monorepo optimized (Turborepo + pnpm)

**Documentation**
- [ ] All migration docs updated
- [ ] `FRONTEND_FILE_STRUCTURE_PLAN.md` validated
- [ ] `BACKEND_MIGRATION_PLAN.md` validated
- [ ] Component library documented
- [ ] API client documented
- [ ] Deployment guide updated

**Deployment**
- [ ] Development environment validated
- [ ] Staging environment validated
- [ ] Production environment ready
- [ ] Rollback plan tested
- [ ] Monitoring configured
- [ ] Alerts configured

**Team**
- [ ] All team members trained on new structure
- [ ] Migration guide reviewed
- [ ] Retrospective completed
- [ ] v10.0.0 release notes published

### Success Criteria

- ✅ All validation checks pass
- ✅ Production deployment successful
- ✅ v10.0.0 released

### Notes

_Add notes during execution..._

---

## Metrics Tracking

### Code Reduction

| Metric | Baseline | Current | Target | Progress |
|--------|----------|---------|--------|----------|
| Total LOC | TBD | - | -30% | 0% |
| Duplicate Code | 85% | - | <5% | 0% |
| Top-level Dirs | 35+ | - | 12 | 0% |

### Component Reuse

| Metric | Baseline | Current | Target | Progress |
|--------|----------|---------|--------|----------|
| Components in @rag/ui | 20 | - | 27+ | 0% |
| Reuse Rate | 20% | - | 90% | 0% |

### Performance

| Metric | Baseline | Current | Target | Progress |
|--------|----------|---------|--------|----------|
| Build Time | 8 min | - | <5 min | 0% |
| Bundle Size | TBD | - | <1MB | 0% |
| Page Load (Search) | TBD | - | <500ms | 0% |

### Testing

| Metric | Baseline | Current | Target | Progress |
|--------|----------|---------|--------|----------|
| Test Coverage | 50% | - | 80% | 0% |
| Unit Tests | TBD | - | 100+ | 0% |
| Integration Tests | TBD | - | 20+ | 0% |
| E2E Tests | TBD | - | 5+ | 0% |

---

## Weekly Reports

### Week 1 Report

**Dates**: TBD

**Completed**:
- [ ] TBD

**In Progress**:
- [ ] TBD

**Blocked**:
- [ ] TBD

**Metrics**:
- Code reduced: -%
- Component reuse: %
- Tests written:
- Coverage: %

**Risks**:
- None

**Next Week**:
- [ ] TBD

---

### Week 2 Report

**Dates**: TBD

_To be filled during execution..._

---

## Risk Log

| Date | Risk | Severity | Mitigation | Status |
|------|------|----------|------------|--------|
| - | - | - | - | - |

---

## Issue Log

| Date | Issue | Impact | Resolution | Status |
|------|-------|--------|------------|--------|
| - | - | - | - | - |

---

## Decisions Log

| Date | Decision | Rationale | Impact |
|------|----------|-----------|--------|
| 2025-11-15 | Use Turborepo for monorepo | Industry standard, great caching | Faster builds |
| 2025-11-15 | Archive instead of delete | Safety, easy rollback | Can restore if needed |

---

## Notes

_General notes during migration..._

---

**Last Updated**: 2025-11-15
**Next Review**: TBD (Week 1 start)
