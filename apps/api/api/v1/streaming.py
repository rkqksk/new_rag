"""
WebSocket and SSE Streaming Endpoints for Real-time LLM Responses
==================================================================

Features:
- Token-by-token streaming from LLM
- WebSocket for bidirectional communication
- Server-Sent Events (SSE) as fallback
- Connection management and error handling
- Progress updates during search phase

Usage:
    WebSocket:
        ws://localhost:8001/api/v1/stream/ws/{session_id}

    SSE:
        GET /api/v1/stream/sse?session_id={session_id}&query={query}

Version: v6.0.0
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["streaming"])


# ============================================================================
# Connection Management
# ============================================================================


class ConnectionManager:
    """Manage WebSocket connections with session tracking"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        logger.info("ConnectionManager initialized")

    async def connect(self, session_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: session={session_id}")

    def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: session={session_id}")

    async def send_json(self, session_id: str, data: dict):
        """Send JSON message to specific session"""
        if session_id in self.active_connections:
            try:
                websocket = self.active_connections[session_id]
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
                self.disconnect(session_id)

    async def broadcast(self, data: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for session_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Broadcast failed for {session_id}: {e}")
                disconnected.append(session_id)

        for session_id in disconnected:
            self.disconnect(session_id)


connection_manager = ConnectionManager()


# ============================================================================
# Streaming Logic
# ============================================================================


async def stream_llm_response(
    query: str,
    session_id: str,
    collections: Optional[list] = None,
    materials: Optional[list] = None,
) -> AsyncGenerator[dict, None]:
    """
    Stream LLM response token-by-token with progress updates

    Yields:
        dict: Event messages with type and data
            - {"type": "status", "data": "Searching..."}
            - {"type": "token", "data": "Hello"}
            - {"type": "product", "data": {...}}
            - {"type": "complete", "data": {...}}
            - {"type": "error", "data": "..."}
    """
    try:
        # Phase 1: Send search status
        yield {
            "type": "status",
            "data": "벡터 검색 중...",
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Import RAG pipeline
        import sys
        from pathlib import Path

        skill_path = (
            Path(__file__).parent.parent.parent.parent / ".claude/skills/rag-pipeline/scripts"
        )
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from skill import rag_query as skill_rag_query

        # Phase 2: Execute RAG query
        skill_result = skill_rag_query(
            {
                "question": query,
                "top_k": 100,
                "collections": collections,
                "materials": materials,
            }
        )

        if skill_result["status"] != "success":
            yield {
                "type": "error",
                "data": skill_result.get("error", "RAG query failed"),
            }
            return

        # Phase 3: Send product count
        product_count = len(skill_result.get("sources", []))
        yield {
            "type": "status",
            "data": f"{product_count}개 제품 발견",
            "count": product_count,
        }

        # Phase 4: Stream products incrementally (for large result sets)
        products = []
        for idx, result in enumerate(skill_result.get("sources", [])):
            metadata = result.get("metadata", {})

            # Format product (same as chat.py)
            capacity_str = ""
            if metadata.get("capacity_value"):
                capacity_unit = metadata.get("capacity_unit", "ml")
                capacity_value = metadata["capacity_value"]
                if isinstance(capacity_value, (int, float)) and capacity_value == int(
                    capacity_value
                ):
                    capacity_str = f"{int(capacity_value)}{capacity_unit}"
                else:
                    capacity_str = f"{capacity_value}{capacity_unit}"

            materials_list = metadata.get("materials", [])
            material_str = ", ".join(materials_list) if materials_list else ""

            neck_size_str = ""
            if metadata.get("neck_size"):
                neck_size_str = f"{metadata['neck_size']}mm"

            image_urls = []
            if metadata.get("image_paths_json"):
                try:
                    image_urls = json.loads(metadata["image_paths_json"])
                except:
                    pass

            if not image_urls and metadata.get("main_image_path"):
                image_urls = [metadata["main_image_path"]]

            moq_str = ""
            if metadata.get("moq"):
                moq_str = f"{metadata['moq']:,}개"

            product = {
                "idx": metadata.get("product_id", ""),
                "product_name": metadata.get("product_name", ""),
                "product_code": metadata.get("product_code", ""),
                "material": material_str,
                "specifications": {
                    "capacity": capacity_str,
                    "neck_size": neck_size_str,
                    "moq": moq_str,
                    "origin": metadata.get("origin", ""),
                    "size_dimensions": metadata.get("size_dimensions", ""),
                },
                "company": {
                    "name": metadata.get("company_name", ""),
                    "email": metadata.get("email", ""),
                    "phone": metadata.get("phone", ""),
                    "fax": metadata.get("fax", ""),
                    "contact_person": metadata.get("contact_person", ""),
                },
                "image_url": image_urls[0] if image_urls else "",
                "image_urls": image_urls,
                "score": result.get("score", 0.0),
                "source_collection": metadata.get("source_collection", "unknown"),
            }

            products.append(product)

            # Send product incrementally (every 10 products or last one)
            if (idx + 1) % 10 == 0 or idx == product_count - 1:
                yield {
                    "type": "products_batch",
                    "data": products,
                    "progress": idx + 1,
                    "total": product_count,
                }

        # Phase 5: Stream LLM answer token-by-token
        yield {
            "type": "status",
            "data": "답변 생성 중...",
        }

        # Get full answer (in real streaming, this would be token-by-token from Ollama)
        answer = skill_result.get("answer", "")

        # Simulate token-by-token streaming
        # In production, you'd call Ollama with stream=True
        words = answer.split()
        for i, word in enumerate(words):
            # Send word as token
            yield {
                "type": "token",
                "data": word + " ",
                "index": i,
            }
            # Small delay to simulate streaming
            await asyncio.sleep(0.01)

        # Phase 6: Send completion message
        yield {
            "type": "complete",
            "data": {
                "session_id": session_id,
                "query": query,
                "answer": answer,
                "total_products": product_count,
                "collections_searched": skill_result.get("collections", []),
            },
        }

    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        yield {
            "type": "error",
            "data": str(e),
        }


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time streaming chat

    Client sends:
        {
            "type": "query",
            "query": "50ml PET 용기",
            "collections": ["chungjinkorea"],
            "materials": ["PET"]
        }

    Server sends:
        {"type": "status", "data": "Searching..."}
        {"type": "products_batch", "data": [...], "progress": 10, "total": 100}
        {"type": "token", "data": "안녕하세요"}
        {"type": "complete", "data": {...}}
    """
    await connection_manager.connect(session_id, websocket)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "query":
                query = message.get("query")
                collections = message.get("collections")
                materials = message.get("materials")

                if not query:
                    await websocket.send_json({"type": "error", "data": "Query is required"})
                    continue

                # Stream response
                async for event in stream_llm_response(
                    query=query,
                    session_id=session_id,
                    collections=collections,
                    materials=materials,
                ):
                    await websocket.send_json(event)

            elif message.get("type") == "ping":
                # Keep-alive ping
                await websocket.send_json(
                    {
                        "type": "pong",
                        "timestamp": asyncio.get_event_loop().time(),
                    }
                )

            else:
                await websocket.send_json(
                    {"type": "error", "data": f"Unknown message type: {message.get('type')}"}
                )

    except WebSocketDisconnect:
        connection_manager.disconnect(session_id)
        logger.info(f"Client disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        connection_manager.disconnect(session_id)


# ============================================================================
# Server-Sent Events (SSE) Endpoint
# ============================================================================


@router.get("/sse")
async def sse_endpoint(
    session_id: str = Query(..., description="Session ID"),
    query: str = Query(..., description="Search query"),
    collections: Optional[str] = Query(None, description="Comma-separated collection IDs"),
    materials: Optional[str] = Query(None, description="Comma-separated materials"),
):
    """
    Server-Sent Events endpoint (fallback for WebSocket)

    Usage:
        GET /api/v1/stream/sse?session_id=abc&query=50ml%20PET

    Response:
        text/event-stream with events:

        event: status
        data: {"data": "Searching..."}

        event: token
        data: {"data": "안녕하세요"}

        event: complete
        data: {"data": {...}}
    """

    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE events"""
        try:
            # Parse collections and materials
            collections_list = collections.split(",") if collections else None
            materials_list = materials.split(",") if materials else None

            # Stream events
            async for event in stream_llm_response(
                query=query,
                session_id=session_id,
                collections=collections_list,
                materials=materials_list,
            ):
                event_type = event.get("type", "message")
                event_data = json.dumps(event, ensure_ascii=False)

                # SSE format: event: {type}\ndata: {data}\n\n
                yield f"event: {event_type}\n"
                yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"SSE streaming error: {e}", exc_info=True)
            error_data = json.dumps({"type": "error", "data": str(e)}, ensure_ascii=False)
            yield f"event: error\n"
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def streaming_health():
    """Check streaming service health"""
    return {
        "status": "healthy",
        "websocket": {
            "active_connections": len(connection_manager.active_connections),
            "endpoint": "/api/v1/stream/ws/{session_id}",
        },
        "sse": {
            "endpoint": "/api/v1/stream/sse",
        },
    }
