"""
JWT Authentication Handler for Cerberus
Provides unified authentication across all services
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Configuration from environment
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "cerberus-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data"""
    username: str
    service: str  # gatekeeper, switch, labyrinth, sentinel, warroom
    roles: List[str] = []  # admin, analyst, readonly
    exp: Optional[datetime] = None


class User(BaseModel):
    """User model"""
    username: str
    service: str
    roles: List[str]
    disabled: bool = False
    api_key_hash: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Bcrypt hash
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash password with bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Bcrypt hash
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("username")
        service: str = payload.get("service")
        roles: List[str] = payload.get("roles", [])
        
        if username is None:
            return None
        
        return TokenData(username=username, service=service, roles=roles)
    
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def verify_token(token: str, required_service: Optional[str] = None, required_roles: Optional[List[str]] = None) -> bool:
    """
    Verify token and check service/role requirements
    
    Args:
        token: JWT token
        required_service: Optional service name to check
        required_roles: Optional list of roles, user must have at least one
        
    Returns:
        True if token is valid and meets requirements
    """
    token_data = decode_token(token)
    if not token_data:
        return False
    
    # Check service
    if required_service and token_data.service != required_service:
        logger.warning(f"Service mismatch: expected {required_service}, got {token_data.service}")
        return False
    
    # Check roles
    if required_roles:
        if not any(role in token_data.roles for role in required_roles):
            logger.warning(f"Role check failed: user has {token_data.roles}, required one of {required_roles}")
            return False
    
    return True


def create_api_key(username: str, service: str) -> str:
    """
    Create long-lived API key for service-to-service communication
    
    Args:
        username: Username/service name
        service: Service identifier
        
    Returns:
        API key string
    """
    import secrets
    
    # API key format: cerberus_<service>_<random_32_chars>
    random_part = secrets.token_urlsafe(24)
    api_key = f"cerberus_{service}_{random_part}"
    
    return api_key


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for storage
    
    Args:
        api_key: API key to hash
        
    Returns:
        Hashed API key
    """
    return get_password_hash(api_key)


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """
    Verify API key against stored hash
    
    Args:
        api_key: API key to verify
        hashed_key: Stored hash
        
    Returns:
        True if API key matches
    """
    return verify_password(api_key, hashed_key)


# Predefined service accounts for internal communication
SERVICE_ACCOUNTS = {
    "gatekeeper": {
        "username": "gatekeeper-service",
        "service": "gatekeeper",
        "roles": ["service"],
        "api_key": os.getenv("GATEKEEPER_API_KEY", "gatekeeper-dev-key-change-me")
    },
    "switch": {
        "username": "switch-service",
        "service": "switch",
        "roles": ["service"],
        "api_key": os.getenv("SWITCH_API_KEY", "switch-dev-key-change-me")
    },
    "labyrinth": {
        "username": "labyrinth-service",
        "service": "labyrinth",
        "roles": ["service"],
        "api_key": os.getenv("LABYRINTH_API_KEY", "labyrinth-dev-key-change-me")
    },
    "sentinel": {
        "username": "sentinel-service",
        "service": "sentinel",
        "roles": ["service", "admin"],
        "api_key": os.getenv("SENTINEL_API_KEY", "sentinel-dev-key-change-me")
    },
    "warroom": {
        "username": "warroom-service",
        "service": "warroom",
        "roles": ["service", "readonly"],
        "api_key": os.getenv("WARROOM_API_KEY", "warroom-dev-key-change-me")
    }
}


def get_service_token(service_name: str) -> Optional[str]:
    """
    Get JWT token for service account
    
    Args:
        service_name: Name of service (gatekeeper, switch, etc.)
        
    Returns:
        JWT token or None if service not found
    """
    service_account = SERVICE_ACCOUNTS.get(service_name)
    if not service_account:
        return None
    
    token = create_access_token(
        data={
            "username": service_account["username"],
            "service": service_account["service"],
            "roles": service_account["roles"]
        },
        expires_delta=timedelta(hours=24)  # Service tokens last longer
    )
    
    return token


def verify_service_api_key(api_key: str) -> Optional[Dict[str, any]]:
    """
    Verify service API key and return service info
    
    Args:
        api_key: API key to verify
        
    Returns:
        Service account dict if valid, None otherwise
    """
    for service_name, service_account in SERVICE_ACCOUNTS.items():
        if api_key == service_account["api_key"]:
            return service_account
    
    return None
