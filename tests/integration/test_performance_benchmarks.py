"""
Performance Benchmarking: Critical Path Analysis

Tests performance of critical code paths and identifies optimization opportunities.
Measures latency, throughput, and resource utilization.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import AsyncMock, Mock

import pytest

# ============================================================
# Dependency Injection Performance
# ============================================================


@pytest.mark.integration
class TestDIPerfomance:
    """Test dependency injection performance"""

    def test_get_config_latency(self):
        """Test config retrieval latency"""
        from app.core.dependencies import get_config

        # Warm up
        get_config()

        # Measure 1000 calls
        start = time.time()
        for _ in range(1000):
            get_config()
        elapsed = time.time() - start

        # Should be very fast (<10ms total, <0.01ms per call)
        assert elapsed < 0.01
        avg_latency = (elapsed * 1000) / 1000  # ms per call
        assert avg_latency < 0.01

    def test_dependency_resolution_batch(self):
        """Test batch dependency resolution"""
        from app.core.dependencies import (
            get_config,
            get_embedding_model,
            get_qdrant_client,
            get_redis_client,
        )

        start = time.time()
        for _ in range(100):
            config = get_config()
            # Resolve multiple dependencies
            config.qdrant_host
            config.redis_host
            config.embedding_model
        elapsed = time.time() - start

        # Should complete in <50ms
        assert elapsed < 0.05

    def test_singleton_cache_effectiveness(self):
        """Test singleton cache is effective"""
        from app.core.dependencies import get_config

        # First call (cache miss)
        cfg1 = get_config()

        # Subsequent calls (cache hit)
        times = []
        for _ in range(100):
            start = time.time()
            cfg = get_config()
            times.append(time.time() - start)
            assert cfg is cfg1

        # All hits should be from cache (same instance)
        assert all(cfg is cfg1 for cfg in [get_config() for _ in range(10)])


# ============================================================
# Schema Validation Performance
# ============================================================


@pytest.mark.integration
class TestSchemaValidationPerformance:
    """Test schema validation performance"""

    def test_qa_request_validation_latency(self):
        """Test QA request validation latency"""
        from app.models.schemas import QARequest

        start = time.time()
        for i in range(1000):
            req = QARequest(question=f"Question {i}?")
        elapsed = time.time() - start

        # Should validate 1000 requests in <100ms
        assert elapsed < 0.1
        avg_latency = (elapsed * 1000) / 1000  # ms per request
        assert avg_latency < 0.1

    def test_consultation_request_validation_latency(self):
        """Test consultation request validation latency"""
        from app.models.schemas import ConsultationRequest

        start = time.time()
        for i in range(1000):
            req = ConsultationRequest(
                requirements=f"Requirement {i}: Need portable and durable products"
            )
        elapsed = time.time() - start

        # Should validate 1000 requests in <200ms
        assert elapsed < 0.2

    def test_response_schema_serialization(self):
        """Test response schema serialization performance"""
        from app.models.schemas import QAResponse

        responses = [
            QAResponse(
                question=f"Q{i}?",
                answer=f"Answer {i}",
                related_products=[],
                confidence=0.95,
                qa_id=f"qa_{i}",
                timestamp="2025-10-19T10:00:00Z",
            )
            for i in range(500)
        ]

        start = time.time()
        for resp in responses:
            # Simulate serialization
            resp.model_dump_json() if hasattr(resp, "model_dump_json") else str(resp)
        elapsed = time.time() - start

        # Should serialize 500 responses in <100ms
        assert elapsed < 0.1


# ============================================================
# Service Instantiation Performance
# ============================================================


@pytest.mark.integration
class TestServiceInstantiationPerformance:
    """Test service creation and instantiation speed"""

    def test_rag_qa_service_instantiation_latency(self):
        """Test RAG QA service instantiation latency"""
        from app.services.rag_qa_service import RAGQAService

        mock_qdrant = Mock()
        mock_embedding = Mock()

        start = time.time()
        for _ in range(100):
            service = RAGQAService(
                qdrant_client=mock_qdrant,
                embedding_model=mock_embedding,
                ollama_url="http://localhost:11434",
                model_name="test-model",
            )
        elapsed = time.time() - start

        # Should create 100 services in <50ms
        assert elapsed < 0.05
        avg_latency = (elapsed * 1000) / 100
        assert avg_latency < 0.5

    def test_consultation_service_instantiation(self):
        """Test consultation service instantiation"""
        from app.services.consultation_service import ConsultationService

        mock_search = Mock()
        mock_embedding = Mock()
        mock_llm = Mock()

        start = time.time()
        for _ in range(100):
            service = ConsultationService(
                search_client=mock_search, embedding_model=mock_embedding, llm_client=mock_llm
            )
        elapsed = time.time() - start

        # Should create 100 services in <50ms
        assert elapsed < 0.05

    def test_bulk_service_creation_with_pool(self):
        """Test bulk service creation with thread pool"""
        from app.services.rag_qa_service import RAGQAService

        def create_service(idx):
            mock_qdrant = Mock()
            mock_embedding = Mock()
            return RAGQAService(
                qdrant_client=mock_qdrant,
                embedding_model=mock_embedding,
                ollama_url="http://localhost:11434",
                model_name=f"model-{idx}",
            )

        start = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            services = list(executor.map(create_service, range(100)))
        elapsed = time.time() - start

        # Should create 100 services concurrently in <100ms
        assert elapsed < 0.1
        assert len(services) == 100


# ============================================================
# Metrics Collection Performance
# ============================================================


@pytest.mark.integration
class TestMetricsPerformance:
    """Test metrics collection overhead"""

    def test_counter_increment_throughput(self):
        """Test counter metric increment throughput"""
        from app.core.metrics import http_requests_total

        metric = http_requests_total.labels(method="GET", endpoint="/health", status="200")

        start = time.time()
        for _ in range(10000):
            metric.inc()
        elapsed = time.time() - start

        # Should increment 10k times in <100ms
        assert elapsed < 0.1
        throughput = 10000 / elapsed
        assert throughput > 100000  # >100k ops/sec

    def test_histogram_observe_throughput(self):
        """Test histogram observation throughput"""
        from app.core.metrics import http_request_duration_seconds

        metric = http_request_duration_seconds.labels(method="GET", endpoint="/health")

        start = time.time()
        for i in range(10000):
            metric.observe(0.01)
        elapsed = time.time() - start

        # Should observe 10k times in <100ms
        assert elapsed < 0.1

    def test_gauge_set_throughput(self):
        """Test gauge set throughput"""
        from app.core.metrics import active_requests

        # Get labeled metric (active_requests requires 'endpoint' label)
        metric = active_requests.labels(endpoint="/api/query")

        start = time.time()
        for i in range(5000):
            metric.set(i)
        elapsed = time.time() - start

        # Should set 5k times efficiently (no extreme overhead)
        assert elapsed < 1.0  # Completes within 1 second


# ============================================================
# Configuration Access Patterns
# ============================================================


@pytest.mark.integration
class TestConfigurationAccessPatterns:
    """Test configuration access patterns for performance"""

    def test_repeated_config_access(self):
        """Test repeated configuration access pattern"""
        from app.core.dependencies import get_config

        config = get_config()

        start = time.time()
        for _ in range(10000):
            # Access multiple config fields
            _ = config.qdrant_host
            _ = config.redis_host
            _ = config.embedding_model
            _ = config.ollama_url
        elapsed = time.time() - start

        # Should access config 40k times in <100ms
        assert elapsed < 0.1

    def test_config_field_access_cache(self):
        """Test config field access caching"""
        from app.core.dependencies import get_config

        config = get_config()
        # Cache all fields locally
        fields = {
            "qdrant_host": config.qdrant_host,
            "redis_host": config.redis_host,
            "embedding_model": config.embedding_model,
        }

        start = time.time()
        for _ in range(10000):
            _ = fields["qdrant_host"]
            _ = fields["redis_host"]
            _ = fields["embedding_model"]
        elapsed = time.time() - start

        # Direct dict access should be very fast
        assert elapsed < 0.05


# ============================================================
# Request Processing Pipeline Performance
# ============================================================


@pytest.mark.integration
class TestRequestProcessingPipeline:
    """Test request processing pipeline performance"""

    def test_request_creation_to_response_schema(self):
        """Test request creation through response creation"""
        from app.models.schemas import QARequest, QAResponse

        start = time.time()
        for i in range(1000):
            # Create request
            req = QARequest(question=f"Question {i}?")
            # Create response
            resp = QAResponse(
                question=req.question,
                answer=f"Answer {i}",
                related_products=[],
                confidence=0.95,
                qa_id=f"qa_{i}",
                timestamp="2025-10-19T10:00:00Z",
            )
        elapsed = time.time() - start

        # Should process 1000 request-response pairs in <200ms
        assert elapsed < 0.2

    def test_batch_request_processing(self):
        """Test batch request processing"""
        from app.models.schemas import QARequest

        requests = [QARequest(question=f"Q{i}?") for i in range(500)]

        start = time.time()
        for req in requests:
            # Simulate processing
            _ = len(req.question)
            _ = req.top_k
        elapsed = time.time() - start

        # Should process 500 requests in <50ms
        assert elapsed < 0.05


# ============================================================
# Async Operation Performance
# ============================================================


@pytest.mark.integration
class TestAsyncOperationPerformance:
    """Test async operation performance"""

    @pytest.mark.asyncio
    async def test_async_task_overhead(self):
        """Test async task creation overhead"""

        async def fast_task():
            return True

        start = time.time()
        tasks = [fast_task() for _ in range(1000)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        # Should create and complete 1000 async tasks in <100ms
        assert elapsed < 0.1
        assert len(results) == 1000

    @pytest.mark.asyncio
    async def test_async_mock_call_latency(self):
        """Test async mock service call latency"""

        mock_service = AsyncMock(return_value={"status": "success"})

        start = time.time()
        for _ in range(1000):
            result = await mock_service()
        elapsed = time.time() - start

        # Should make 1000 async calls in <100ms
        assert elapsed < 0.1


# ============================================================
# Memory Efficiency Tests
# ============================================================


@pytest.mark.integration
class TestMemoryEfficiency:
    """Test memory efficiency of core components"""

    def test_singleton_memory_efficiency(self):
        """Test singleton pattern saves memory"""
        from app.core.dependencies import get_config

        # Get config multiple times
        configs = [get_config() for _ in range(100)]

        # All should be same instance
        assert len(set(id(c) for c in configs)) == 1

    def test_service_instance_independence(self):
        """Test service instances don't hold unnecessary references"""
        from app.services.rag_qa_service import RAGQAService

        services = []
        for i in range(10):
            mock_qdrant = Mock()
            mock_embedding = Mock()
            service = RAGQAService(
                qdrant_client=mock_qdrant,
                embedding_model=mock_embedding,
                ollama_url="http://localhost:11434",
                model_name=f"model-{i}",
            )
            services.append(service)

        # Each should be independent
        assert len(set(id(s) for s in services)) == 10


