---
name: architecture-optimizer
description: Architecture Optimizer Skill
---

# Architecture Optimizer Skill

**Purpose**: Analyze, optimize, and clean up RAG Enterprise system architecture, documentation, and modular organization

**Version**: 1.0.0
**Last Updated**: 2025-11-08
**Project**: rag-enterprise

---

## 📖 Overview

This skill provides comprehensive architecture analysis, optimization, and cleanup capabilities for the RAG Enterprise platform. It helps maintain clean, efficient, and well-documented system architecture.

## 🎯 Core Capabilities

1. **Architecture Analysis**: Analyze current system structure and identify optimization opportunities
2. **Documentation Cleanup**: Merge, split, and organize documentation files
3. **Service Orchestration**: Optimize service/module distribution
4. **Code Organization**: Identify and fix code duplication and structure issues
5. **Performance Optimization**: Suggest architectural improvements

---

## 📋 Commands

### `analyze`
Analyze current system architecture and generate comprehensive report

**Usage**:
```
/architecture-optimizer analyze [--scope=<scope>] [--output=<format>]
```

**Options**:
- `--scope`: `full` (default) | `backend` | `frontend` | `docs` | `services`
- `--output`: `report` (default) | `json` | `markdown`

**Examples**:
```bash
# Full system analysis
/architecture-optimizer analyze

# Backend services only
/architecture-optimizer analyze --scope=backend

# JSON output for automation
/architecture-optimizer analyze --output=json
```

---

### `optimize`
Optimize system architecture based on analysis

**Usage**:
```
/architecture-optimizer optimize [--target=<target>] [--dry-run]
```

**Options**:
- `--target`: `services` | `docs` | `code` | `all` (default)
- `--dry-run`: Preview changes without applying

**Examples**:
```bash
# Optimize all aspects
/architecture-optimizer optimize

# Optimize documentation only (dry run)
/architecture-optimizer optimize --target=docs --dry-run

# Optimize services
/architecture-optimizer optimize --target=services
```

---

### `cleanup`
Clean up documentation, merge redundant files, remove duplicates

**Usage**:
```
/architecture-optimizer cleanup [--target=<target>] [--aggressive]
```

**Options**:
- `--target`: `docs` | `code` | `configs` | `all` (default)
- `--aggressive`: Enable aggressive cleanup (removes more files)

**Examples**:
```bash
# Cleanup documentation
/architecture-optimizer cleanup --target=docs

# Full cleanup (aggressive)
/architecture-optimizer cleanup --aggressive
```

---

### `orchestrate`
Analyze and optimize service orchestration

**Usage**:
```
/architecture-optimizer orchestrate [--visualize]
```

**Options**:
- `--visualize`: Generate visual service map

**Examples**:
```bash
# Analyze service orchestration
/architecture-optimizer orchestrate

# Generate visual map
/architecture-optimizer orchestrate --visualize
```

---

### `consolidate`
Consolidate similar/redundant documents

**Usage**:
```
/architecture-optimizer consolidate [--category=<category>]
```

**Options**:
- `--category`: `api` | `architecture` | `guides` | `all` (default)

**Examples**:
```bash
# Consolidate all documents
/architecture-optimizer consolidate

# Consolidate API docs only
/architecture-optimizer consolidate --category=api
```

---

## 🔧 Implementation Guide

### Architecture Analysis Process

1. **Service Discovery**
   - Scan `app/`, `src/`, `services/` directories
   - Identify all FastAPI routers
   - Map service dependencies
   - Detect circular dependencies

2. **Documentation Audit**
   - List all `.md` files
   - Identify overlapping content
   - Detect outdated information
   - Find missing documentation

3. **Code Quality Analysis**
   - Find duplicate code
   - Detect unused imports
   - Identify long files (> 500 lines)
   - Check naming consistency

4. **Performance Analysis**
   - Database query optimization
   - API endpoint performance
   - Caching strategy review
   - Resource utilization

### Optimization Strategies

#### 1. Service Modularization
```
Current Issues:
- Monolithic API files
- Circular dependencies
- Unclear service boundaries

Optimization:
- Split large routers into modules
- Implement dependency injection
- Clear service layer separation
```

#### 2. Documentation Consolidation
```
Issues:
- Multiple architecture docs
- Redundant API documentation
- Scattered integration guides

Solution:
- Merge related documents
- Create single source of truth
- Maintain cross-references
- Version documentation
```

#### 3. Code Organization
```
Problems:
- Mixed concerns in files
- Deep nesting (> 4 levels)
- Long functions (> 100 lines)
- Duplicate utilities

Fixes:
- Extract common utilities
- Flatten directory structure
- Split large files
- Remove dead code
```

---

## 📊 Analysis Outputs

### 1. Architecture Report

**File**: `docs/reports/architecture-analysis-YYYY-MM-DD.md`

**Sections**:
- System Overview
- Service Map
- Dependency Graph
- Performance Metrics
- Recommendations
- Action Items

### 2. Cleanup Plan

**File**: `docs/plans/cleanup-plan-YYYY-MM-DD.md`

**Contents**:
- Files to merge
- Files to split
- Files to delete
- Refactoring suggestions

### 3. Optimization Roadmap

**File**: `docs/roadmaps/optimization-roadmap-YYYY-MM-DD.md`

**Sections**:
- Quick wins (< 1 day)
- Medium-term improvements (1-5 days)
- Long-term architecture changes (> 5 days)

---

## 🚀 Automation Workflows

### Workflow 1: Weekly Documentation Cleanup

