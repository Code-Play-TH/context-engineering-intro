-- Factory ERP Database Initialization Script
-- This script runs when PostgreSQL container is first created

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Set timezone
SET timezone = 'UTC';

-- Create database user if it doesn't exist (for development)
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE rolname = 'factory_erp_user'
   ) THEN
      CREATE USER factory_erp_user WITH PASSWORD 'factory_erp_password';
   END IF;
END
$do$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE factory_erp TO factory_erp_user;

-- Create audit schema for tracking changes
CREATE SCHEMA IF NOT EXISTS audit;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    table_name VARCHAR(100) NOT NULL,
    record_id VARCHAR(100) NOT NULL,
    operation VARCHAR(10) NOT NULL, -- INSERT, UPDATE, DELETE
    old_values JSONB,
    new_values JSONB,
    changed_by UUID,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes on audit table
CREATE INDEX IF NOT EXISTS idx_audit_log_table_record ON audit.audit_log(table_name, record_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit.audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_by ON audit.audit_log(changed_by);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit.audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log(
            table_name,
            record_id,
            operation,
            old_values,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            OLD.id::text,
            TG_OP,
            row_to_json(OLD),
            NOW()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log(
            table_name,
            record_id,
            operation,
            old_values,
            new_values,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            NEW.id::text,
            TG_OP,
            row_to_json(OLD),
            row_to_json(NEW),
            NOW()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log(
            table_name,
            record_id,
            operation,
            new_values,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            NEW.id::text,
            TG_OP,
            row_to_json(NEW),
            NOW()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create function to generate unique identifiers
CREATE OR REPLACE FUNCTION generate_unique_id(prefix TEXT DEFAULT '')
RETURNS TEXT AS $$
DECLARE
    timestamp_part TEXT;
    random_part TEXT;
BEGIN
    timestamp_part := EXTRACT(EPOCH FROM NOW())::TEXT;
    random_part := UPPER(SUBSTRING(gen_random_uuid()::TEXT FROM 1 FOR 8));
    
    IF prefix = '' THEN
        RETURN timestamp_part || '-' || random_part;
    ELSE
        RETURN prefix || '-' || timestamp_part || '-' || random_part;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create database performance monitoring view
CREATE OR REPLACE VIEW audit.database_stats AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
ORDER BY schemaname, tablename, attname;

-- Create table size monitoring view
CREATE OR REPLACE VIEW audit.table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
ORDER BY size_bytes DESC;

-- Set up default privileges for audit schema
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON TABLES TO factory_erp_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT ALL ON SEQUENCES TO factory_erp_user;

-- Cleanup old audit logs (keep only 90 days)
CREATE OR REPLACE FUNCTION audit.cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit.audit_log 
    WHERE changed_at < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job to cleanup old audit logs (requires pg_cron extension)
-- This is optional and requires pg_cron extension to be installed
-- SELECT cron.schedule('cleanup-audit-logs', '0 2 * * *', 'SELECT audit.cleanup_old_audit_logs();');

-- Log initialization completion
INSERT INTO audit.audit_log(
    table_name,
    record_id,
    operation,
    new_values
) VALUES (
    'system',
    'initialization',
    'INIT',
    '{"message": "Database initialization completed successfully", "version": "1.0.0"}'
);

-- Display completion message
DO $$
BEGIN
    RAISE NOTICE 'Factory ERP Database initialization completed successfully!';
END $$;