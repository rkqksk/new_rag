"""Query Logging Utility"""
import time
from typing import Any, Callable, Dict, Optional
from functools import wraps
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)

# Global query log (in-memory for debug mode)
_query_log: list = []
MAX_LOG_SIZE = 1000

def log_query(
    query_type: str,  # "postgres", "qdrant", "redis"
    operation: str,   # "SELECT", "search", "GET", etc.
    details: Optional[Dict[str, Any]] = None
):
    """Decorator to log database/cache queries"""
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not settings.debug_config.log_sql:
                return await func(*args, **kwargs)
            
            start_time = time.time()
            error = None
            result = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                # Create log entry
                log_entry = {
                    "timestamp": time.time(),
                    "query_type": query_type,
                    "operation": operation,
                    "function": func.__name__,
                    "duration_ms": round(duration_ms, 2),
                    "success": error is None,
                    "error": error,
                    **(details or {})
                }
                
                # Add to in-memory log
                _query_log.append(log_entry)
                if len(_query_log) > MAX_LOG_SIZE:
                    _query_log.pop(0)
                
                # Log to structured logging
                log_message = f"{query_type} {operation}: {func.__name__}"
                if duration_ms > 100:  # Slow query threshold
                    logger.warning(
                        f"⚠️ SLOW QUERY: {log_message}",
                        extra=log_entry
                    )
                else:
                    logger.debug(log_message, extra=log_entry)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.debug_config.log_sql:
                return func(*args, **kwargs)
            
            start_time = time.time()
            error = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                log_entry = {
                    "timestamp": time.time(),
                    "query_type": query_type,
                    "operation": operation,
                    "function": func.__name__,
                    "duration_ms": round(duration_ms, 2),
                    "success": error is None,
                    "error": error,
                    **(details or {})
                }
                
                _query_log.append(log_entry)
                if len(_query_log) > MAX_LOG_SIZE:
                    _query_log.pop(0)
                
                log_message = f"{query_type} {operation}: {func.__name__}"
                if duration_ms > 100:
                    logger.warning(f"⚠️ SLOW QUERY: {log_message}", extra=log_entry)
                else:
                    logger.debug(log_message, extra=log_entry)
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def get_recent_queries(limit: int = 20, slow_only: bool = False) -> list:
    """Get recent queries from in-memory log"""
    queries = _query_log.copy()
    
    if slow_only:
        queries = [q for q in queries if q["duration_ms"] > 100]
    
    # Sort by timestamp descending
    queries.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return queries[:limit]


def clear_query_log():
    """Clear query log (useful for testing)"""
    global _query_log
    _query_log = []
