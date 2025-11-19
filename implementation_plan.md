# v10.0.0 Implementation Plan

**Date**: 2025-11-19
**Status**: Strategic Planning Complete
**Type**: Technical Roadmap & Execution Guide
**Companion Doc**: `task.md` (Detailed Task List)

---

## 1. Executive Summary

This document provides **strategic guidance** for completing the v10.0.0 migration. While `task.md` lists 60 discrete tasks, this plan focuses on:

- **Technical decisions** and trade-offs
- **Risk mitigation** strategies
- **Best practices** for each phase
- **Quality gates** and validation criteria
- **Rollback procedures**

### Current State Assessment

```
┌─────────────────────────────────────────────────────────────┐
│ INCOMPLETE MIGRATION                                        │
├─────────────────────────────────────────────────────────────┤
│ Backend:   [████████░░] 80% (apps/api works, legacy exists)│
│ Frontend:  [███░░░░░░░] 30% (skeleton only)                │
│ Packages:  [██████░░░░] 60% (core good, ui empty)          │
│ Services:  [█░░░░░░░░░] 10% (scaffolds only)               │
│ Tests:     [█████████░] 90% (exist but target unclear)     │
│ Docs:      [████░░░░░░] 40% (outdated, optimistic)         │
└─────────────────────────────────────────────────────────────┘
Overall: 52% Complete (was claimed 100%)
```

### Strategic Priorities

1. **Eliminate Confusion**: Single source of truth (no legacy code)
2. **Establish Baseline**: Tests must pass against new structure
3. **Functional Frontend**: `apps/web` must reach feature parity
4. **Honest Documentation**: Reflect actual state, not aspirations
5. **Defer Microservices**: Focus on monolith first ("Monolith First" strategy)

---

## 2. Phase 1: Immediate Cleanup

**Duration**: 1 day
**Parallelization**: Medium (some tasks can run concurrently)
**Risk Level**: Medium (code deletion)

### 2.1 Pre-Cleanup Validation

**Before deleting anything**, verify that `apps/api` is the superset of legacy backends.

#### Technical Approach

```bash
# 1. List all Python modules in legacy backends
find app/ -name "*.py" | grep -v "__pycache__" > legacy_app_modules.txt
find backend/ -name "*.py" | grep -v "__pycache__" > legacy_backend_modules.txt

# 2. List all Python modules in new backend
find apps/api/ -name "*.py" | grep -v "__pycache__" > new_api_modules.txt

# 3. Compare module counts
wc -l legacy_app_modules.txt legacy_backend_modules.txt new_api_modules.txt

# 4. Identify unique features in legacy code
# Search for function definitions
grep -r "^def " app/ backend/ | cut -d: -f2 | sort | uniq > legacy_functions.txt
grep -r "^def " apps/api/ | cut -d: -f2 | sort | uniq > new_functions.txt
comm -23 legacy_functions.txt new_functions.txt > missing_functions.txt
```

#### Decision Matrix

| Scenario | Action |
|----------|--------|
| `apps/api` has **more** modules/functions | ✅ Safe to archive legacy |
| `apps/api` has **equal** modules/functions | ⚠️ Manual review of critical paths |
| `apps/api` has **fewer** modules/functions | 🛑 STOP - Investigate missing code |

#### Rollback Procedure

```bash
# If archiving causes issues, restore immediately
cp -r .archive/app-v9 app
cp -r .archive/backend-v9 backend
git checkout HEAD -- .  # Discard cleanup commits
```

### 2.2 Frontend Cleanup Strategy

**Critical Decision**: Do NOT archive `frontend-v2` in Phase 1.

**Rationale**:
- `frontend-v2` contains **50+ shadcn/ui components**
- `apps/web` is a skeleton with placeholders
- Migration will take 56 hours (Phase 3)
- Premature deletion = loss of UI assets

**Archive Only**: `frontend/` (static HTML, confirmed obsolete)

### 2.3 CI/CD Consolidation

**Technical Detail**:
- GitHub Actions prioritizes `.yml` over `.yaml` when both exist
- Current state: `.yml` and `.yaml` both exist → undefined behavior

**Action**:
```bash
# Compare files first
diff .github/workflows/ci.yml .github/workflows/ci.yaml

# If identical, delete .yaml
rm .github/workflows/ci.yaml .github/workflows/cd.yaml

# If different, manual merge required
```

