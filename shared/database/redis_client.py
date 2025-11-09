"""
Redis client wrapper for Cerberus services
Provides connection pooling and helper methods for common operations
"""
import os
import json
import redis
from typing import Optional, Dict, Any, List
from datetime import timedelta


class RedisClient:
    """Redis client with connection pooling and helper methods"""
    
    def __init__(self, url: Optional[str] = None):
        """
        Initialize Redis client
        
        Args:
            url: Redis connection URL (defaults to REDIS_URL env var)
        """
        redis_url = url or os.getenv("REDIS_URL", "redis://redis:6379")
        self.client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
    def ping(self) -> bool:
        """Check if Redis is accessible"""
        try:
            return self.client.ping()
        except Exception:
            return False
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a key-value pair
        
        Args:
            key: Cache key
            value: Value to store (will be JSON-serialized if dict/list)
            ttl: Time-to-live in seconds (optional)
        
        Returns:
            True if successful
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if ttl:
                return self.client.setex(key, ttl, value)
            else:
                return self.client.set(key, value)
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    def get(self, key: str, as_json: bool = False) -> Optional[Any]:
        """
        Get a value by key
        
        Args:
            key: Cache key
            as_json: If True, parse value as JSON
        
        Returns:
            Value or None if not found
        """
        try:
            value = self.client.get(key)
            if value and as_json:
                return json.loads(value)
            return value
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None
    
    def delete(self, *keys: str) -> int:
        """
        Delete one or more keys
        
        Returns:
            Number of keys deleted
        """
        try:
            return self.client.delete(*keys)
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if a key exists"""
        try:
            return self.client.exists(key) > 0
        except Exception:
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on a key"""
        try:
            return self.client.expire(key, ttl)
        except Exception:
            return False
    
    def hset(self, name: str, key: str, value: Any) -> int:
        """Set hash field"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.hset(name, key, value)
        except Exception as e:
            print(f"Redis HSET error: {e}")
            return 0
    
    def hget(self, name: str, key: str, as_json: bool = False) -> Optional[Any]:
        """Get hash field"""
        try:
            value = self.client.hget(name, key)
            if value and as_json:
                return json.loads(value)
            return value
        except Exception as e:
            print(f"Redis HGET error: {e}")
            return None
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """Get all hash fields"""
        try:
            return self.client.hgetall(name)
        except Exception as e:
            print(f"Redis HGETALL error: {e}")
            return {}
    
    def hdel(self, name: str, *keys: str) -> int:
        """Delete hash fields"""
        try:
            return self.client.hdel(name, *keys)
        except Exception:
            return 0
    
    def lpush(self, key: str, *values: Any) -> int:
        """Push values to list (left)"""
        try:
            json_values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
            return self.client.lpush(key, *json_values)
        except Exception:
            return 0
    
    def rpush(self, key: str, *values: Any) -> int:
        """Push values to list (right)"""
        try:
            json_values = [json.dumps(v) if isinstance(v, (dict, list)) else v for v in values]
            return self.client.rpush(key, *json_values)
        except Exception:
            return 0
    
    def lrange(self, key: str, start: int = 0, end: int = -1, as_json: bool = False) -> List[Any]:
        """Get list range"""
        try:
            values = self.client.lrange(key, start, end)
            if as_json:
                return [json.loads(v) for v in values]
            return values
        except Exception:
            return []
    
    def llen(self, key: str) -> int:
        """Get list length"""
        try:
            return self.client.llen(key)
        except Exception:
            return 0
    
    def sadd(self, key: str, *members: Any) -> int:
        """Add members to set"""
        try:
            return self.client.sadd(key, *members)
        except Exception:
            return 0
    
    def smembers(self, key: str) -> set:
        """Get all set members"""
        try:
            return self.client.smembers(key)
        except Exception:
            return set()
    
    def sismember(self, key: str, member: Any) -> bool:
        """Check if member is in set"""
        try:
            return self.client.sismember(key, member)
        except Exception:
            return False
    
    def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter"""
        try:
            return self.client.incr(key, amount)
        except Exception:
            return 0
    
    def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a counter"""
        try:
            return self.client.decr(key, amount)
        except Exception:
            return 0
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            return self.client.keys(pattern)
        except Exception:
            return []
    
    def ttl(self, key: str) -> int:
        """Get time-to-live of a key"""
        try:
            return self.client.ttl(key)
        except Exception:
            return -2
    
    def flushdb(self) -> bool:
        """Flush current database (use with caution!)"""
        try:
            return self.client.flushdb()
        except Exception:
            return False


# Global instance
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """Get or create Redis client singleton"""
    global _redis_client
    if _redis_client is None:
        _redis_client = RedisClient()
    return _redis_client
