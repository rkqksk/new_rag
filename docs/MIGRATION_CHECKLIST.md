# Backend Migration Checklist

**Quick reference for app/ + src/ → backend/ migration**

---

## Pre-Migration (30 min)

### Preparation
- [ ] Read BACKEND_MIGRATION_PLAN.md
- [ ] Read scripts/migration/README.md
- [ ] Current branch: `git status`
- [ ] All tests passing: `pytest tests/ -v`
- [ ] Services healthy: `docker-compose ps`
- [ ] Uncommitted changes: stash or commit

### Backups
- [ ] Create backup branch: `git branch backup-before-migration`
- [ ] Database backup (if needed): `pg_dump rag_enterprise > backup.sql`
- [ ] Note current metrics:
  ```bash
  # Test count
  pytest tests/ --collect-only | tail -1
  # Service health
  curl http://localhost:8001/health/ready
  ```

### Team Communication
- [ ] Notify team of migration window
- [ ] Expected downtime: ~30 min for rebuild
- [ ] Rollback plan communicated

---

## Migration Execution (3-4 hours)

### Option A: Automated (Recommended)

- [ ] **Dry run first**:
  ```bash
  ./scripts/migration/00_run_migration.sh --dry-run
  ```

- [ ] Review dry-run output

- [ ] **Execute migration**:
  ```bash
  ./scripts/migration/00_run_migration.sh
  ```

- [ ] Monitor output for errors/warnings

### Option B: Manual Step-by-Step

- [ ] **Phase 3B - Copy files**:
  ```bash
  ./scripts/migration/01_copy_src_to_backend.sh
  ```
  - Review conflicts (files ending in `_v2.py`)
  - Resolve manually if needed

- [ ] **Phase 3C - Update imports**:
  ```bash
  ./scripts/migration/02_update_imports.sh
  ```
  - Check for remaining old imports
  - Review backup in `.migration_backup_*/`

- [ ] **Manual updates**:
  - [ ] Update `backend/main.py` imports (see plan)
  - [ ] Update `docker-compose.yml`: `app.main` → `backend.main`
  - [ ] Update `Dockerfile`: `app.main` → `backend.main`
  - [ ] Update `pytest.ini`: `source = app` → `source = backend`
  - [ ] Update `alembic/env.py` imports

- [ ] **Phase 5 - Validation**:
  ```bash
  ./scripts/migration/03_validate_structure.sh
  ```
  - All tests must pass
  - 0 import errors

---

## Post-Migration Validation (1 hour)

### Build & Deploy
- [ ] Rebuild API container:
  ```bash
  docker-compose build api
  ```

- [ ] Start services:
  ```bash
  docker-compose up -d
  ```

- [ ] Wait for startup (30s):
  ```bash
  sleep 30
  ```

### Health Checks
- [ ] Liveness: `curl http://localhost:8001/health/live`
- [ ] Readiness: `curl http://localhost:8001/health/ready`
- [ ] All services: `docker-compose ps`

### API Testing
- [ ] **v1 Search API**:
  ```bash
  curl -X POST http://localhost:8001/api/v1/search/ \
    -H "Content-Type: application/json" \
    -d '{"query":"packaging","top_k":5}'
  ```

- [ ] **v1 Analytics API**:
  ```bash
  curl http://localhost:8001/api/v1/analytics/stats
  ```

- [ ] **v2 APIs** (if available):
  ```bash
  curl http://localhost:8001/api/v2/metrics/system
  ```

### Test Suite
- [ ] Quick tests:
  ```bash
  pytest tests/test_api_quick.py -v
  ```

- [ ] Full suite:
  ```bash
  pytest tests/ -v
  ```

- [ ] Integration tests:
  ```bash
  pytest tests/integration/ -v
  ```

### Log Review
- [ ] Check for import errors:
  ```bash
  docker-compose logs api | grep -i "importerror\|modulenotfounderror"
  ```

- [ ] Check for warnings:
  ```bash
  docker-compose logs api | grep -i "warning"
  ```

- [ ] Monitor real-time:
  ```bash
  docker-compose logs -f api
  ```

---

## Quality Assurance (30 min)

### Code Quality
- [ ] No `app.*` imports in backend/:
  ```bash
  grep -r "from app\." backend/ || echo "✓ Clean"
  ```

- [ ] No `src.*` imports in backend/:
  ```bash
  grep -r "from src\." backend/ || echo "✓ Clean"
  ```

- [ ] Syntax check:
  ```bash
  find backend/ -name "*.py" -exec python3 -m py_compile {} \;
  ```

### File Structure
- [ ] `backend/api/v1/` exists (11+ files)
- [ ] `backend/api/v2/` exists (5+ files)
- [ ] `backend/middleware/advanced/` exists
- [ ] `backend/core/advanced_rag/` exists
- [ ] `backend/auth/` exists
- [ ] `backend/db/` exists

