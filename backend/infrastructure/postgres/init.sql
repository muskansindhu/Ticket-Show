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
    city VARCHAR(100),
    role VARCHAR(10) NOT NULL DEFAULT 'USER' CHECK (role IN ('ADMIN', 'USER')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON auth.users(email);
CREATE INDEX idx_users_role ON auth.users(role);
CREATE INDEX idx_users_city ON auth.users(city);

CREATE TABLE IF NOT EXISTS auth.wallets (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
    current_amount DECIMAL(12, 2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS auth.wallet_transactions (
    id SERIAL PRIMARY KEY,
    wallet_id INTEGER NOT NULL REFERENCES auth.wallets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    amount DECIMAL(12, 2) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('REFUND', 'DEBIT')),
    description VARCHAR(500) NOT NULL,
    reference_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_wallets_user_id ON auth.wallets(user_id);
CREATE INDEX idx_wallet_transactions_user_id ON auth.wallet_transactions(user_id);
CREATE INDEX idx_wallet_transactions_ref ON auth.wallet_transactions(reference_id);

-- ==================== EVENTS SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS events;

CREATE TABLE IF NOT EXISTS events.shows (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'CANCELLED')),
    description TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
    price INTEGER NOT NULL,
    language VARCHAR(50),
    rating VARCHAR(10),
    poster_url VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Venues table
CREATE TABLE IF NOT EXISTS events.venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'INACTIVE')),
    location VARCHAR(500) NOT NULL,
    city VARCHAR(100) NOT NULL,
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
    locked_until TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(screen_id, seat_number)
);

CREATE INDEX idx_seats_screen ON events.seats(screen_id);

-- ==================== BOOKINGS SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS bookings;

CREATE TABLE IF NOT EXISTS bookings.bookings (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    schedule_id INTEGER NOT NULL,
    seat_ids INTEGER[] NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    correlation_id VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bookings_user ON bookings.bookings(user_id);
CREATE INDEX idx_bookings_event ON bookings.bookings(schedule_id);
CREATE INDEX idx_bookings_status ON bookings.bookings(status);
CREATE INDEX idx_bookings_idempotency ON bookings.bookings(idempotency_key);
CREATE INDEX idx_bookings_correlation ON bookings.bookings(correlation_id);

-- ==================== PAYMENTS SCHEMA ====================
CREATE SCHEMA IF NOT EXISTS payments;

CREATE TABLE IF NOT EXISTS payments.payments (
    id SERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    booking_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    payment_method VARCHAR(20) NOT NULL,
    transaction_id VARCHAR(255),
    correlation_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_payments_booking ON payments.payments(booking_id);
CREATE INDEX idx_payments_user ON payments.payments(user_id);
CREATE INDEX idx_payments_status ON payments.payments(status);
CREATE INDEX idx_payments_idempotency ON payments.payments(idempotency_key);




-- ==================== SAMPLE DATA ====================

-- Insert sample admin user (password: Admin123!)
INSERT INTO auth.users (email, password_hash, username, role) VALUES
('admin@ticketshow.com', '$2b$12$UKh.ak8mOPBQc8YTfbSfm.oOb9ccGZ0nszJutSDDgLFyFO7coTScC', 'Admin User', 'ADMIN')
ON CONFLICT (email) DO NOTHING;

-- Insert sample regular user (password: User123!)
INSERT INTO auth.users (email, password_hash, username, role) VALUES
('user@ticketshow.com', '$2b$12$ij4.6bmZ7LoCuPRLl0z/pelxfBDBTAAK95MMHTYdtjzQWb.vYUxry', 'Regular User', 'USER')
ON CONFLICT (email) DO NOTHING;

INSERT INTO auth.wallets (user_id, current_amount)
SELECT id, CASE WHEN email = 'user@ticketshow.com' THEN 5000.00 ELSE 0.00 END FROM auth.users
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO auth.wallet_transactions (wallet_id, user_id, amount, transaction_type, description, reference_id)
SELECT w.id, u.id, 5000.00, 'REFUND', 'Welcome bonus refund added to wallet', 'ref-welcome-bonus'
FROM auth.users u JOIN auth.wallets w ON u.id = w.user_id
WHERE u.email = 'user@ticketshow.com'
ON CONFLICT (reference_id) DO NOTHING;

INSERT INTO events.shows (title, description, duration_minutes, price, language, rating, status) VALUES
('Inception', 'A skilled thief enters dreams to steal secrets.', 148, 350, 'English', 'PG-13', 'ACTIVE'),
('The Dark Knight', 'Batman faces the Joker in Gotham City.', 152, 400, 'English', 'PG-13', 'ACTIVE'),
('Interstellar', 'A team travels through a wormhole in space.', 169, 450, 'English', 'PG-13', 'ACTIVE'),
('Dunkirk', 'Allied soldiers are evacuated during WWII.', 106, 300, 'English', 'PG-13', 'ACTIVE'),
('Tenet', 'A secret agent manipulates time to prevent disaster.', 150, 375, 'English', 'PG-13', 'ACTIVE'),
('Avatar (Cancelled)', 'A marine on an alien planet.', 162, 500, 'English', 'PG-13', 'CANCELLED')
ON CONFLICT DO NOTHING;


-- Insert sample venues
INSERT INTO events.venues (name, location, city, opening_time, closing_time, status) VALUES
('Cineplex Downtown', '123 Main St, Downtown', 'Toronto', '09:00:00', '23:00:00', 'ACTIVE'),
('IMAX Theater', '456 Broadway Ave', 'Toronto', '10:00:00', '22:00:00', 'ACTIVE'),
('Multiplex Mall', '789 Shopping Center', 'Vancouver', '08:00:00', '23:59:59', 'ACTIVE'),
('Old Town Cinema (Inactive)', '321 Retro Blvd', 'Calgary', '10:00:00', '20:00:00', 'INACTIVE')
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
