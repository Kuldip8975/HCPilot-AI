"""Security utilities for authentication and authorization."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.exceptions import AuthenticationError


# Use pbkdf2_sha256 - no 72-byte limit like bcrypt!
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


class SecurityConfig:
    """Security configuration and utilities."""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        expire = datetime.utcnow() + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode = data.copy()
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4()),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_REFRESH_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str, is_refresh: bool = False) -> Dict[str, Any]:
        """Decode and validate a JWT token."""
        try:
            secret = (
                settings.JWT_REFRESH_SECRET
                if is_refresh
                else settings.JWT_SECRET_KEY
            )
            payload = jwt.decode(
                token,
                secret,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def generate_user_id() -> str:
        """Generate a unique user ID."""
        return str(uuid.uuid4())