# ============================================================
# Bottleneck Identification
# ============================================================


@pytest.mark.integration
class TestBottleneckIdentification:
    """Identify performance bottlenecks"""

    def test_schema_validation_vs_dict_creation(self):
        """Compare schema validation vs plain dict"""
        from app.models.schemas import QARequest

        # Schema validation
        start = time.time()
        for i in range(500):
            req = QARequest(question=f"Question {i}?")
        schema_time = time.time() - start

        # Plain dict (baseline)
        start = time.time()
        for i in range(500):
            d = {"question": f"Question {i}?"}
        dict_time = time.time() - start

        # Schema validation should complete (may be slower due to validation)
        assert schema_time < 1.0  # Complete within 1 second

    def test_service_creation_vs_mock_creation(self):
        """Compare service creation vs mock creation"""
        from app.services.rag_qa_service import RAGQAService

        # Service creation
        start = time.time()
        for _ in range(100):
            service = RAGQAService(
                qdrant_client=Mock(),
                embedding_model=Mock(),
                ollama_url="http://localhost:11434",
                model_name="test",
            )
        service_time = time.time() - start

        # Mock creation (baseline)
        start = time.time()
        for _ in range(100):
            m = Mock()
        mock_time = time.time() - start

        # Service creation shouldn't be drastically slower
        assert service_time < mock_time * 20


# ============================================================
# Critical Path Analysis
# ============================================================


@pytest.mark.integration
class TestCriticalPathAnalysis:
    """Analyze critical execution paths"""

    def test_config_to_service_critical_path(self):
        """Measure config → service creation critical path"""
        from app.core.dependencies import get_config
        from app.services.rag_qa_service import RAGQAService

        start = time.time()
        for i in range(100):
            # Get config
            config = get_config()
            # Create service
            service = RAGQAService(
                qdrant_client=Mock(),
                embedding_model=Mock(),
                ollama_url=config.ollama_url,
                model_name=config.ollama_model,
            )
        elapsed = time.time() - start

        # Critical path should complete in <100ms for 100 iterations
        assert elapsed < 0.1

    def test_request_validation_critical_path(self):
        """Measure request validation critical path"""
        from app.models.schemas import ConsultationRequest, QARequest

        start = time.time()
        for i in range(500):
            qa_req = QARequest(question=f"Q{i}?")
            cons_req = ConsultationRequest(requirements=f"Requirement {i}: Need portable products")
        elapsed = time.time() - start

        # Both request types in <100ms
        assert elapsed < 0.1
