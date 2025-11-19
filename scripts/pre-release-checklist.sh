#!/usr/bin/env bash
# Pre-release checklist for v10.0.0

set -e

echo "📋 Pre-Release Checklist - v10.0.0"
echo "===================================="
echo ""

REPORT_FILE="reports/validation/pre-release-checklist-$(date +%Y%m%d).md"
mkdir -p reports/validation

cat > $REPORT_FILE <<EOF
# Pre-Release Checklist - v10.0.0

**Date**: $(date -Iseconds)
**Version**: v10.0.0 "Unified Maximum"
**Release Manager**: [Your Name]

---

## Code Quality

EOF

echo "## Code Quality Checks" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE

# Linting
echo "🔍 Running linters..."
cat >> $REPORT_FILE <<EOF
- [ ] Code linting passed
  \`\`\`bash
  make lint  # or pnpm lint
  \`\`\`

EOF

# Type checking
cat >> $REPORT_FILE <<EOF
- [ ] Type checking passed
  \`\`\`bash
  make type-check  # or pnpm type-check
  \`\`\`

EOF

# Tests
echo "🧪 Checking tests..."
cat >> $REPORT_FILE <<EOF
- [ ] All unit tests passing
  \`\`\`bash
  pytest tests/ -v
  \`\`\`

- [ ] All integration tests passing
  \`\`\`bash
  pytest tests/integration/ -v
  \`\`\`

- [ ] All E2E tests passing
  \`\`\`bash
  pnpm exec playwright test
  \`\`\`

- [ ] Test coverage ≥ 80%
  \`\`\`bash
  pytest --cov=apps/api --cov-report=term
  \`\`\`

EOF

# Security
echo "🔒 Security checks..."
cat >> $REPORT_FILE <<EOF
## Security

- [ ] No dependency vulnerabilities
  \`\`\`bash
  ./scripts/security-audit.sh
  \`\`\`

- [ ] SAST scan clean
  \`\`\`bash
  ./scripts/sast-scan.sh
  \`\`\`

- [ ] No hardcoded secrets
  \`\`\`bash
  grep -r "password.*=.*['\"]" apps/
  \`\`\`

- [ ] SECURITY.md updated
- [ ] Security headers configured
- [ ] Authentication/authorization tested

EOF

# Performance
cat >> $REPORT_FILE <<EOF
## Performance

- [ ] Performance benchmarks run
  \`\`\`bash
  ./scripts/benchmark.sh
  \`\`\`

- [ ] Load testing completed
  \`\`\`bash
  ./scripts/load-test.sh
  \`\`\`

- [ ] Bundle size optimized
  \`\`\`bash
  ./scripts/optimize-bundle.sh
  \`\`\`

- [ ] API response times acceptable (< 500ms)
- [ ] Database query performance optimized
- [ ] No memory leaks detected

EOF

# Documentation
cat >> $REPORT_FILE <<EOF
## Documentation

- [ ] README.md updated with v10.0.0 info
- [ ] CLAUDE.md updated
- [ ] PROGRESS.md updated with v10.0.0 changes
- [ ] API documentation generated
  \`\`\`bash
  # Check docs/API_REFERENCE.md
  \`\`\`
- [ ] Architecture diagrams updated
- [ ] CHANGELOG.md created/updated
- [ ] Migration guide written (if needed)
- [ ] All code comments accurate
- [ ] All broken links fixed

EOF

# Build & Deployment
cat >> $REPORT_FILE <<EOF
## Build & Deployment

- [ ] Production build successful
  \`\`\`bash
  pnpm build
  \`\`\`

- [ ] Docker images build successfully
  \`\`\`bash
  docker build -f apps/api/Dockerfile.prod -t api:v10.0.0 .
  docker build -f apps/web/Dockerfile.prod -t web:v10.0.0 .
  \`\`\`

- [ ] Kubernetes manifests validated
  \`\`\`bash
  kubectl apply --dry-run=client -f infrastructure/k8s/
  \`\`\`

- [ ] Environment variables documented
- [ ] Deployment runbook reviewed
- [ ] Rollback procedure tested
- [ ] Health checks working
- [ ] Monitoring configured

EOF

# Database
cat >> $REPORT_FILE <<EOF
## Database

- [ ] Database migrations tested
  \`\`\`bash
  alembic upgrade head
  alembic downgrade -1
  alembic upgrade head
  \`\`\`

- [ ] Backup and restore tested
- [ ] Data migration script ready (if needed)
- [ ] Database indexes optimized
- [ ] Connection pooling configured

EOF

# Third-party Services
cat >> $REPORT_FILE <<EOF
## Third-party Services

- [ ] All API keys configured
- [ ] Rate limits verified
- [ ] Service dependencies documented
- [ ] Fallback mechanisms tested
- [ ] External service monitoring enabled

EOF

# Release Management
cat >> $REPORT_FILE <<EOF
## Release Management

- [ ] Version number updated in all files
  - package.json
  - pyproject.toml / setup.py
  - docker-compose.yml
  - README.md

- [ ] CHANGELOG.md updated with:
  - New features
  - Bug fixes
  - Breaking changes
  - Deprecations

- [ ] Git tags created
  \`\`\`bash
  git tag -a v10.0.0 -m "Release v10.0.0 - Unified Maximum"
  git push origin v10.0.0
  \`\`\`

- [ ] Release notes prepared
- [ ] Communication plan ready
  - Email to users
  - Blog post
  - Social media
  - Documentation site

EOF

# Post-Deployment
cat >> $REPORT_FILE <<EOF
## Post-Deployment Validation

- [ ] Smoke tests on staging
- [ ] Smoke tests on production
- [ ] Monitoring dashboards checked
- [ ] Error rates normal
- [ ] Performance metrics normal
- [ ] User feedback collected

EOF

# Sign-off
cat >> $REPORT_FILE <<EOF
---

## Sign-off

- [ ] Technical Lead: _____________________ Date: _______
- [ ] Security Review: ____________________ Date: _______
- [ ] QA Lead: ___________________________ Date: _______
- [ ] Product Manager: ____________________ Date: _______
- [ ] Release Manager: ____________________ Date: _______

---

## Additional Notes

<!-- Add any additional notes, concerns, or items here -->

EOF

cat >> $REPORT_FILE <<EOF

---

## Quick Commands Reference

\`\`\`bash
# Full validation
./scripts/final-validation.sh

# Run all tests
./scripts/test-all.sh

# Security audit
./scripts/security-audit.sh
./scripts/sast-scan.sh

# Performance testing
./scripts/benchmark.sh
./scripts/load-test.sh

# Build everything
./scripts/build-all.sh

# Deploy to staging
./scripts/deploy-production.sh staging

# Deploy to production
./scripts/deploy-production.sh production
\`\`\`

---

**Report generated**: $(date)
**Location**: $REPORT_FILE
EOF

cat $REPORT_FILE

echo ""
echo "✅ Pre-release checklist generated!"
echo "📄 Review and complete: $REPORT_FILE"
