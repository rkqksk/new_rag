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
- ✅ **Test generation** (AI-powered)
- ✅ **Parallel execution** (pytest-xdist)

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

## 🔧 Configuration

Located in `agent.json`:

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
**Last Updated**: 2025-11-08
