"""Performance Timing Middleware"""
import time
from typing import Callable, Dict
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import get_logger
from contextvars import ContextVar

logger = get_logger(__name__)

# Context variable for timing data
timing_context: ContextVar[Dict[str, float]] = ContextVar('timing_context', default={})

class PerformanceTimingMiddleware(BaseHTTPMiddleware):
    """
    Tracks request performance and identifies slow requests.
    
    Features:
    - Measures total request duration
    - Detects slow requests (configurable threshold)
    - Provides timing breakdown hooks
    - Adds timing headers to response
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.slow_threshold_ms = settings.debug_config.slow_request_threshold_ms
        self.profile_enabled = settings.debug_config.profile_requests
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Initialize timing context
        timings = {'request_start': time.time()}
        timing_context.set(timings)
        
        # Process request
        start_time = time.time()
        response = await call_next(request)
        total_duration_ms = (time.time() - start_time) * 1000
        
        # Add timing header
        response.headers['X-Response-Time'] = f"{total_duration_ms:.2f}ms"
        
        # Log slow requests
        if total_duration_ms > self.slow_threshold_ms:
            logger.warning(
                f"⚠️ SLOW REQUEST: {request.method} {request.url.path}",
                extra={
                    'duration_ms': total_duration_ms,
                    'threshold_ms': self.slow_threshold_ms,
                    'path': request.url.path,
                    'method': request.method
                }
            )
        
        # Log detailed timing if profiling enabled
        if self.profile_enabled:
            timings = timing_context.get()
            if len(timings) > 1:  # Has detailed breakdowns
                logger.info(
                    f"Request timing breakdown: {request.method} {request.url.path}",
                    extra={
                        'total_ms': total_duration_ms,
                        'breakdowns': self._calculate_breakdowns(timings)
                    }
                )
        
        return response
    
    def _calculate_breakdowns(self, timings: Dict[str, float]) -> Dict[str, float]:
        """Calculate timing breakdowns"""
        start = timings.get('request_start', 0)
        breakdowns = {}
        
        sorted_timings = sorted(timings.items(), key=lambda x: x[1])
        
        prev_time = start
        for key, timestamp in sorted_timings:
            if key != 'request_start':
                duration = (timestamp - prev_time) * 1000
                breakdowns[key] = round(duration, 2)
                prev_time = timestamp
        
        return breakdowns


# Helper function to record timing checkpoints
def record_timing(checkpoint_name: str):
    """Record a timing checkpoint in the current request"""
    try:
        timings = timing_context.get({})
        timings[checkpoint_name] = time.time()
        timing_context.set(timings)
    except Exception:
        # Silently fail if no timing context
        pass
