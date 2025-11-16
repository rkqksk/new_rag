"""
Admin API Endpoints

Provides administrative endpoints for system monitoring and configuration.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from apps.api.services.unified_llm_service import get_unified_llm

router = APIRouter(prefix="/admin", tags=["admin"])


class RouterConfigUpdate(BaseModel):
    """Router configuration update"""

    simple_threshold: Optional[float] = None
    complex_threshold: Optional[float] = None


@router.get("/health")
async def get_health():
    """
    Get system health status

    Returns health status for all engines (NexaAI, Ollama)
    """
    llm = get_unified_llm()
    health = await llm.health_check()

    return health


@router.get("/stats")
async def get_stats():
    """
    Get system statistics

    Returns request counts, error rates, and engine availability
    """
    llm = get_unified_llm()
    stats = llm.get_stats()

    return stats


@router.get("/models")
async def get_models():
    """
    Get list of available models

    Returns list of models from NexaAI server
    """
    llm = get_unified_llm()

    if not llm.nexa_available:
        raise HTTPException(status_code=503, detail="NexaAI not available")

    try:
        models = llm.nexa.list_models()

        return [{"id": model} for model in models]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/router/config")
async def get_router_config():
    """
    Get current router configuration

    Returns thresholds and routing rules
    """
    llm = get_unified_llm()
    config = llm.router.get_stats()

    return config


@router.post("/router/config")
async def update_router_config(update: RouterConfigUpdate):
    """
    Update router configuration

    Update complexity thresholds for routing decisions
    """
    llm = get_unified_llm()

    if update.simple_threshold is not None:
        if not 0 <= update.simple_threshold <= 1:
            raise HTTPException(status_code=400, detail="simple_threshold must be between 0 and 1")
        llm.router.simple_threshold = update.simple_threshold

    if update.complex_threshold is not None:
        if not 0 <= update.complex_threshold <= 1:
            raise HTTPException(status_code=400, detail="complex_threshold must be between 0 and 1")
        llm.router.complex_threshold = update.complex_threshold

    return {
        "success": True,
        "config": {
            "simple_threshold": llm.router.simple_threshold,
            "complex_threshold": llm.router.complex_threshold,
        },
    }


@router.post("/reset-stats")
async def reset_stats():
    """
    Reset statistics counters

    Resets request counts and error counts to zero
    """
    llm = get_unified_llm()

    llm.stats["nexa_requests"] = 0
    llm.stats["ollama_requests"] = 0
    llm.stats["errors"] = 0

    return {"success": True, "message": "Statistics reset"}


@router.get("/engine/{engine}/status")
async def get_engine_status(engine: str):
    """
    Get detailed status for specific engine

    Args:
        engine: Engine name ('nexa' or 'ollama')

    Returns:
        Detailed engine status
    """
    llm = get_unified_llm()

    if engine == "nexa":
        if not llm.nexa_available:
            raise HTTPException(status_code=503, detail="NexaAI not available")

        health = await llm.nexa.health_check()

        return {
            "engine": "nexa",
            "available": llm.nexa_available,
            "healthy": health.get("healthy", False),
            "config": {
                "base_url": llm.nexa.config.base_url,
                "default_model": llm.nexa.config.default_text_model,
                "vision_model": llm.nexa.config.default_vision_model,
                "embedding_model": llm.nexa.config.default_embedding_model,
            },
        }

    elif engine == "ollama":
        if not llm.ollama_available:
            raise HTTPException(status_code=503, detail="Ollama not available")

        health = await llm.ollama.health_check()

        return {
            "engine": "ollama",
            "available": llm.ollama_available,
            "healthy": health.get("healthy", False),
            "config": {
                "base_url": llm.ollama.config.base_url,
                "default_model": llm.ollama.config.default_model,
            },
        }

    else:
        raise HTTPException(
            status_code=400, detail=f"Invalid engine: {engine}. Must be 'nexa' or 'ollama'"
        )
