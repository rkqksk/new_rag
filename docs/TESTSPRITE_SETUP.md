# TestSprite MCP Server Setup Guide

**Purpose**: AI-powered automatic testing, debugging, and code quality validation

**Status**: ⭐ **Recommended** - Improves code quality from 42% to 93%

---

## 📋 Overview

TestSprite is an AI-powered testing agent that integrates with Claude Code via MCP (Model Context Protocol). It automatically:

- ✅ Generates test cases from PRD (Product Requirements Document)
- ✅ Creates smart test plans based on code changes
- ✅ Executes tests in parallel on cloud infrastructure
- ✅ Diagnoses failures with AI-powered insights
- ✅ Provides structured feedback for code improvements

### Performance Metrics

- **42% → 93%** code quality improvement (internal benchmarks)
- Automatic test generation (no manual writing)
- Cloud-based parallel execution
- Real-time failure diagnosis

---

## 🚀 Quick Start

### 1. Get API Key (Free Tier Available)

```bash
# Visit TestSprite website
open https://testsprite.com

# Sign up for free account
# Copy your API key from dashboard
```

### 2. Configure Environment

```bash
# Add to .env file
echo "TESTSPRITE_API_KEY=your_api_key_here" >> .env

# Or set as environment variable
export TESTSPRITE_API_KEY="your_api_key_here"
```

### 3. Verify Installation

TestSprite MCP server is **already configured** in:
- `.claude/agents/code-review-agent/agent.json`
- `.claude/agents/testing-agent/agent.json`

No additional installation needed! The MCP server will auto-install via `npx` when first used.

---

## 🎯 Usage Examples

### Example 1: Code Review with Testing

```python
# Use code-review-agent with TestSprite
Task(
    subagent_type="code-review-agent",
    prompt="""
    Review the changes in src/services/billing_service.py and:
    1. Generate test cases for all new functions
    2. Run tests and identify issues
    3. Fix any bugs found
    4. Provide structured feedback
    """
)
```

**TestSprite will automatically:**
1. Analyze the code changes
2. Generate comprehensive test cases
3. Execute tests in parallel on cloud
4. Diagnose failures with AI insights
5. Suggest fixes for failing tests

### Example 2: Automated Testing

```python
# Use testing-agent with TestSprite
Task(
    subagent_type="testing-agent",
    prompt="""
    For the new SaaS authentication module:
    1. Generate test plan from docs/PRD.md
    2. Create unit and integration tests
    3. Run tests with coverage analysis
    4. Report on code quality
    """
)
```

**TestSprite will:**
1. Parse PRD to understand requirements
2. Generate smart test plan
3. Write test code (pytest format)
4. Execute tests in parallel
5. Provide coverage report + recommendations

### Example 3: Debugging Failed Tests

```python
Task(
    subagent_type="testing-agent",
    prompt="""
    Tests are failing in tests/test_saas.py.
    Use TestSprite to:
    1. Diagnose the failures
    2. Identify root causes
    3. Fix the code
    4. Re-run tests to verify
    """
)
```

**TestSprite will:**
1. Analyze test failures
2. Use AI to diagnose root cause
3. Suggest code fixes
4. Validate fixes with re-run

---

## 🔧 Advanced Configuration

### Agent-Specific Settings

#### Code Review Agent (`.claude/agents/code-review-agent/agent.json`)

```json
{
  "mcpServers": {
    "testsprite": {
      "enabled": true,
      "priority": "critical",
      "features": [
        "automatic-test-generation",
        "smart-test-plans",
        "failure-diagnosis",
        "code-quality-validation",
        "prd-based-testing"
      ]
    }
  }
}
```

#### Testing Agent (`.claude/agents/testing-agent/agent.json`)

```json
{
  "mcpServers": {
    "testsprite": {
      "enabled": true,
      "priority": "critical",
      "features": [
        "automatic-test-generation",
        "smart-test-plans",
        "parallel-test-execution",
        "failure-diagnosis",
        "structured-test-reports",
        "cloud-infrastructure"
      ]
    }
  }
}
```