**Validation**:
```bash
# Trigger workflow manually via GitHub UI
# Or push to test branch
git checkout -b test-ci-consolidation
git push origin test-ci-consolidation
# Observe Actions tab
```

### 2.4 Quality Gate

**Criteria to Proceed to Phase 2**:
- [ ] Legacy directories archived (not deleted from git history)
- [ ] `git status` shows clean tree (or only .archive changes)
- [ ] CI/CD workflow triggers successfully
- [ ] No immediate errors in IDE (import errors, etc.)
- [ ] Documented comparison results showing `apps/api` completeness

---

## 3. Phase 2: Verification & Testing

**Duration**: 3-5 days
**Parallelization**: Low (sequential execution required)
**Risk Level**: High (reveals unknown issues)

### 3.1 Import Path Migration Strategy

**Challenge**: Tests currently use `from app.` or `from backend.`

**Automated Approach**:

```bash
# Step 1: Analyze current import patterns
grep -r "from app\." tests/ | wc -l
grep -r "from backend\." tests/ | wc -l
grep -r "import app\." tests/ | wc -l

# Step 2: Dry run (safe)
find tests/ -type f -name "*.py" -exec grep -l "from app\." {} \; > files_to_update.txt

# Step 3: Backup
cp -r tests/ tests.backup/

# Step 4: Execute replacement
find tests/ -type f -name "*.py" -exec sed -i 's/from app\./from apps.api./g' {} \;
find tests/ -type f -name "*.py" -exec sed -i 's/from backend\./from apps.api./g' {} \;
find tests/ -type f -name "*.py" -exec sed -i 's/import app\./import apps.api./g' {} \;

# Step 5: Verify no accidental replacements
git diff tests/
```

**Manual Review Required**:
- Imports like `from app import create_app` → May need `from apps.api.main import app`
- Fixture imports in `conftest.py`
- Mock paths in test files

### 3.2 Test Execution Strategy

**Incremental Approach** (preferred over "run all tests"):

```bash
# Level 1: Sanity check (fastest tests first)
pytest tests/unit/test_health.py -v

# Level 2: Critical path tests
pytest tests/unit/test_dependencies.py tests/unit/test_schemas.py -v

# Level 3: Service layer
pytest tests/unit/services/ -v

# Level 4: Full unit suite
pytest tests/unit/ -v --tb=short

# Level 5: Integration tests (requires Docker)
docker-compose up -d
pytest tests/integration/ -v --tb=short

# Level 6: E2E tests
pytest tests/e2e/ -v --tb=short
```

**Rationale**: Early failure detection prevents wasted time running full suite.

### 3.3 Common Failure Patterns & Fixes

#### Pattern 1: Import Errors

```python
# Error
ModuleNotFoundError: No module named 'app.services'

# Fix
# In tests/unit/services/test_search_service.py
- from app.services.search_service import SearchService
+ from apps.api.services.search_service import SearchService
```

#### Pattern 2: Fixture Path Issues

```python
# Error in conftest.py
@pytest.fixture
def app():
    from app.main import create_app  # Old path
    return create_app()

# Fix
@pytest.fixture
def app():
    from apps.api.main import app  # New structure
    return app
```

#### Pattern 3: Database Connection Issues

```python
# Error
sqlalchemy.exc.OperationalError: could not connect to server

# Fix
# Ensure docker-compose is running
docker-compose ps  # Check status
docker-compose up -d postgres  # Start if needed

# Update DATABASE_URL in .env.test
DATABASE_URL=postgresql://user:pass@localhost:15432/test_db
```

#### Pattern 4: Qdrant Connection Errors

```python
# Error
ConnectionError: [Errno 111] Connection refused (Qdrant)

# Fix
docker-compose restart qdrant
# Wait for health check
curl http://localhost:6333/health
```

### 3.4 Coverage Baseline

**Goal**: Establish baseline before adding new code.

```bash
# Generate coverage report
pytest tests/ --cov=apps.api --cov=packages --cov-report=html --cov-report=term

# View report
open htmlcov/index.html

# Export baseline
pytest tests/ --cov=apps.api --cov-report=json -q
cp coverage.json coverage_baseline_v10.json
```

**Acceptance Criteria**:
- Overall coverage: ≥ 70% (target: 80%)
- Critical modules (routing, services): ≥ 85%
- No critical path with 0% coverage

