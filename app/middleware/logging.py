"""
Request/Response logging middleware.

Logs all incoming requests and outgoing responses with timing information.
"""
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip logging for health check endpoints
        if request.url.path in ['/health', '/']:
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Get client info
        client_ip = request.client.host if request.client else 'unknown'
        
        # Log incoming request
        logger.info(
            f"> {request.method} {request.url.path}"
            f"{('?' + str(request.query_params)) if request.query_params else ''}"
            f" | Client: {client_ip}"
        )
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[ERR] {request.method} {request.url.path} | "
                f"Exception after {duration_ms:.2f}ms: {str(e)}"
            )
            raise
        
        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log response
        status_indicator = "[OK]" if response.status_code < 400 else "[ERR]"
        log_method = logger.info if response.status_code < 400 else logger.warning
        
        log_method(
            f"{status_indicator} {request.method} {request.url.path} | "
            f"Status: {response.status_code} | Duration: {duration_ms:.2f}ms"
        )
        
        return response
