# Backend Migration Scripts

**Purpose**: Safely migrate `app/` and `src/` directories into a unified `backend/` structure.

**Version**: v1.0.0
**Status**: Ready for execution

---

## Quick Start

### Option 1: Automated Migration (Recommended)

Run the master script that orchestrates all phases:

```bash
# Dry run (no changes made)
./scripts/migration/00_run_migration.sh --dry-run

# Full migration
./scripts/migration/00_run_migration.sh

# Full migration with auto-commit
./scripts/migration/00_run_migration.sh --auto-commit

# Skip pre-migration tests (faster)
./scripts/migration/00_run_migration.sh --skip-tests
```

### Option 2: Manual Step-by-Step

Execute each phase individually for more control:

```bash
# Phase 3B: Copy files
./scripts/migration/01_copy_src_to_backend.sh

# Phase 3C: Update imports
./scripts/migration/02_update_imports.sh

# Phase 5: Validate
./scripts/migration/03_validate_structure.sh
```

---

## Scripts Overview

### 00_run_migration.sh (Master Orchestrator)

**Purpose**: Runs the complete migration process with safety checks

**Features**:
- Pre-flight validation
- Automatic backup creation
- Dry-run mode
- Progress tracking
- Error handling
- Post-migration validation

**Usage**:
```bash
./scripts/migration/00_run_migration.sh [OPTIONS]

Options:
  --dry-run       Preview changes without applying them
  --skip-tests    Skip pre-migration test suite
  --auto-commit   Automatically commit changes after validation
```

**Duration**: ~4-6 hours (depending on manual review needs)

---

### 01_copy_src_to_backend.sh (Phase 3B)

**Purpose**: Copy src/ features into backend/ structure

**Actions**:
1. Creates `backend/api/v2/` directory
2. Copies src/api/routes/ → backend/api/v2/
3. Copies src/middleware/ → backend/middleware/advanced/
4. Copies src/services/ → backend/services/
5. Copies src/core/ subdirectories → backend/core/
6. Copies top-level modules (auth, db, integrations, etc.)

**Conflict Resolution**:
- If file exists and is identical: Skip
- If file exists and differs: Create `*_v2.py` version
- If file doesn't exist: Copy directly

**Output**:
```
Statistics:
  Files copied:    150
  Files skipped:   20
  Conflicts:       5
```

---

### 02_update_imports.sh (Phase 3C)

**Purpose**: Update all import statements to use `backend.*` namespace

**Transformations**:
```python
# Before
from app.core.config import settings
from src.api.routes.auth import router
from src.middleware.rate_limiting import RateLimitMiddleware

# After
from backend.core.config import settings
from backend.api.v2.auth import router
from backend.middleware.advanced.rate_limiting import RateLimitMiddleware
```

**Scope**:
- All Python files in `backend/`
- `pytest.ini`
- `alembic/env.py`
- `tests/` directory
- `scripts/` directory

**Safety**:
- Creates timestamped backup in `.migration_backup_*/`
- Validates syntax after changes
- Reports remaining old imports

---

### 03_validate_structure.sh (Phase 5)

**Purpose**: Comprehensive post-migration validation

**Tests**:
1. **Directory Structure** - Verify all expected directories exist
2. **File Counts** - Check v1/v2 API counts
3. **Import Validation** - Ensure no `app.*` or `src.*` imports remain
4. **Python Imports** - Test that modules can be imported
5. **Syntax Validation** - Check all Python files compile
6. **Configuration Files** - Verify pytest.ini, docker-compose.yml updated
7. **Key Files** - Ensure critical files exist
8. **API Structure** - Verify v2 routes are present

**Output**:
```
Results:
  Passed:   25
  Failed:   0
  Warnings: 3
```

**Exit Codes**:
- `0` - Validation passed
- `1` - Validation failed (rollback recommended)

---

## Migration Workflow

### Pre-Migration Checklist

- [ ] Review BACKEND_MIGRATION_PLAN.md
- [ ] Ensure all tests passing: `pytest tests/ -v`
- [ ] Commit or stash uncommitted changes
- [ ] Backup database if needed
- [ ] Notify team of migration

### During Migration

1. **Create backup branch**
   ```bash
   git branch backup-before-migration
   ```

2. **Run dry-run**
   ```bash
   ./scripts/migration/00_run_migration.sh --dry-run
   ```

3. **Execute migration**
   ```bash
   ./scripts/migration/00_run_migration.sh
   ```

4. **Review output** for any warnings or errors

5. **Manual fixes** (if needed):
   - Check backend/main.py imports
   - Resolve any conflicts in *_v2.py files
   - Update custom scripts

### Post-Migration Validation

1. **Rebuild Docker**
   ```bash
   docker-compose build api
   docker-compose up -d
   ```

2. **Test health endpoints**
   ```bash
   curl http://localhost:8001/health/ready
   curl http://localhost:8001/health/live
   ```

3. **Run test suite**
   ```bash
   pytest tests/ -v
   ```

4. **Test v1 APIs**
   ```bash
   curl -X POST http://localhost:8001/api/v1/search/ \
     -H "Content-Type: application/json" \
     -d '{"query":"test","top_k":5}'
   ```

