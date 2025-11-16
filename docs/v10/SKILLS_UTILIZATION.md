# v10.0.0 Skills & MCP Server Utilization Guide

**Version**: v10.0.0
**Date**: 2025-11-16
**Status**: Complete Implementation Guide

---

## 📋 Overview

This guide details how Claude Skills and MCP servers are utilized throughout the v10.0.0 upgrade process.

**Philosophy**: Automate with Skills → Validate manually → Iterate

---

## 🤖 Claude Skills Validation Status

All 9 Skills tested and validated:

| # | Skill | Status | Scripts | Usage in v10 |
|---|-------|--------|---------|-------------|
| 1 | `rag-optimization` | ✅ 100% | `analyze_chunks.py` | Phase 1.3, 4.1 |
| 2 | `data-collection` | ✅ 100% | `create_crawler.py` | Optional enhancements |
| 3 | `manufacturing-vision` | ✅ 100% | `train_yolo.py` | Optional enhancements |
| 4 | `testing-suite` | ✅ 100% | `generate_tests.py` | Phase 2.1, 4.1 |
| 5 | `deployment-automation` | ✅ 100% | `generate_k8s.py` | Phase 4.2 |
| 6 | `excel-processing` | ✅ 100% | `batch_process.py` | Optional (reports) |
| 7 | `pdf-processing` | ✅ 100% | `extract_tables.py` | Optional (docs) |
| 8 | `web-testing` | ✅ 100% | N/A | Phase 3.3, 4.1 |
| 9 | `saas-operations` | ✅ 100% | N/A | Optional enhancements |

**Validation Date**: 2025-11-16
**Environment**: Claude Code Web
**Dependencies Installed**: pandas, openpyxl

---

## 🔧 Skills Usage by Phase

### Phase 1: Backend Maximal

#### 1.1: Backend Unification
**Skills Used**: None (bash + MCP filesystem)
- **Why**: File operations (copy, merge, move)
- **MCP**: `filesystem` for reading/writing files
- **Manual**: Import path updates (automated via sed)

#### 1.2: AI/ML Pipeline Setup
**Skills Used**: `deployment-automation`
- **Purpose**: Generate MLflow docker-compose configuration
- **Script**: `generate_k8s.py` (adapted for docker-compose)
- **Output**: `docker-compose.yml` (mlflow service added)

#### 1.3: Advanced RAG Features
**Skills Used**: `rag-optimization`
- **Purpose**: Analyze current chunking strategy
- **Script**: `analyze_chunks.py`
- **Command**:
  ```bash
  python .claude/skills/rag-optimization/scripts/analyze_chunks.py \
    --collection products \
    --output /tmp/chunk_analysis.json
  ```
- **Output**: Chunk size distribution, recommendations

**Manual Implementation**:
- Cross-encoder re-ranking (coded manually)
- Hybrid search (coded manually)
- Query expansion (coded manually)

**Why Manual**: Complex logic requiring deep understanding of RAG architecture.

---

### Phase 2: Backend Trimming

#### 2.1: Code Cleanup
**Skills Used**: `testing-suite`
- **Purpose**: Generate tests for coverage analysis
- **Script**: `generate_tests.py`
- **Command**:
  ```bash
  python .claude/skills/testing-suite/scripts/generate_tests.py \
    --source apps/api/services/ \
    --output tests/api/services/
  ```
- **Output**: pytest test files for all services

**Tools Used**:
- `ruff` - Remove unused imports, fix linting
- `black` - Code formatting
- `isort` - Import sorting
- `coverage` - Dead code detection

#### 2.2: Package Extraction
**Skills Used**: Task agent with `Explore` subagent
- **Purpose**: Analyze codebase to find common code patterns
- **Why**: Need to identify duplicated code across app/, backend/, src/
- **Task**:
  ```
  Analyze apps/api/ to find:
  1. Common models (used in 3+ modules)
  2. Shared utilities (used in 5+ files)
  3. Configuration patterns (duplicated settings)
  ```
- **Output**: List of candidates for packages/core/, packages/utils/

**MCP**: `filesystem` for file operations

#### 2.3: Documentation
**Skills Used**: None (manual writing)
- **Why**: Architecture Decision Records require human context
- **Manual**: ADR 001, ADR 002, migration guides

---

### Phase 3: Frontend Maximal

#### 3.1: Frontend Unification
**Skills Used**: Task agent with `Explore` subagent
- **Purpose**: Analyze frontend/, frontend-next/, frontend-v2/, apps/
- **Why**: Understand differences to merge correctly
- **Task**:
  ```
  Compare 4 frontend directories:
  1. What's unique in each?
  2. What's duplicated?
  3. Which has most recent code?
  ```