### 3.5 Quality Gate

**Criteria to Proceed to Phase 3**:
- [ ] ≥ 80% of unit tests passing
- [ ] ≥ 70% of integration tests passing
- [ ] All import errors resolved
- [ ] Coverage baseline established (≥ 70%)
- [ ] CI/CD pipeline green
- [ ] Performance regression check (API response < 500ms for search)

---

## 4. Phase 3: Frontend Migration

**Duration**: 7-10 days
**Parallelization**: High (components can be migrated in parallel)
**Risk Level**: Medium (UI-only, limited backend impact)

### 4.1 Migration Architecture Decision

**Option A**: Migrate to `packages/ui` (Shared Component Library)
**Option B**: Migrate to `apps/web/components` (App-Specific)

**Recommendation**: **Hybrid Approach**

```
packages/ui/          ← Base components (button, input, card)
apps/web/components/  ← Composed components (SearchBar, ProductCard)
```

**Rationale**:
- Base components in `packages/ui` → Reusable in `apps/mobile`, `apps/pwa`
- App-specific compositions in `apps/web` → Avoid premature abstraction

### 4.2 Component Migration Priority

**Tier 1: Foundation** (Migrate First)
- `button`, `input`, `label`, `card`, `badge`
- **Dependency**: None
- **Timeline**: Day 1

**Tier 2: Forms** (Depends on Tier 1)
- `select`, `checkbox`, `radio-group`, `textarea`, `switch`
- **Dependency**: `button`, `label`
- **Timeline**: Day 2

**Tier 3: Overlays** (Depends on Tier 1)
- `dialog`, `alert-dialog`, `popover`, `tooltip`, `sheet`
- **Dependency**: `button`, Portal API
- **Timeline**: Day 3

**Tier 4: Data Display** (Depends on Tier 1, 3)
- `table`, `tabs`, `accordion`, `dropdown-menu`
- **Dependency**: `button`, `dialog`
- **Timeline**: Day 4

**Tier 5: Feedback** (Depends on Tier 1)
- `toast`, `alert`, `progress`, `skeleton`
- **Dependency**: `card`, `button`
- **Timeline**: Day 5

### 4.3 Pure Black Design System Adaptation

**Critical Rule**: Remove ALL icons during migration.

**Before (frontend-v2)**:
```tsx
// frontend-v2/components/ui/button.tsx
import { ChevronRight } from "lucide-react"

<Button>
  Next <ChevronRight className="ml-2" />
</Button>
```

**After (apps/web or packages/ui)**:
```tsx
// packages/ui/components/button.tsx
// NO icon imports

<Button>
  Next →  {/* Use Unicode arrow instead */}
</Button>
```

**Validation Script**:
```bash
# Ensure no icon imports exist
grep -r "lucide-react" packages/ui/ apps/web/
grep -r "react-icons" packages/ui/ apps/web/
grep -r "heroicons" packages/ui/ apps/web/

# Should return: no results
```

### 4.4 API Integration Pattern

**Centralized API Client** (Recommended):

```typescript
// apps/web/lib/api-client.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export async function searchProducts(query: string, top_k = 5) {
  const response = await fetch(`${API_BASE}/api/v1/search/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, top_k })
  })

  if (!response.ok) throw new Error(`Search failed: ${response.statusText}`)
  return response.json()
}

// Usage in components
import { searchProducts } from '@/lib/api-client'

const results = await searchProducts("PET 용기", 10)
```

**Environment Configuration**:
```bash
# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8001

# apps/web/.env.production
NEXT_PUBLIC_API_URL=https://api.production.com
```

### 4.5 State Management Decision

**Scenario**: Do we need Redux/Zustand?

**Analysis**:
- `apps/web` is primarily a **search interface**, not a complex app
- Most state is **server state** (fetched from API)
- React Query/SWR is more appropriate than global state

**Recommendation**: **React Query** (or Next.js SWR)

```typescript
// apps/web/lib/queries.ts
import { useQuery } from '@tanstack/react-query'
import { searchProducts } from './api-client'

export function useProductSearch(query: string) {
  return useQuery({
    queryKey: ['products', query],
    queryFn: () => searchProducts(query),
    enabled: query.length > 0
  })
}

