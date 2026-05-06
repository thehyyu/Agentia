-- Create the langfuse database if it doesn't exist.
-- PostgreSQL doesn't support IF NOT EXISTS for CREATE DATABASE,
-- so we check pg_database first.
SELECT 'CREATE DATABASE langfuse OWNER agentia'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'langfuse')\gexec
