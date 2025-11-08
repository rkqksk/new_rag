# RAG Enterprise - Complete Project Cleanup Plan

## Analysis Date: 2025-11-03

---

## 🎯 Cleanup Summary

| Directory | Status | Action | Files |
|-----------|--------|--------|-------|
| `..bfg-report/` | ❌ Git cleanup artifact | **DELETE** | 1 dir |
| `.direnv/` | ❌ Unused (not using direnv) | **DELETE** | 1 dir |
| `archives/` | ❌ Duplicate of docs/archive | **DELETE** | ~50+ |
| `.github/workflows/` | ⚠️ Review needed | **AUDIT** | 4 files |
| `config/` | ⚠️ Potential duplicates | **CONSOLIDATE** | ~10 files |
| `data/` | ⚠️ Needs organization | **REORGANIZE** | Many subdirs |
| `examples/` | ⚠️ May overlap with skills | **REVIEW** | 2 files |
| `files/` | ❓ Unclear purpose | **CHECK & DELETE** | 1 subdir |
| `frontend/` | ⚠️ Restore white design | **RESTORE** | Multiple |
| `monitoring/` | ⚠️ Check vs config/ | **AUDIT** | 3 files |
| `scripts/` | ⚠️ **400+ files!** | **MAJOR CLEANUP** | 400+ |
| `src/` | ⚠️ Code cleanup | **AUDIT** | TBD |

---

## 1. Immediate Deletions (No Risk)

### ❌ ..bfg-report/
- **What**: BFG Repo-Cleaner report (git history cleanup tool)
- **Action**: DELETE entirely
- **Reason**: Temporary artifact, not needed

### ❌ .direnv/
- **What**: direnv Python environment cache
- **Action**: DELETE entirely
- **Reason**: Not using direnv, using standard venv/.venv

### ❌ archives/
- **What**: Old archive directory (duplicate of docs/archive)
- **Contents**: backups/, cleanup logs, deprecated/, finetuning_guides/, logs/
- **Action**: DELETE entirely
- **Reason**: Already have docs/archive/, this is redundant

### ❌ files/print_area/
- **What**: Unclear purpose directory
- **Action**: CHECK contents, then DELETE
- **Reason**: Likely temporary test files

---

## 2. .github/workflows/ Audit

**Current Files:**
- `ci.yml` (1.6k) - Basic CI
- `ci_cd.yml` (3.7k) - Full CI/CD
- `security.yml` (15k) - Security checks
- `_disabled/` - Disabled workflows

**Issues:**
- ✅ `ci.yml` vs `ci_cd.yml` - DUPLICATE functionality
- ⚠️ `security.yml` - Very large, check if active

**Action:**
1. Keep `ci_cd.yml` (comprehensive)
2. Move `ci.yml` to `_disabled/`
3. Review `security.yml` - keep if used, disable if not
4. Clean up `_disabled/` folder

---

## 3. config/ Consolidation

**Current Structure:**
```
config/
├── clean_deploy_config.json
├── crawl_schedule.yaml
├── docker/
├── grafana/
├── mcp/
│   ├── .mcp.minimal.json
│   ├── .mcp.max.json
│   └── .mcp.zero.json
├── mcp_extended_config.json
├── pipeline_config.json
├── prometheus.yml
├── requirements/
└── system_config.yaml
```

