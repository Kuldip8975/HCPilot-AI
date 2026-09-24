"""Global error handlers for the application."""

import logging
from datetime import datetime
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.config import settings
from app.core.exceptions import AppException, DatabaseError

logger = logging.getLogger(__name__)


def _safe_details(details: dict) -> dict | None:
    """Only include raw internal error text in the response when running
    in debug mode. In production, the real error always still goes to the
    server logs (see the logger.error calls below) - it's just not handed
    to whoever is calling the API, since that can leak internal details
    (SQL structure, stack info, library internals) to an end user."""
    if settings.DEBUG:
        return details
    return None


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    Handle application-specific exceptions.
    """
    logger.error(
        f"Application error: {exc.code} - {exc.message}",
        extra={"code": exc.code, "details": exc.details}
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": _safe_details(exc.details),
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors.

    Field-level validation messages (e.g. "email is required") are safe to
    show in any environment - they describe what the CALLER got wrong in
    their own request, not internal server details, so these are not
    gated behind DEBUG the way the other handlers below are.
    """
    logger.error(f"Validation error: {exc.errors()}")

    # Format validation errors
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"],
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": errors,
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unhandled exceptions.
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)

    # Handle database errors
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "error": {
                    "code": "DB_CONFLICT",
                    "message": "Database conflict error",
                    "details": _safe_details({"error": str(exc)}),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }
        )

    if isinstance(exc, SQLAlchemyError):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "DB_ERROR",
                    "message": "Database error occurred",
                    "details": _safe_details({"error": str(exc)}),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            }
        )

    # Generic error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": _safe_details({"error": str(exc)} if str(exc) else None),
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )