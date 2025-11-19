"""Security Headers Middleware - Production Ready

Adds enterprise-grade security headers to all HTTP responses to protect against:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME type sniffing
- Information leakage
- Man-in-the-middle attacks
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.api.core.logging import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses

    Headers added:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Control resource loading
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Control browser features
    """

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment
        logger.info(f"🛡️  Security Headers Middleware initialized (environment: {environment})")

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        # ============================================================================
        # 1. X-Frame-Options - Prevent clickjacking attacks
        # ============================================================================
        # DENY: Page cannot be displayed in frame/iframe
        response.headers["X-Frame-Options"] = "DENY"

        # ============================================================================
        # 2. X-Content-Type-Options - Prevent MIME type sniffing
        # ============================================================================
        # nosniff: Browser must not interpret files as different MIME type
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ============================================================================
        # 3. X-XSS-Protection - Enable XSS filter (legacy browsers)
        # ============================================================================
        # 1; mode=block: Enable XSS filter and block page if attack detected
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ============================================================================
        # 4. Strict-Transport-Security (HSTS) - Force HTTPS
        # ============================================================================
        # Only enable for HTTPS connections in production
        if request.url.scheme == "https" or self.environment == "production":
            # max-age=31536000: Remember for 1 year
            # includeSubDomains: Apply to all subdomains
            # preload: Allow inclusion in browser HSTS preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # ============================================================================
        # 5. Content-Security-Policy (CSP) - Control resource loading
        # ============================================================================
        # Define which sources are allowed for various resource types
        csp_directives = [
            "default-src 'self'",  # Default: only same origin
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Allow inline scripts (needed for some frameworks)
            "style-src 'self' 'unsafe-inline'",  # Allow inline styles
            "img-src 'self' data: https:",  # Allow images from same origin, data URIs, and HTTPS
            "font-src 'self' data:",  # Allow fonts from same origin and data URIs
            "connect-src 'self' ws: wss:",  # Allow WebSocket connections
            "frame-ancestors 'none'",  # Don't allow embedding (same as X-Frame-Options)
            "base-uri 'self'",  # Restrict base tag URLs
            "form-action 'self'",  # Restrict form submissions
        ]

        # Relaxed CSP for development
        if self.environment == "development":
            csp_directives.append("script-src 'self' 'unsafe-inline' 'unsafe-eval'")

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # ============================================================================
        # 6. Referrer-Policy - Control referrer information
        # ============================================================================
        # strict-origin-when-cross-origin: Send full URL for same-origin,
        # origin only for cross-origin HTTPS, nothing for HTTP
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ============================================================================
        # 7. Permissions-Policy - Control browser features
        # ============================================================================
        # Disable potentially dangerous browser features
        permissions = [
            "geolocation=()",  # No geolocation
            "microphone=()",  # No microphone
            "camera=()",  # No camera
            "payment=()",  # No payment APIs
            "usb=()",  # No USB access
            "magnetometer=()",  # No magnetometer
            "gyroscope=()",  # No gyroscope
            "accelerometer=()",  # No accelerometer
            "ambient-light-sensor=()",  # No light sensor
            "autoplay=()",  # No autoplay
            "encrypted-media=()",  # No encrypted media
            "fullscreen=(self)",  # Fullscreen only for same origin
            "picture-in-picture=()",  # No picture-in-picture
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # ============================================================================
        # 8. Additional Security Headers
        # ============================================================================

        # Remove server information leakage
        response.headers.pop("Server", None)

        # Remove X-Powered-By (if present from middleware)
        response.headers.pop("X-Powered-By", None)

        return response
