# v10.0.0 Migration Tasks

**Date**: 2025-11-19
**Status**: Planning Complete - Ready for Implementation
**Priority**: Critical - Prevents Development Confusion

---

## Overview

This document consolidates findings from:
- `ANALYSIS_REPORT_V10_PLANNING.md`
- `STRUCTURE_AND_PACKAGE_ANALYSIS_REPORT_V2.md`

The v10.0.0 migration is **incomplete**. Legacy code coexists with new structure, causing:
- Development confusion (which codebase to modify?)
- Potential code divergence
- CI/CD ambiguity
- Test target uncertainty

**Critical Path**: Complete cleanup → verify tests → migrate frontend components

---

## Task Categories

### 🔴 Critical (Immediate)
Tasks that prevent development confusion and technical debt accumulation.

### 🟡 High Priority (Week 1)
Tasks required for v10.0.0 functional completeness.

### 🟢 Medium Priority (Week 2)
Enhancement and optimization tasks.

### 🔵 Future Work
Post-v10.0.0 improvements.

---

## Phase 1: Immediate Cleanup (🔴 Critical)

**Goal**: Remove legacy code to establish single source of truth.

### Backend Cleanup
- [ ] **TASK-001**: Verify `apps/api` functionality
  - **Action**: Run health checks, test all endpoints
  - **Validation**: `curl http://localhost:8001/health/ready`
  - **Estimated Time**: 30 minutes

- [ ] **TASK-002**: Archive `app/` directory
  - **Action**: `mv app .archive/app-v9/`
  - **Risk**: Medium - may contain unique code
  - **Mitigation**: Compare with `apps/api` before archiving
  - **Estimated Time**: 1 hour

- [ ] **TASK-003**: Archive `backend/` directory
  - **Action**: `mv backend .archive/backend-v9/`
  - **Risk**: Medium - may contain unique code
  - **Mitigation**: Compare with `apps/api` before archiving
  - **Estimated Time**: 1 hour

- [ ] **TASK-004**: Verify `src/` directory status
  - **Action**: Determine if legacy, archive if confirmed
  - **Estimated Time**: 30 minutes

### Frontend Cleanup
- [ ] **TASK-005**: Archive `frontend/` (static HTML)
  - **Action**: `mv frontend .archive/frontend-v1/`
  - **Risk**: Low - confirmed legacy
  - **Estimated Time**: 15 minutes

- [ ] **TASK-006**: Analyze `frontend-v2` components
  - **Action**: Document all shadcn/ui components for migration
  - **Output**: Component inventory list
  - **Estimated Time**: 2 hours

- [ ] **TASK-007**: Create migration checklist for `frontend-v2`
  - **Action**: List components to port to `packages/ui` or `apps/web`
  - **Dependencies**: TASK-006 complete
  - **Estimated Time**: 1 hour

### CI/CD Cleanup
- [ ] **TASK-008**: Consolidate CI workflow
  - **Action**: Keep `.github/workflows/ci.yml`, delete `ci.yaml`
  - **Validation**: GitHub Actions runs successfully
  - **Estimated Time**: 30 minutes

- [ ] **TASK-009**: Consolidate CD workflow
  - **Action**: Keep `.github/workflows/cd.yml`, delete `cd.yaml`
  - **Validation**: Deployment workflow triggers correctly
  - **Estimated Time**: 30 minutes

### Git Cleanup
- [ ] **TASK-010**: Update `.gitignore`
  - **Action**: Add `.archive/` to .gitignore
  - **Estimated Time**: 10 minutes

- [ ] **TASK-011**: Commit cleanup changes
  - **Action**: `git add . && git commit -m "chore(v10): Complete Phase 1 cleanup"`
  - **Estimated Time**: 15 minutes

**Phase 1 Total Time**: ~8 hours

---

## Phase 2: Verification & Testing (🔴 Critical)

**Goal**: Establish test baseline for new structure.

