"""
RAG Enterprise API - Main Application
High-end, enterprise-grade backend system with comprehensive debugging
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import image_processing, excel, health, async_qa
from app.api.v1 import admin, analytics, analytics_realtime, debug, hybrid, multi_agent, personalization, rag_advanced, search, streaming
from app.api import workflow_routes, consultation, dashboard_routes, ingestion_routes, query_routes
from app.routes import products, qa, inquiries, tracking
from src.api.v1 import saas
from src.api.routes import manufacturing  # v7.1.0 Advanced Manufacturing
from src.api.routes.auth import create_auth_router  # v8.0.0 JWT Authentication

# v8.5.0 Phase 9 - Advanced Infrastructure
from src.api.routes import metrics, recommendations, search_ranking, websocket
from src.middleware.rate_limiting import RateLimitMiddleware, RateLimitTier, RateLimitAlgorithm
from src.middleware.error_tracking import ErrorTrackingMiddleware, RequestContextMiddleware, AnalyticsMiddleware

from app.core.config import settings
from app.core.exceptions import RAGEnterpriseException
from app.core.logging import get_logger, setup_logging
from app.middleware.performance_timing import PerformanceTimingMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.request_tracing import RequestTracingMiddleware

# v7.0.0+ Realtime Backend (Convex-like functionality)
try:
    from app.realtime.socketio_server import RealtimeServer, get_realtime_server
    from app.realtime.postgres_notify import get_notify_manager
    from app.realtime.redis_pubsub import get_pubsub_manager
    REALTIME_AVAILABLE = True
except ImportError as e:
    REALTIME_AVAILABLE = False
    app_logger.warning(f"Realtime backend not available: {e}")

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

# Mount Socket.IO realtime server (v7.0.0+)
if REALTIME_AVAILABLE:
    try:
        realtime_server = get_realtime_server()
        # Mount Socket.IO as a sub-application
        import socketio
        socketio_asgi = socketio.ASGIApp(realtime_server.sio, other_asgi_app=app)
        app.mount('/socket.io', socketio_asgi)
        app_logger.info("⚡ Socket.IO mounted at /socket.io (Convex-like realtime API)")
    except Exception as e:
        app_logger.warning(f"Could not mount Socket.IO: {e}")

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

# 5. Analytics middleware (v8.5.0) - Track all requests
app.add_middleware(AnalyticsMiddleware, track_all_requests=True)

# 6. Error tracking middleware (v8.5.0) - Automatic error capture
app.add_middleware(ErrorTrackingMiddleware, track_performance=True, track_errors_only=False)

# 7. Request context middleware (v8.5.0) - Add breadcrumbs
app.add_middleware(RequestContextMiddleware)

# 8. Rate limiting middleware (v8.5.0) - Protect against abuse
app.add_middleware(
    RateLimitMiddleware,
    default_tier=RateLimitTier.FREE,
    algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
    identifier_strategy="user_id",  # Use user_id if authenticated, fall back to IP
    excluded_paths=["/health", "/docs", "/openapi.json", "/redoc", "/socket.io"]
)

app_logger.info("🛡️  Phase 9 middleware enabled (Analytics, Error Tracking, Rate Limiting)")

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

# Real-time Analytics routes (ClickHouse + Kafka pipeline) ⭐ NEW v6.0.0
app.include_router(analytics_realtime.router, prefix=f"{settings.api_prefix}/analytics/realtime", tags=["analytics-realtime"])
app_logger.info("📊 Real-time analytics enabled (ClickHouse + Kafka)")

# Streaming routes (WebSocket + SSE for real-time LLM responses) ⭐ NEW v6.0.0
app.include_router(streaming.router, prefix=settings.api_prefix, tags=["streaming"])
app_logger.info("🔄 Streaming endpoints enabled (WebSocket + SSE)")

# Hybrid Search routes (Dense + Sparse + Re-ranking) ⭐ NEW v6.0.0
app.include_router(hybrid.router, prefix=settings.api_prefix, tags=["hybrid-search"])
app_logger.info("🔍 Hybrid search enabled (Dense + BM25 + Cross-Encoder)")

# Multi-Agent System routes (Orchestrated agent workflow) ⭐ NEW v6.0.0
app.include_router(multi_agent.router, prefix=settings.api_prefix, tags=["multi-agent"])
app_logger.info("🤖 Multi-agent system enabled (Router + Search + Reasoning + Synthesis + Validation)")

# GraphQL API (Flexible type-safe querying) ⭐ NEW v6.0.0
try:
    from app.graphql import create_graphql_router
    graphql_router = create_graphql_router()
    app.include_router(graphql_router, prefix=settings.api_prefix)
    app_logger.info("🔷 GraphQL API enabled at /api/v1/graphql")
except ImportError as e:
    app_logger.warning(f"GraphQL not available: {e}")

# Advanced RAG routes (Query optimization + Conversational memory) ⭐ NEW v6.0.0
app.include_router(rag_advanced.router, prefix=f"{settings.api_prefix}/rag", tags=["advanced-rag"])
app_logger.info("🧠 Advanced RAG enabled (Query optimization + Citations + Conversational memory)")

# Manufacturing routes (LORA + UR10e robot integration) ⭐ NEW v7.1.0
app.include_router(manufacturing.router, prefix=settings.api_prefix, tags=["manufacturing"])
app_logger.info("🏭 Advanced Manufacturing enabled (LORA fine-tuning + UR10e collaborative robot)")

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
# Authentication - JWT-based user authentication (v8.0.0)
# ============================================================================
auth_router = create_auth_router()
app.include_router(
    auth_router,
    prefix=settings.api_prefix,
    tags=["Authentication"]
)
app_logger.info("🔐 JWT Authentication enabled at /api/v1/auth")

# ============================================================================
# Phase 9 - Advanced Infrastructure (v8.5.0)
# ============================================================================
# Metrics & Analytics API
app.include_router(
    metrics.router,
    prefix=settings.api_prefix,
    tags=["Metrics"]
)
app_logger.info("📊 Metrics API enabled at /api/v1/metrics")

# Recommendations API
app.include_router(
    recommendations.router,
    prefix=settings.api_prefix,
    tags=["Recommendations"]
)
app_logger.info("🎯 Recommendations API enabled at /api/v1/recommendations")

# Search Ranking API
app.include_router(
    search_ranking.router,
    prefix=settings.api_prefix,
    tags=["Search Ranking"]
)
app_logger.info("🏆 Search Ranking API enabled at /api/v1/search")

# WebSocket Notifications API
app.include_router(
    websocket.router,
    prefix=settings.api_prefix,
    tags=["WebSocket"]
)
app_logger.info("⚡ WebSocket Notifications API enabled at /api/v1/ws")

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

    # Initialize realtime backend (v7.0.0+)
    if REALTIME_AVAILABLE:
        try:
            app_logger.info("⚡ Initializing realtime backend (Convex-like)...")

            # 1. Get realtime server instance
            realtime = get_realtime_server()

            # 2. Register query handlers (example)
            @realtime.query("products")
            async def get_products(params):
                """Get products by material"""
                from app.repositories.product_repository import ProductRepository
                repo = ProductRepository()
                material = params.get("material")
                if material:
                    products = await repo.get_by_material(material)
                else:
                    products = await repo.get_all(limit=100)
                return [p.dict() for p in products]

            @realtime.query("search_results")
            async def get_search_results(params):
                """Get search results"""
                from app.services.search_service import SearchService
                service = SearchService()
                query = params.get("query", "")
                top_k = params.get("top_k", 5)
                results = await service.search(query, top_k)
                return results

            # 3. Get PostgreSQL notify manager
            notify_manager = get_notify_manager()

            # 4. Setup database triggers for realtime updates
            if notify_manager.connection:
                from app.realtime.postgres_notify import setup_table_notifications

                # Setup triggers for key tables
                tables_to_watch = ['products', 'inquiries', 'qa_pairs']
                for table in tables_to_watch:
                    try:
                        setup_table_notifications(
                            notify_manager.connection,
                            table,
                            channel=f"{table}_changes"
                        )
                        app_logger.info(f"✅ Database trigger created for table: {table}")
                    except Exception as e:
                        app_logger.warning(f"Could not create trigger for {table}: {e}")

                # Listen to product changes and broadcast to Socket.IO clients
                async def handle_product_change(channel, data):
                    """Handle product change notifications"""
                    app_logger.debug(f"Product changed: {data}")
                    # Broadcast update to all subscribed clients
                    await realtime.broadcast_update("products", {})

                notify_manager.listen('product_changes', handle_product_change)
                notify_manager.start_listener_task()
                app_logger.info("✅ PostgreSQL LISTEN/NOTIFY activated")

            # 5. Initialize Redis Pub/Sub for multi-server sync
            pubsub = await get_pubsub_manager()

            # Subscribe to query updates from other servers
            async def handle_query_update(channel, message):
                """Handle query updates from other servers"""
                if message.get('type') == 'query_update':
                    query_name = message.get('query')
                    params = message.get('params')
                    await realtime.broadcast_update(query_name, params)

            await pubsub.subscribe_to_query_updates(handle_query_update)
            app_logger.info("✅ Redis Pub/Sub activated")

            # Store instances in app state
            app.state.realtime = realtime
            app.state.notify_manager = notify_manager
            app.state.pubsub = pubsub

            app_logger.info("⚡ Realtime backend ready (Socket.IO + PostgreSQL + Redis)")

        except Exception as e:
            app_logger.error(f"Failed to initialize realtime backend: {e}")
            app_logger.warning("Continuing without realtime features")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    app_logger.info("👋 RAG Enterprise API shutting down...")

    # Cleanup realtime backend
    if REALTIME_AVAILABLE and hasattr(app.state, 'realtime'):
        try:
            # Stop PostgreSQL listener
            if hasattr(app.state, 'notify_manager'):
                app.state.notify_manager.close()

            # Disconnect Redis Pub/Sub
            if hasattr(app.state, 'pubsub'):
                await app.state.pubsub.disconnect()

            app_logger.info("✅ Realtime backend cleaned up")
        except Exception as e:
            app_logger.error(f"Error during realtime cleanup: {e}")


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