### Metrics Comparison
- [ ] Test count matches pre-migration
- [ ] API response time <10% slower
- [ ] Memory usage stable
- [ ] All 17 services healthy

---

## Git Commit (15 min)

### Review Changes
- [ ] Check status:
  ```bash
  git status
  ```

- [ ] Diff review:
  ```bash
  git diff backend/main.py
  git diff docker-compose.yml
  ```

### Stage & Commit
- [ ] Stage changes:
  ```bash
  git add backend/ pytest.ini alembic/env.py docker-compose.yml Dockerfile scripts/
  ```

- [ ] Commit with standard message:
  ```bash
  git commit -m "feat: Unify app/ and src/ into backend/

  - Create backend/api/v2/ for v8-v9 experimental features
  - Create backend/middleware/advanced/ for Phase 9 middleware
  - Update all imports: app.* → backend.*, src.* → backend.*
  - Update Docker, pytest, alembic configs
  - All tests passing
  - Zero downtime migration

  BREAKING CHANGE: Import paths changed from app.*/src.* to backend.*

  Migrated files:
  - app/: 142 files
  - src/: 174 files
  - Total: 316 files

  API structure:
  - backend/api/v1/: Stable v7.x APIs
  - backend/api/v2/: Experimental v8-v9 APIs

  Co-authored-by: Claude <noreply@anthropic.com>"
  ```

- [ ] Tag migration:
  ```bash
  git tag -a v10.0.0-migration -m "Backend unification migration"
  ```

---

## Cleanup (Optional - After 7 days)

### Archive Old Directories
- [ ] After 1 week of stability, archive:
  ```bash
  mkdir -p archive/pre-migration/
  mv app/ archive/pre-migration/app_$(date +%Y%m%d)/
  mv src/ archive/pre-migration/src_$(date +%Y%m%d)/
  ```

- [ ] Update .gitignore:
  ```bash
  echo "archive/pre-migration/" >> .gitignore
  ```

- [ ] Commit cleanup:
  ```bash
  git add .gitignore
  git rm -r app/ src/
  git commit -m "chore: Archive pre-migration app/ and src/ directories"
  ```

---

## Rollback (If Needed)

### Immediate Rollback

If critical failures:

- [ ] Checkout backup:
  ```bash
  git checkout backup-before-migration
  ```

- [ ] Rebuild:
  ```bash
  docker-compose down
  docker-compose build api
  docker-compose up -d
  ```

- [ ] Verify:
  ```bash
  curl http://localhost:8001/health/ready
  pytest tests/test_api_quick.py -v
  ```

### Partial Rollback

If specific features broken:

- [ ] Restore file:
  ```bash
  git checkout backup-before-migration -- backend/api/v2/problematic.py
  ```

- [ ] Fix imports:
  ```bash
  sed -i 's/from src\./from backend./g' backend/api/v2/problematic.py
  ```

- [ ] Restart:
  ```bash
  docker-compose restart api
  ```

---

## Success Criteria

Migration is successful when:

- ✅ All tests passing (same count as before)
- ✅ 0 import errors in logs
- ✅ All 17 services healthy
- ✅ API response times within 10% of baseline
- ✅ v1 APIs unchanged behavior
- ✅ v2 APIs accessible (even if experimental)
- ✅ No `app.*` or `src.*` imports in backend/
- ✅ Clean git status
- ✅ Team notified of completion

---

## Timeline Summary

| Phase | Duration | Tasks |
|-------|----------|-------|
| Pre-migration | 30 min | Backups, checks, planning |
| Execution | 3-4 hours | Copy, update, validate |
| Post-validation | 1 hour | Build, test, verify |
| Git commit | 15 min | Review, commit, tag |
| **Total** | **5-6 hours** | |

---

## Quick Commands Reference

```bash
# Migration
./scripts/migration/00_run_migration.sh --dry-run   # Test run
./scripts/migration/00_run_migration.sh             # Execute

# Validation
./scripts/migration/03_validate_structure.sh        # Validate

# Docker
docker-compose build api                            # Rebuild
docker-compose up -d                                # Start
docker-compose ps                                   # Status
docker-compose logs -f api                          # Logs

# Testing
pytest tests/test_api_quick.py -v                   # Quick test
pytest tests/ -v                                    # Full suite
curl http://localhost:8001/health/ready             # Health

# Cleanup
grep -r "from app\." backend/                       # Check old imports
find backend/ -name "*_v2.py"                       # Find conflicts

# Rollback
git checkout backup-before-migration                # Full rollback
```

---

**Migration Checklist v1.0.0** | **Safe, Tested, Reversible**

Print this checklist and check off items as you complete the migration.