### Test Configuration
- [ ] **TASK-012**: Update `pytest.ini` to target `apps/api`
  - **Action**: Verify `testpaths = tests/` points to correct modules
  - **Estimated Time**: 30 minutes

- [ ] **TASK-013**: Update test imports
  - **Action**: Change `from app.` → `from apps.api.`
  - **Tool**: `find tests/ -type f -name "*.py" -exec sed -i 's/from app\./from apps.api./g' {}`
  - **Validation**: No import errors
  - **Estimated Time**: 2 hours

- [ ] **TASK-014**: Update test imports for `backend`
  - **Action**: Change `from backend.` → `from apps.api.`
  - **Estimated Time**: 1 hour

### Test Execution
- [ ] **TASK-015**: Run unit tests
  - **Action**: `pytest tests/unit/ -v`
  - **Expected**: Establish baseline pass rate
  - **Estimated Time**: 1 hour

- [ ] **TASK-016**: Fix failing unit tests
  - **Action**: Address import errors, deprecated APIs
  - **Dependencies**: TASK-015 identifies failures
  - **Estimated Time**: 4-8 hours

- [ ] **TASK-017**: Run integration tests
  - **Action**: `pytest tests/integration/ -v`
  - **Estimated Time**: 1 hour

- [ ] **TASK-018**: Fix failing integration tests
  - **Action**: Update API endpoints, service configurations
  - **Dependencies**: TASK-017 identifies failures
  - **Estimated Time**: 4-8 hours

- [ ] **TASK-019**: Run E2E tests
  - **Action**: `pytest tests/e2e/ -v`
  - **Estimated Time**: 1 hour

- [ ] **TASK-020**: Fix failing E2E tests
  - **Action**: Update frontend interactions if needed
  - **Dependencies**: TASK-019 identifies failures
  - **Estimated Time**: 2-4 hours

### Build Verification
- [ ] **TASK-021**: Verify backend build
  - **Action**: `cd apps/api && docker build -t api:test .`
  - **Estimated Time**: 30 minutes

- [ ] **TASK-022**: Verify frontend build
  - **Action**: `cd apps/web && pnpm build`
  - **Expected**: May have warnings due to TODOs
  - **Estimated Time**: 30 minutes

- [ ] **TASK-023**: Verify monorepo build
  - **Action**: `pnpm build` (root)
  - **Estimated Time**: 1 hour

**Phase 2 Total Time**: 18-28 hours

---

## Phase 3: Frontend Migration (🟡 High Priority)

**Goal**: Make `apps/web` fully functional by migrating from `frontend-v2`.

### Component Migration to `packages/ui`
- [ ] **TASK-024**: Create `packages/ui` structure
  - **Action**: Setup Tailwind, shadcn/ui in `packages/ui`
  - **Files**: `packages/ui/tailwind.config.js`, `packages/ui/tsconfig.json`
  - **Estimated Time**: 2 hours

- [ ] **TASK-025**: Migrate base components (Tier 1)
  - **Components**: button, input, label, card, badge
  - **Source**: `frontend-v2/components/ui/`
  - **Destination**: `packages/ui/components/`
  - **Adaptation**: Apply "Pure Black" design system
  - **Estimated Time**: 4 hours

- [ ] **TASK-026**: Migrate form components (Tier 2)
  - **Components**: select, switch, checkbox, radio-group, textarea
  - **Estimated Time**: 4 hours

- [ ] **TASK-027**: Migrate dialog components (Tier 3)
  - **Components**: alert-dialog, dialog, sheet, popover, tooltip
  - **Estimated Time**: 4 hours

- [ ] **TASK-028**: Migrate data components (Tier 4)
  - **Components**: table, tabs, accordion, dropdown-menu
  - **Estimated Time**: 4 hours

- [ ] **TASK-029**: Migrate feedback components (Tier 5)
  - **Components**: toast, alert, progress, skeleton
  - **Estimated Time**: 3 hours

