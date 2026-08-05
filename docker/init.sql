-- #==========================================
-- Schema Initialization Script for PostgreSQL
-- Data Engineering Setup
-- ==========================================

-- Create a custom ENUM type for product quality variants
-- Restricts machine quality variants exclusively to 'L' (Low), 'M' (Medium), or 'H' (High)
CREATE TYPE product_type_enum AS ENUM ('L', 'M', 'H');

-- Create 'machines' table
-- Acts as the dimension table storing static metadata about each machine
CREATE TABLE IF NOT EXISTS machines (
    product_id VARCHAR(20) PRIMARY KEY,          -- Unique identifier for each machine (e.g., 'M14860')
    product_type product_type_enum NOT NULL      -- Quality variant enforced by the ENUM type
);

-- Create 'failure_types' lookup table
-- Stores master data describing all specific types of machine failure
CREATE TABLE IF NOT EXISTS failure_types (
    failure_code VARCHAR(10) PRIMARY KEY,        -- Short identifier code (e.g., 'TWF', 'HDF')
    failure_name VARCHAR(100) NOT NULL,          -- Full descriptive name of the failure mode
    description TEXT                             -- Detailed explanation of failure cause
);

-- Pre-populate lookup data for 'failure_types'
-- Inserts standard failure definitions; skips insertion if codes already exist
INSERT INTO failure_types (failure_code, failure_name, description) VALUES
    ('TWF', 'Tool Wear Failure', 'Failure caused by tool wear over time'),
    ('HDF', 'Heat Dissipation Failure', 'Failure caused by excessive heat build-up'),
    ('PWF', 'Power Failure', 'Failure caused by power limits exceeding bounds'),
    ('OSF', 'Overstrain Failure', 'Failure caused by overstrain due to torque/time'),
    ('RNF', 'Random Failure', 'Unexplained or random process failure')
ON CONFLICT (failure_code) DO NOTHING;

-- Create 'maintenance_events' fact table
-- Captures specific failure occurrences alongside sensor metrics recorded at failure time
CREATE TABLE IF NOT EXISTS maintenance_events (
    event_id SERIAL PRIMARY KEY,                                              -- Auto-incrementing unique identifier
    product_id VARCHAR(20) REFERENCES machines(product_id) ON DELETE CASCADE, -- Foreign key to machines
    failure_code VARCHAR(10) REFERENCES failure_types(failure_code),          -- Foreign key to failure_types
    air_temp_k NUMERIC(5, 2),                                                 -- Air temperature in Kelvin
    process_temp_k NUMERIC(5, 2),                                             -- Process temperature in Kelvin
    rotational_speed_rpm INT,                                                 -- Rotational speed in RPM
    torque_nm NUMERIC(5, 2),                                                  -- Torque in Newton-meters
    tool_wear_min INT,                                                        -- Accumulated tool wear in minutes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP                            -- Automatic insertion timestamp
);