- **Output**: Merge strategy document

**MCP**: `filesystem` for file operations

#### 3.2: Modern UI Stack
**Skills Used**: None (manual coding)
- **Why**: Design system requires human creativity
- **Manual**:
  - Tailwind config (Pure Black theme)
  - Component library (shadcn customization)
  - Design system documentation

**Critical Rule**: Pure Black + No Icons + Natural theme (human enforced)

#### 3.3: Advanced Features
**Skills Used**: `web-testing`
- **Purpose**: Generate E2E tests for new features
- **Tests Generated**:
  - Socket.IO connection tests
  - i18n language switching
  - Offline mode (Service Worker)
  - Dark mode (always on in v10)

**Command** (using Playwright):
```bash
# Manual test creation with web-testing skill guidance
# Skill provides best practices, human writes actual tests
```

#### 3.4: Mobile App (Optional)
**Skills Used**: None
- **Why**: Expo-specific, not covered by current skills
- **Future**: Consider creating `mobile-app` skill

---

### Phase 4: Final Trimming

#### 4.1: Testing & Quality
**Skills Used**: `testing-suite`, `web-testing`

**Backend Tests**:
```bash
python .claude/skills/testing-suite/scripts/generate_tests.py \
  --source apps/api/ \
  --output tests/api/ \
  --coverage-target 80
```

**Frontend Tests**:
- E2E: Playwright (manual + skill-guided)
- Visual Regression: Percy/Chromatic (manual setup)
- Accessibility: axe-core (skill-guided)

**Output**:
- 200+ unit tests (auto-generated)
- 50+ integration tests (manual)
- 30+ E2E tests (manual + skill-guided)

#### 4.2: Infrastructure & DevOps
**Skills Used**: `deployment-automation`

**Kubernetes Manifests**:
```bash
# API service
python .claude/skills/deployment-automation/scripts/generate_k8s.py \
  --app api \
  --image rag-api:10.0.0 \
  --port 8001 \
  --replicas 3 \
  --output infrastructure/k8s/api.yaml

# Web service
python .claude/skills/deployment-automation/scripts/generate_k8s.py \
  --app web \
  --image rag-web:10.0.0 \
  --port 3000 \
  --replicas 2 \
  --output infrastructure/k8s/web.yaml

# Qdrant service
python .claude/skills/deployment-automation/scripts/generate_k8s.py \
  --app qdrant \
  --image qdrant/qdrant:latest \
  --port 6333 \
  --replicas 1 \
  --output infrastructure/k8s/qdrant.yaml
```

**Helm Chart**: Manual (requires complex templating)

**Terraform**: Manual (requires cloud provider specifics)

#### 4.3: Documentation & Launch
**Skills Used**: None (human writing)
- **Why**: Documentation requires strategic thinking, context
- **Manual**:
  - CHANGELOG.md
  - Migration guides
  - Design system docs
  - Video scripts (future)

---

## 🔌 MCP Server Usage

### Available MCP Servers

#### 1. `filesystem`
**Provider**: MCP official
**Usage**: All phases

**Operations**:
- Read files: `mcp__filesystem__read_file`
- Write files: `mcp__filesystem__write_file`
- List directories: `mcp__filesystem__list_directory`
- Move files: `mcp__filesystem__move_file`

**Example**:
```typescript
// Read backend files for analysis
await mcp__filesystem__read_file({
  path: "/home/user/new_rag_ubuntu/backend/main.py"
})

// Write merged file
await mcp__filesystem__write_file({
  path: "/home/user/new_rag_ubuntu/apps/api/main.py",
  content: mergedContent
})
```

#### 2. `github`
**Provider**: MCP official
**Usage**: Phase 4.3 (optional)

**Operations**:
- Create issues: Track migration tasks
- Create PRs: Submit v10 changes
- Manage releases: v10.0.0 release

**Example**:
```bash
# Create release (if MCP used)
# Currently using git commands instead
git tag v10.0.0
git push origin v10.0.0
```

---

## 📊 Automation vs Manual Work

### Automation (Skills + Scripts)

| Task | Automation % | Tool |
|------|--------------|------|
| Test generation | 70% | `testing-suite` skill |
| K8s manifests | 90% | `deployment-automation` skill |
| Code formatting | 100% | ruff, black, isort |
| Import updates | 90% | sed scripts |
| Chunk analysis | 80% | `rag-optimization` skill |
| Crawler generation | 100% | `data-collection` skill |

**Total Automation**: ~60% (by effort hours)

### Manual Work (Human Required)

