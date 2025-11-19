# Automation Scripts Guide

**Version**: v10.0.0
**Status**: Production Ready
**Author**: PETER Team

---

## Overview

PETER v10.0.0 includes three critical automation scripts to streamline development workflow:

1. **setup.sh** - One-command project setup
2. **build-all.sh** - Monorepo build automation
3. **Pre-commit hooks** - Code quality enforcement

---

## 1. setup.sh - One-Command Project Setup

### Purpose
Fresh environment setup in one command. Installs all dependencies, configures services, and verifies the setup.

### Location
```bash
/home/rkqksk/projects/new_rag/setup.sh
```

### Usage

**Basic Usage**:
```bash
./setup.sh
```

**With Options**:
```bash
./setup.sh --skip-docker    # Skip Docker services
./setup.sh --skip-data      # Skip data seeding
./setup.sh --help           # Show help
```

### What It Does

#### Step 1: Check System Requirements
- Python 3.11+
- Node.js 18+
- pnpm
- Docker & Docker Compose
- Git

#### Step 2: Install Python Dependencies
- Creates virtual environment (`.venv`)
- Upgrades pip, setuptools, wheel
- Installs `requirements.txt`
- Installs pre-commit hooks

#### Step 3: Install Node Dependencies
- Runs `pnpm install` (monorepo)
- Installs all workspace dependencies

#### Step 4: Setup Environment
- Creates `.env` from `.env.example` if missing
- Prompts to update configuration

#### Step 5: Start Docker Services
- Starts `docker-compose.yml`
- Waits 30 seconds for services to be ready

#### Step 6: Initialize Databases
- Checks PostgreSQL connection
- Checks Qdrant connection
- Checks Redis connection

#### Step 7: Run Migrations
- Runs `alembic upgrade head`
- Applies all database migrations

#### Step 8: Seed Initial Data
- Runs `scripts/seed_data.py` if exists
- Loads sample data

#### Step 9: Verify Setup
- Checks API health
- Checks frontend dependencies
- Verifies Docker services

### Output Example

```
═══════════════════════════════════════════════════════════
  PETER v10.0.0 Setup Script
═══════════════════════════════════════════════════════════

This script will set up your development environment.
Press Ctrl+C to cancel at any time.


═══════════════════════════════════════════════════════════
  Step 1/9: Checking System Requirements
═══════════════════════════════════════════════════════════

✓ Python is installed (/usr/bin/python3)
→ Checking Python version: 3.11.6 (minimum: 3.11.0)
✓ Node.js is installed (/usr/bin/node)
→ Checking Node.js version: 18.19.0 (minimum: 18.0.0)
✓ pnpm is installed (/usr/bin/pnpm)
✓ Docker is installed (/usr/bin/docker)
✓ Docker Compose is installed (/usr/bin/docker-compose)
✓ Git is installed (/usr/bin/git)
✓ All system requirements met

...

═══════════════════════════════════════════════════════════
  Setup Complete!
═══════════════════════════════════════════════════════════

✓ Setup completed successfully!

Next Steps:
  1. Update .env file with your configuration
  2. Start development servers:
     pnpm dev          # All apps
     pnpm web          # Frontend only
     pnpm api          # API only

  3. View interfaces:
     http://localhost:3000              # Web App
     http://localhost:8001/api/v1/docs  # API Docs
     http://localhost:6333/dashboard    # Qdrant

  4. Run tests:
     ./scripts/test-all.sh

  5. Build for production:
     ./scripts/build-all.sh

Documentation:
  • Quick reference: CLAUDE.md
  • Full guide: README.md
  • API docs: docs/reference/API_DOCUMENTATION.md

Happy coding! 🚀
```

### Features

- **Color-coded output**: Green for success, red for errors, yellow for warnings
- **Progress indicators**: Clear step-by-step progress
- **Error handling**: Helpful error messages with solutions
- **Idempotent**: Safe to run multiple times
- **Flexible**: Skip steps with flags

### Troubleshooting

**Port already in use**:
```bash
# Kill processes on ports
lsof -i :8001 | grep LISTEN | awk '{print $2}' | xargs kill -9
lsof -i :3000 | grep LISTEN | awk '{print $2}' | xargs kill -9
```

**Docker services not starting**:
```bash
docker-compose down -v
docker-compose up -d
```

**Permission denied**:
```bash
chmod +x setup.sh
```

---

## 2. build-all.sh - Monorepo Build Automation

### Purpose
Build all apps and packages in the correct dependency order with optimizations.

### Location
```bash
/home/rkqksk/projects/new_rag/build-all.sh
```

### Usage

**Basic Usage**:
```bash
./build-all.sh
```

**With Options**:
```bash
./build-all.sh --parallel      # Parallel builds (faster)
./build-all.sh --skip-lint     # Skip linting
./build-all.sh --production    # Production build
./build-all.sh --help          # Show help
```

