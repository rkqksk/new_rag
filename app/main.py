"""
RAG Enterprise API - Main Application
High-end, enterprise-grade backend system with comprehensive debugging
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import image_processing, excel, health, async_qa
from app.api.v1 import admin, analytics, debug, hybrid, personalization, search, streaming
from app.api import workflow_routes, consultation, dashboard_routes, ingestion_routes, query_routes
from app.routes import products, qa, inquiries, tracking
from src.api.v1 import saas
from app.core.config import settings
from app.core.exceptions import RAGEnterpriseException
from app.core.logging import get_logger, setup_logging
from app.middleware.performance_timing import PerformanceTimingMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_tracing import RequestTracingMiddleware

# Setup logging
logger = setup_logging(settings.environment)
app_logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
    description="Enterprise-grade RAG system with multi-modal search, personalization, and analytics",
)

# ============================================================================
# Middleware Stack (order matters!)
# ============================================================================

# 1. CORS middleware (first to handle preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request tracing (correlation IDs)
app.add_middleware(RequestTracingMiddleware)

# 3. Performance timing
app.add_middleware(PerformanceTimingMiddleware)

# 4. Request/response logging (if debug enabled)
if settings.debug_config.enabled:
    app.add_middleware(RequestLoggingMiddleware)
    app_logger.info("🔍 Debug mode enabled - Request logging active")

# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(RAGEnterpriseException)
async def rag_exception_handler(request: Request, exc: RAGEnterpriseException):
    """Handle custom RAG exceptions with context"""
    app_logger.error(
        f"RAG Exception: {exc.message}",
        extra={"exception": exc.to_dict(), "path": request.url.path},
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "context": exc.context if settings.debug_config.enabled else None,
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    app_logger.error(
        f"Unexpected error: {str(exc)}",
        extra={"exception_type": exc.__class__.__name__, "path": request.url.path},
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": (
                str(exc) if settings.debug_config.enabled else "An unexpected error occurred"
            ),
        },
    )


# ============================================================================
# Include Routers
# ============================================================================

# Core API routes
app.include_router(search.router, prefix=f"{settings.api_prefix}/search", tags=["search"])

app.include_router(
    personalization.router,
    prefix=f"{settings.api_prefix}/personalization",
    tags=["personalization"],
)

app.include_router(analytics.router, prefix=f"{settings.api_prefix}/analytics", tags=["analytics"])

# Streaming routes (WebSocket + SSE for real-time LLM responses) ⭐ NEW v6.0.0
app.include_router(streaming.router, prefix=settings.api_prefix, tags=["streaming"])
app_logger.info("🔄 Streaming endpoints enabled (WebSocket + SSE)")

# Hybrid Search routes (Dense + Sparse + Re-ranking) ⭐ NEW v6.0.0
app.include_router(hybrid.router, prefix=settings.api_prefix, tags=["hybrid-search"])
app_logger.info("🔍 Hybrid search enabled (Dense + BM25 + Cross-Encoder)")

# Image processing routes (watermark removal, OCR preprocessing)
app.include_router(image_processing.router)
app_logger.info("🎨 Image processing endpoints enabled at /api/v1/image")

# Debug routes (only if debug enabled)
if settings.debug_config.enabled:
    app.include_router(debug.router, prefix=f"{settings.api_prefix}/debug", tags=["debug"])
    app_logger.info("🔧 Debug endpoints enabled at /api/v1/debug")

# Admin routes (NexaAI integration)
app.include_router(admin.router, prefix=settings.api_prefix, tags=["admin"])
app_logger.info("⚙️  Admin endpoints enabled at /api/v1/admin")

# ============================================================================
# SaaS Platform - Multi-Tenancy, Authentication, Billing
# ============================================================================
app.include_router(
    saas.router,
    prefix=f"{settings.api_prefix}/saas",
    tags=["SaaS Platform"]
)
app_logger.info("🏢 SaaS Platform endpoints enabled at /api/v1/saas")

# ============================================================================
# Product Management - Products, Q&A, Inquiries
# ============================================================================
# Products API (already has /api/v1 prefix in router)
app.include_router(products.router)
app_logger.info("📦 Product endpoints enabled at /api/v1/products")

# Q&A API (already has /api/v1 prefix in router)
app.include_router(qa.router)
app_logger.info("❓ Q&A endpoints enabled at /api/v1/qa")

# Async Q&A (has /api/v2 prefix in router)
app.include_router(async_qa.router)
app_logger.info("⚡ Async Q&A endpoints enabled at /api/v2/async-qa")

# Inquiries API (already has /api/v1 prefix in router)
app.include_router(inquiries.router)
app_logger.info("💬 Inquiries endpoints enabled at /api/v1/inquiries")

# ============================================================================
# Workflow Orchestration
# ============================================================================
# Workflow API (already has /api/v1/workflow prefix in router)
app.include_router(workflow_routes.router)
app_logger.info("🔄 Workflow endpoints enabled at /api/v1/workflow")

# ============================================================================
# Data Management - Excel, Ingestion
# ============================================================================
# Excel Processing (already has /api/v1/admin/excel prefix in router)
app.include_router(excel.router)
app_logger.info("📊 Excel processing endpoints enabled at /api/v1/admin/excel")

# Data Ingestion (already has /api/v1/ingestion prefix in router)
app.include_router(ingestion_routes.router)
app_logger.info("📥 Data ingestion endpoints enabled at /api/v1/ingestion")

# ============================================================================
# Dashboard & Monitoring
# ============================================================================
# Dashboard routes
app.include_router(dashboard_routes.router, prefix=settings.api_prefix)
app_logger.info("📈 Dashboard endpoints enabled at /api/v1/dashboard")

# Consultation routes (already has /consultation prefix)
app.include_router(consultation.router, prefix=settings.api_prefix)
app_logger.info("🤝 Consultation endpoints enabled at /api/v1/consultation")

# ============================================================================
# System Health & Tracking
# ============================================================================
# Health monitoring (comprehensive health checks beyond basic liveness/readiness)
app.include_router(health.router)
app_logger.info("❤️  Health monitoring endpoints enabled")

# Tracking system (already has /api/v1 prefix in router)
app.include_router(tracking.router)
app_logger.info("📍 Tracking endpoints enabled at /api/v1/tracking")

# Query management (already has /api/v1/query prefix in router)
app.include_router(query_routes.router)
app_logger.info("🔍 Query management endpoints enabled at /api/v1/query")

# ============================================================================
# Health Check Endpoints
# ============================================================================


@app.get("/health/live")
async def liveness():
    """Liveness probe - is the app running?"""
    return {"status": "alive", "version": "1.0.0"}


@app.get("/health/ready")
async def readiness():
    """Readiness probe - is the app ready to serve traffic?"""
    from app.core.health import check_all_services

    services_status = await check_all_services()
    all_healthy = all(service["status"] == "healthy" for service in services_status.values())

    return {
        "status": "ready" if all_healthy else "degraded",
        "debug_enabled": settings.debug_config.enabled,
        "services": services_status
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "message": "RAG Enterprise API",
        "version": "1.0.0",
        "environment": settings.environment,
        "debug_mode": settings.debug_config.enabled,
        "docs": f"{settings.api_prefix}/docs",
        "features": [
            "Multi-modal search (text + image + shape)",
            "Personalized recommendations",
            "Real-time analytics",
            "Cross-encoder re-ranking",
            "Intelligent query routing",
            "Session-based profiling",
        ],
    }


# ============================================================================
# Startup/Shutdown Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    app_logger.info("🚀 RAG Enterprise API starting...")
    app_logger.info(f"Environment: {settings.environment}")
    app_logger.info(f"Debug Mode: {settings.debug_config.enabled}")
    app_logger.info(f"API Prefix: {settings.api_prefix}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    app_logger.info("👋 RAG Enterprise API shutting down...")


# ============================================================================
# Run Application
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info" if not settings.debug_config.enabled else "debug",
    )