### API Integration in `apps/web`
- [ ] **TASK-030**: Create API client in `apps/web`
  - **Action**: Implement fetch/axios wrapper pointing to `http://localhost:8001`
  - **File**: `apps/web/lib/api-client.ts`
  - **Estimated Time**: 2 hours

- [ ] **TASK-031**: Implement search functionality
  - **Action**: Replace `// TODO: Connect to apps/api`
  - **Endpoint**: `/api/v1/search/`
  - **Estimated Time**: 3 hours

- [ ] **TASK-032**: Implement product listing
  - **Action**: Fetch and display products
  - **Endpoint**: `/api/v1/products/`
  - **Estimated Time**: 2 hours

- [ ] **TASK-033**: Implement RAG Q&A
  - **Action**: Connect chat interface to QA endpoint
  - **Endpoint**: `/api/v1/qa/`
  - **Estimated Time**: 4 hours

### Layout & Pages
- [ ] **TASK-034**: Create main layout
  - **Action**: Header, sidebar, footer with Pure Black design
  - **File**: `apps/web/components/layout/MainLayout.tsx`
  - **Estimated Time**: 3 hours

- [ ] **TASK-035**: Implement home page
  - **Action**: Dashboard with search, recent products
  - **File**: `apps/web/app/page.tsx`
  - **Estimated Time**: 4 hours

- [ ] **TASK-036**: Implement search page
  - **Action**: Search interface with filters
  - **File**: `apps/web/app/search/page.tsx`
  - **Estimated Time**: 4 hours

- [ ] **TASK-037**: Implement product detail page
  - **Action**: Product view with specs
  - **File**: `apps/web/app/products/[id]/page.tsx`
  - **Estimated Time**: 3 hours

### Testing
- [ ] **TASK-038**: Add component tests
  - **Action**: Jest + React Testing Library tests
  - **Estimated Time**: 6 hours

- [ ] **TASK-039**: Add E2E tests with Playwright
  - **Action**: Critical user flows
  - **Files**: `tests/e2e/auth.spec.ts`, `tests/e2e/search.spec.ts`
  - **Estimated Time**: 4 hours

### Finalization
- [ ] **TASK-040**: Archive `frontend-v2`
  - **Action**: `mv frontend-v2 .archive/frontend-v2-v2.0.0/`
  - **Dependencies**: All TASK-024 to TASK-039 complete
  - **Estimated Time**: 15 minutes

**Phase 3 Total Time**: 56 hours

---

## Phase 4: Package & Service Organization (🟡 High Priority)

**Goal**: Optimize shared packages and clarify service status.

### Package Enhancement
- [ ] **TASK-041**: Populate `@rag/core` with shared logic
  - **Action**: Move common utilities from `apps/api` to `packages/core`
  - **Estimated Time**: 4 hours

- [ ] **TASK-042**: Create `@rag/config` package
  - **Action**: Shared configuration, environment variables
  - **Estimated Time**: 2 hours

- [ ] **TASK-043**: Create `@rag/utils` package
  - **Action**: Date helpers, validators, formatters
  - **Estimated Time**: 3 hours

- [ ] **TASK-044**: Add unit tests for packages
  - **Action**: Test coverage for `packages/*`
  - **Target**: 80%+ coverage
  - **Estimated Time**: 6 hours

### Service Documentation
- [ ] **TASK-045**: Document `services/` status
  - **Action**: Add README to each service clarifying "Scaffold Only"
  - **Files**: `services/rag/README.md`, etc.
  - **Estimated Time**: 1 hour

- [ ] **TASK-046**: Create microservices roadmap
  - **Action**: Plan for when to decompose `apps/api` monolith
  - **File**: `docs/planning/MICROSERVICES_ROADMAP.md`
  - **Estimated Time**: 2 hours

- [ ] **TASK-047**: Mark services as future work
  - **Action**: Update CLAUDE.md to clarify current monolith focus
  - **Estimated Time**: 30 minutes

**Phase 4 Total Time**: 18.5 hours

---

## Phase 5: Documentation & Validation (🟡 High Priority)