### Environment Variables

```bash
# Required
TESTSPRITE_API_KEY=your_api_key_here

# Optional (for advanced features)
TESTSPRITE_PROJECT_ID=your_project_id  # Link to specific project
TESTSPRITE_TIMEOUT=300                 # Test timeout in seconds (default: 300)
TESTSPRITE_MAX_PARALLEL=10             # Max parallel tests (default: auto)
```

---

## 📊 Integration Workflow

### Typical Development Cycle

```
1. Write Code
   ↓
2. Invoke TestSprite Agent
   ↓
3. TestSprite Generates Tests
   ↓
4. Tests Execute in Cloud
   ↓
5. AI Diagnoses Failures
   ↓
6. Agent Fixes Code
   ↓
7. Re-run Tests
   ↓
8. Quality Report (42% → 93%)
```

### Example PR Workflow

```bash
# 1. Create feature branch
git checkout -b feature/new-api

# 2. Write code
vim app/api/v1/new_endpoint.py

# 3. Use TestSprite via agent
# (See usage examples above)

# 4. Review TestSprite report
# - All tests passing
# - Coverage: 95%+
# - Code quality: 93%

# 5. Commit and push
git add .
git commit -m "feat: Add new API endpoint (TestSprite validated)"
git push origin feature/new-api
```

---

## 🎨 Features Deep Dive

### 1. Automatic Test Generation

**Input**: Code file or PRD document

**Output**: Complete test suite (pytest format)

```python
# Given this code in src/services/billing_service.py:
def calculate_total(items: List[Item]) -> Decimal:
    return sum(item.price * item.quantity for item in items)

# TestSprite generates:
def test_calculate_total_empty_list():
    assert calculate_total([]) == Decimal(0)

def test_calculate_total_single_item():
    item = Item(price=10.00, quantity=2)
    assert calculate_total([item]) == Decimal(20.00)

def test_calculate_total_multiple_items():
    items = [Item(10.00, 2), Item(5.00, 3)]
    assert calculate_total(items) == Decimal(35.00)

# ... and more edge cases!
```

### 2. Smart Test Plans

TestSprite understands your PRD and creates strategic test plans:

```markdown
## Test Plan for SaaS Authentication Module

### Functional Tests
- User registration (happy path)
- User registration (duplicate email)
- Login with valid credentials
- Login with invalid credentials
- JWT token generation
- JWT token validation
- API key creation
- API key validation

### Security Tests
- SQL injection prevention
- XSS prevention
- Rate limiting
- Password strength validation

### Performance Tests
- Login latency < 200ms
- Token validation < 50ms
- 1000 concurrent users
```

### 3. Parallel Execution

TestSprite runs tests in parallel on cloud infrastructure:

```
Traditional pytest:  118 tests in 2m 30s
TestSprite Cloud:    118 tests in 15s  (10x faster!)
```

### 4. AI-Powered Diagnosis

When tests fail, TestSprite provides intelligent insights:

```
❌ test_create_tenant_duplicate_email FAILED

AI Diagnosis:
- Root Cause: Missing database constraint
- Location: src/models/saas_models.py:89
- Fix: Add unique constraint to Tenant.email field

Suggested Code Change:
  email = Column(String(255), unique=True, nullable=False, index=True)
                              ^^^^^^^^^^^
```

---

## 💡 Best Practices

### 1. Use with PRD Documents

```python
Task(
    subagent_type="testing-agent",
    prompt="""
    Read docs/PRD_SAAS_MODULE.md and generate comprehensive tests.
    Focus on:
    - User authentication flows
    - Multi-tenancy isolation
    - Billing integration
    """
)
```

### 2. Iterative Testing

