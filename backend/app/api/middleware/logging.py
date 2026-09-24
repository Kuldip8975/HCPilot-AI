"""Request/Response logging middleware."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging requests and responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Log request and response details.
        """
        # Request start time
        start_time = time.time()
        
        # Log request
        request_body = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_body = body.decode("utf-8")[:1000]  # Truncate for logging
            except Exception:
                request_body = "Unable to read body"
        
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            f"Response: {request.method} {request.url.path} - {response.status_code} ({process_time:.3f}s)",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time": process_time,
            }
        )
        
        # Add process time header
        response.headers["X-Process-Time"] = str(process_time)
        
        return response