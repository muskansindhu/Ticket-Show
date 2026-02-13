-- Ticket Show Database Initialization Script
-- This script creates all necessary schemas, tables, and sample data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ==================== AUTH SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS auth;

CREATE TABLE IF NOT EXISTS auth.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    role VARCHAR(10) NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN', 'USER')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_role ON auth.users(role);


-- ==================== SAMPLE DATA ====================

-- Insert sample regular user (password: User123!)
INSERT INTO auth.users (email, password_hash, username, role) VALUES
('user@ticketshow.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS6NzXJqe', 'Regular User', 'USER')
ON CONFLICT (email) DO NOTHING;


-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA auth TO ticketshow;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO ticketshow;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO ticketshow;

