"""
Celery Configuration for GenovaAI
==================================
This file configures Celery for asynchronous task processing.

CURRENT STATUS: SCAFFOLDING ONLY
---------------------------------
Celery is NOT currently active. This file provides the configuration
structure for future implementation when async task processing is needed.

TO ENABLE CELERY:
1. Uncomment celery and kombu in requirements.txt
2. Uncomment RabbitMQ and celery-worker services in docker-compose.yml
3. Set CELERY_ENABLED=true in environment
4. pip install celery kombu
5. Run: celery -A celery_app worker --loglevel=info

USAGE:
------
Once enabled, import tasks like:
    from tasks.snp_analysis import analyze_snp_file_async
    result = analyze_snp_file_async.delay(file_path)
"""
import os
from functools import wraps

# Check if Celery is enabled
CELERY_ENABLED = os.environ.get('CELERY_ENABLED', 'false').lower() == 'true'

# Try to import Celery
try:
    from celery import Celery
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    Celery = None


def get_celery_config():
    """Get Celery configuration from environment"""
    return {
        'broker_url': os.environ.get(
            'CELERY_BROKER_URL',
            'amqp://genovaai:genovaai_rabbit_2024@rabbitmq:5672//'
        ),
        'result_backend': os.environ.get(
            'CELERY_RESULT_BACKEND',
            'redis://redis:6379/1'
        ),
        'task_serializer': 'json',
        'result_serializer': 'json',
        'accept_content': ['json'],
        'timezone': 'UTC',
        'enable_utc': True,
        'task_track_started': True,
        'task_time_limit': 3600,  # 1 hour max
        'task_soft_time_limit': 3300,  # 55 minutes soft limit
        'worker_prefetch_multiplier': 1,
        'worker_concurrency': 2,
    }


def create_celery_app(flask_app=None):
    """
    Create and configure Celery application.
    
    Args:
        flask_app: Optional Flask app for context integration
    
    Returns:
        Celery app instance or None if Celery is unavailable
    """
    if not CELERY_AVAILABLE or not CELERY_ENABLED:
        return None
    
    celery = Celery('genovaai')
    celery.config_from_object(get_celery_config())
    
    # Auto-discover tasks in tasks/ directory
    celery.autodiscover_tasks(['tasks'])
    
    # Integrate with Flask app context if provided
    if flask_app:
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with flask_app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery


# Create the celery app instance (None if disabled)
celery_app = create_celery_app()

# Alias for backwards compatibility
celery = celery_app


# ============================================================
# Task Decorator Helper
# ============================================================

def async_task(name=None, bind=False, **options):
    """
    Decorator that creates a Celery task when Celery is enabled,
    or returns a synchronous function when disabled.
    
    This allows the same code to work with or without Celery.
    
    Usage:
        @async_task(name='process_file')
        def process_file(file_path):
            # This runs async when Celery is enabled
            # This runs sync when Celery is disabled
            return do_processing(file_path)
        
        # Call the task
        if CELERY_ENABLED:
            result = process_file.delay(file_path)  # Async
        else:
            result = process_file(file_path)  # Sync
    """
    def decorator(func):
        if celery_app and CELERY_ENABLED:
            # Create actual Celery task
            return celery_app.task(name=name, bind=bind, **options)(func)
        else:
            # Return sync wrapper that mimics Celery task interface
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            
            # Add delay method for compatibility
            def delay(*args, **kwargs):
                """Synchronous execution (Celery not enabled)"""
                return SyncResult(func(*args, **kwargs))
            
            sync_wrapper.delay = delay
            sync_wrapper.apply_async = delay
            sync_wrapper.name = name or func.__name__
            
            return sync_wrapper
    
    return decorator


class SyncResult:
    """
    Mock Celery AsyncResult for synchronous execution.
    Provides compatible interface when Celery is disabled.
    """
    
    def __init__(self, result):
        self._result = result
        self.id = 'sync-result'
        self.status = 'SUCCESS'
    
    def get(self, timeout=None):
        """Get the result (already available for sync)"""
        return self._result
    
    def ready(self):
        """Check if task is complete (always True for sync)"""
        return True
    
    def successful(self):
        """Check if task succeeded (True for sync without exception)"""
        return True
    
    def failed(self):
        """Check if task failed"""
        return False
    
    @property
    def result(self):
        """Get the result value"""
        return self._result


# ============================================================
# Celery Beat Schedule (for periodic tasks)
# ============================================================

# Import crontab for schedule definitions
try:
    from celery.schedules import crontab
    CRONTAB_AVAILABLE = True
except ImportError:
    CRONTAB_AVAILABLE = False
    crontab = None

CELERY_BEAT_SCHEDULE = {}

if CRONTAB_AVAILABLE and crontab:
    CELERY_BEAT_SCHEDULE = {
        # Clean up expired VEP cache every day at 3am
        'cleanup-vep-cache': {
            'task': 'tasks.maintenance.cleanup_expired_cache',
            'schedule': crontab(hour=3, minute=0),
        },
        
        # Clean up old chat sessions weekly (Sunday at 4am)
        'cleanup-sessions': {
            'task': 'tasks.maintenance.cleanup_old_sessions',
            'schedule': crontab(day_of_week=0, hour=4, minute=0),
        },
        
        # Health check every 5 minutes
        'celery-health-check': {
            'task': 'tasks.maintenance.celery_health_check',
            'schedule': 300.0,  # Every 5 minutes
        },
    }

if celery_app:
    celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE


# ============================================================
# Status Check
# ============================================================

def get_celery_status():
    """Get Celery status and configuration"""
    return {
        'available': CELERY_AVAILABLE,
        'enabled': CELERY_ENABLED,
        'active': celery_app is not None,
        'broker_url': os.environ.get('CELERY_BROKER_URL', 'not_configured'),
        'result_backend': os.environ.get('CELERY_RESULT_BACKEND', 'not_configured'),
    }


if __name__ == '__main__':
    print("Celery Status:", get_celery_status())
    
    if celery_app:
        print("Starting Celery worker...")
        celery_app.start()
    else:
        print("Celery is not enabled. Set CELERY_ENABLED=true to activate.")



