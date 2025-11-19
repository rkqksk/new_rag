# Test Import Quick Fix Guide

**Generated**: 2025-11-19
**Status**: Ready to Execute
**Time Required**: 15-20 minutes

---

## Quick Stats

```
Total Test Files: 97
Files to Fix:     7
Risk Level:       LOW
Backups:          Automatic
```

---

## Three-Step Fix

### 1. Run Automated Script

```bash
# Execute the fix script
./scripts/fix-test-imports.sh
```

### 2. Verify Changes

```bash
# Check old patterns are gone
grep -r "from app\.main" tests/           # Should be empty
grep -r "from apps\.api\.api\." tests/    # Should be empty

# Check new patterns exist
grep "from apps\.api\.main" tests/conftest.py   # Should find 1
```

### 3. Test Everything

```bash
# Test critical fixture
pytest tests/conftest.py -v

# Test affected files
pytest tests/integration/test_api_integration.py -v
pytest tests/integration/test_app_initialization.py -v
pytest tests/integration/test_e2e_pipeline.py -v

# Run full suite
pytest tests/ -v
```

---

## Files Being Updated

1. **tests/conftest.py** (1 import)
   - `from app.main` → `from apps.api.main`
   - **Priority: HIGH** (used by all tests)

2. **tests/integration/test_api_integration.py** (1 import)
   - `from apps.api.api.main` → `from apps.api.main`

3. **tests/integration/test_app_initialization.py** (5 imports)
   - `from apps.api.api.main` → `from apps.api.main`

4. **tests/integration/test_e2e_pipeline.py** (4 imports)
   - `from apps.api.api.main` → `from apps.api.main`

5. **tests/integration/test_e2e_simple.py** (6 imports)
   - `from apps.api.api.main` → `from apps.api.main`

6. **tests/integration/test_nexa_integration.py** (2 imports)
   - `from apps.api.api.v1` → `from apps.api.v1`

7. **tests/integration/test_product_loading.py** (1 import)
   - `from apps.api.api.v1` → `from apps.api.v1`

---

## Rollback (If Needed)

```bash
# Restore from automatic backups
BACKUP_DIR=$(ls -dt .backups/test-imports-* | head -1)
cp $BACKUP_DIR/* tests/

# Or use git
git checkout tests/conftest.py
git checkout tests/integration/test_*.py
```

---

## Manual Fix Alternative

If you prefer manual updates:

```bash
# Fix 1: conftest.py
sed -i 's/from app\.main import app/from apps.api.main import app/' tests/conftest.py

# Fix 2: apps.api.api.main → apps.api.main
sed -i 's/from apps\.api\.api\.main/from apps.api.main/g' \
  tests/integration/test_api_integration.py \
  tests/integration/test_app_initialization.py \
  tests/integration/test_e2e_pipeline.py \
  tests/integration/test_e2e_simple.py

# Fix 3: apps.api.api.v1 → apps.api.v1
sed -i 's/from apps\.api\.api\.v1\./from apps.api.v1./g' \
  tests/integration/test_nexa_integration.py \
  tests/integration/test_product_loading.py
```

---

## What Gets Fixed

### Before (Incorrect)
```python
# tests/conftest.py
from app.main import app  # ✗ Old v9 pattern

# tests/integration/test_api_integration.py
from apps.api.api.main import app  # ✗ Redundant .api.

# tests/integration/test_nexa_integration.py
from apps.api.api.v1.admin import health_check  # ✗ Redundant .api.
```

### After (Correct)
```python
# tests/conftest.py
from apps.api.main import app  # ✓ v10 pattern

# tests/integration/test_api_integration.py
from apps.api.main import app  # ✓ Clean path

# tests/integration/test_nexa_integration.py
from apps.api.v1.admin import health_check  # ✓ Clean path
```

---

## Why These Changes?

### v9 Structure (Old)
```
app/
├── api/
│   ├── main.py
│   └── v1/
└── main.py  # ← Old main.py location
```

Import: `from app.main import app`

### v10 Structure (New)
```
apps/
└── api/
    ├── main.py      # ← New unified location
    ├── api/         # ← Legacy routes (will be moved)
    │   ├── main.py
    │   └── v1/
    └── v1/          # ← Should be here, not in api/v1/
```

Correct import: `from apps.api.main import app`

The `apps.api.api.*` pattern is redundant because the v10 migration consolidated the backend into `apps/api/`, eliminating the need for the double `api` reference.

---

## Verification Checklist

- [ ] Script executed successfully
- [ ] No "from app.main" in tests/conftest.py
- [ ] No "from apps.api.api.*" in any test files
- [ ] conftest.py fixture loads correctly
- [ ] Integration tests pass
- [ ] Full test suite passes
- [ ] Backups created in .backups/ directory

---

## Support

**Documentation**: TEST_IMPORT_ANALYSIS.md (detailed analysis)
**Script**: scripts/fix-test-imports.sh (automated fix)

**Questions?** Check TEST_IMPORT_ANALYSIS.md for:
- Detailed import pattern analysis
- Line-by-line breakdown
- Architecture explanation
- Full rollback procedures
