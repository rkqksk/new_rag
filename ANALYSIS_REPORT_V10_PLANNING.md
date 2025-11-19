# v10.0.0 Codebase Analysis & Planning Report

**Date**: 2025-11-19
**Status**: Analysis Complete
**Target**: v10.0.0 "Unified Maximum"

---

## 1. Executive Summary

The `new_rag` project is currently in a **transitional state** between v9.3.0/v2.0.0 and v10.0.0. While the `V10_EXECUTION_PLAN.md` claims that structural transformation and backend unification are "Completed", the actual codebase reveals significant **incomplete migration artifacts**.

- **Backend**: The new unified backend exists at `apps/api`, but legacy `app` and `backend` directories persist, causing confusion and potential code divergence.
- **Frontend**: The new v10 frontend (`apps/web`) is a minimal skeleton (Next.js 15), while the previous version (`frontend-v2`) and legacy HTML (`frontend`) still exist.
- **Infrastructure**: CI/CD workflows are duplicated and conflicting.
- **Verification**: A comprehensive test suite exists, but its execution against the new structure is unverified.

**Immediate Action Required**: Clean up legacy directories to prevent development on the wrong codebase and verify the "Unified" components.

---

## 2. Detailed Findings

### 2.1 Backend Architecture
- **Current State**: Three distinct backend directories exist:
    1.  `apps/api` (Active v10): Contains the "Unified" FastAPI application with v10 features (Smart Caching, Rate Limiting, etc.).
    2.  `app` (Legacy): Contains a full backend structure.
    3.  `backend` (Legacy): Contains a full backend structure.
- **Issue**: `V10_EXECUTION_PLAN.md` marks backend unification as complete, but the presence of `app` and `backend` suggests the cleanup phase was skipped.
- **Recommendation**: Verify `apps/api` functionality and **delete** `app` and `backend`.

### 2.2 Frontend Architecture
- **Current State**:
    1.  `apps/web` (Active v10): Next.js 15 project. Currently a skeleton with a "Pure Black" design placeholder and TODOs (`// TODO: Connect to apps/api`).
    2.  `frontend-v2` (Previous v2): Next.js 14 project. More complete UI (shadcn/ui, radix-ui) but targets v2.0.0.
    3.  `frontend` (Legacy): Static HTML/JS files.
- **Issue**: `apps/web` is not yet a functional replacement for `frontend-v2`.
- **Recommendation**:
    - Archive `frontend` and `frontend-v2`.
    - Port necessary components and logic from `frontend-v2` to `apps/web`, upgrading to Next.js 15 patterns.

### 2.3 CI/CD & Infrastructure
- **Current State**: `.github/workflows` contains conflicting files:
    - `ci.yml` vs `ci.yaml`
    - `cd.yml` vs `cd.yaml`
- **Issue**: Ambiguous CI/CD configuration.
- **Recommendation**: Consolidate into single canonical workflow files (e.g., `ci.yml`, `cd.yml`) and remove duplicates.

### 2.4 Testing
- **Current State**: `tests/` directory is well-populated (Unit, Integration, E2E).
- **Issue**: It is unclear if these tests run against `apps/api` or the legacy backends.
- **Recommendation**: Update `pytest.ini` or test configuration to target `apps/api` and run the full suite to establish a baseline.

---

## 3. Action Plan (Roadmap to Completion)

### Phase 1: Cleanup (Immediate)
- [ ] **Delete** `app/` directory.
- [ ] **Delete** `backend/` directory.
- [ ] **Delete** `src/` directory (if confirmed legacy).
- [ ] **Archive** `frontend/` and `frontend-v2/` to `.archive/`.
- [ ] **Consolidate** `.github/workflows/` (Keep `*.yml`, delete `*.yaml`).

### Phase 2: Verification
- [ ] **Run Tests**: Execute `pytest` targeting `apps/api`.
- [ ] **Fix Tests**: Update imports in `tests/` to point to `apps.api`.
- [ ] **Verify Build**: Run `pnpm build` in `apps/web`.

### Phase 3: Implementation (Frontend)
- [ ] **Connect Frontend**: Implement API client in `apps/web` to talk to `apps/api`.
- [ ] **Port Components**: Move UI components from `frontend-v2` to `apps/web` (adapting for "Pure Black" design).

### Phase 4: Documentation
- [ ] **Update Plans**: Update `V10_EXECUTION_PLAN.md` to reflect the actual state (reset "Completed" status where appropriate).

---

## 4. Conclusion

The project has a solid foundation for v10 in `apps/api`, but the migration is incomplete. The presence of legacy code is a major technical debt that must be resolved immediately to avoid confusion. The `apps/web` frontend needs significant development to match the backend's maturity.
