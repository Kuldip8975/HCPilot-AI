"""Custom exception classes for the application."""

from typing import Any, Dict, Optional
from fastapi import status


class AppException(Exception):
    """Base application exception."""
    
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(AppException):
    """Authentication related errors."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTH_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class AuthorizationError(AppException):
    """Authorization related errors."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            message=message,
            code="AUTHZ_ERROR",
            status_code=status.HTTP_403_FORBIDDEN
        )


class NotFoundError(AppException):
    """Resource not found errors."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"resource": resource, "identifier": identifier}
        )


class ValidationError(AppException):
    """Data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"field": field} if field else {}
        )


class DatabaseError(AppException):
    """Database related errors."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(
            message=message,
            code="DB_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ConflictError(AppException):
    """Resource conflict errors (e.g., duplicate entry)."""
    
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            code="CONFLICT_ERROR",
            status_code=status.HTTP_409_CONFLICT
        )


class RateLimitError(AppException):
    """Rate limit exceeded errors."""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )


class ExternalServiceError(AppException):
    """External service errors."""
    
    def __init__(self, service: str, message: str = "External service error"):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# NEW: Add these missing exceptions
class GroqAPIError(AppException):
    """Groq API related errors."""
    
    def __init__(self, message: str = "Groq API request failed"):
        super().__init__(
            message=message,
            code="GROQ_ERROR",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


class ToolExecutionError(AppException):
    """LangGraph tool execution errors."""
    
    def __init__(self, tool_name: str, message: str):
        super().__init__(
            message=f"Tool '{tool_name}' execution failed: {message}",
            code="TOOL_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"tool": tool_name}
        )


class AIServiceError(AppException):
    """AI service related errors."""
    
    def __init__(self, message: str = "AI service error"):
        super().__init__(
            message=message,
            code="AI_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )