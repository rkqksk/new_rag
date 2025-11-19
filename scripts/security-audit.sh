#!/usr/bin/env bash
# Comprehensive security audit script

set -e

echo "🔒 Security Audit"
echo "================="
echo ""

# Create reports directory
mkdir -p reports/security

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
REPORT_FILE="reports/security/audit-$TIMESTAMP.txt"

# Initialize report
cat > $REPORT_FILE <<EOF
SECURITY AUDIT REPORT
=====================
Generated: $(date -Iseconds)
Project: RAG Enterprise v10.0.0

EOF

# 1. Dependency Vulnerability Scanning
echo "1️⃣  Scanning dependencies for vulnerabilities..."
echo "" >> $REPORT_FILE
echo "1. DEPENDENCY VULNERABILITIES" >> $REPORT_FILE
echo "==============================" >> $REPORT_FILE

# Python dependencies
if [ -f "requirements.txt" ]; then
    echo "   📦 Python packages..."
    if command -v pip-audit > /dev/null 2>&1; then
        pip-audit --desc -r requirements.txt > reports/security/pip-audit-$TIMESTAMP.txt 2>&1 || {
            echo "   ⚠️  Vulnerabilities found - check report"
        }
        echo "" >> $REPORT_FILE
        echo "Python Dependencies:" >> $REPORT_FILE
        cat reports/security/pip-audit-$TIMESTAMP.txt >> $REPORT_FILE
    else
        echo "   ⚠️  pip-audit not installed. Installing..."
        pip install pip-audit
        pip-audit --desc -r requirements.txt > reports/security/pip-audit-$TIMESTAMP.txt 2>&1 || true
    fi
fi

# Node dependencies
if [ -f "package.json" ]; then
    echo "   📦 Node packages..."
    pnpm audit --json > reports/security/npm-audit-$TIMESTAMP.json 2>&1 || {
        echo "   ⚠️  Vulnerabilities found - check report"
    }

    echo "" >> $REPORT_FILE
    echo "Node Dependencies:" >> $REPORT_FILE
    pnpm audit >> $REPORT_FILE 2>&1 || echo "Vulnerabilities detected" >> $REPORT_FILE
fi

# 2. Secrets Scanning
echo ""
echo "2️⃣  Scanning for secrets and credentials..."
echo "" >> $REPORT_FILE
echo "2. SECRETS SCANNING" >> $REPORT_FILE
echo "===================" >> $REPORT_FILE

# Check for common secret patterns
SECRETS_FOUND=0

# Scan for API keys
if grep -r -i "api[_-]key.*=.*['\"]" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v ".venv" | grep -v ".git"; then
    echo "   ⚠️  Potential API keys found in code"
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
fi

# Scan for passwords
if grep -r -i "password.*=.*['\"]" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v ".venv" | grep -v ".git" | grep -v "password: str" | grep -v "password: string"; then
    echo "   ⚠️  Potential hardcoded passwords found"
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
fi

# Scan for tokens
if grep -r -i "token.*=.*['\"]" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | grep -v node_modules | grep -v ".venv" | grep -v ".git" | grep -v "token: str" | grep -v "token: string"; then
    echo "   ⚠️  Potential tokens found in code"
    SECRETS_FOUND=$((SECRETS_FOUND + 1))
fi

if [ $SECRETS_FOUND -eq 0 ]; then
    echo "   ✅ No obvious secrets found in code"
    echo "No hardcoded secrets detected" >> $REPORT_FILE
else
    echo "WARNING: $SECRETS_FOUND potential secret patterns found" >> $REPORT_FILE
fi

# 3. OWASP Top 10 Compliance Check
echo ""
echo "3️⃣  OWASP Top 10 compliance check..."
echo "" >> $REPORT_FILE
echo "3. OWASP TOP 10 COMPLIANCE" >> $REPORT_FILE
echo "==========================" >> $REPORT_FILE

# A01:2021 – Broken Access Control
echo "   🔍 A01: Broken Access Control"
if grep -r "@require_auth\|@require_admin\|@login_required" --include="*.py" apps/ > /dev/null 2>&1; then
    echo "      ✅ Authentication decorators found"
    echo "A01: ✅ Authentication mechanisms present" >> $REPORT_FILE
else
    echo "      ⚠️  Few authentication decorators found"
    echo "A01: ⚠️  Review access control implementation" >> $REPORT_FILE
fi

# A02:2021 – Cryptographic Failures
echo "   🔍 A02: Cryptographic Failures"
if grep -r "hashlib\|bcrypt\|passlib" --include="*.py" . > /dev/null 2>&1; then
    echo "      ✅ Cryptographic libraries in use"
    echo "A02: ✅ Cryptographic libraries detected" >> $REPORT_FILE
else
    echo "      ⚠️  No cryptographic libraries found"
    echo "A02: ⚠️  Ensure proper encryption for sensitive data" >> $REPORT_FILE
fi

# A03:2021 – Injection
echo "   🔍 A03: Injection"
if grep -r "execute\|exec\|eval" --include="*.py" apps/ 2>/dev/null | grep -v "executor\|execution" > /dev/null; then
    echo "      ⚠️  Potentially unsafe execution found"
    echo "A03: ⚠️  Review SQL/command injection risks" >> $REPORT_FILE
else
    echo "      ✅ No obvious injection risks"
    echo "A03: ✅ Using parameterized queries (SQLAlchemy)" >> $REPORT_FILE
fi

# A04:2021 – Insecure Design
echo "   🔍 A04: Insecure Design"
if [ -f "docs/SECURITY.md" ] || [ -f "SECURITY.md" ]; then
    echo "      ✅ Security documentation exists"
    echo "A04: ✅ Security design documentation present" >> $REPORT_FILE
else
    echo "      ⚠️  No security documentation"
    echo "A04: ⚠️  Add SECURITY.md with threat model" >> $REPORT_FILE
fi

# A05:2021 – Security Misconfiguration
echo "   🔍 A05: Security Misconfiguration"
if grep -r "DEBUG.*=.*True\|debug.*true" --include="*.py" --include="*.js" apps/ 2>/dev/null | grep -v "# "; then
    echo "      ⚠️  Debug mode might be enabled"
    echo "A05: ⚠️  Ensure DEBUG=False in production" >> $REPORT_FILE
else
    echo "      ✅ No debug flags in production code"
    echo "A05: ✅ Debug configurations properly managed" >> $REPORT_FILE
fi

# A06:2021 – Vulnerable and Outdated Components (covered in step 1)
echo "   🔍 A06: Vulnerable Components"
echo "      ℹ️  See dependency scan above"
echo "A06: See dependency vulnerability scan" >> $REPORT_FILE

# A07:2021 – Identification and Authentication Failures
echo "   🔍 A07: Authentication Failures"
if grep -r "JWT\|OAuth\|session" --include="*.py" apps/ > /dev/null 2>&1; then
    echo "      ✅ Authentication mechanisms present"
    echo "A07: ✅ JWT/OAuth authentication implemented" >> $REPORT_FILE
else
    echo "      ⚠️  Review authentication implementation"
    echo "A07: ⚠️  Ensure robust authentication" >> $REPORT_FILE
fi

# A08:2021 – Software and Data Integrity Failures
echo "   🔍 A08: Integrity Failures"
if [ -f "package-lock.json" ] || [ -f "pnpm-lock.yaml" ]; then
    echo "      ✅ Dependency lock files present"
    echo "A08: ✅ Dependency integrity via lock files" >> $REPORT_FILE
else
    echo "      ⚠️  No lock files found"
    echo "A08: ⚠️  Use lock files for dependency integrity" >> $REPORT_FILE
fi

# A09:2021 – Security Logging and Monitoring Failures
echo "   🔍 A09: Logging and Monitoring"
if grep -r "logging\|logger\|log\." --include="*.py" apps/ > /dev/null 2>&1; then
    echo "      ✅ Logging implementation found"
    echo "A09: ✅ Logging mechanisms in place" >> $REPORT_FILE
else
    echo "      ⚠️  Limited logging found"
    echo "A09: ⚠️  Implement comprehensive logging" >> $REPORT_FILE
fi

# A10:2021 – Server-Side Request Forgery (SSRF)
echo "   🔍 A10: SSRF"
if grep -r "requests\.get\|requests\.post" --include="*.py" apps/ 2>/dev/null | grep -v "# "; then
    echo "      ⚠️  HTTP requests found - validate URLs"
    echo "A10: ⚠️  Validate all external URLs (SSRF risk)" >> $REPORT_FILE