**Trigger**: Every Monday 00:00 UTC
**Actions**:
1. Analyze all `docs/` files
2. Identify duplicates
3. Generate cleanup plan
4. Create PR with suggested changes

### Workflow 2: Monthly Architecture Review

**Trigger**: First day of month
**Actions**:
1. Full system analysis
2. Generate architecture report
3. Identify optimization opportunities
4. Update architecture diagrams

### Workflow 3: Pre-Release Optimization

**Trigger**: Before major version release
**Actions**:
1. Comprehensive analysis
2. Code quality checks
3. Performance benchmarks
4. Documentation review
5. Generate release readiness report

---

## 🎨 Best Practices

### Documentation Organization

```
docs/
├── guides/              # User-facing guides
│   ├── getting-started/
│   ├── deployment/
│   └── api-usage/
├── reference/           # Technical reference
│   ├── api/
│   ├── architecture/
│   └── configuration/
├── architecture/        # System architecture
│   ├── diagrams/
│   ├── decisions/       # ADRs
│   └── patterns/
└── development/         # Developer docs
    ├── contributing/
    ├── testing/
    └── debugging/
```

### Service Organization

```
app/
├── api/                 # API layer
│   ├── v1/             # Versioned endpoints
│   └── routes/         # Route handlers
├── services/           # Business logic
│   ├── rag/
│   ├── saas/
│   └── manufacturing/
├── repositories/       # Data access
│   ├── qdrant/
│   ├── postgres/
│   └── redis/
└── core/               # Core utilities
    ├── config/
    ├── auth/
    └── logging/
```

---

## 📝 Reporting Templates

### Architecture Analysis Template

```markdown
# Architecture Analysis Report
Date: {date}
Version: {version}

## Executive Summary
- {summary}

## System Metrics
- Total Services: {count}
- Total API Endpoints: {count}
- Lines of Code: {loc}
- Test Coverage: {coverage}%

## Issues Found
### Critical (P0)
- {issue_list}

### High Priority (P1)
- {issue_list}

### Medium Priority (P2)
- {issue_list}

## Recommendations
1. {recommendation}
2. {recommendation}

## Action Items
- [ ] {action}
- [ ] {action}
```

---

## 🔍 Analysis Checklist

### Pre-Analysis
- [ ] Backup current codebase
- [ ] Document current state
- [ ] Identify critical paths
- [ ] Set optimization goals

### During Analysis
- [ ] Run static code analysis
- [ ] Check test coverage
- [ ] Review API performance
- [ ] Audit documentation
- [ ] Map dependencies

### Post-Analysis
- [ ] Generate reports
- [ ] Create action plan
- [ ] Prioritize improvements
- [ ] Schedule implementation
- [ ] Document decisions

---

## 🎯 Optimization Metrics

### Code Quality
- **Maintainability Index**: Target > 80
- **Cyclomatic Complexity**: Target < 10 per function
- **Code Duplication**: Target < 3%
- **Test Coverage**: Target > 80%

### Performance
- **API Response Time**: Target < 200ms (p95)
- **Database Queries**: Target < 5 per request
- **Cache Hit Rate**: Target > 70%
- **Memory Usage**: Target < 2GB per worker

### Documentation
- **Coverage**: All public APIs documented
- **Freshness**: Updated within 30 days
- **Examples**: Every major feature
- **Diagrams**: Architecture visualized

---

## 🛠️ Tools Integration

### Static Analysis
- `pylint`, `flake8`, `mypy` for Python
- `eslint`, `prettier` for JavaScript/TypeScript
- `radon` for complexity metrics
- `bandit` for security checks

### Documentation
- `mkdocs` for documentation site
- `sphinx` for API documentation
- `mermaid` for diagrams
- `doctoc` for table of contents

### Performance
- `pytest-benchmark` for benchmarks
- `locust` for load testing
- `py-spy` for profiling
- `memray` for memory analysis

---

## 📚 Related Skills

- **rag-pipeline**: RAG system optimization
- **data-collector**: Data pipeline analysis
- **saas-platform**: SaaS architecture review
- **frontend-platform**: Frontend optimization

---

## 🚦 Usage Examples

### Example 1: Full System Analysis

```bash
# Run comprehensive analysis
/architecture-optimizer analyze --scope=full

# Review generated report
cat docs/reports/architecture-analysis-2025-11-08.md

# Generate optimization plan
/architecture-optimizer optimize --dry-run

# Apply optimizations
/architecture-optimizer optimize
```

### Example 2: Documentation Cleanup

```bash
# Analyze documentation
/architecture-optimizer analyze --scope=docs

# Preview cleanup
/architecture-optimizer cleanup --target=docs --dry-run

# Apply cleanup
/architecture-optimizer cleanup --target=docs

# Consolidate related docs
/architecture-optimizer consolidate
```

### Example 3: Service Orchestration

```bash
# Analyze services
/architecture-optimizer orchestrate --visualize

# Generate service map
# → docs/architecture/diagrams/service-map.md

# Review dependencies
# → docs/architecture/dependencies.md

# Optimize service boundaries
/architecture-optimizer optimize --target=services
```

---

## 🎓 Learning Resources

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Service-Oriented Architecture](https://microservices.io/patterns/microservices.html)
- [Documentation Best Practices](https://www.writethedocs.org/guide/)
- [Code Quality Metrics](https://www.sonarsource.com/learn/code-quality/)

---

**Skill Version**: 1.0.0
**Last Updated**: 2025-11-08
**Maintainer**: RAG Enterprise Team
