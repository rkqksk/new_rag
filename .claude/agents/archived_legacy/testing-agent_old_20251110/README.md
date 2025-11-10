# Testing Agent

**Purpose**: Automated testing - unit tests, integration tests, coverage analysis

**Version**: 1.0.0
**Status**: ✅ Production-Ready

---

## 🎯 Overview

Specialized sub-agent for test automation and quality assurance.

### Key Features

- ✅ **Unit testing** (pytest)
- ✅ **Integration testing** (API, DB, services)
- ✅ **Coverage analysis** (pytest-cov)
- ⭐ **AI-powered test generation** (TestSprite)
- ✅ **Parallel execution** (pytest-xdist + TestSprite Cloud)
- ⭐ **Automatic debugging & fixing** (TestSprite)

---

## 🚀 Usage

### Via Task Tool

```python
# Launch testing agent
Task(
    subagent_type="testing-agent",
    prompt="Run all tests and generate coverage report"
)
```

### Common Commands

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov=app --cov-report=html

# Run specific test file
pytest tests/test_search.py -v

# Run in parallel
pytest tests/ -n auto
```

---

## 🔧 MCP Servers

| Server | Purpose | Cost | Priority |
|--------|---------|------|----------|
| **testsprite** ⭐ | AI-powered testing & debugging | Free tier available | Critical |
| **filesystem** | File operations | $0/month | High |

**Total Cost**: $0/month (with free tier)

### ⭐ TestSprite Features

- **Automatic test generation** from PRD
- **Smart test plans** based on code changes
- **Parallel execution** on cloud infrastructure
- **Failure diagnosis** with AI-powered insights
- **Structured reports** for coding agents
- **42% → 93% quality improvement**

---

## ⚙️ Configuration

### TestSprite API Key Setup (Recommended) ⭐

```bash
# Get free API key at: https://testsprite.com
export TESTSPRITE_API_KEY="your_api_key_here"

# Or add to .env file
echo "TESTSPRITE_API_KEY=your_api_key_here" >> .env
```

### Agent Config (in `agent.json`)

```json
{
  "test_framework": "pytest",
  "coverage_threshold": 95,
  "parallel_tests": true,
  "auto_generate": false
}
```

---

## 📊 Performance

- ✅ **122+ test cases**
- ✅ **95%+ coverage target**
- ✅ **Parallel execution**
- ✅ **Fast feedback loop**

---

## 📚 Related

- Tools: `pytest`, `pytest-cov`, `pytest-asyncio`
- Docs: `docs/guides/TESTING_GUIDE.md`
- Scripts: `scripts/test-optimized.sh`

---

**Created**: 2025-11-08
**Last Updated**: 2025-11-09
**Enhancement**: Added TestSprite MCP for intelligent test automation and AI-powered debugging
