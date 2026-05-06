-- CitaMonitor database initialization
-- This runs once on first PostgreSQL start

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- fuzzy text search

-- Indexes will be created by SQLAlchemy on startup.
-- This file can be used for seed data or additional setup.

-- Create a read-only reporting user (optional)
-- CREATE USER citamonitor_ro WITH PASSWORD 'readonly_password';
-- GRANT CONNECT ON DATABASE citamonitor TO citamonitor_ro;
-- GRANT USAGE ON SCHEMA public TO citamonitor_ro;
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO citamonitor_ro;

SELECT 'CitaMonitor database initialized' AS status;
