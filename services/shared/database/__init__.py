"""
Database Package - SQLAlchemy models and database utilities
Supports both SQLite (development) and PostgreSQL (production)
"""
from .models import (
    db, 
    User, 
    AnalysisHistory, 
    SNPInfo, 
    Notification,
    GeneticRiskProfile,
    init_db, 
    create_admin_user
)

__all__ = [
    'db', 
    'User', 
    'AnalysisHistory', 
    'SNPInfo', 
    'Notification',
    'GeneticRiskProfile',
    'init_db', 
    'create_admin_user'
]