// In component
const { data, isLoading } = useProductSearch(searchTerm)
```

### 4.6 Testing Strategy

**Component Tests** (Jest + React Testing Library):
```typescript
// packages/ui/components/button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react'
import { Button } from './button'

test('renders button with text', () => {
  render(<Button>Click Me</Button>)
  expect(screen.getByText('Click Me')).toBeInTheDocument()
})

test('calls onClick when clicked', () => {
  const handleClick = jest.fn()
  render(<Button onClick={handleClick}>Click</Button>)
  fireEvent.click(screen.getByText('Click'))
  expect(handleClick).toHaveBeenCalledTimes(1)
})
```

**E2E Tests** (Playwright):
```typescript
// tests/e2e/search.spec.ts
import { test, expect } from '@playwright/test'

test('search flow', async ({ page }) => {
  await page.goto('http://localhost:3000')

  await page.fill('[placeholder="Search products..."]', 'PET 용기')
  await page.click('button:has-text("Search")')

  await expect(page.locator('.product-card')).toHaveCount(5)
  await expect(page.locator('.product-card').first()).toContainText('PET')
})
```

### 4.7 Quality Gate

**Criteria to Proceed to Phase 4**:
- [ ] All Tier 1-5 components migrated
- [ ] Zero icon imports (`grep -r "Icon" returns nothing`)
- [ ] `#000000` background enforced (no `#111`, `#1a1a1a`)
- [ ] API client functional (all endpoints working)
- [ ] ≥ 3 pages implemented (home, search, product detail)
- [ ] Component tests: ≥ 80% coverage
- [ ] E2E tests: Critical flows passing
- [ ] `pnpm build` succeeds with 0 errors
- [ ] Lighthouse score: ≥ 90 (Performance, Accessibility)

---

## 5. Phase 4: Package & Service Organization

**Duration**: 2-3 days
**Parallelization**: High
**Risk Level**: Low (refactoring, not feature changes)

### 5.1 Shared Logic Extraction

**Goal**: Move duplicated code from `apps/api` to `packages/core`.

**Identification Process**:
```bash
# Find potential candidates for extraction
# 1. Utils used in multiple files
find apps/api -name "utils.py" -o -name "helpers.py"

# 2. Common validators
grep -r "def validate_" apps/api/ | cut -d: -f1 | sort | uniq -c | sort -rn

# 3. Shared types
find apps/api -name "schemas.py" -o -name "models.py"
```

**Example Extraction**:

**Before**:
```
apps/api/services/search_service.py  ← has format_product()
apps/api/services/qa_service.py      ← has format_product() (duplicate!)
```

**After**:
```python
# packages/core/src/formatters/product.py
def format_product(product: dict) -> dict:
    """Shared product formatting logic."""
    return {
        "id": product["id"],
        "name": product["name"],
        # ...
    }

# apps/api/services/search_service.py
from packages.core.formatters.product import format_product
```

### 5.2 Configuration Package Strategy

**Create**: `packages/config` for environment-aware settings.

```python
# packages/config/src/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10

    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    class Config:
        env_file = ".env"

settings = Settings()

# Usage in apps/api
from packages.config import settings
```

**Benefits**:
- Single source of truth for config
- Reusable in `services/` when microservices are implemented
- Type-safe environment variables

### 5.3 Service Documentation Strategy

**Do NOT implement services** - Document their future purpose.

```markdown
# services/rag/README.md

# RAG Microservice (Planned)

**Status**: 🚧 Scaffold Only - Not Production Ready

## Purpose
Standalone RAG service for semantic search, to be extracted from `apps/api`.

## Current Implementation
👉 **All RAG functionality currently lives in `apps/api/rag_consultation/`**

## Roadmap
- [ ] Extract after `apps/api` reaches maturity
- [ ] Estimated timeline: Q2 2025
- [ ] See `docs/planning/MICROSERVICES_ROADMAP.md`

## DO NOT USE
This service is a placeholder and will return 404 errors.
```

### 5.4 Quality Gate

**Criteria to Proceed to Phase 5**:
- [ ] `packages/core` exports shared utilities
- [ ] `packages/config` manages all environment variables
- [ ] `packages/utils` contains generic helpers
- [ ] Package tests: ≥ 80% coverage
- [ ] All `services/` have README clarifying status
- [ ] No new code in `services/` (scaffold only)
- [ ] Dependency graph validated (no circular deps)

