
"""FastAPI application entry point."""

import contextlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.api.v1.router import api_router
from app.api.middleware.error_handler import (
    app_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.rate_limit import limiter
from app.core.exceptions import AppException
from app.utils.logger import setup_logging, get_logger
from app.models.database import init_db, close_db
from app.mcp.server import mcp as mcp_server

# Setup logging
setup_logging()
logger = get_logger(__name__)

# The MCP server is its own tiny ASGI app (Streamable HTTP transport).
# FastAPI does NOT automatically start/stop the lifespans of apps mounted
# with app.mount(), so we have to explicitly run the MCP server's
# session_manager alongside our own startup/shutdown below. Without this,
# every MCP request would hang or fail because its internal session
# manager was never started.
mcp_asgi_app = mcp_server.streamable_http_app()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.

    This also starts/stops the MCP server's session manager, since the
    MCP app is mounted as a sub-application (see app.mount("/mcp", ...)
    below) and FastAPI won't drive its lifespan on its own.
    """
    async with contextlib.AsyncExitStack() as stack:
        # Startup
        logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"Environment: {settings.APP_ENV}")
        logger.info(f"Debug mode: {settings.DEBUG}")
        logger.info(f"Database: {settings.DATABASE_URL.split('@')[0]}@...")

        # Initialize database
        try:
            await init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

        # Start the MCP server's session manager
        await stack.enter_async_context(mcp_server.session_manager.run())
        logger.info("MCP server mounted at /mcp (Streamable HTTP)")

        yield

        # Shutdown
        logger.info("Shutting down application...")
        await close_db()
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-First CRM HCP Module with LangGraph and Groq",
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)


# Rate limiting (slowapi) - see app/api/middleware/rate_limit.py for the
# limiter config. app.state.limiter is where slowapi looks for it when a
# route uses the @limiter.limit(...) decorator.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Trusted Host Middleware - rejects requests whose Host header isn't in
# ALLOWED_HOSTS. Set ALLOWED_HOSTS in your production .env to your real
# backend domain (e.g. api.yourapp.com or your AWS load balancer's
# hostname), or every request will be rejected with a 400.
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS,
)


# CORS Middleware - reads allowed origins from settings (.env
# CORS_ORIGINS), instead of a hardcoded localhost-only list. Set
# CORS_ORIGINS in your production .env to your Cloudflare Pages domain
# (e.g. https://yourapp.pages.dev, plus your custom domain if you add
# one), or the browser will block every request from your deployed
# frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Logging Middleware
app.add_middleware(LoggingMiddleware)


# Exception Handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


# Include API Router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health Check
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "documentation": "/docs" if settings.DEBUG else None,
        "health": "/health",
    }


# Mount the MCP server (Model Context Protocol - Streamable HTTP transport).
# Any MCP-compatible client (Claude Desktop, another agent, etc.) can point
# at http://<host>:<port>/mcp and get the same 6 CRM actions the AI chat
# uses, as callable "tools". See app/mcp/server.py for the tool definitions
# and how auth (JWT token per call) works.
#
# IMPORTANT: mcp_asgi_app (from FastMCP.streamable_http_app()) already has
# its OWN internal route registered at "/mcp" (FastMCP's default
# streamable_http_path). If we mounted it at prefix "/mcp" here too, the
# real endpoint would end up nested at "/mcp/mcp" instead of "/mcp".
# Mounting at an empty prefix "" lets that internal "/mcp" route surface
# at exactly http://<host>:<port>/mcp. This mount is placed LAST so it
# only catches paths not already matched by the routes above (an empty
# prefix would otherwise shadow everything if placed earlier).
app.mount("", mcp_asgi_app)