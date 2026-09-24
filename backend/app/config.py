"""Application configuration using Pydantic Settings."""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    APP_NAME: str = Field("Naukri CRM HCP Module", env="APP_NAME")
    APP_VERSION: str = Field("1.0.0", env="APP_VERSION")
    APP_ENV: str = Field("development", env="APP_ENV")
    DEBUG: bool = Field(True, env="DEBUG")
    
    # Server
    BACKEND_HOST: str = Field("0.0.0.0", env="BACKEND_HOST")
    BACKEND_PORT: int = Field(8000, env="BACKEND_PORT")
    BACKEND_DEBUG: bool = Field(True, env="BACKEND_DEBUG")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(False, env="DATABASE_ECHO")
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY", min_length=32)
    JWT_REFRESH_SECRET: str = Field(..., env="JWT_REFRESH_SECRET", min_length=32)
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Security
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
        env="CORS_ORIGINS"
    )
    ALLOWED_HOSTS: List[str] = Field(
        ["localhost", "127.0.0.1"],
        env="ALLOWED_HOSTS"
    )
    
    # Rate Limiting
    RATE_LIMIT_AUTH: str = Field("5/minute", env="RATE_LIMIT_AUTH")
    RATE_LIMIT_CHAT: str = Field("20/minute", env="RATE_LIMIT_CHAT")
    RATE_LIMIT_API: str = Field("100/minute", env="RATE_LIMIT_API")
    RATE_LIMIT_ANALYTICS: str = Field("50/minute", env="RATE_LIMIT_ANALYTICS")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")
    LOG_FILE: Optional[str] = Field("logs/app.log", env="LOG_FILE")
    
    # Frontend URL
    FRONTEND_URL: str = Field("http://localhost:5173", env="FRONTEND_URL")
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Groq API
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    GROQ_MODEL: str = Field("gemma2-9b-it", env="GROQ_MODEL")
    GROQ_ALTERNATIVE_MODEL: str = Field("llama-3.3-70b-versatile", env="GROQ_ALTERNATIVE_MODEL")
    GROQ_API_BASE: str = Field("https://api.groq.com/openai/v1", env="GROQ_API_BASE")
    GROQ_MAX_TOKENS: int = Field(4096, env="GROQ_MAX_TOKENS")
    GROQ_TEMPERATURE: float = Field(0.7, env="GROQ_TEMPERATURE")

    # Langfuse observability (optional - app runs fine without these set)
    LANGFUSE_PUBLIC_KEY: Optional[str] = Field(None, env="LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: Optional[str] = Field(None, env="LANGFUSE_SECRET_KEY")
    LANGFUSE_HOST: str = Field("https://cloud.langfuse.com", env="LANGFUSE_HOST")

    @field_validator("CORS_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_comma_or_json_list(cls, v):
        """Accept either a JSON array (e.g. '["a","b"]') or a plain
        comma-separated string (e.g. "a,b,c") for these two env vars.

        pydantic-settings only understands JSON-array-formatted strings
        for List[str] fields by default. The .env.example file in this
        project documents the comma-separated form, which otherwise
        crashes app startup with a confusing "field required" error
        instead of a clear message about the actual formatting problem.
        """
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                # Looks like JSON already - let pydantic's own parsing handle it.
                return v
            if not v:
                return []
            return [item.strip() for item in v.split(",") if item.strip()]
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL."""
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key length."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


settings = Settings()