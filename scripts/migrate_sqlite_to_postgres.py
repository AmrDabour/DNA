#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
Migrates data from SQLite database to PostgreSQL

Usage:
    python scripts/migrate_sqlite_to_postgres.py

Environment Variables:
    SQLITE_PATH - Path to SQLite database (default: instance/genovaai.db)
    DATABASE_URL - PostgreSQL connection URL
"""
import os
import sys
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import models
from database.models import db, User, AnalysisHistory, SNPInfo, Notification, GeneticRiskProfile


def get_sqlite_engine():
    """Create SQLite engine for source database"""
    sqlite_path = os.environ.get('SQLITE_PATH', 'instance/genovaai.db')
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at: {sqlite_path}")
        sys.exit(1)
    return create_engine(f'sqlite:///{sqlite_path}')


def get_postgres_engine():
    """Create PostgreSQL engine for target database"""
    postgres_url = os.environ.get('DATABASE_URL')
    if not postgres_url:
        # Build from components
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        port = os.environ.get('POSTGRES_PORT', '5432')
        db_name = os.environ.get('POSTGRES_DB', 'genovaai')
        user = os.environ.get('POSTGRES_USER', 'genovaai_user')
        password = os.environ.get('POSTGRES_PASSWORD', 'genovaai_secure_password_2024')
        postgres_url = f'postgresql://{user}:{password}@{host}:{port}/{db_name}'
    
    return create_engine(postgres_url)


def migrate_table(sqlite_session, postgres_session, model, table_name):
    """
    Migrate a single table from SQLite to PostgreSQL
    
    Args:
        sqlite_session: SQLite session
        postgres_session: PostgreSQL session
        model: SQLAlchemy model class
        table_name: Name of the table
    """
    print(f"\n📋 Migrating {table_name}...")
    
    # Get all records from SQLite
    records = sqlite_session.query(model).all()
    count = len(records)
    
    if count == 0:
        print(f"   ⏭️  No records to migrate")
        return 0
    
    print(f"   Found {count} records")
    
    migrated = 0
    errors = 0
    
    for record in records:
        try:
            # Create a new instance with the same data
            data = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                data[column.name] = value
            
            new_record = model(**data)
            postgres_session.merge(new_record)
            migrated += 1
            
            # Commit in batches of 100
            if migrated % 100 == 0:
                postgres_session.commit()
                print(f"   Migrated {migrated}/{count} records...")
                
        except Exception as e:
            errors += 1
            print(f"   ⚠️  Error migrating record {record.id}: {e}")
    
    # Final commit
    postgres_session.commit()
    
    print(f"   ✅ Migrated {migrated} records ({errors} errors)")
    return migrated


def reset_sequences(postgres_engine):
    """Reset PostgreSQL sequences to max ID + 1"""
    print("\n🔢 Resetting sequences...")
    
    tables = ['users', 'analysis_history', 'snp_info', 'notifications', 'genetic_risk_profiles']
    
    with postgres_engine.connect() as conn:
        for table in tables:
            try:
                # Get max ID
                result = conn.execute(text(f"SELECT MAX(id) FROM {table}"))
                max_id = result.scalar() or 0
                
                # Reset sequence
                seq_name = f"{table}_id_seq"
                conn.execute(text(f"SELECT setval('{seq_name}', {max_id + 1}, false)"))
                conn.commit()
                
                print(f"   ✅ {table}: sequence reset to {max_id + 1}")
            except Exception as e:
                print(f"   ⚠️  {table}: {e}")


def validate_migration(sqlite_session, postgres_session):
    """Validate that migration was successful"""
    print("\n🔍 Validating migration...")
    
    models = [
        (User, 'users'),
        (AnalysisHistory, 'analysis_history'),
        (SNPInfo, 'snp_info'),
        (Notification, 'notifications'),
        (GeneticRiskProfile, 'genetic_risk_profiles')
    ]
    
    all_valid = True
    
    for model, name in models:
        sqlite_count = sqlite_session.query(model).count()
        postgres_count = postgres_session.query(model).count()
        
        status = "✅" if sqlite_count == postgres_count else "❌"
        print(f"   {status} {name}: SQLite={sqlite_count}, PostgreSQL={postgres_count}")
        
        if sqlite_count != postgres_count:
            all_valid = False
    
    return all_valid


def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 GenovaAI Database Migration: SQLite → PostgreSQL")
    print("=" * 60)
    
    # Create engines
    print("\n📡 Connecting to databases...")
    sqlite_engine = get_sqlite_engine()
    postgres_engine = get_postgres_engine()
    
    print("   ✅ SQLite connection established")
    print("   ✅ PostgreSQL connection established")
    
    # Create sessions
    SqliteSession = sessionmaker(bind=sqlite_engine)
    PostgresSession = sessionmaker(bind=postgres_engine)
    
    sqlite_session = SqliteSession()
    postgres_session = PostgresSession()
    
    try:
        # Create tables in PostgreSQL (if not exists)
        print("\n📊 Creating PostgreSQL tables...")
        db.metadata.create_all(postgres_engine)
        print("   ✅ Tables created/verified")
        
        # Migrate each table
        models = [
            (User, 'users'),
            (SNPInfo, 'snp_info'),  # Migrate SNP info before analysis history
            (AnalysisHistory, 'analysis_history'),
            (Notification, 'notifications'),
            (GeneticRiskProfile, 'genetic_risk_profiles')
        ]
        
        total_migrated = 0
        for model, name in models:
            migrated = migrate_table(sqlite_session, postgres_session, model, name)
            total_migrated += migrated
        
        # Reset sequences
        reset_sequences(postgres_engine)
        
        # Validate
        is_valid = validate_migration(sqlite_session, postgres_session)
        
        print("\n" + "=" * 60)
        if is_valid:
            print(f"✅ Migration completed successfully!")
            print(f"   Total records migrated: {total_migrated}")
        else:
            print(f"⚠️  Migration completed with warnings")
            print(f"   Please review the counts above")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        postgres_session.rollback()
        raise
    finally:
        sqlite_session.close()
        postgres_session.close()


if __name__ == '__main__':
    main()
