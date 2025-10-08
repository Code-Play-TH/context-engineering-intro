-- Initialize database with extensions and settings

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For JSONB indexing

-- Set timezone
SET timezone = 'UTC';

-- Create application user (optional, for better security)
-- Uncomment for production
-- CREATE USER kol_app WITH PASSWORD 'your_secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE kol_management TO kol_app;

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Database initialized successfully with extensions: uuid-ossp, pg_trgm, btree_gin';
END $$;
