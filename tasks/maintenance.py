"""
Maintenance Tasks
==================
Background tasks for cache cleanup and system maintenance.

These tasks can be scheduled with Celery Beat for periodic execution.
"""
import logging
from typing import Dict, Any

from celery_app import async_task

logger = logging.getLogger(__name__)


@async_task(name='tasks.maintenance.cleanup_expired_cache')
def cleanup_expired_cache_task() -> Dict[str, Any]:
    """
    Clean up expired cache entries from Redis and database.
    
    This task should be scheduled to run periodically (e.g., daily).
    
    Returns:
        Dict with cleanup statistics
    """
    logger.info("Starting cache cleanup task")
    
    results = {
        "success": True,
        "vep_cache": {},
        "memory_cache": {},
        "redis_cache": {},
    }
    
    # Clean VEP service cache
    try:
        from services.vep_service import vep_service
        vep_cleanup = vep_service.clear_expired_cache()
        results["vep_cache"] = {
            "cleared_memory": vep_cleanup.get("cleared_memory", 0),
            "cleared_db": vep_cleanup.get("cleared_db", 0),
        }
        logger.info(f"VEP cache cleanup: {vep_cleanup}")
    except Exception as e:
        logger.error(f"VEP cache cleanup error: {e}")
        results["vep_cache"] = {"error": str(e)}
    
    # Clean Redis caches (if available)
    try:
        from config.redis import is_redis_available, get_redis_client
        
        if is_redis_available():
            client = get_redis_client()
            # Note: Redis TTL handles expiration automatically
            # This is just for reporting
            vep_keys = client.keys("genovaai:vep:*")
            memory_keys = client.keys("genovaai:memory:*")
            
            results["redis_cache"] = {
                "status": "healthy",
                "vep_entries": len(vep_keys) if vep_keys else 0,
                "memory_entries": len(memory_keys) if memory_keys else 0,
            }
        else:
            results["redis_cache"] = {"status": "not_available"}
    except Exception as e:
        logger.error(f"Redis status check error: {e}")
        results["redis_cache"] = {"error": str(e)}
    
    logger.info(f"Cache cleanup complete: {results}")
    return results


@async_task(name='tasks.maintenance.cleanup_old_sessions')
def cleanup_old_sessions_task(max_sessions: int = 100) -> Dict[str, Any]:
    """
    Clean up old chat sessions to prevent memory bloat.
    
    This task should be scheduled to run periodically (e.g., weekly).
    
    Args:
        max_sessions: Maximum number of sessions to keep
    
    Returns:
        Dict with cleanup statistics
    """
    logger.info(f"Starting session cleanup task (max: {max_sessions})")
    
    results = {
        "success": True,
        "sessions_removed": 0,
        "sessions_remaining": 0,
    }
    
    try:
        from agent.memory import cleanup_old_sessions, get_memory_stats
        
        # Get stats before cleanup
        stats_before = get_memory_stats()
        
        # Run cleanup
        removed = cleanup_old_sessions(max_sessions=max_sessions)
        
        # Get stats after cleanup
        stats_after = get_memory_stats()
        
        results["sessions_removed"] = removed
        results["sessions_remaining"] = stats_after.get("in_memory_sessions", 0)
        results["redis_sessions"] = stats_after.get("redis_sessions", 0)
        
        logger.info(f"Session cleanup complete: {removed} removed")
        
    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        results["success"] = False
        results["error"] = str(e)
    
    return results


@async_task(name='tasks.maintenance.health_check')
def health_check_task() -> Dict[str, Any]:
    """
    Perform comprehensive health check of all services.
    
    Returns:
        Dict with health status of all components
    """
    logger.info("Running health check task")
    
    health = {
        "success": True,
        "components": {},
    }
    
    # Check PostgreSQL
    try:
        from database import db
        db.session.execute(db.text("SELECT 1"))
        health["components"]["postgresql"] = {"status": "healthy"}
    except Exception as e:
        health["components"]["postgresql"] = {"status": "unhealthy", "error": str(e)}
        health["success"] = False
    
    # Check MongoDB
    try:
        from config.mongodb import is_mongodb_available
        if is_mongodb_available():
            health["components"]["mongodb"] = {"status": "healthy"}
        else:
            health["components"]["mongodb"] = {"status": "unhealthy"}
    except Exception as e:
        health["components"]["mongodb"] = {"status": "error", "error": str(e)}
    
    # Check Redis
    try:
        from config.redis import redis_health_check
        health["components"]["redis"] = redis_health_check()
    except Exception as e:
        health["components"]["redis"] = {"status": "error", "error": str(e)}
    
    # Check VEP service
    try:
        from services.vep_service import vep_service
        vep_status = vep_service.get_service_status()
        health["components"]["vep"] = {
            "status": "healthy" if vep_status.get("api_available") else "degraded",
            "enabled": vep_status.get("enabled"),
            "response_time_ms": vep_status.get("response_time_ms"),
        }
    except Exception as e:
        health["components"]["vep"] = {"status": "error", "error": str(e)}
    
    # Check Gemini API
    try:
        import os
        gemini_key = os.environ.get("GEMINI_API_KEY")
        health["components"]["gemini"] = {
            "status": "configured" if gemini_key else "not_configured",
        }
    except Exception as e:
        health["components"]["gemini"] = {"status": "error", "error": str(e)}
    
    logger.info(f"Health check complete: {health['success']}")
    return health


# ============================================================
# Utility functions
# ============================================================

@async_task(name='tasks.maintenance.celery_health_check')
def celery_health_check_task() -> Dict[str, Any]:
    """
    Celery-specific health check for monitoring.
    Runs periodically to confirm workers are operational.
    
    Returns:
        Dict with Celery status
    """
    import time
    from datetime import datetime
    
    return {
        "success": True,
        "worker": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "task": "celery_health_check"
    }


def run_all_maintenance() -> Dict[str, Any]:
    """Run all maintenance tasks synchronously"""
    return {
        "cache_cleanup": cleanup_expired_cache_task(),
        "session_cleanup": cleanup_old_sessions_task(),
        "health_check": health_check_task(),
    }

