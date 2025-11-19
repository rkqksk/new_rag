# Scripts Directory

**Version**: v10.0.0
**Status**: Production Ready

This directory contains automation scripts for the PETER v10.0.0 monorepo.

---

## Core Automation Scripts

### 1. setup.sh (Project Root)
**Location**: `/home/rkqksk/projects/new_rag/setup.sh`

One-command project setup for fresh environments.

```bash
# Full setup
./setup.sh

# Without Docker
./setup.sh --skip-docker

# Without data seeding
./setup.sh --skip-data

# Help
./setup.sh --help
```

**What it does**:
- Checks system requirements (Python 3.11+, Node 18+, Docker, pnpm)
- Installs Python dependencies (requirements.txt)
- Installs Node dependencies (pnpm install)
- Sets up .env file
- Starts Docker services
- Initializes databases
- Runs migrations
- Seeds initial data
- Verifies setup

**Time**: 3-5 minutes

---

### 2. build-all.sh (Project Root)
**Location**: `/home/rkqksk/projects/new_rag/build-all.sh`

Build all apps and packages in correct dependency order.

```bash
# Standard build
./build-all.sh

# Fast parallel build
./build-all.sh --parallel

# Production optimized build
./build-all.sh --production

# Skip linting
./build-all.sh --skip-lint

# Help
./build-all.sh --help
```

**What it does**:
- Pre-build checks
- TypeScript type checking
- Linting (ESLint, Prettier, Black, Flake8)
- Builds packages in order (config → utils → core → ui)
- Builds apps (api, web, pwa)
- Generates build report

**Time**: 2-3 minutes (1-2 with --parallel)

---

## Other Scripts

### Deployment
- `deploy-optimized.sh` - Deploy to environments
- `deploy-production.sh` - Production deployment
- `rollback.sh` - Rollback deployment

### Testing
- `test-all.sh` - Run all tests
- `test-optimized.sh` - Optimized test run
- `benchmark.sh` - Performance benchmarks
- `load-test.sh` - Load testing

### Database
- `db-migrate.sh` - Run migrations
- `migrate_to_hierarchical_chunks.py` - Migrate to hierarchical chunks
- `create_multimodal_collection.py` - Create multimodal Qdrant collection

### Health & Monitoring
- `health-check.sh` - Check service health
- `analyze-performance.py` - Performance analysis
- `train-predictive-alerts.py` - Train ML models for alerts

### Development
- `dev.sh` - Start development environment
- `fix-file-watchers.sh` - Fix file watcher limits
- `setup-ssh-keepalive.sh` - SSH keepalive configuration

### Security
- `sast-scan.sh` - Static security scanning
- `security-audit.sh` - Security audit
- `pre-release-checklist.sh` - Pre-release checks

### Validation
- `validate-v10.sh` - Validate v10 structure
- `final-validation.sh` - Final validation before release

### Build & Optimization
- `optimize-bundle.sh` - Optimize bundle size

---

## Pre-commit Hooks

**Location**: `.pre-commit-config.yaml` (project root)

Automatic code quality enforcement on every commit.

```bash
# Install
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

**Hooks**:
- Python: black, isort, flake8, mypy
- TypeScript: prettier, eslint
- General: trailing whitespace, EOF newlines, YAML/JSON validation
- Security: detect-secrets, private key detection
- Design System: no icons, pure black backgrounds

---

## Usage Patterns

### First Time Setup
```bash
# 1. Clone repository
git clone <repo-url>
cd new_rag

# 2. Run setup
./setup.sh

# 3. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 4. Start development
pnpm dev
```

### Daily Development
```bash
# Start development
pnpm dev

# Make changes
# ... edit code ...

# Commit (pre-commit hooks run automatically)
git add .
git commit -m "feat: add feature"

# Build for testing
./build-all.sh --parallel
```

### Before Deployment
```bash
# Build production
./build-all.sh --production

# Run tests
./scripts/test-all.sh

# Security checks
./scripts/security-audit.sh

# Validate
./scripts/validate-v10.sh

# Deploy
./scripts/deploy-production.sh
```

---

## Script Guidelines

### Creating New Scripts

1. **Naming**: Use kebab-case (e.g., `my-script.sh`)
2. **Shebang**: Always start with `#!/bin/bash`
3. **Set flags**: Use `set -e` to exit on error
4. **Colors**: Use color codes for output (RED, GREEN, YELLOW, BLUE, NC)
5. **Help**: Include `--help` flag
6. **Location**: Add to `/scripts/` directory
7. **Executable**: Make executable with `chmod +x`
8. **Documentation**: Add to this README

### Script Template

```bash
#!/bin/bash

################################################################################
# Script Name - Brief Description
################################################################################
# Purpose: Detailed description
# Usage: ./script-name.sh [OPTIONS]
# Author: PETER Team
# Version: 10.0.0
################################################################################

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper functions
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}!${NC} $1"; }
print_info() { echo -e "${BLUE}→${NC} $1"; }

# Main function
main() {
    print_info "Starting..."
    # ... script logic ...
    print_success "Complete!"
}

main "$@"
```

---

## Performance Metrics

| Script | Time | Network | Disk |
|--------|------|---------|------|
| setup.sh | 3-5 min | ~500MB | ~2GB |
| setup.sh --skip-docker | 1-2 min | ~200MB | ~500MB |
| build-all.sh | 2-3 min | - | ~50MB |
| build-all.sh --parallel | 1-2 min | - | ~50MB |
| pre-commit hooks | 5-15s | - | - |

---

## Troubleshooting

### setup.sh fails
```bash
# Check requirements
python3 --version  # Need 3.11+
node --version     # Need 18+
docker --version   # Need Docker
pnpm --version     # Need pnpm

# Install missing dependencies
sudo apt install python3.11 nodejs docker.io
npm install -g pnpm
```

### build-all.sh fails
```bash
# Check node_modules
ls -la node_modules/  # Should exist
pnpm install          # Reinstall if needed

# Check types
pnpm run type-check

# Increase memory (if OOM)
export NODE_OPTIONS="--max-old-space-size=4096"
```

### pre-commit hooks fail
```bash
# Run manually to see errors
pre-commit run --all-files

# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean
pre-commit install --install-hooks
```

---

## Documentation

**Complete Guide**: `docs/guides/AUTOMATION_SCRIPTS.md`
**Quick Reference**: `CLAUDE.md` → Essential Commands
**API Reference**: `docs/reference/API_DOCUMENTATION.md`

---

## Support

For issues or questions:
1. Check documentation: `docs/guides/AUTOMATION_SCRIPTS.md`
2. Check troubleshooting: `docs/guides/TROUBLESHOOTING.md`
3. Check CLAUDE.md for quick reference

---

**Version**: v10.0.0
**Last Updated**: 2025-11-19
**Maintainer**: PETER Team
