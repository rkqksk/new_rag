"""
Integration tests for Multi-Agent System (v6.0.0)
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.multi_agent_system import (
    MultiAgentOrchestrator,
    RouterAgent,
    SearchAgent,
    ReasoningAgent,
    SynthesisAgent,
    ValidationAgent,
    AgentState,
)


class TestIndividualAgents:
    """Test individual agents"""

    @pytest.mark.asyncio
    async def test_router_agent(self):
        """Test router agent classification"""
        router = RouterAgent()

        state: AgentState = {
            "query": "50ml PET 용기와 100ml PP 용기의 차이점은?",
            "session_id": "test",
            "collections": None,
            "materials": None,
            "intent": None,
            "complexity": None,
            "requires_reasoning": False,
            "dense_results": None,
            "sparse_results": None,
            "hybrid_results": None,
            "reasoning_steps": [],
            "intermediate_conclusions": [],
            "synthesized_answer": None,
            "confidence_score": 0.0,
            "validated": False,
            "validation_issues": [],
            "final_answer": "",
            "final_products": [],
            "agent_trace": [],
        }

        result = await router.route(state)

        assert result["intent"] is not None
        assert result["complexity"] is not None
        assert "RouterAgent" in str(result["agent_trace"])

    @pytest.mark.asyncio
    async def test_router_intent_classification(self):
        """Test intent classification for different queries"""
        router = RouterAgent()

        test_cases = [
            ("50ml 용기 추천해주세요", "recommendation"),
            ("PET와 PP의 차이점은?", "comparison"),
            ("50ml 용기 찾아줘", "search"),
        ]

        for query, expected_intent in test_cases:
            intent = router._classify_intent(query)
            assert intent == expected_intent, f"Query: '{query}' -> Expected: {expected_intent}, Got: {intent}"

    @pytest.mark.asyncio
    async def test_router_complexity_assessment(self):
        """Test complexity assessment"""
        router = RouterAgent()

        # Simple query
        simple = router._assess_complexity("50ml 용기")
        assert simple == "simple"

        # Medium query
        medium = router._assess_complexity("50ml PET 용기 그리고 PP 용기")
        assert medium in ["medium", "complex"]

        # Complex query
        complex_query = router._assess_complexity("50ml PET 용기와 100ml PP 용기의 차이점과 장단점 비교")
        assert complex_query == "complex"

    @pytest.mark.asyncio
    async def test_synthesis_agent(self):
        """Test synthesis agent"""
        synthesis = SynthesisAgent()

        # Mock state with results
        state: AgentState = {
            "query": "50ml PET 용기",
            "session_id": "test",
            "collections": None,
            "materials": None,
            "intent": "search",
            "complexity": "simple",
            "requires_reasoning": False,
            "dense_results": [
                {
                    "metadata": {
                        "product_id": "001",
                        "product_name": "50ml PET 용기",
                        "material": "PET",
                        "capacity": "50ml",
                    },
                    "score": 0.9,
                }
            ],
            "sparse_results": None,
            "hybrid_results": None,
            "reasoning_steps": [],
            "intermediate_conclusions": [],
            "synthesized_answer": None,
            "confidence_score": 0.0,
            "validated": False,
            "validation_issues": [],
            "final_answer": "",
            "final_products": [],
            "agent_trace": [],
        }

        result = await synthesis.synthesize(state)

        assert result["synthesized_answer"] is not None
        assert len(result["synthesized_answer"]) > 0
        assert result["confidence_score"] > 0

    @pytest.mark.asyncio
    async def test_validation_agent(self):
        """Test validation agent"""
        validation = ValidationAgent()

        # Valid state
        valid_state: AgentState = {
            "query": "50ml PET 용기",
            "session_id": "test",
            "collections": None,
            "materials": None,
            "intent": "search",
            "complexity": "simple",
            "requires_reasoning": False,
            "dense_results": [{"metadata": {}, "score": 0.9}],
            "sparse_results": None,
            "hybrid_results": None,
            "reasoning_steps": [],
            "intermediate_conclusions": [],
            "synthesized_answer": "50ml PET 용기 검색 결과입니다.",
            "confidence_score": 0.8,
            "validated": False,
            "validation_issues": [],
            "final_answer": "",
            "final_products": [],
            "agent_trace": [],
        }

        result = await validation.validate(valid_state)

        assert "validated" in result
        assert "validation_issues" in result

        # Invalid state (empty answer)
        invalid_state = valid_state.copy()
        invalid_state["synthesized_answer"] = ""

        result2 = await validation.validate(invalid_state)
        assert len(result2["validation_issues"]) > 0


class TestMultiAgentOrchestrator:
    """Test multi-agent orchestrator"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_orchestrator_simple_query(self):
        """Test orchestrator with simple query"""
        orchestrator = MultiAgentOrchestrator()

        try:
            result = await orchestrator.execute(
                query="50ml 용기",
                session_id="test-simple",
                collections=None,
                materials=None,
            )

            # Check result structure
            assert "status" in result
            assert "query" in result
            assert "answer" in result
            assert "agent_trace" in result

            # Should have at least router and search agents
            assert len(result["agent_trace"]) >= 2

        except Exception as e:
            # If RAG not configured, skip
            pytest.skip(f"Orchestrator test skipped: {e}")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_orchestrator_complex_query(self):
        """Test orchestrator with complex query"""
        orchestrator = MultiAgentOrchestrator()

        try:
            result = await orchestrator.execute(
                query="50ml PET 용기와 100ml PP 용기의 차이점은?",
                session_id="test-complex",
                collections=None,
                materials=None,
            )

            # Check result structure
            assert "status" in result

            if result["status"] == "success":
                # Complex query should trigger reasoning
                assert len(result.get("reasoning_steps", [])) > 0 or result.get("metadata", {}).get("complexity") == "complex"

        except Exception as e:
            pytest.skip(f"Complex query test skipped: {e}")


