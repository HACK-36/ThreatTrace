"""
FastAPI Authentication Dependencies for Cerberus Services
"""
from typing import Optional, List

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
    APIKeyHeader
)

from shared.auth.jwt_handler import (
    decode_token,
    verify_token,
    TokenData,
    verify_service_api_key,
    SERVICE_ACCOUNTS
)


bearer_scheme = HTTPBearer(auto_error=False)
api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> TokenData:
    """
    Dependency that extracts JWT token data.
    Raises 401 if token missing or invalid.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = decode_token(credentials.credentials)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token_data


def require_roles(required_roles: Optional[List[str]] = None):
    """Factory returning dependency that enforces role membership."""

    async def dependency(token: TokenData = Depends(get_current_token)) -> TokenData:
        if required_roles:
            if not any(role in token.roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions",
                )
        return token

    return dependency


async def get_current_service(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    api_key: Optional[str] = Security(api_key_scheme)
) -> TokenData:
    """
    Dependency accepting either JWT bearer tokens or service API keys.
    Used for service-to-service authentication.
    """
    # Try JWT first
    if credentials:
        token_data = decode_token(credentials.credentials)
        if token_data:
            return token_data

    # Fallback to API key
    if api_key:
        service_info = verify_service_api_key(api_key)
        if service_info:
            return TokenData(
                username=service_info["username"],
                service=service_info["service"],
                roles=service_info["roles"]
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_service(
    service: str,
    token: TokenData = Depends(get_current_service)
) -> TokenData:
    """Ensure the calling service matches the required service name."""
    if token.service != service:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Service {service} required",
        )
    return token


async def require_service_roles(
    roles: List[str],
    token: TokenData = Depends(get_current_service)
) -> TokenData:
    """Ensure service token carries one of the required roles."""
    if not any(role in token.roles for role in roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Service lacks required role",
        )
    return token


async def get_service_account(service_name: str) -> str:
    """Helper to fetch API key for outgoing calls."""
    account = SERVICE_ACCOUNTS.get(service_name)
    if not account:
        raise ValueError(f"Unknown service: {service_name}")
    return account["api_key"]
