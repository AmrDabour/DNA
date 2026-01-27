"""
Redis Configuration Module
Connection handling and utilities for Redis caching
"""
import os
import json
import logging
from typing import Optional, Any, Dict
from datetime import timedelta

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client = None
_redis_available = None
_session_redis_client = None  # Separate client for sessions (binary data)


def get_redis_config(decode_responses: bool = True) -> Dict[str, Any]:
    """Get Redis configuration from environment variables
    
    Args:
        decode_responses: If True, decode responses as UTF-8 strings.
                         Set to False for binary data (e.g., Flask-Session).
    """
    return {
        'host': os.environ.get('REDIS_HOST', 'localhost'),
        'port': int(os.environ.get('REDIS_PORT', 6379)),
        'db': int(os.environ.get('REDIS_DB', 0)),
        'password': os.environ.get('REDIS_PASSWORD', None),
        'decode_responses': decode_responses,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
        'retry_on_timeout': True,
    }


def get_redis_url() -> str:
    """Get Redis URL from environment or build from components"""
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        return redis_url
    
    config = get_redis_config()
    password_part = f":{config['password']}@" if config['password'] else ""
    return f"redis://{password_part}{config['host']}:{config['port']}/{config['db']}"


def get_redis_client():
    """
    Get or create Redis client singleton.
    Returns None if Redis is not available.
    """
    global _redis_client, _redis_available
    
    # Return cached result if we already know Redis is unavailable
    if _redis_available is False:
        return None
    
    if _redis_client is None:
        try:
            import redis
            
            config = get_redis_config(decode_responses=True)
            _redis_client = redis.Redis(**config)
            
            # Test connection
            _redis_client.ping()
            _redis_available = True
            logger.info("✅ Redis connection established!")
            
        except ImportError:
            logger.warning("⚠️ Redis package not installed. Caching disabled.")
            _redis_available = False
            return None
        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}. Using in-memory fallback.")
            _redis_available = False
            _redis_client = None
            return None
    
    return _redis_client


def get_session_redis_client():
    """
    Get or create Redis client for Flask-Session.
    This client does NOT decode responses, as Flask-Session stores binary data.
    Returns None if Redis is not available.
    """
    global _session_redis_client, _redis_available
    
    # Check availability first
    if not is_redis_available():
        return None
    
    if _session_redis_client is None:
        try:
            import redis
            
            # Session client must NOT decode responses (binary serialized data)
            config = get_redis_config(decode_responses=False)
            _session_redis_client = redis.Redis(**config)
            
            # Test connection
            _session_redis_client.ping()
            logger.info("✅ Session Redis client established!")
            
        except Exception as e:
            logger.warning(f"⚠️ Session Redis client failed: {e}")
            return None
    
    return _session_redis_client


def is_redis_available() -> bool:
    """Check if Redis is available"""
    global _redis_available
    
    if _redis_available is None:
        get_redis_client()
    
    return _redis_available or False


