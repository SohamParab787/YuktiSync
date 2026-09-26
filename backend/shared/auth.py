import logging
from typing import Optional
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.config import settings

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
) -> dict:
    """
    FastAPI dependency to extract authenticated user.
    Supports standard Bearer JWT token, explicit test/dev headers, or falls back to demo caregiver user.
    """
    if credentials:
        token = credentials.credentials
        try:
            payload = decode_token(token)
            return {
                "id": payload.get("sub", payload.get("user_id", "caregiver-201")),
                "email": payload.get("email", "caregiver@example.com"),
                "name": payload.get("name", "Caregiver User"),
                "role": payload.get("role", "caregiver"),
            }
        except HTTPException:
            # If invalid token provided
            raise
        except Exception:
            pass

    if x_user_id:
        return {
            "id": x_user_id,
            "email": f"{x_user_id}@example.com",
            "name": x_user_name or "Test User",
            "role": x_user_role or "caregiver",
        }

    # Default fallback for development/demo ease
    return {
        "id": "caregiver-201",
        "email": "priya@example.com",
        "name": "Priya Patel",
        "role": "caregiver",
    }
