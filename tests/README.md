# RAG Enterprise Backend Tests

Comprehensive test suite for the RAG Enterprise backend system.

## Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── unit/                       # Unit tests
│   ├── repositories/          # Repository layer tests
│   │   ├── test_qdrant_repository.py
│   │   ├── test_redis_repository.py
│   │   └── test_postgres_repository.py
│   └── services/              # Service layer tests
│       ├── test_search_service.py
│       ├── test_personalization_service.py
│       └── test_analytics_service.py
└── integration/               # Integration tests
    ├── test_search_api.py
    ├── test_personalization_api.py
    ├── test_analytics_api.py
    └── test_health_endpoints.py
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run unit tests only
```bash
pytest tests/unit/ -m unit
```

### Run integration tests only
```bash
pytest tests/integration/ -m integration
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest tests/unit/services/test_search_service.py -v
```

### Run specific test
```bash
pytest tests/unit/services/test_search_service.py::TestSearchService::test_search_with_cache_hit -v
```

## Test Coverage Target

- **Target**: 95%+ coverage
- **Current**: Run `pytest --cov=app --cov-report=term` to see current coverage

## Writing Tests

### Unit Test Example
```python
@pytest.mark.unit
class TestMyService:
    @pytest.fixture
    def service(self, mock_repo):
        return MyService(repo=mock_repo)
    
    @pytest.mark.asyncio
    async def test_my_method(self, service):
        result = await service.my_method()
        assert result is not None
```

### Integration Test Example
```python
@pytest.mark.integration
class TestMyAPI:
    def test_endpoint(self):
        response = client.post("/api/v1/endpoint", json={...})
        assert response.status_code == 200
```

## Fixtures

Available fixtures in `conftest.py`:
- `sample_product` - Single product data
- `sample_products` - List of products
- `sample_search_results` - Qdrant search results
- `sample_session_id` - Test session ID
- `sample_user_profile` - User profile data
- `mock_qdrant_repo` - Mock Qdrant repository
- `mock_redis_repo` - Mock Redis repository
- `mock_postgres_repo` - Mock Postgres repository
- `mock_embedder` - Mock embedding service
- `mock_reranker` - Mock re-ranker
- `mock_router` - Mock query router
- `test_client` - FastAPI test client

## CI/CD Integration

Tests are automatically run in CI/CD pipeline:
- Pre-commit: Fast unit tests
- Pre-push: Full test suite
- GitHub Actions: Full suite + coverage report

## Performance

- Unit tests: ~2-5 seconds total
- Integration tests: ~5-10 seconds total
- Full suite: ~10-15 seconds

## Notes

- All database operations are mocked in unit tests
- Integration tests use TestClient (no real HTTP)
- Async tests use pytest-asyncio
- Coverage reports in `htmlcov/` directory
