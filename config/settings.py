"""
Application Configuration Module
Environment-based configuration for GenovaAI
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration class"""
    
    # Flask
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'genetic_prediction_app_secret_key')
    
    # Database - Default to PostgreSQL in production
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Enable connection health checks
        'pool_recycle': 300,    # Recycle connections after 5 minutes
    }
    
    # Upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_DIR', './uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Admin defaults
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@genovaai.com')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    @staticmethod
    def init_app(app):
        """Initialize application with this config"""
        pass


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
    # Use SQLite for local development if no DATABASE_URL is set
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///genovaai_dev.db'
    )
    
    # Development-specific pool settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': True,  # Log SQL queries in development
    }


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    
    # Use in-memory SQLite for tests or separate test database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'TEST_DATABASE_URL',
        'sqlite:///:memory:'
    )


class ProductionConfig(Config):
    """Production configuration with PostgreSQL"""
    DEBUG = False
    
    # PostgreSQL Configuration
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'postgres')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '5432')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'genovaai')
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'genovaai_user')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'genovaai_secure_password_2024')
    
    # Build DATABASE_URL from components or use provided URL
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.environ.get(
            'DATABASE_URL',
            f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )
    
    # Production connection pool settings
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '10'))
    DB_MAX_OVERFLOW = int(os.environ.get('DB_MAX_OVERFLOW', '20'))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', '30'))
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
        'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '20')),
        'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
    }
    
    @staticmethod
    def init_app(app):
        """Production-specific initialization"""
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        
        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)


class DockerConfig(ProductionConfig):
    """Docker-specific configuration"""
    
    @staticmethod
    def init_app(app):
        ProductionConfig.init_app(app)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get configuration based on FLASK_ENV environment variable"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