**Goal**: Update docs to reflect actual state and validate v10 completeness.

### Documentation Updates
- [ ] **TASK-048**: Update `V10_EXECUTION_PLAN.md`
  - **Action**: Reset "Completed" status where migration is incomplete
  - **Estimated Time**: 1 hour

- [ ] **TASK-049**: Update `PROGRESS.md`
  - **Action**: Add v10.0.0 actual completion status
  - **Estimated Time**: 1 hour

- [ ] **TASK-050**: Update `CHANGELOG.md`
  - **Action**: Document v10.0.0 changes accurately
  - **Estimated Time**: 1 hour

- [ ] **TASK-051**: Update `README.md`
  - **Action**: Remove references to legacy directories
  - **Estimated Time**: 30 minutes

- [ ] **TASK-052**: Update `CLAUDE.md`
  - **Action**: Reflect actual v10 structure and package usage
  - **Estimated Time**: 2 hours

- [ ] **TASK-053**: Create migration retrospective
  - **Action**: Document lessons learned from v9 → v10
  - **File**: `docs/planning/V10_MIGRATION_RETROSPECTIVE.md`
  - **Estimated Time**: 2 hours

### Validation
- [ ] **TASK-054**: Run `scripts/v10/validate_v10.sh`
  - **Action**: Execute validation script
  - **Expected**: All checks pass
  - **Estimated Time**: 30 minutes

- [ ] **TASK-055**: Fix validation failures
  - **Action**: Address any issues from TASK-054
  - **Estimated Time**: 2-4 hours

- [ ] **TASK-056**: Full test suite execution
  - **Action**: `pytest tests/ --cov=apps --cov=packages`
  - **Target**: 80%+ coverage
  - **Estimated Time**: 1 hour

- [ ] **TASK-057**: Performance baseline
  - **Action**: Measure API response times, frontend build times
  - **Output**: Performance report
  - **Estimated Time**: 2 hours

- [ ] **TASK-058**: Security audit
  - **Action**: Run `scripts/security-audit.sh`
  - **Estimated Time**: 1 hour

### Final Review
- [ ] **TASK-059**: Code review checklist
  - **Action**: Verify all TODOs resolved, design system compliance
  - **Estimated Time**: 2 hours

- [ ] **TASK-060**: Create v10.0.0 release notes
  - **Action**: Comprehensive release documentation
  - **File**: `RELEASE_NOTES_V10.0.0.md`
  - **Estimated Time**: 2 hours

**Phase 5 Total Time**: 18-20 hours

---

## Post-Implementation Tasks (🔵 Future Work)

### Service Implementation (Post-v10.0.0)
- [ ] Implement `services/rag` (Node.js microservice)
- [ ] Implement `services/collector` (Python scraping service)
- [ ] Implement `services/manufacturing` (Vision AI service)
- [ ] Implement `services/ml` (MLflow service)
- [ ] Implement `services/realtime` (Socket.IO standalone)

### Advanced Features
- [ ] Mobile app (`apps/mobile`) full implementation
- [ ] PWA (`apps/pwa`) offline capabilities
- [ ] Multi-tenant SaaS features
- [ ] Advanced analytics dashboard
- [ ] ML-powered recommendations

---

## Summary

**Total Estimated Time**: 118.5 - 138.5 hours (~3-4 weeks for 1 developer)

**Critical Path**:
1. Phase 1 (8h) → Phase 2 (18-28h) → Phase 3 (56h) → Phase 4 (18.5h) → Phase 5 (18-20h)

**Risk Areas**:
- Test failures in Phase 2 may cascade
- Component migration in Phase 3 may reveal design system conflicts
- Performance validation in Phase 5 may require optimizations

**Success Criteria**:
- ✅ Single source of truth (no legacy code)
- ✅ 80%+ test coverage
- ✅ `apps/web` fully functional
- ✅ All documentation accurate
- ✅ `scripts/v10/validate_v10.sh` passes