def redis_health_check() -> Dict[str, Any]:
    """
    Check Redis health status.
    Returns dict with status and info.
    """
    try:
        client = get_redis_client()
        if client is None:
            return {
                'status': 'unavailable',
                'message': 'Redis client not connected'
            }
        
        info = client.info('server')
        return {
            'status': 'healthy',
            'version': info.get('redis_version', 'unknown'),
            'uptime_seconds': info.get('uptime_in_seconds', 0),
            'connected_clients': client.info('clients').get('connected_clients', 0)
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


def close_redis_connection():
    """Close Redis connection"""
    global _redis_client, _redis_available, _session_redis_client
    
    if _redis_client:
        try:
            _redis_client.close()
            logger.info("✅ Redis connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing Redis: {e}")
        finally:
            _redis_client = None
            _redis_available = None
    
    if _session_redis_client:
        try:
            _session_redis_client.close()
            logger.info("✅ Session Redis connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing session Redis: {e}")
        finally:
            _session_redis_client = None


# ============================================================
# Cache Utility Functions
# ============================================================

class RedisCache:
    """
    Redis cache wrapper with automatic JSON serialization
    and graceful fallback to in-memory storage.
    """
    
    # In-memory fallback cache
    _fallback_cache: Dict[str, Any] = {}
    
    def __init__(self, prefix: str = "genovaai", default_ttl: int = 3600):
        """
        Initialize cache with optional prefix and TTL.
        
        Args:
            prefix: Key prefix for namespacing
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.prefix = prefix
        self.default_ttl = default_ttl
    
    def _make_key(self, key: str) -> str:
        """Create namespaced key"""
        return f"{self.prefix}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        Returns None if key doesn't exist.
        """
        full_key = self._make_key(key)
        
        client = get_redis_client()
        if client:
            try:
                value = client.get(full_key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {e}")
        
        # Fallback to in-memory
        return self._fallback_cache.get(full_key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: TTL in seconds (uses default if not specified)
        
        Returns:
            True if successful
        """
        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        client = get_redis_client()
        if client:
            try:
                serialized = json.dumps(value)
                client.setex(full_key, ttl, serialized)
                return True
            except Exception as e:
                logger.warning(f"Redis set error: {e}")
        
        # Fallback to in-memory (no TTL support)
        self._fallback_cache[full_key] = value
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        full_key = self._make_key(key)
        
        client = get_redis_client()
        if client:
            try:
                client.delete(full_key)
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        
        # Also remove from fallback
        self._fallback_cache.pop(full_key, None)
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        full_key = self._make_key(key)
        
        client = get_redis_client()
        if client:
            try:
                return client.exists(full_key) > 0
            except Exception as e:
                logger.warning(f"Redis exists error: {e}")
        
        return full_key in self._fallback_cache
    
    def clear_prefix(self, pattern: str = "*") -> int:
        """
        Clear all keys matching pattern under this cache's prefix.
        
        Args:
            pattern: Pattern to match (default: all keys)
        
        Returns:
            Number of keys deleted
        """
        full_pattern = self._make_key(pattern)
        deleted = 0
        
        client = get_redis_client()
        if client:
            try:
                keys = client.keys(full_pattern)
                if keys:
                    deleted = client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear error: {e}")
        
        # Clear matching fallback keys
        keys_to_delete = [k for k in self._fallback_cache.keys() 
                         if k.startswith(self.prefix)]
        for k in keys_to_delete:
            del self._fallback_cache[k]
            deleted += 1
        
        return deleted
    
    def get_or_set(self, key: str, factory, ttl: Optional[int] = None) -> Any:
        """
        Get value from cache or compute and store it.
        
        Args:
            key: Cache key
            factory: Callable that returns value if not cached
            ttl: TTL in seconds
        
        Returns:
            Cached or computed value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value


# ============================================================
# Specialized Cache Instances
# ============================================================

# VEP API response cache (7 days default)
vep_cache = RedisCache(prefix="genovaai:vep", default_ttl=7 * 24 * 3600)

# Agent chat memory cache (24 hours default)
memory_cache = RedisCache(prefix="genovaai:memory", default_ttl=24 * 3600)

# General application cache (1 hour default)
app_cache = RedisCache(prefix="genovaai:cache", default_ttl=3600)

# Rate limiting cache (short TTL)
rate_limit_cache = RedisCache(prefix="genovaai:ratelimit", default_ttl=60)


# ============================================================
# Session Configuration for Flask-Session
# ============================================================

def get_session_config() -> Dict[str, Any]:
    """
    Get Flask-Session configuration for Redis.
    Returns config dict to update app.config.
    """
    return {
        'SESSION_TYPE': 'redis',
        'SESSION_REDIS': get_session_redis_client(),  # Use non-decoding client for binary data
        'SESSION_PERMANENT': True,
        'SESSION_USE_SIGNER': True,
        'SESSION_KEY_PREFIX': 'genovaai:session:',
        'PERMANENT_SESSION_LIFETIME': timedelta(days=7),
    }


def configure_flask_session(app):
    """
    Configure Flask-Session with Redis.
    Falls back to filesystem sessions if Redis unavailable.
    """
    try:
        from flask_session import Session
        
        if is_redis_available():
            app.config.update(get_session_config())
            logger.info("✅ Flask-Session configured with Redis")
        else:
            # Fallback to filesystem sessions
            app.config['SESSION_TYPE'] = 'filesystem'
            app.config['SESSION_FILE_DIR'] = '/tmp/flask_sessions'
            app.config['SESSION_PERMANENT'] = True
            app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
            logger.info("⚠️ Flask-Session using filesystem (Redis unavailable)")
        
        Session(app)
        return True
        
    except ImportError:
        logger.warning("⚠️ flask-session not installed. Using default sessions.")
        return False
    except Exception as e:
        logger.error(f"❌ Error configuring Flask-Session: {e}")
        return False