**Examples**:
```bash
# Standard development build
./build-all.sh

# Fast parallel build
./build-all.sh --parallel

# Production optimized build
./build-all.sh --production

# Quick build without linting
./build-all.sh --skip-lint --parallel
```

### What It Does

#### Step 1: Pre-Build Checks
- Verifies `node_modules` exists
- Checks pnpm availability
- Cleans previous build artifacts
- Creates `dist/` directory

#### Step 2: TypeScript Type Checking
- Runs `tsc` on all packages
- Reports type errors
- Continues on warnings

#### Step 3: Linting (Optional)
- Runs ESLint on TypeScript/JavaScript
- Runs Prettier format check
- Runs Black/Flake8 on Python (if `.venv` exists)

#### Step 4: Build Packages
Builds in dependency order:
1. `@rag/config`
2. `@rag/utils`
3. `@rag/core`
4. `@rag/ui`

#### Step 5: Build Applications
1. **API** (Python) - Validates Python syntax
2. **Web** (Next.js) - Builds production bundle
3. **PWA** (Vite) - Builds static assets

#### Step 6: Generate Build Report
- Total build time
- Package sizes
- Application sizes
- Build options used
- Saves to `dist/build-report.txt`

### Build Order

**Why Order Matters**:
```
@rag/config     (no dependencies)
  ↓
@rag/utils      (depends on config)
  ↓
@rag/core       (depends on config, utils)
  ↓
@rag/ui         (depends on core, utils)
  ↓
apps/*          (depends on packages)
```

### Output Example

```
═══════════════════════════════════════════════════════════
  PETER v10.0.0 Build Script
═══════════════════════════════════════════════════════════

Building for DEVELOPMENT


═══════════════════════════════════════════════════════════
  Step 1/6: Pre-Build Checks
═══════════════════════════════════════════════════════════

✓ node_modules found
✓ pnpm is available
→ Cleaning previous build artifacts...
✓ Build directory cleaned


═══════════════════════════════════════════════════════════
  Step 4/6: Building Packages
═══════════════════════════════════════════════════════════

→ Building @rag/config...
✓ @rag/config built (size: 24K)
→ Building @rag/utils...
✓ @rag/utils built (size: 48K)
→ Building @rag/core...
✓ @rag/core built (size: 156K)
→ Building @rag/ui...
✓ @rag/ui built (size: 312K)
✓ Packages built in 1m 23s


═══════════════════════════════════════════════════════════
  Step 6/6: Generating Build Report
═══════════════════════════════════════════════════════════

═══════════════════════════════════════════════════════════
  PETER v10.0.0 Build Report
═══════════════════════════════════════════════════════════

Build Time: Wed Nov 19 16:30:45 2025
Total Duration: 2m 45s
Mode: Development

Package Sizes:
  @rag/config: 24K
  @rag/utils: 48K
  @rag/core: 156K
  @rag/ui: 312K

Application Sizes:
  api: 12M
  web: 8.4M
  pwa: 2.1M

Build Options:
  Parallel: false
  Skip Lint: false
  Production: false

═══════════════════════════════════════════════════════════

✓ Build report saved to dist/build-report.txt


═══════════════════════════════════════════════════════════
  Build Complete!
═══════════════════════════════════════════════════════════

✓ Build completed successfully in 2m 45s!

Build Artifacts:
  • Packages: packages/*/dist
  • Web: apps/web/.next
  • PWA: apps/pwa/dist
  • Report: dist/build-report.txt

Next Steps:
  1. Start development server:
     pnpm dev

  2. Or run tests:
     ./scripts/test-all.sh

Build artifacts ready for deployment! 🚀
```

### Performance

**Build Times** (approximate):

| Mode | Packages | Apps | Total |
|------|----------|------|-------|
| Standard | 1m 20s | 1m 30s | 2m 50s |
| Parallel | 45s | 1m 10s | 1m 55s |
| Production | 1m 30s | 2m 30s | 4m 00s |

**Optimization Tips**:
- Use `--parallel` for faster builds (recommended for development)
- Use `--skip-lint` to skip linting (only when needed)
- Production builds are slower but optimized for deployment

### Build Artifacts

**Packages**:
```
packages/config/dist/
packages/utils/dist/
packages/core/dist/
packages/ui/dist/
```

**Applications**:
```
apps/web/.next/          # Next.js production build
apps/pwa/dist/           # Vite static build
apps/api/                # Python source (no build)
```

**Reports**:
```
dist/build-report.txt    # Build summary
```

### Troubleshooting

**Build fails on type errors**:
```bash
# Fix types first
pnpm run type-check

# Or skip type check
# (edit build-all.sh, comment out type_check function call)
```