**vs monitoring/**
```
monitoring/
├── alert-rules.yml
├── grafana-dashboard.json
└── prometheus.yml
```

**Issues:**
- `prometheus.yml` exists in BOTH config/ and monitoring/
- `grafana` exists in BOTH
- Unclear which is active

**Action:**
1. Consolidate monitoring configs into `config/monitoring/`
2. Keep active prometheus.yml (likely config/)
3. Move monitoring/ contents to config/monitoring/
4. Delete monitoring/ directory

---

## 4. data/ Reorganization

**Current Chaos:**
```
data/
├── products/
├── archive/
├── quality/
├── excel_uploads/
├── test_documents/
├── crawler/
├── plastics_kr/
├── onehago/
├── freemold/
```

**Proposed Clean Structure:**
```
data/
├── crawled/              # All crawled data
│   ├── onehago/
│   ├── freemold/
│   ├── plastics_kr/
│   └── jangup/
├── processed/            # Processed/enriched data
│   ├── products/
│   └── metadata/
├── uploads/              # User uploads
│   ├── excel/
│   └── documents/
├── quality/              # Quality checks
│   ├── validation/
│   └── reconciliation/
├── test/                 # Test data
│   └── test_documents/
└── archive/              # Old data backups
```

**Action:**
1. Create new structure
2. Move files to appropriate locations
3. Update code references
4. Delete empty old directories

---

## 5. scripts/ MAJOR CLEANUP (400+ files!)

**Categories:**

### A. Crawlers (100+ files)
**Keep:**
- Latest production crawlers (onehago, freemold, plastics_kr)
- Active monitoring scripts
- Working orchestrators

**Archive:**
- Old versions (_old, _v2, _backup, _complete, etc.)
- Test crawlers (test_*, *_test.py)
- Experimental versions

**Delete:**
- Failed experiments
- Duplicate crawlers

### B. Data Processing (50+ files)
**Keep:**
- Active phase1-4 scripts
- Production data validators
- Essential utils

**Archive:**
- Old phase scripts
- One-time migration scripts
- Analysis scripts

### C. Test Scripts (50+ files)
**Archive ALL:**
- All test_*.py files → tests/ or archive
- Integration tests → proper test suite

### D. Monitoring Scripts (20+ files)
**Keep:**
- Active monitoring scripts
- Production orchestrators

**Delete:**
- Duplicate monitors
- Old monitoring versions

### E. Setup/Deploy Scripts (10+ files)
**Keep:**
- `deploy.sh`, `rollback.sh`
- Active setup scripts

**Delete:**
- Old setup scripts
- Temporary test scripts

### F. One-off Scripts (100+ files)
**Archive:**
- All analysis_*.py
- All fix_*.py (already applied)
- All enhance_*.py (one-time use)

**Proposed Structure:**
```
scripts/
├── crawlers/           # Active production crawlers only
│   ├── onehago_crawler.py
│   ├── freemold_crawler.py
│   └── monitoring/
├── data_processing/    # Essential data tools
│   ├── phase1_collect.py
│   ├── phase2_extract.py
│   └── validators/
├── deployment/         # Deploy scripts
│   ├── deploy.sh
│   └── rollback.sh
├── maintenance/        # Maintenance utils
└── archive/            # Old scripts (300+ files)
    ├── crawlers_old/
    ├── tests/
    ├── experiments/
    └── one_off/
```

---

## 6. examples/ Review

**Current:**
- `manufacturing_defect_analysis.py`
- `rag_pipeline_demo.py`

**vs .claude/skills/:**
- `manufacturing-expert/`
- `rag-pipeline/`

**Action:**
1. Check if examples duplicate skills
2. If yes: DELETE examples, skills are authoritative
3. If no: Keep as separate demos

---

## 7. frontend/ Design Restore

**Current Issue:** Need minimal white background design

**Action:**
1. Find last working white design version in git history
2. Restore that version
3. Keep minimal, clean design
4. Remove unnecessary styling

---

## 8. src/ Code Audit

**Check for:**
- Unused imports
- Dead code
- Duplicate functions
- Unused files
- Test code in src/

**Action:**
1. Run code analysis tools
2. Remove dead code
3. Consolidate duplicates
4. Ensure all code is actually used

---

## Execution Priority

### Phase 1: Safe Deletions (5 min)
1. ❌ Delete `..bfg-report/`
2. ❌ Delete `.direnv/`
3. ❌ Delete `archives/`
4. ❌ Delete `files/` (after check)

### Phase 2: Configuration Cleanup (15 min)
1. Consolidate config/ and monitoring/
2. Audit .github/workflows/
3. Update references

### Phase 3: Data Reorganization (30 min)
1. Create new data/ structure
2. Move files systematically
3. Update code paths
4. Test

### Phase 4: Scripts MAJOR CLEANUP (60 min)
1. Create archive structure
2. Identify keepers (20 files)
3. Move 380+ files to archive
4. Update any hard-coded paths
5. Test crawlers still work

### Phase 5: Final Touches (30 min)
1. Review examples/
2. Restore frontend design
3. Audit src/ code
4. Update documentation

---

## Estimated Results

**Before:**
- Total files: 1000+
- Clarity: Low
- Maintainability: Poor
- Find things: Hard

**After:**
- Active files: ~150
- Archived files: ~850 (organized)
- Clarity: High
- Maintainability: Excellent
- Find things: Easy

---

## Risk Mitigation

1. ✅ Make git commit before each phase
2. ✅ Test after each major change
3. ✅ Keep archives, don't delete permanently
4. ✅ Document all moves in this file

---

## Next Steps

Run this plan phase by phase, testing after each step.