---

## 6. Phase 5: Documentation & Validation

**Duration**: 2-3 days
**Parallelization**: Medium
**Risk Level**: Low (documentation only)

### 6.1 Documentation Audit Checklist

| Document | Status | Action Required |
|----------|--------|-----------------|
| `CLAUDE.md` | ⚠️ Outdated | Update structure, remove legacy references |
| `README.md` | ⚠️ Optimistic | Clarify v10 incomplete items |
| `PROGRESS.md` | ⚠️ Misleading | Reset completion % to actual state |
| `V10_EXECUTION_PLAN.md` | ❌ Incorrect | Mark incomplete phases |
| `CHANGELOG.md` | ⚠️ Missing v10 details | Add comprehensive v10 notes |
| `docs/V7_COMPLETE_GUIDE.md` | ✅ OK | No changes needed |
| `docs/reference/SYMBOLS.md` | ⚠️ Needs update | Add new v10 symbols |

### 6.2 Validation Script Analysis

**Current Script**: `scripts/v10/validate_v10.sh`

**Expected Checks** (Add if missing):
```bash
#!/bin/bash

echo "v10 Structure Validation"

# 1. No legacy directories
if [ -d "app" ] || [ -d "backend" ]; then
    echo "❌ FAIL: Legacy backend directories exist"
    exit 1
fi

# 2. Frontend
if [ ! -d "apps/web" ]; then
    echo "❌ FAIL: apps/web missing"
    exit 1
fi

# 3. Packages exist
for pkg in core ui config utils; do
    if [ ! -d "packages/$pkg" ]; then
        echo "❌ FAIL: packages/$pkg missing"
        exit 1
    fi
done

# 4. Build succeeds
pnpm build || { echo "❌ FAIL: Build failed"; exit 1; }

# 5. Tests pass
pytest tests/ -q || { echo "❌ FAIL: Tests failed"; exit 1; }

# 6. Design system compliance
if grep -r "lucide-react" apps/ packages/; then
    echo "❌ FAIL: Icon imports found (violates Pure Black design)"
    exit 1
fi

echo "✅ All v10 validations passed"
```

### 6.3 Performance Baseline

**Metrics to Capture**:

```bash
# API Performance
echo "Testing API response times..."
time curl -X POST http://localhost:8001/api/v1/search/ \
  -H "Content-Type: application/json" \
  -d '{"query":"PET 용기","top_k":5}'

# Expected: < 500ms

# Frontend Build Time
echo "Testing frontend build..."
cd apps/web
time pnpm build
# Expected: < 60s

# Database Query Performance
psql -h localhost -p 15432 -U user -d rag_db -c "EXPLAIN ANALYZE SELECT * FROM products LIMIT 100;"
# Expected: < 10ms
```

**Establish Baseline Document**:
```markdown
# Performance Baseline v10.0.0

**Date**: 2025-11-19

## API
- Search endpoint: 287ms (avg)
- QA endpoint: 1.2s (avg)
- Health check: 12ms

## Frontend
- Build time: 43s
- Lighthouse Performance: 92/100
- First Contentful Paint: 1.1s

## Database
- Product query (100 rows): 7ms
- Vector search (top 5): 234ms
```

### 6.4 Quality Gate

**Criteria to Mark v10.0.0 as Complete**:
- [ ] All documentation updated and accurate
- [ ] `scripts/v10/validate_v10.sh` passes
- [ ] Test coverage ≥ 80%
- [ ] Performance baseline documented
- [ ] Security audit clean (no critical vulnerabilities)
- [ ] Design system compliance (no icons, `#000000` background)
- [ ] Zero legacy code (all archived)
- [ ] CI/CD pipeline green
- [ ] Release notes published

---

## 7. Risk Management

### 7.1 Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Test failures cascade | High | High | Incremental test execution (Phase 2) |
| Missing code in legacy | Medium | High | Pre-cleanup comparison (Phase 1) |
| Component design conflicts | Medium | Medium | Tier-based migration (Phase 3) |
| Performance regression | Low | High | Baseline measurement (Phase 5) |
| Timeline overrun | Medium | Medium | Buffer time (3-4 weeks vs 2-3 weeks) |

### 7.2 Rollback Procedures

