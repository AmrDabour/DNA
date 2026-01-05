-- ============================================================
-- GenovaAI PostgreSQL Initialization Script
-- This script runs automatically when the container starts
-- ============================================================

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search

-- Set timezone
SET timezone = 'UTC';

-- Create indexes for better performance (will be created by SQLAlchemy,
-- but we add some optimization indexes here)

-- Note: Tables will be created by SQLAlchemy/Alembic
-- This script is for extensions and initial optimizations

-- Grant privileges (if using different roles)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO genovaai_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO genovaai_user;

-- Create a read-only user for reporting (optional)
-- CREATE USER genovaai_readonly WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE genovaai TO genovaai_readonly;
-- GRANT USAGE ON SCHEMA public TO genovaai_readonly;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO genovaai_readonly;

-- Log completion
DO $$
BEGIN
    RAISE NOTICE 'GenovaAI database initialization complete!';
END $$;
