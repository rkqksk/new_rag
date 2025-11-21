# CI/CD Implementation Plan

## Goal
Fix and consolidate the CI/CD workflows to ensure a "proper" and functional pipeline.

## Current State
- `ci.yml` exists but will fail due to missing `type-check` script in `package.json`.
- `cd.yml` exists but deployment steps are commented out.
- `ci.yaml` and `cd.yaml` are already gone (good).
- `task.md` lists CI/CD cleanup as incomplete.

## Proposed Changes

### 1. Fix Type Checking
The `ci.yml` workflow calls `pnpm type-check`, but this script is missing.

#### [MODIFY] [package.json](file:///home/rkqksk/projects/new_rag/package.json)
- Add `"type-check": "turbo run type-check"` to `scripts`.

#### [MODIFY] [turbo.json](file:///home/rkqksk/projects/new_rag/turbo.json)
- Add `type-check` to the pipeline.

#### [MODIFY] [apps/web/package.json](file:///home/rkqksk/projects/new_rag/apps/web/package.json)
- Add `"type-check": "tsc --noEmit"` to `scripts`.

### 2. Verify CI Workflow
- Ensure `ci.yml` runs all necessary checks:
    - Lint (Node.js)
    - Type Check (Node.js)
    - Backend Tests (Python)
    - Build Frontend
    - Security Scan

### 3. Refine CD Workflow
- The `cd.yml` is currently a template.
- I will uncomment the `kubectl` commands but wrap them in a conditional or ensure they are valid.
- **Note**: Actual deployment requires a running K8s cluster and secrets (`KUBE_CONFIG` or similar). I will add a check for secrets or leave them commented with a clearer TODO if credentials are not available.
- Given the user's request "proper CI/CD", I will assume they want the *workflow file* to be correct, even if the environment isn't ready.

### 4. Update Documentation
- Update `task.md` to mark CI/CD tasks as complete.

## Verification Plan

### Automated Tests
- Run `pnpm type-check` locally to verify it works.
- Run `pnpm lint` locally.
- Run `pytest` locally.

### Manual Verification
- I cannot run GitHub Actions locally, but I can verify the scripts they call.
- I will verify `docker build` works (already in `task.md` as TASK-021).

## User Review Required
- Please confirm if you want `cd.yml` to have active `kubectl` commands or if they should remain commented out until the cluster is ready.
- I will assume active but needing secrets.