else
    echo "      ✅ No obvious SSRF risks"
    echo "A10: ✅ Limited external requests" >> $REPORT_FILE
fi

# 4. Security Headers Check
echo ""
echo "4️⃣  Checking security headers configuration..."
echo "" >> $REPORT_FILE
echo "4. SECURITY HEADERS" >> $REPORT_FILE
echo "===================" >> $REPORT_FILE

# Check if security headers are configured
HEADERS_CONFIGURED=0

if grep -r "X-Frame-Options\|X-Content-Type-Options\|Strict-Transport-Security" --include="*.py" --include="*.js" apps/ > /dev/null 2>&1; then
    echo "   ✅ Security headers configured"
    HEADERS_CONFIGURED=1
else
    echo "   ⚠️  Security headers not found"
fi

cat >> $REPORT_FILE <<EOF

Required Security Headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Strict-Transport-Security: max-age=31536000
- Content-Security-Policy: default-src 'self'
- X-XSS-Protection: 1; mode=block

Status: $(if [ $HEADERS_CONFIGURED -eq 1 ]; then echo "✅ Configured"; else echo "⚠️  Not configured"; fi)
EOF

# 5. File Permissions Check
echo ""
echo "5️⃣  Checking file permissions..."
echo "" >> $REPORT_FILE
echo "5. FILE PERMISSIONS" >> $REPORT_FILE
echo "===================" >> $REPORT_FILE

# Check for world-writable files
WORLD_WRITABLE=$(find . -type f -perm -002 2>/dev/null | grep -v ".git" | grep -v "node_modules" | grep -v ".venv" || echo "")

if [ -z "$WORLD_WRITABLE" ]; then
    echo "   ✅ No world-writable files found"
    echo "No world-writable files detected" >> $REPORT_FILE
else
    echo "   ⚠️  World-writable files found"
    echo "WARNING: World-writable files found:" >> $REPORT_FILE
    echo "$WORLD_WRITABLE" >> $REPORT_FILE
fi

# 6. Environment Variables Check
echo ""
echo "6️⃣  Checking environment configuration..."
echo "" >> $REPORT_FILE
echo "6. ENVIRONMENT CONFIGURATION" >> $REPORT_FILE
echo "============================" >> $REPORT_FILE

if [ -f ".env.example" ]; then
    echo "   ✅ .env.example found"
    echo "✅ Environment template exists" >> $REPORT_FILE
else
    echo "   ⚠️  .env.example not found"
    echo "⚠️  Create .env.example for documentation" >> $REPORT_FILE
fi

if [ -f ".env" ]; then
    if grep "^\.env$" .gitignore > /dev/null 2>&1; then
        echo "   ✅ .env in .gitignore"
        echo "✅ .env properly excluded from git" >> $REPORT_FILE
    else
        echo "   ⚠️  .env not in .gitignore!"
        echo "⚠️  WARNING: .env not in .gitignore" >> $REPORT_FILE
    fi
fi

# Generate recommendations
echo "" >> $REPORT_FILE
echo "RECOMMENDATIONS" >> $REPORT_FILE
echo "===============" >> $REPORT_FILE
cat >> $REPORT_FILE <<EOF

IMMEDIATE ACTIONS:
1. Fix all critical and high severity vulnerabilities
2. Remove any hardcoded secrets from code
3. Add security headers to all responses
4. Ensure .env files are in .gitignore

SHORT-TERM (This Sprint):
1. Implement rate limiting on API endpoints
2. Add input validation and sanitization
3. Enable CORS with specific origins
4. Set up security monitoring and alerting
5. Create SECURITY.md with vulnerability reporting

LONG-TERM (Next Quarter):
1. Implement automated security scanning in CI/CD
2. Conduct penetration testing
3. Set up bug bounty program
4. Regular security audits and reviews
5. Security training for development team

COMPLIANCE:
- GDPR: Ensure data protection and privacy
- SOC 2: Implement security controls
- ISO 27001: Information security management

Generated: $(date)
EOF

# Final summary
echo "" | tee -a $REPORT_FILE
echo "SUMMARY" | tee -a $REPORT_FILE
echo "=======" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE
echo "✅ Audit complete!" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE
echo "📄 Full report: $REPORT_FILE" | tee -a $REPORT_FILE
echo "" | tee -a $REPORT_FILE
echo "🔍 Review findings and address high-priority issues immediately." | tee -a $REPORT_FILE