```python
# First iteration: Generate tests
Task(subagent_type="testing-agent", prompt="Generate tests for auth module")

# Second iteration: Fix failures
Task(subagent_type="testing-agent", prompt="Fix all failing auth tests")

# Third iteration: Verify
Task(subagent_type="testing-agent", prompt="Run full test suite and report coverage")
```

### 3. Integration with CI/CD

```yaml
# .github/workflows/ci.yaml
- name: Run TestSprite Tests
  env:
    TESTSPRITE_API_KEY: ${{ secrets.TESTSPRITE_API_KEY }}
  run: |
    # TestSprite will auto-run via agent
    python -m claude_agent testing-agent "Run all tests"
```

---

## 🔍 Troubleshooting

### Issue 1: API Key Not Found

**Error**: `TESTSPRITE_API_KEY environment variable not set`

**Solution**:
```bash
# Check if key is set
echo $TESTSPRITE_API_KEY

# Set it if missing
export TESTSPRITE_API_KEY="your_key_here"

# Or add to .env
echo "TESTSPRITE_API_KEY=your_key_here" >> .env
```

### Issue 2: MCP Server Not Starting

**Error**: `Failed to start TestSprite MCP server`

**Solution**:
```bash
# Check Node.js version
node --version  # Should be 18+

# Clear npm cache
npm cache clean --force

# Manually install MCP server
npx -y @testsprite/testsprite-mcp
```

### Issue 3: Tests Not Running

**Error**: `No tests were collected`

**Solution**:
```bash
# Check test file naming
ls tests/test_*.py  # Should follow pytest convention

# Verify pytest is installed
pytest --version

# Run pytest manually first
pytest tests/ -v
```

---

## 📚 Resources

### Official Documentation
- TestSprite Website: https://testsprite.com
- MCP Documentation: https://docs.testsprite.com/mcp/overview
- NPM Package: https://www.npmjs.com/package/@testsprite/testsprite-mcp

### Integration Guides
- Cursor IDE: https://cursor.directory/mcp/testsprite-mcp
- GitHub Copilot: https://docs.testsprite.com/integrations/github-copilot
- Claude Code: This document!

### Community
- GitHub Issues: https://github.com/testsprite/testsprite-mcp/issues
- Discord: https://discord.gg/testsprite
- Twitter: @TestSprite

---

## 🎉 Success Stories

### Before TestSprite

```
❌ Manual test writing (2 hours per module)
❌ Tests often miss edge cases
❌ Debugging takes hours
❌ Code quality: 42% pass rate
```

### After TestSprite

```
✅ Automatic test generation (5 minutes)
✅ Comprehensive edge case coverage
✅ AI-powered instant diagnosis
✅ Code quality: 93% pass rate
```

**Time Saved**: 90% reduction in testing effort
**Quality Improvement**: 121% increase in pass rate

---

## 🔐 Security & Privacy

- ✅ Code is analyzed securely in TestSprite cloud
- ✅ No code is stored permanently
- ✅ API keys are encrypted in transit
- ✅ Compliant with SOC 2, GDPR, HIPAA
- ✅ Enterprise plans available for on-premise

---

## 💰 Pricing

| Tier | Price | Tests/Month | Support |
|------|-------|-------------|---------|
| **Free** | $0 | 1,000 | Community |
| **Pro** | $29 | 10,000 | Email |
| **Team** | $99 | 50,000 | Priority |
| **Enterprise** | Custom | Unlimited | Dedicated |

**Current Setup**: Free tier (1,000 tests/month)
**Recommended**: Pro tier for active development

---

## ✅ Quick Checklist

Before using TestSprite, make sure:

- [ ] API key obtained from https://testsprite.com
- [ ] Environment variable set (`TESTSPRITE_API_KEY`)
- [ ] Agent configurations verified (agent.json files)
- [ ] Node.js 18+ installed
- [ ] npm or npx available

---

**Created**: 2025-11-09
**Version**: 1.0.0
**Status**: ✅ Production-Ready

**Next Steps**: Try the usage examples above! 🚀
