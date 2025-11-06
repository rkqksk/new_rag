"""Request/Response Logging Middleware"""
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs request and response details for debugging.
    
    Features:
    - Logs request body (if enabled)
    - Logs response body (if enabled)
    - Respects debug configuration
    - Sanitizes sensitive data
    """
    
    def __init__(self, app, sensitive_fields: list = None):
        super().__init__(app)
        self.sensitive_fields = sensitive_fields or ['password', 'token', 'api_key', 'secret']
        self.log_requests = settings.debug_config.log_requests
        self.log_responses = settings.debug_config.log_responses
    
    def sanitize_data(self, data: dict) -> dict:
        """Remove sensitive fields from logging"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if key.lower() in self.sensitive_fields:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request if enabled
        if self.log_requests:
            try:
                # Read request body
                body = await request.body()
                
                if body:
                    try:
                        body_json = json.loads(body.decode())
                        body_json = self.sanitize_data(body_json)
                        
                        logger.debug(
                            f"Request body: {request.method} {request.url.path}",
                            extra={
                                'request_body': body_json,
                                'content_type': request.headers.get('content-type')
                            }
                        )
                    except json.JSONDecodeError:
                        logger.debug(
                            f"Request body (non-JSON): {request.method} {request.url.path}",
                            extra={
                                'body_size': len(body),
                                'content_type': request.headers.get('content-type')
                            }
                        )
                
                # Restore body for downstream processing
                async def receive():
                    return {'type': 'http.request', 'body': body}
                
                request._receive = receive
            
            except Exception as e:
                logger.warning(f"Failed to log request body: {e}")
        
        # Process request
        response = await call_next(request)
        
        # Log response if enabled (note: response body already consumed)
        if self.log_responses and response.status_code >= 400:
            logger.debug(
                f"Response: {request.method} {request.url.path}",
                extra={
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
            )
        
        return response