**Out of memory**:
```bash
# Increase Node memory
export NODE_OPTIONS="--max-old-space-size=4096"
./build-all.sh
```

**Parallel build hangs**:
```bash
# Use standard build
./build-all.sh
```

---

## 3. Pre-commit Hooks - Code Quality Enforcement

### Purpose
Automatically enforce code quality standards before every commit.

### Location
```bash
/home/rkqksk/projects/new_rag/.pre-commit-config.yaml
```

### Installation

**Install pre-commit**:
```bash
pip install pre-commit
```

**Install hooks**:
```bash
pre-commit install
```

**Run manually**:
```bash
pre-commit run --all-files
```

### Hooks Overview

#### General File Checks
- **trailing-whitespace** - Trim trailing spaces
- **end-of-file-fixer** - Fix EOF newlines
- **check-yaml** - Validate YAML syntax
- **check-json** - Validate JSON syntax
- **check-toml** - Validate TOML syntax
- **check-added-large-files** - Block files >1MB
- **check-merge-conflict** - Detect merge markers
- **detect-private-key** - Find private keys
- **check-case-conflict** - Case-sensitive duplicates
- **mixed-line-ending** - Consistent line endings

#### Python Code Formatting
- **black** - Auto-format Python code
  - Line length: 100
  - Python 3.11 target
  - Example:
    ```python
    # Before
    def foo(x,y,z):return x+y+z

    # After
    def foo(x, y, z):
        return x + y + z
    ```

#### Import Sorting
- **isort** - Sort Python imports
  - Profile: black-compatible
  - Line length: 100
  - Example:
    ```python
    # Before
    from typing import Dict
    import os
    from fastapi import FastAPI

    # After
    import os
    from typing import Dict

    from fastapi import FastAPI
    ```

#### Python Linting
- **flake8** - Python linter
  - Max line length: 100
  - Ignores: E203, W503, F401, F841, E501
  - Excludes: migrations, docs, build

#### Security Checks
- **detect-secrets** - Find secrets
  - Baseline: `.secrets.baseline`
  - Checks for:
    - API keys
    - Passwords
    - AWS keys
    - Private keys

#### Dockerfile Linting
- **hadolint** - Dockerfile best practices
  - Checks for:
    - FROM ordering
    - Layer optimization
    - Security issues

#### Markdown Linting
- **markdownlint** - Markdown formatting
  - Auto-fixes issues
  - Consistent style

#### TypeScript/JavaScript - Prettier
- **prettier** - Code formatter
  - Formats: TS, TSX, JS, JSX, JSON, CSS, Markdown
  - Auto-fixes formatting

#### TypeScript/JavaScript - ESLint
- **eslint** - JavaScript linter
  - TypeScript support
  - Max warnings: 0 (fail on warnings)

#### v10 Design System Validation
- **no-icons** - Block lucide-react imports
  - Enforces text-only design
  - Example blocked code:
    ```tsx
    // ❌ BLOCKED
    import { SearchIcon } from 'lucide-react'
    ```

- **no-icon-imports** - Block any Icon imports
  - Catches all icon libraries
  - Example blocked code:
    ```tsx
    // ❌ BLOCKED
    import { Icon } from 'any-icon-library'
    ```

- **pure-black-background** - Validate #000000 backgrounds
  - Blocks non-black colors
  - Example blocked code:
    ```tsx
    // ❌ BLOCKED
    <div className="bg-gray-900">
    <div style={{ background: '#111111' }}>

    // ✅ ALLOWED
    <div className="bg-black">
    <div style={{ background: '#000000' }}>
    ```

### Usage

**Automatic** (on git commit):
```bash
git add .
git commit -m "feat: add feature"

# Hooks run automatically
# If hooks fail, commit is blocked
```

**Manual** (before commit):
```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run no-icons --all-files
```

**Update hooks**:
```bash
pre-commit autoupdate
```

**Skip hooks** (use sparingly):
```bash
git commit -m "message" --no-verify
```

### Output Example

```
✂️  Trim trailing whitespace...........................................Passed
📝 Fix end of files.................................................Passed
✅ Check YAML syntax................................................Passed
✅ Check JSON syntax................................................Passed
⚫ Black (code formatter)............................................Passed
📦 isort (import sorter)............................................Passed
🔍 flake8 (linter)..................................................Passed
🔐 detect-secrets (find secrets)....................................Passed
🐳 hadolint (Dockerfile linter).....................................Passed
💅 Prettier (code formatter)........................................Passed
🔍 ESLint (linter)..................................................Passed
🚫 Validate NO Icons (lucide-react).................................Passed
🚫 Validate NO Icon Imports.........................................Passed
⚫ Validate Pure Black Background....................................Passed
```

### Design System Enforcement

The pre-commit hooks enforce v10 design system rules:

