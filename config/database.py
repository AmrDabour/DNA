"""
Database Configuration Module
PostgreSQL connection handling and utilities
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time


def get_database_url():
    """
    Get database URL with fallback logic.
    Priority: DATABASE_URL env var > PostgreSQL components > SQLite fallback
    """
    # Check for explicit DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Handle Heroku-style postgres:// URLs
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Build from components
    postgres_host = os.environ.get('POSTGRES_HOST')
    if postgres_host:
        postgres_port = os.environ.get('POSTGRES_PORT', '5432')
        postgres_db = os.environ.get('POSTGRES_DB', 'genovaai')
        postgres_user = os.environ.get('POSTGRES_USER', 'genovaai_user')
        postgres_password = os.environ.get('POSTGRES_PASSWORD', 'genovaai_secure_password_2024')
        
        return f'postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}'
    
    # Fallback to SQLite for local development
    return 'sqlite:///genovaai.db'


def wait_for_database(max_retries=30, retry_interval=2):
    """
    Wait for database to be available (useful in Docker/K8s environments).
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds between retries
        
    Returns:
        bool: True if database is available, False otherwise
    """
    database_url = get_database_url()
    
    # Skip waiting for SQLite
    if 'sqlite' in database_url:
        return True
    
    print(f"⏳ Waiting for database connection...")
    
    for attempt in range(max_retries):
        try:
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"✅ Database connection established!")
            return True
        except OperationalError as e:
            print(f"⏳ Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(retry_interval)
    
    print(f"❌ Failed to connect to database after {max_retries} attempts")
    return False


def get_engine_options():
    """
    Get SQLAlchemy engine options based on database type.
    
    Returns:
        dict: Engine configuration options
    """
    database_url = get_database_url()
    
    if 'postgresql' in database_url:
        return {
            'pool_pre_ping': True,
            'pool_recycle': 300,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
            'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
        }
    else:
        # SQLite options
        return {
            'pool_pre_ping': True,
        }


def is_postgres():
    """Check if using PostgreSQL"""
    return 'postgresql' in get_database_url()


def is_sqlite():
    """Check if using SQLite"""
    return 'sqlite' in get_database_url()
