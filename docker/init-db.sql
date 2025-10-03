-- Database initialization script for KOL Management System
-- Creates extensions and sets up initial configuration
-- Note: Database is already created via Docker environment variables

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by Alembic migrations, but we prepare the extensions

-- Set timezone
SET timezone = 'UTC';

-- Create schema for analytics if needed
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA analytics TO koluser;