**Rule 1: NO Icons** (text only)
```tsx
// ❌ BLOCKED by pre-commit
import { SearchIcon } from 'lucide-react'
<button><SearchIcon /> Search</button>

// ✅ ALLOWED
<button>Search</button>
```

**Rule 2: Pure Black Backgrounds** (#000000 only)
```tsx
// ❌ BLOCKED by pre-commit
<div className="bg-gray-900">
<div style={{ background: '#111111' }}>

// ✅ ALLOWED
<div className="bg-black">
<div style={{ background: '#000000' }}>
```

### Troubleshooting

**Hooks failing on commit**:
```bash
# Run manually to see errors
pre-commit run --all-files

# Fix errors, then commit again
git add .
git commit -m "message"
```

**Update hook versions**:
```bash
pre-commit autoupdate
```

**Disable specific hook**:
```yaml
# Edit .pre-commit-config.yaml
# Comment out the hook you want to disable
```

**Clear hook cache**:
```bash
pre-commit clean
pre-commit install --install-hooks
```

---

## Integration with CLAUDE.md

The automation scripts have been integrated into `CLAUDE.md`:

### Quick Commands Section

```bash
# Setup
./setup.sh                    # Full setup
./setup.sh --skip-docker      # Without Docker

# Build
./build-all.sh                # Standard build
./build-all.sh --parallel     # Fast parallel build
./build-all.sh --production   # Production build

# Pre-commit
pre-commit run --all-files    # Run all hooks
pre-commit autoupdate         # Update hooks
```

### Development Workflow

```bash
# 1. Initial setup (once)
./setup.sh

# 2. Start development
pnpm dev

# 3. Make changes
# ... edit code ...

# 4. Pre-commit runs automatically on commit
git add .
git commit -m "feat: add feature"

# 5. Build for production
./build-all.sh --production
```

---

## Best Practices

### Setup Script
- Run once for initial setup
- Run again after major dependency updates
- Use `--skip-docker` for CI environments
- Use `--skip-data` for faster setup

### Build Script
- Use `--parallel` for development (faster)
- Use `--production` for deployment (optimized)
- Review build report for size optimization
- Clean build occasionally: `rm -rf dist/ */dist/`

### Pre-commit Hooks
- Keep hooks enabled (don't skip)
- Update regularly: `pre-commit autoupdate`
- Run manually before large commits
- Fix issues immediately (don't accumulate)

---

## Performance Metrics

### Setup Script
- **Time**: 3-5 minutes (with Docker)
- **Time**: 1-2 minutes (without Docker)
- **Network**: ~500MB downloads
- **Disk**: ~2GB total

### Build Script
- **Standard**: 2-3 minutes
- **Parallel**: 1-2 minutes
- **Production**: 3-4 minutes
- **Disk**: ~50MB artifacts

### Pre-commit Hooks
- **Python hooks**: 1-5 seconds
- **TypeScript hooks**: 2-10 seconds
- **Design hooks**: <1 second
- **Total**: 5-15 seconds per commit

---

## Troubleshooting Matrix

| Issue | Solution |
|-------|----------|
| setup.sh fails on Python | Install Python 3.11+: `sudo apt install python3.11` |
| setup.sh fails on Node | Install Node 18+: `nvm install 18` |
| setup.sh fails on Docker | Start Docker: `sudo systemctl start docker` |
| build-all.sh fails on types | Fix types: `pnpm run type-check` |
| build-all.sh OOM | Increase memory: `export NODE_OPTIONS="--max-old-space-size=4096"` |
| pre-commit slow | Update hooks: `pre-commit autoupdate` |
| pre-commit fails | Fix issues: `pre-commit run --all-files` |
| Icon hook triggers | Remove icons: Replace with text |
| Black background hook triggers | Use #000000: Replace with pure black |

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  setup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup
        run: ./setup.sh --skip-docker --skip-data

  build:
    runs-on: ubuntu-latest
    needs: setup
    steps:
      - name: Build
        run: ./build-all.sh --production

  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Pre-commit
        run: pre-commit run --all-files
```

---

## Summary

### setup.sh
- **Purpose**: One-command project setup
- **Time**: 3-5 minutes
- **When**: Initial setup, after updates
- **Command**: `./setup.sh`

### build-all.sh
- **Purpose**: Build all packages/apps
- **Time**: 2-3 minutes (1-2 with --parallel)
- **When**: Before deployment, after changes
- **Command**: `./build-all.sh [--parallel|--production]`

### Pre-commit Hooks
- **Purpose**: Enforce code quality
- **Time**: 5-15 seconds per commit
- **When**: Automatically on commit
- **Command**: `pre-commit run --all-files`

---

**Version**: v10.0.0
**Last Updated**: 2025-11-19
**Maintainer**: PETER Team
