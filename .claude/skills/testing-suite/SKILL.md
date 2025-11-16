---
name: testing-suite
description: pytest test coverage unit integration E2E testing 테스트 자동 생성 커버리지 단위 통합 playwright FastAPI TestClient mock fixture 테스트 주도 개발 TDD CI/CD quality assurance
---

# Comprehensive Testing Suite

## When to Use
- 테스트 생성, generate tests
- 커버리지 향상, improve coverage
- 단위 테스트, unit testing
- 통합 테스트, integration testing
- E2E 테스트, end-to-end testing
- CI/CD 파이프라인, continuous integration
- 테스트 자동화, test automation

## Core Capabilities
1. **Unit Tests** - pytest, 90%+ coverage target
2. **Integration Tests** - FastAPI TestClient, service interactions
3. **E2E Tests** - Playwright, user workflows
4. **Test Generation** - Automatic test creation from code
5. **Coverage Analysis** - pytest-cov, coverage reports

## Quick Actions

### Generate Unit Tests
```python
# Auto-generate from code
python scripts/generate_unit_tests.py \
  --target src/services/rag_service.py \
  --output tests/unit/test_rag_service.py \
  --coverage 90
```

### Run Tests
```bash
# All tests with coverage
pytest tests/ --cov=src --cov=app --cov-report=html

# Specific module
pytest tests/unit/test_rag_service.py -v

# Integration tests only
pytest tests/integration/ -v
```

### E2E Testing
```python
# Generate Playwright tests
python scripts/create_e2e_suite.py \
  --flows login,search,checkout \
  --output tests/e2e/
```

### Measure Coverage
```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## Test Templates

### Unit Test (pytest)
```python
import pytest
from src.services.example import ExampleService

class TestExampleService:
    @pytest.fixture
    def service(self):
        return ExampleService()

    def test_happy_path(self, service):
        result = service.method("input")
        assert result == "expected"

    @pytest.mark.asyncio
    async def test_async_method(self, service):
        result = await service.async_method()
        assert result is not None
```

### Integration Test (FastAPI)
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_search_endpoint():
    response = client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code == 200
    assert "results" in response.json()
```

### E2E Test (Playwright)
```typescript
import { test, expect } from '@playwright/test';

test('user can search products', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="search"]', 'bottle');
  await page.click('[data-testid="submit"]');
  await expect(page.locator('[data-testid="results"]')).toBeVisible();
});
```

## Integration
- **rag-optimization**: Generate RAG component tests
- **data-collection**: Test crawlers and parsers
- **manufacturing-vision**: Validate vision models
- **deployment-automation**: Pre-deployment testing

## Key Files
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests
- `pytest.ini` - pytest configuration
- `.coveragerc` - Coverage settings

## Coverage Targets
- **Critical paths**: 95%+
- **Services**: 90%+
- **Utilities**: 85%+
- **Overall**: 80%+