| Task | Reason for Manual |
|------|-------------------|
| Design system | Creative decisions (Pure Black theme) |
| Architecture decisions | Strategic thinking (ADRs) |
| Complex RAG logic | Deep domain knowledge |
| UI/UX | User experience design |
| Documentation writing | Context, storytelling |
| Code review | Quality assurance |

**Total Manual**: ~40% (by effort hours)

---

## 🎯 Skills Best Practices

### 1. Use Skills for Repetitive Tasks
✅ **Good**:
```bash
# Generate 50 test files
for module in apps/api/*/; do
  python .claude/skills/testing-suite/scripts/generate_tests.py \
    --source "$module" \
    --output "tests/$(basename $module)/"
done
```

❌ **Bad**:
```bash
# Write 50 test files manually
```

### 2. Validate Skill Output
✅ **Good**:
```bash
# Generate tests
python .claude/skills/testing-suite/scripts/generate_tests.py --source app.py --output test_app.py

# Review and edit test_app.py (manual)
# Run tests to validate
pytest test_app.py -v
```

❌ **Bad**:
```bash
# Generate and commit without review
python generate_tests.py --source app.py --output test_app.py
git add test_app.py && git commit -m "Add tests"
```

### 3. Combine Skills with Human Expertise
✅ **Good**:
```python
# 1. Use skill to analyze chunks
chunk_analysis = run_skill("rag-optimization", "analyze_chunks")

# 2. Human reviews analysis
# Found: 80% chunks are 500 tokens, 20% are 2000 tokens

# 3. Human decides: Split large chunks
# 4. Implement split logic (manual coding)
```

❌ **Bad**:
```python
# Let skill decide everything (no human judgment)
```

### 4. Document Skill Usage
✅ **Good**:
```markdown
## Tests Generated

Generated using `testing-suite` skill:
- Command: `python .claude/skills/testing-suite/scripts/generate_tests.py --source apps/api/`
- Date: 2025-11-16
- Files: 47 test files created
- Coverage: 82% (meets 80% target)
- Manual edits: 12 files (edge cases, mocks)
```

❌ **Bad**:
```markdown
## Tests
Tests added.
```

---

## 🚀 Quick Reference

### Phase 1: Backend
```bash
# MLflow setup
python .claude/skills/deployment-automation/scripts/generate_k8s.py \
  --app mlflow --image ghcr.io/mlflow/mlflow:latest --port 5000

# Chunk analysis
python .claude/skills/rag-optimization/scripts/analyze_chunks.py \
  --collection products
```

### Phase 2: Trimming
```bash
# Generate tests
python .claude/skills/testing-suite/scripts/generate_tests.py \
  --source apps/api/ --output tests/api/

# Code quality
ruff check . --fix
black . --line-length 100
```

### Phase 3: Frontend
```bash
# Web testing (manual + skill-guided)
cd apps/web
npx playwright test
```

### Phase 4: Deploy
```bash
# Generate all K8s manifests
for service in api web qdrant redis postgres; do
  python .claude/skills/deployment-automation/scripts/generate_k8s.py \
    --app $service --image $service:10.0.0 --output infrastructure/k8s/${service}.yaml
done
```

---

## 📈 Expected Outcomes

### Time Savings (Skills vs Manual)

| Task | Manual | With Skills | Savings |
|------|--------|-------------|---------|
| Generate 50 tests | 8 hours | 1 hour | 87% |
| Create 10 K8s manifests | 4 hours | 30 min | 87% |
| Analyze RAG chunks | 2 hours | 15 min | 87% |
| Format codebase | 1 hour | 5 min | 92% |
| **Total** | **15 hours** | **2 hours** | **87%** |

### Quality Improvements

- **Consistency**: Skills generate uniform code (same patterns)
- **Coverage**: Auto-generated tests achieve 70-80% coverage baseline
- **Best Practices**: Skills follow industry standards (K8s, pytest)
- **Documentation**: Skills include docstrings, comments

---

## 🔍 Validation Checklist

After using each skill, validate:

- [ ] **Output Quality**: Does it meet requirements?
- [ ] **Code Style**: Follows project conventions?
- [ ] **Tests Pass**: Generated code works?
- [ ] **Documentation**: Properly documented?
- [ ] **No Errors**: No syntax/runtime errors?
- [ ] **Human Review**: Code reviewed by human?

---

## 📚 References

- **Skills Documentation**: `.claude/skills/README.md`
- **Skill Validation**: Test results from 2025-11-16
- **MCP Servers**: `.claude/mcp.json`
- **Phase Scripts**: `scripts/v10/phase*.sh`

---

**Version**: v10.0.0
**Author**: Claude + Human collaboration
**License**: MIT
**Status**: ✅ Complete implementation guide
