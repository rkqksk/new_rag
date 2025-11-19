# Archive Directory - Legacy Code

This directory contains legacy/deprecated code from previous versions of the project. These directories are preserved for reference and historical purposes, but should NOT be used for active development.

## Directory Structure

### v9 Legacy Code (Superseded)
```
.archive/
├── app-v9/              # Legacy monolithic application (v9)
├── backend-v9/          # Legacy backend code (v9)
└── src-v9/              # Legacy source code (v9)
```

**Status**: DEPRECATED - Replaced by unified v10 structure
**Reason**: Refactored into monorepo with single source of truth

---

### v10 Pre-Cleanup Code (Preserved for Migration)
```
.archive/
├── app-v10-pre-cleanup/          # Pre-cleanup application code
│   └── Moved from root app/ directory on 2025-11-19
│   └── Reason: Functionality merged into apps/api/
│
├── backend-v10-pre-cleanup/      # Pre-cleanup backend code
│   └── Moved from root backend/ directory on 2025-11-19
│   └── Reason: Functionality merged into apps/api/
│
└── frontend-v1-static/           # Static HTML frontend (v1)
    └── Updated 2025-11-19 with legacy frontend/ contents
    └── Reason: Replaced by apps/web/ (Next.js 15)
```

**Status**: ARCHIVED - These are preserved for rollback reference only
**Deprecation Date**: 2025-11-19

---

## Migration Summary

### What Changed
The project underwent a major refactoring from a scattered multi-directory structure to a clean monorepo architecture:

**Before (v9-v10 pre-cleanup)**:
- `app/` - Monolithic app directory
- `backend/` - Backend microservices
- `frontend/` - Static HTML frontend
- 33+ other scattered directories (-76% reduction)

**After (v10 final)**:
- `apps/` - All applications (api, web, pwa, mobile)
- `packages/` - Shared code (@rag/core, @rag/config, @rag/utils, @rag/ui)
- `services/` - Microservices (rag, collector, manufacturing, realtime, ml)
- `infrastructure/` - IaC (k8s, terraform)
- `docs/` - Documentation
- **Total: 8 root directories** (down from 33)

### Code Consolidation
- **apps/api/** supersedes both `app/` and `backend/` directories
- **apps/web/** replaces `frontend/` with modern Next.js 15
- All shared logic extracted to `packages/core/` and related packages
- Result: <5% code duplication (down from 40%+)

### Files Affected
The following directories were consolidated during v10 migration:

| Old Path | New Path | Details |
|----------|----------|---------|
| app/ | apps/api/ | All API routes and services unified |
| backend/ | apps/api/ | Database, services, and business logic |
| frontend/ | apps/web/ | Next.js 15 with Pure Black design system |
| components/ | packages/ui/ | Reusable React components |
| config/ | packages/config/ | Shared configuration |
| src/ | packages/core/ | Core business logic |

---

## When to Use Archive

### Reading
- **Version comparison**: Compare old code patterns with v10 implementation
- **Migration reference**: Check how specific features were refactored
- **Historical context**: Understand design decisions and evolution
- **Rollback reference**: Last resort if v10 needs to compare against pre-cleanup state

### NEVER Use Archive For
- ❌ Active development (use `apps/`, `packages/`, `services/`)
- ❌ Production deployments (use v10 final code in root)
- ❌ Component references (use `packages/ui/` and `apps/web/`)
- ❌ Running tests (use root `tests/` directory)

---

## Rollback Instructions

If a specific feature needs to be restored from v10 pre-cleanup:

```bash
# 1. Locate the file in archive
find .archive/app-v10-pre-cleanup -name "your_file.py"
find .archive/backend-v10-pre-cleanup -name "your_file.py"
find .archive/frontend-v1-static -name "your_file.html"

# 2. Compare with current implementation
diff .archive/app-v10-pre-cleanup/path/to/file apps/api/path/to/file

# 3. Selectively restore only what's needed
# DO NOT restore entire directories - cherry-pick changes only

# 4. Test thoroughly before committing
pytest tests/ -v
pnpm test
```

---

## Important Notes

### Directory Ownership
These archived directories preserve the original file permissions and timestamps from before cleanup. Do not modify them to preserve historical accuracy.

### Size
```
app-v9:             ~3.2 MB
backend-v9:         ~2.8 MB
src-v9:             ~1.5 MB
app-v10-pre-cleanup:    ~3.3 MB
backend-v10-pre-cleanup: ~3.4 MB
frontend-v1-static:     ~364 KB
```

Total archive size: ~14 MB (vs ~80 MB for full project before cleanup)

### Git History
All archived code is preserved in git history. Use these commands to view:

```bash
# Show when code was moved to archive
git log --oneline -- app backend frontend | head -5

# View original code at any commit
git show <commit-hash>:path/to/file

# Diff against archived version
git diff HEAD -- archived-path
```

---

## v10 Structure (Current)

For active development, use this structure:

```
new_rag/
├── apps/
│   ├── api/        ← FastAPI backend (production ready)
│   ├── web/        ← Next.js 15 frontend (Pure Black design)
│   ├── pwa/        ← Vite PWA app
│   └── mobile/     ← React Native / Expo
├── packages/
│   ├── core/       ← Shared business logic
│   ├── config/     ← Configuration management
│   ├── utils/      ← Utility functions
│   └── ui/         ← React component library
├── services/
│   ├── rag/        ← RAG engine
│   ├── collector/  ← Data collection
│   ├── manufacturing/  ← Vision AI
│   ├── realtime/   ← Socket.IO server
│   └── ml/         ← MLflow services
├── infrastructure/ ← Kubernetes, Terraform
├── docs/           ← Documentation
├── tests/          ← Test suite
└── tools/          ← Dev tools
```

---

## Contact & Questions

For questions about archived code or migration:

1. Check `docs/guides/V9_TO_V10_MIGRATION.md` for detailed migration guide
2. Review `docs/ARCHITECTURE_OVERVIEW.md` for v10 architecture
3. See `PROGRESS.md` for version history and timeline

**Last Updated**: 2025-11-19
**Archive Version**: v10.0.0
**Git Branch**: v10-review