5. **Monitor logs**
   ```bash
   docker-compose logs -f api | grep -i error
   ```

### Commit Changes

```bash
git add backend/ pytest.ini alembic/env.py docker-compose.yml Dockerfile scripts/
git commit -m "feat: Unify app/ and src/ into backend/

- Create backend/api/v2/ for v8-v9 experimental features
- Create backend/middleware/advanced/ for Phase 9 middleware
- Update all imports: app.* → backend.*, src.* → backend.*
- Update Docker, pytest, alembic configs

BREAKING CHANGE: Import paths changed from app.*/src.* to backend.*"

git tag -a v10.0.0-migration -m "Backend unification migration"
```

---

## Rollback Procedures

### Immediate Rollback (Within 1 hour)

If critical issues found:

```bash
# 1. Checkout backup branch
git checkout backup-before-migration

# 2. Rebuild containers
docker-compose down
docker-compose build api
docker-compose up -d

# 3. Verify
curl http://localhost:8001/health/ready
```

### Partial Rollback (Specific files)

If only certain features broken:

```bash
# Restore specific file from backup
git checkout backup-before-migration -- backend/api/v2/problematic_feature.py

# Fix imports
sed -i 's/from src\./from backend./g' backend/api/v2/problematic_feature.py

# Restart
docker-compose restart api
```

### Restore from Backup Directory

If migration scripts created backup:

```bash
# Find backup
ls -la .migration_backup_*

# Restore
rm -rf backend/
cp -r .migration_backup_TIMESTAMP/backend .

# Rebuild
docker-compose build api
docker-compose up -d
```

---

## Troubleshooting

### Issue: Import errors after migration

**Symptoms**:
```
ModuleNotFoundError: No module named 'app'
```

**Solution**:
```bash
# Check for remaining old imports
grep -r "from app\." backend/
grep -r "from src\." backend/

# Re-run import update
./scripts/migration/02_update_imports.sh
```

---

### Issue: Syntax errors in backend/

**Symptoms**:
```
SyntaxError: invalid syntax
```

**Solution**:
```bash
# Find files with syntax errors
find backend/ -name "*.py" -exec python3 -m py_compile {} \; 2>&1 | grep -i error

# Fix manually or restore from backup
```

---

### Issue: Docker build fails

**Symptoms**:
```
ERROR: Service 'api' failed to build
```

**Solution**:
```bash
# Check Dockerfile
grep "backend.main" Dockerfile

# Verify PYTHONPATH
docker-compose config | grep PYTHONPATH

# Rebuild with no cache
docker-compose build --no-cache api
```

---

### Issue: Tests fail after migration

**Symptoms**:
```
ImportError in tests/
```

**Solution**:
```bash
# Update test imports
find tests/ -name "*.py" -exec sed -i 's/from app\./from backend./g' {} \;
find tests/ -name "*.py" -exec sed -i 's/from src\./from backend./g' {} \;

# Re-run tests
pytest tests/ -v
```

---

## Success Metrics

After migration, verify:

- [ ] All tests passing (same count as before)
- [ ] API responds to health checks
- [ ] Docker services all healthy
- [ ] No import errors in logs
- [ ] v1 APIs work unchanged
- [ ] v2 APIs accessible

**Baseline metrics** (record before migration):
```bash
# Test count
pytest tests/ -v --collect-only | grep "tests collected"

# API response time
time curl http://localhost:8001/api/v1/search/ -X POST -H "Content-Type: application/json" -d '{"query":"test","top_k":5}'

# Docker health
docker-compose ps
```

---

## File Structure After Migration

```
backend/
├── api/
│   ├── v1/          # Stable production APIs (from app/)
│   │   ├── search.py
│   │   ├── analytics.py
│   │   └── ...
│   ├── v2/          # Experimental APIs (from src/) ⭐ NEW
│   │   ├── auth.py
│   │   ├── manufacturing.py
│   │   ├── metrics.py
│   │   └── ...
│   └── routes/      # Legacy routes
├── middleware/
│   ├── (basic middleware from app/)
│   └── advanced/    # Advanced middleware (from src/) ⭐ NEW
│       ├── rate_limiting.py
│       └── error_tracking.py
├── core/
│   ├── (infrastructure from app/)
│   ├── advanced_rag/    # ⭐ NEW from src/
│   ├── multimodal/      # ⭐ NEW from src/
│   └── ocr/             # ⭐ NEW from src/
├── services/        # Merged from app/ + src/
├── auth/            # ⭐ NEW from src/
├── db/              # ⭐ NEW from src/
└── main.py          # Updated entry point
```

---

## Additional Resources

- **BACKEND_MIGRATION_PLAN.md** - Complete migration plan (60 pages)
- **PROGRESS.md** - Version history
- **docs/logs/CHANGELOG.md** - Detailed changelog

---

## Support

If migration fails or you encounter issues:

1. Check the logs in `.migration_backup_*/`
2. Review BACKEND_MIGRATION_PLAN.md troubleshooting section
3. Rollback using backup branch
4. Report issues with full error logs

---

**Migration Scripts v1.0.0** | **2025-11-15** | **Safe & Reversible**