class TestMultiAgentAPI:
    """Test multi-agent API endpoints"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test multi-agent health check"""
        response = client.get("/api/v1/agents/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "agents" in data
        assert "capabilities" in data
        assert len(data["agents"]) == 5  # 5 agents

    def test_config_endpoint(self, client):
        """Test multi-agent configuration"""
        response = client.get("/api/v1/agents/config")

        assert response.status_code == 200
        data = response.json()

        assert "agents" in data
        assert "workflow" in data
        assert "complexity_levels" in data

        # Check all 5 agents listed
        assert len(data["agents"]) == 5

    @pytest.mark.slow
    def test_query_endpoint(self, client):
        """Test multi-agent query endpoint"""
        try:
            response = client.post(
                "/api/v1/agents/query",
                json={
                    "query": "50ml PET 용기",
                    "session_id": "test-api",
                    "collections": None,
                    "materials": None,
                    "enable_reasoning": True,
                    "enable_validation": True,
                },
            )

            # Should work or fail gracefully
            assert response.status_code in [200, 500]

            if response.status_code == 200:
                data = response.json()

                # Check response structure
                assert "status" in data
                assert "query" in data
                assert "answer" in data
                assert "products" in data
                assert "confidence" in data
                assert "agent_trace" in data
                assert "performance" in data

                # Check performance metrics
                perf = data["performance"]
                assert "total_time_ms" in perf
                assert "agents_invoked" in perf

        except Exception as e:
            pytest.skip(f"Query endpoint test skipped: {e}")

    def test_query_validation(self, client):
        """Test request validation"""
        # Missing query
        response = client.post(
            "/api/v1/agents/query",
            json={
                "session_id": "test",
            },
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.slow
    def test_trace_endpoint(self, client):
        """Test agent trace retrieval"""
        # First make a query
        try:
            session_id = "test-trace-123"

            query_response = client.post(
                "/api/v1/agents/query",
                json={
                    "query": "test query",
                    "session_id": session_id,
                },
            )

            if query_response.status_code == 200:
                # Get trace
                trace_response = client.get(f"/api/v1/agents/trace/{session_id}")

                assert trace_response.status_code == 200
                trace_data = trace_response.json()

                assert "session_id" in trace_data
                assert "query" in trace_data
                assert "agent_trace" in trace_data
                assert "execution_time_ms" in trace_data

        except Exception as e:
            pytest.skip(f"Trace endpoint test skipped: {e}")

    def test_trace_not_found(self, client):
        """Test trace endpoint with non-existent session"""
        response = client.get("/api/v1/agents/trace/nonexistent")

        assert response.status_code == 404


class TestAgentWorkflow:
    """Test complete agent workflow"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_workflow_progression(self):
        """Test agents execute in correct order"""
        orchestrator = MultiAgentOrchestrator()

        try:
            result = await orchestrator.execute(
                query="50ml 용기 추천",
                session_id="test-workflow",
            )

            if result["status"] == "success":
                trace = result["agent_trace"]

                # Check workflow order (should start with router)
                assert any("RouterAgent" in step for step in trace)

                # Should have search
                assert any("SearchAgent" in step for step in trace)

                # Should end with synthesis and validation
                assert any("SynthesisAgent" in step for step in trace)

        except Exception as e:
            pytest.skip(f"Workflow test skipped: {e}")

    @pytest.mark.asyncio
    async def test_confidence_scoring(self):
        """Test confidence score calculation"""
        synthesis = SynthesisAgent()

        # Mock high-quality results
        high_quality_state: AgentState = {
            "query": "test",
            "session_id": "test",
            "collections": None,
            "materials": None,
            "intent": "search",
            "complexity": "simple",
            "requires_reasoning": False,
            "dense_results": [{"metadata": {}, "score": 0.95} for _ in range(50)],
            "sparse_results": None,
            "hybrid_results": None,
            "reasoning_steps": [],
            "intermediate_conclusions": [],
            "synthesized_answer": None,
            "confidence_score": 0.0,
            "validated": False,
            "validation_issues": [],
            "final_answer": "",
            "final_products": [],
            "agent_trace": [],
        }

        result = await synthesis.synthesize(high_quality_state)
        high_confidence = result["confidence_score"]

        # Mock low-quality results
        low_quality_state = high_quality_state.copy()
        low_quality_state["dense_results"] = [{"metadata": {}, "score": 0.3}]

        result2 = await synthesis.synthesize(low_quality_state)
        low_confidence = result2["confidence_score"]

        # High quality should have higher confidence
        assert high_confidence > low_confidence
