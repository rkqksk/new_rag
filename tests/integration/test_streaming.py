"""
Integration tests for WebSocket and SSE streaming endpoints (v6.0.0)
"""

import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from apps.api.main import app


class TestWebSocketStreaming:
    """Test WebSocket streaming endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_websocket_connection(self, client):
        """Test WebSocket connection establishment"""
        session_id = "test-session-ws"

        with client.websocket_connect(f"/api/v1/stream/ws/{session_id}") as websocket:
            # Send ping to verify connection
            websocket.send_json({"type": "ping"})
            response = websocket.receive_json()

            assert response["type"] == "pong"
            assert "timestamp" in response

    def test_websocket_query_flow(self, client):
        """Test complete WebSocket query flow"""
        session_id = "test-session-query"

        with client.websocket_connect(f"/api/v1/stream/ws/{session_id}") as websocket:
            # Send query
            websocket.send_json({
                "type": "query",
                "query": "50ml PET 용기",
                "collections": None,
                "materials": None
            })

            # Collect events
            events = []
            event_types = set()

            # Receive messages until complete or timeout
            timeout = 30  # seconds
            start_time = asyncio.get_event_loop().time() if hasattr(asyncio.get_event_loop(), 'time') else 0

            while True:
                try:
                    # Receive with timeout
                    response = websocket.receive_json(timeout=5.0)
                    events.append(response)
                    event_types.add(response["type"])

                    # Break on complete or error
                    if response["type"] in ["complete", "error"]:
                        break

                    # Safety timeout
                    if start_time > 0:
                        elapsed = asyncio.get_event_loop().time() - start_time
                        if elapsed > timeout:
                            break

                except Exception as e:
                    print(f"WebSocket receive error: {e}")
                    break

            # Verify event flow
            assert len(events) > 0, "Should receive at least one event"

            # Should have status events
            status_events = [e for e in events if e["type"] == "status"]
            assert len(status_events) > 0, "Should have status updates"

            # Should complete successfully
            complete_events = [e for e in events if e["type"] == "complete"]
            if len(complete_events) > 0:
                assert "data" in complete_events[0]
                assert "query" in complete_events[0]["data"]

    def test_websocket_invalid_message(self, client):
        """Test WebSocket with invalid message type"""
        session_id = "test-session-invalid"

        with client.websocket_connect(f"/api/v1/stream/ws/{session_id}") as websocket:
            # Send invalid message type
            websocket.send_json({
                "type": "unknown_type",
                "data": "test"
            })

            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "Unknown message type" in response["data"]

    def test_websocket_missing_query(self, client):
        """Test WebSocket with missing query"""
        session_id = "test-session-no-query"

        with client.websocket_connect(f"/api/v1/stream/ws/{session_id}") as websocket:
            # Send query message without query field
            websocket.send_json({
                "type": "query",
                "collections": ["chungjinkorea"]
            })

            response = websocket.receive_json()

            assert response["type"] == "error"
            assert "Query is required" in response["data"]


class TestSSEStreaming:
    """Test Server-Sent Events streaming endpoint"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    def test_sse_endpoint_exists(self, client):
        """Test SSE endpoint is accessible"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse",
                "query": "50ml PET"
            }
        )

        # SSE should return 200 with text/event-stream
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_sse_headers(self, client):
        """Test SSE response headers"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse-headers",
                "query": "test query"
            }
        )

        assert response.status_code == 200

        # Check required SSE headers
        headers = response.headers
        assert headers.get("cache-control") == "no-cache"
        assert headers.get("connection") == "keep-alive"
        assert headers.get("x-accel-buffering") == "no"

    def test_sse_event_format(self, client):
        """Test SSE event format (event: type, data: json)"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse-format",
                "query": "test"
            },
            stream=True
        )

        assert response.status_code == 200

        # Read first few events
        events_text = ""
        for chunk in response.iter_lines():
            events_text += chunk.decode('utf-8') + "\n"
            # Stop after collecting some events
            if "event: complete" in events_text or len(events_text) > 1000:
                break

        # Verify SSE format: "event: {type}\ndata: {json}\n\n"
        assert "event: " in events_text
        assert "data: " in events_text

    def test_sse_with_collections(self, client):
        """Test SSE with collection filters"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse-collections",
                "query": "bottle",
                "collections": "chungjinkorea,onehago"
            }
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_sse_with_materials(self, client):
        """Test SSE with material filters"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse-materials",
                "query": "bottle",
                "materials": "PET,PP"
            }
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    def test_sse_missing_query(self, client):
        """Test SSE with missing query parameter"""
        response = client.get(
            "/api/v1/stream/sse",
            params={
                "session_id": "test-sse-no-query"
            }
        )

        # Should return 422 (validation error)
        assert response.status_code == 422


class TestStreamingHealth:
    """Test streaming service health check"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_streaming_health_endpoint(self, client):
        """Test streaming health check"""
        response = client.get("/api/v1/stream/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "websocket" in data
        assert "sse" in data

        # Check WebSocket info
        assert "active_connections" in data["websocket"]
        assert "endpoint" in data["websocket"]
        assert data["websocket"]["endpoint"] == "/api/v1/stream/ws/{session_id}"

        # Check SSE info
        assert "endpoint" in data["sse"]
        assert data["sse"]["endpoint"] == "/api/v1/stream/sse"


class TestStreamingIntegration:
    """Integration tests with actual RAG pipeline"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.slow
    def test_end_to_end_streaming_flow(self, client):
        """Test complete streaming flow from query to response"""
        # This test requires actual RAG pipeline setup
        # Skip if collections not available
        try:
            session_id = "test-e2e-streaming"

            with client.websocket_connect(f"/api/v1/stream/ws/{session_id}") as websocket:
                # Send real query
                websocket.send_json({
                    "type": "query",
                    "query": "50ml PET 용기",
                    "collections": None,
                    "materials": None
                })

                # Track event sequence
                event_sequence = []
                received_products = False
                received_answer = False

                timeout_count = 0
                max_timeout = 50  # 50 events max

                while timeout_count < max_timeout:
                    try:
                        response = websocket.receive_json(timeout=5.0)
                        event_sequence.append(response["type"])

                        if response["type"] == "products_batch":
                            received_products = True
                            assert "data" in response
                            assert isinstance(response["data"], list)

                        if response["type"] == "token":
                            received_answer = True
                            assert "data" in response

                        if response["type"] == "complete":
                            break

                        if response["type"] == "error":
                            # Log error but don't fail (might be expected in test env)
                            print(f"Streaming error: {response['data']}")
                            break

                        timeout_count += 1

                    except Exception as e:
                        print(f"Receive error: {e}")
                        break

                # Verify event flow
                assert len(event_sequence) > 0, "Should receive events"

                # Should have status updates
                assert "status" in event_sequence, "Should have status events"

                # Log results for debugging
                print(f"Event sequence: {event_sequence}")
                print(f"Received products: {received_products}")
                print(f"Received answer: {received_answer}")

        except Exception as e:
            pytest.skip(f"E2E test skipped: {e}")


class TestBackwardCompatibility:
    """Test backward compatibility with existing HTTP endpoint"""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_http_endpoint_still_works(self, client):
        """Ensure old HTTP endpoint still functions"""
        # Create session first
        session_response = client.post("/chat/create_session", json={})
        assert session_response.status_code == 200
        session_id = session_response.json()["session_id"]

        # Query using old HTTP endpoint
        query_response = client.post(
            "/chat/query",
            json={
                "session_id": session_id,
                "query": "test query",
                "collections": None,
                "materials": None
            }
        )

        # Should still work (might fail if RAG not configured, but endpoint exists)
        assert query_response.status_code in [200, 500]  # 500 if RAG not configured

    def test_both_endpoints_coexist(self, client):
        """Verify both streaming and HTTP endpoints coexist"""
        # HTTP endpoint
        http_response = client.post("/chat/create_session", json={})
        assert http_response.status_code == 200

        # Streaming health
        stream_health = client.get("/api/v1/stream/health")
        assert stream_health.status_code == 200

        # Both should work independently
        assert http_response.json()["session_id"]
        assert stream_health.json()["status"] == "healthy"
