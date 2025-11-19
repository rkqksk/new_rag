#!/usr/bin/env bash
# Static Application Security Testing (SAST)

set -e

echo "🔍 SAST - Static Analysis"
echo "=========================="
echo ""

# Create reports directory
mkdir -p reports/sast

TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# 1. Bandit (Python Security Linter)
echo "1️⃣  Running Bandit (Python)..."
if command -v bandit > /dev/null 2>&1; then
    bandit -r apps/api -f json -o reports/sast/bandit-$TIMESTAMP.json 2>&1 || {
        echo "   ⚠️  Security issues found - check report"
    }
    bandit -r apps/api -f txt > reports/sast/bandit-$TIMESTAMP.txt 2>&1 || true
    echo "   ✅ Report: reports/sast/bandit-$TIMESTAMP.txt"
else
    echo "   ⚠️  Bandit not installed. Installing..."
    pip install bandit
    bandit -r apps/api -f txt > reports/sast/bandit-$TIMESTAMP.txt 2>&1 || true
fi

# 2. Semgrep (Multi-language SAST)
echo ""
echo "2️⃣  Running Semgrep..."
if command -v semgrep > /dev/null 2>&1; then
    semgrep --config=auto --json --output=reports/sast/semgrep-$TIMESTAMP.json . 2>&1 || {
        echo "   ⚠️  Issues found - check report"
    }
    semgrep --config=auto . > reports/sast/semgrep-$TIMESTAMP.txt 2>&1 || true
    echo "   ✅ Report: reports/sast/semgrep-$TIMESTAMP.txt"
else
    echo "   ⚠️  Semgrep not installed. Install with: pip install semgrep"
    echo "   Skipping Semgrep scan..."
fi

# 3. ESLint Security Plugin (JavaScript/TypeScript)
echo ""
echo "3️⃣  Running ESLint security checks..."
if [ -f "package.json" ]; then
    # Check if eslint-plugin-security is installed
    if pnpm list eslint-plugin-security > /dev/null 2>&1; then
        pnpm eslint --ext .js,.jsx,.ts,.tsx apps/ packages/ > reports/sast/eslint-$TIMESTAMP.txt 2>&1 || {
            echo "   ⚠️  Issues found - check report"
        }
        echo "   ✅ Report: reports/sast/eslint-$TIMESTAMP.txt"
    else
        echo "   ℹ️  eslint-plugin-security not installed"
        echo "   Install: pnpm add -D eslint-plugin-security"
    fi
fi

# 4. Safety (Python Dependency Security)
echo ""
echo "4️⃣  Running Safety check..."
if command -v safety > /dev/null 2>&1; then
    safety check --json > reports/sast/safety-$TIMESTAMP.json 2>&1 || {
        echo "   ⚠️  Vulnerable dependencies found"
    }
    safety check > reports/sast/safety-$TIMESTAMP.txt 2>&1 || true
    echo "   ✅ Report: reports/sast/safety-$TIMESTAMP.txt"
else
    echo "   ⚠️  Safety not installed. Installing..."
    pip install safety
    safety check > reports/sast/safety-$TIMESTAMP.txt 2>&1 || true
fi

# 5. Git Secrets Scan
echo ""
echo "5️⃣  Scanning for exposed secrets..."

# Create simple secrets scanner
cat > /tmp/secrets-patterns.txt <<EOF
(password|passwd|pwd).*=.*['"][^'"]+['"]
(api[_-]?key|apikey).*=.*['"][^'"]+['"]
(secret[_-]?key|secretkey).*=.*['"][^'"]+['"]
(access[_-]?token|accesstoken).*=.*['"][^'"]+['"]
(private[_-]?key|privatekey).*=.*['"][^'"]+['"]
-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----
EOF

grep -r -n -f /tmp/secrets-patterns.txt \
    --include="*.py" \
    --include="*.js" \
    --include="*.ts" \
    --include="*.jsx" \
    --include="*.tsx" \
    --exclude-dir=node_modules \
    --exclude-dir=.venv \
    --exclude-dir=.git \
    . > reports/sast/secrets-scan-$TIMESTAMP.txt 2>&1 || {
    echo "   ✅ No secrets patterns found"
}

if [ -s reports/sast/secrets-scan-$TIMESTAMP.txt ]; then
    echo "   ⚠️  Potential secrets found - review manually"
    echo "   Report: reports/sast/secrets-scan-$TIMESTAMP.txt"
else
    echo "   ✅ No secrets detected"
fi

rm /tmp/secrets-patterns.txt

# 6. Generate Summary Report
echo ""
echo "6️⃣  Generating summary report..."

cat > reports/sast/summary-$TIMESTAMP.md <<EOF
# SAST Summary Report

**Generated**: $(date -Iseconds)
**Project**: RAG Enterprise v10.0.0

## Scans Performed

### 1. Bandit (Python Security)
- **Tool**: Bandit
- **Target**: apps/api
- **Report**: bandit-$TIMESTAMP.txt
- **Status**: $(if [ -f reports/sast/bandit-$TIMESTAMP.txt ]; then echo "✅ Complete"; else echo "⚠️ Not run"; fi)

### 2. Semgrep (Multi-language)
- **Tool**: Semgrep
- **Target**: All files
- **Report**: semgrep-$TIMESTAMP.txt
- **Status**: $(if [ -f reports/sast/semgrep-$TIMESTAMP.txt ]; then echo "✅ Complete"; else echo "⚠️ Not run"; fi)

### 3. ESLint Security
- **Tool**: ESLint + security plugin
- **Target**: apps/, packages/
- **Report**: eslint-$TIMESTAMP.txt
- **Status**: $(if [ -f reports/sast/eslint-$TIMESTAMP.txt ]; then echo "✅ Complete"; else echo "⚠️ Not run"; fi)

### 4. Safety (Python Dependencies)
- **Tool**: Safety
- **Target**: requirements.txt
- **Report**: safety-$TIMESTAMP.txt
- **Status**: $(if [ -f reports/sast/safety-$TIMESTAMP.txt ]; then echo "✅ Complete"; else echo "⚠️ Not run"; fi)

### 5. Secrets Scanning
- **Tool**: grep pattern matching
- **Target**: All code files
- **Report**: secrets-scan-$TIMESTAMP.txt
- **Status**: $(if [ -f reports/sast/secrets-scan-$TIMESTAMP.txt ]; then echo "✅ Complete"; else echo "⚠️ Not run"; fi)

## Key Findings

Review individual reports for detailed findings.

## Recommended Actions

1. **High Priority**: Fix all critical/high severity issues
2. **Medium Priority**: Review and fix medium severity issues
3. **Low Priority**: Consider fixing low severity issues
4. **Documentation**: Update security documentation

## Next Steps

1. Review detailed reports in \`reports/sast/\`
2. Create GitHub issues for findings
3. Fix critical issues immediately
4. Schedule fixes for medium/low issues
5. Re-run scan after fixes

## Automation

Add to CI/CD pipeline:
\`\`\`yaml
- name: SAST Scan
  run: ./scripts/sast-scan.sh
\`\`\`

---
**Note**: This is an automated scan. Manual security review is still recommended.
EOF

cat reports/sast/summary-$TIMESTAMP.md

echo ""
echo "✅ SAST scan complete!"
echo "   Summary: reports/sast/summary-$TIMESTAMP.md"
echo "   All reports: reports/sast/"
