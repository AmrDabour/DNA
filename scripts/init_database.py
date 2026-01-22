#!/usr/bin/env python
"""Initialize database tables"""
import sys
sys.path.insert(0, '/app')

from app import app, db
from database import create_admin_user

with app.app_context():
    print("🔄 Creating database tables...")
    db.create_all()
    print("✅ Database tables created!")
    
    print("👤 Creating admin user...")
    create_admin_user()
    print("✅ Admin user ready!")
    
    # List all tables
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"📊 Tables in database: {', '.join(tables)}")
    
    print("\n✅ Database initialization complete!")


