"""
Product Interaction Tracking Routes
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.conversation import ConversationManager
from app.conversation.states import ConversationContext

router = APIRouter(prefix="/api/v1", tags=["tracking"])

# Initialize conversation manager
conversation_manager = ConversationManager(
    ollama_url="http://localhost:11434", qdrant_url="http://localhost:6333"
)


@router.post("/product/{product_id}/view")
async def track_product_view(product_id: str, session_id: Optional[str] = None):
    """Track product view"""
    if not session_id:
        session_id = str(uuid.uuid4())

    context = conversation_manager.get_context(session_id)

    if not context:
        context = ConversationContext(session_id=session_id)
        conversation_manager.sessions[session_id] = context

    # Update viewed_products
    if product_id in context.viewed_products:
        context.viewed_products[product_id] += 1
    else:
        context.viewed_products[product_id] = 1

    context.last_interacted_product = product_id
    context.updated_at = datetime.now()

    return {
        "success": True,
        "product_id": product_id,
        "view_count": context.viewed_products[product_id],
    }


@router.post("/product/{product_id}/click")
async def track_product_click(product_id: str, session_id: Optional[str] = None):
    """Track product click"""
    if not session_id:
        session_id = str(uuid.uuid4())

    context = conversation_manager.get_context(session_id)

    if not context:
        context = ConversationContext(session_id=session_id)
        conversation_manager.sessions[session_id] = context

    # Add to clicked_products
    if product_id not in context.clicked_products:
        context.clicked_products.append(product_id)

    context.last_interacted_product = product_id
    context.updated_at = datetime.now()

    return {
        "success": True,
        "product_id": product_id,
        "total_clicked": len(context.clicked_products),
    }


@router.post("/product/{product_id}/sample")
async def track_sample_request(product_id: str, session_id: Optional[str] = None):
    """Track sample request"""
    if not session_id:
        session_id = str(uuid.uuid4())

    context = conversation_manager.get_context(session_id)

    if not context:
        context = ConversationContext(session_id=session_id)
        conversation_manager.sessions[session_id] = context

    # Add to sample_requested_products
    if product_id not in context.sample_requested_products:
        context.sample_requested_products.append(product_id)

    context.last_interacted_product = product_id
    context.updated_at = datetime.now()

    return {
        "success": True,
        "product_id": product_id,
        "total_sample_requests": len(context.sample_requested_products),
    }


@router.get("/session/{session_id}/interactions")
async def get_session_interactions(session_id: str):
    """Get all interactions for a session"""
    context = conversation_manager.get_context(session_id)

    if not context:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": session_id,
        "clicked_products": context.clicked_products,
        "sample_requested_products": context.sample_requested_products,
        "viewed_products": context.viewed_products,
        "last_interacted_product": context.last_interacted_product,
        "total_clicks": len(context.clicked_products),
        "total_samples": len(context.sample_requested_products),
        "total_views": sum(context.viewed_products.values()),
    }
