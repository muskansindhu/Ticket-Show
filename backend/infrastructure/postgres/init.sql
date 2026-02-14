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

-- ==================== EVENTS SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS events;

-- Shows table
CREATE TABLE IF NOT EXISTS events.shows (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    language VARCHAR(50),
    rating VARCHAR(10),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Venues table
CREATE TABLE IF NOT EXISTS events.venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(500) NOT NULL,
    opening_time TIME NOT NULL,
    closing_time TIME NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (closing_time > opening_time)
);

-- Screens table
CREATE TABLE IF NOT EXISTS events.screens (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES events.venues(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_screens_venue ON events.screens(venue_id);

-- Schedules table with exclusion constraint for overlapping prevention
CREATE TABLE IF NOT EXISTS events.schedules (
    id SERIAL PRIMARY KEY,
    show_id INTEGER NOT NULL REFERENCES events.shows(id) ON DELETE CASCADE,
    screen_id INTEGER NOT NULL REFERENCES events.screens(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    created_by_admin_id INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CHECK (end_time > start_time),
    EXCLUDE USING gist (
        screen_id WITH =,
        tstzrange(start_time, end_time) WITH &&
    )
);

CREATE INDEX idx_schedules_show ON events.schedules(show_id);
CREATE INDEX idx_schedules_screen ON events.schedules(screen_id);
CREATE INDEX idx_schedules_start_time ON events.schedules(start_time);

-- Seats table
CREATE TABLE IF NOT EXISTS events.seats (
    id SERIAL PRIMARY KEY,
    screen_id INTEGER NOT NULL REFERENCES events.screens(id) ON DELETE CASCADE,
    seat_number VARCHAR(10) NOT NULL,
    row_number VARCHAR(5) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(screen_id, seat_number)
);

CREATE INDEX idx_seats_screen ON events.seats(screen_id);



-- ==================== SAMPLE DATA ====================

-- Insert sample admin user (password: Admin123!)
INSERT INTO auth.users (email, password_hash, username, role) VALUES
('admin@ticketshow.com', '$2b$12$UKh.ak8mOPBQc8YTfbSfm.oOb9ccGZ0nszJutSDDgLFyFO7coTScC', 'Admin User', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- Insert sample regular user (password: User123!)
INSERT INTO auth.users (email, password_hash, username, role) VALUES
('user@ticketshow.com', '$2b$12$ij4.6bmZ7LoCuPRLl0z/pelxfBDBTAAK95MMHTYdtjzQWb.vYUxry', 'Regular User', 'USER')
ON CONFLICT (email) DO NOTHING;

-- Insert sample shows
INSERT INTO events.shows (title, description, duration_minutes, language, rating) VALUES
('Inception', 'A skilled thief enters dreams to steal secrets.', 148, 'English', 'PG-13'),
('The Dark Knight', 'Batman faces the Joker in Gotham City.', 152, 'English', 'PG-13'),
('Interstellar', 'A team travels through a wormhole in space.', 169, 'English', 'PG-13'),
('Dunkirk', 'Allied soldiers are evacuated during WWII.', 106, 'English', 'PG-13'),
('Tenet', 'A secret agent manipulates time to prevent disaster.', 150, 'English', 'PG-13')
ON CONFLICT DO NOTHING;


-- Insert sample venues
INSERT INTO events.venues (name, location, opening_time, closing_time) VALUES
('Cineplex Downtown', '123 Main St, Downtown', '09:00:00', '23:00:00'),
('IMAX Theater', '456 Broadway Ave', '10:00:00', '22:00:00'),
('Multiplex Mall', '789 Shopping Center', '08:00:00', '23:59:59')
ON CONFLICT DO NOTHING;

-- Insert sample screens
INSERT INTO events.screens (venue_id, name, capacity) VALUES
(1, 'Screen 1', 100),
(1, 'Screen 2', 80),
(2, 'IMAX Screen', 200),
(3, 'Screen A', 120),
(3, 'Screen B', 90)
ON CONFLICT DO NOTHING;

-- Insert sample seats for Screen 1 (100 seats)
DO $$
DECLARE
    screen_id_var INTEGER := 1;
    i INTEGER;
BEGIN
    FOR i IN 1..100 LOOP
        INSERT INTO events.seats (screen_id, seat_number, row_number)
        VALUES (
            screen_id_var,
            'S' || LPAD(i::TEXT, 3, '0'),
            'R' || LPAD(((i - 1) / 10 + 1)::TEXT, 2, '0')
        )
        ON CONFLICT (screen_id, seat_number) DO NOTHING;
    END LOOP;
END $$;



-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA auth TO ticketshow;
GRANT ALL PRIVILEGES ON SCHEMA events TO ticketshow;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA auth TO ticketshow;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA events TO ticketshow;

GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA auth TO ticketshow;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA events TO ticketshow;