**If Phase 1 Fails** (Cleanup causes critical issues):
```bash
# Restore from archive
cp -r .archive/app-v9 app
cp -r .archive/backend-v9 backend
git reset --hard HEAD~5  # Undo last 5 commits
```

**If Phase 2 Fails** (Tests unrecoverable):
```bash
# Restore test backup
rm -rf tests/
cp -r tests.backup/ tests/
# Fix imports manually with assistance
```

**If Phase 3 Fails** (Frontend unusable):
```bash
# Revert to frontend-v2 temporarily
cp -r .archive/frontend-v2-v2.0.0 frontend-v2
# Continue development in v2 while fixing v10
```

### 7.3 Go/No-Go Decision Points

**After Phase 1**:
- **GO IF**: Legacy code confirmed redundant, CI/CD green
- **NO-GO IF**: Missing critical code, services fail

**After Phase 2**:
- **GO IF**: ≥ 70% tests passing, clear path to fix remainder
- **NO-GO IF**: < 50% tests passing, architectural issues discovered

**After Phase 3**:
- **GO IF**: `apps/web` functional, design system compliant
- **NO-GO IF**: Performance issues, accessibility failures

**After Phase 5**:
- **GO IF**: All quality gates passed, validation script green
- **NO-GO IF**: Security vulnerabilities, critical bugs

---

## 8. Success Metrics

### 8.1 Quantitative Metrics

- **Code Cleanup**: 0 legacy directories (app, backend, frontend, frontend-v2)
- **Test Coverage**: ≥ 80% overall, ≥ 85% critical paths
- **Build Success**: 100% CI/CD pipeline green
- **Performance**: API < 500ms, Frontend build < 60s
- **Design Compliance**: 0 icon imports, 100% `#000000` backgrounds
- **Documentation**: 100% accuracy (no outdated claims)

### 8.2 Qualitative Metrics

- **Developer Confidence**: New devs know which code to modify (no confusion)
- **Maintainability**: Single source of truth established
- **Scalability**: Monorepo ready for additional apps
- **User Experience**: Functional frontend matching v2 feature parity

### 8.3 Release Readiness

**v10.0.0 is Ready for Release When**:
- ✅ All 5 phases completed
- ✅ Quality gates passed
- ✅ Stakeholder approval obtained
- ✅ Release notes published
- ✅ Rollback plan tested
- ✅ Deployment dry run successful

---

## 9. Post-Implementation

### 9.1 Monitoring Plan

**Week 1 After Release**:
- Daily performance checks
- Error rate monitoring (Sentry/logging)
- User feedback collection

**Week 2-4**:
- Weekly performance reviews
- Test coverage trending
- Technical debt assessment

### 9.2 Continuous Improvement

**Monthly Review**:
- Are microservices ready to extract?
- Is `packages/ui` being reused?
- Are new developers onboarding smoothly?

**Quarterly Planning**:
- Microservices roadmap progress
- Mobile app implementation readiness
- Advanced feature prioritization

---

## 10. Appendix

### 10.1 Tool Recommendations

**Code Migration**:
- `sed` for bulk find/replace
- `rg` (ripgrep) for fast searching
- `ast-grep` for syntax-aware refactoring

**Testing**:
- `pytest` with `--tb=short` for concise errors
- `pytest-xdist` for parallel execution
- `coverage.py` for detailed reports

**Documentation**:
- Markdown linters (`markdownlint`)
- Spell check (`codespell`)
- Link validation (`markdown-link-check`)

### 10.2 References

- **Monolith First**: https://martinfowler.com/bliki/MonolithFirst.html
- **Component Library Best Practices**: https://storybook.js.org/
- **Test-Driven Refactoring**: https://refactoring.com/

### 10.3 Contact & Support

**For Implementation Questions**:
- Review this document + `task.md`
- Check `docs/guides/TROUBLESHOOTING.md`
- Consult `CLAUDE.md` for quick reference

**For Blockers**:
- Document in `BLOCKERS.md`
- Escalate to project lead
- Consider rollback if critical

---

**End of Implementation Plan**

**Next Steps**:
1. Review this plan with team
2. Allocate 3-4 weeks for implementation
3. Begin Phase 1: Immediate Cleanup
4. Track progress in `task.md`
5. Update this document if strategy changes

**Success**: v10.0.0 complete, stable, and production-ready. 🚀
