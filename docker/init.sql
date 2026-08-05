-- #====================================================================
-- Schema Initialization Script for PostgreSQL
-- Predictive Maintenance Telemetry Pipeline
-- Dataset: AI4I 2020 Predictive Maintenance (Stephan Matzka, 2020)
-- =====================================================================

-- Create custom ENUM type for product quality variants
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'product_type_enum') THEN
        CREATE TYPE product_type_enum AS ENUM ('L', 'M', 'H');
    END IF;
END $$;

-- Drop table if it exists to ensure idempotent initialization during local setup
DROP TABLE IF EXISTS process_telemetry CASCADE;

-- Create 'process_telemetry' table
-- Stores 10,000 sequential manufacturing process cycles in exact chronological order
CREATE TABLE process_telemetry (
    udi INT PRIMARY KEY,                         -- Unique Data Identifier (1-10000) preserving cycle sequence
    product_id VARCHAR(20) NOT NULL,             -- Item variant prefix ('L'/'M'/'H') and serial number
    product_type product_type_enum NOT NULL,     -- Product quality variant ('L'=Low 50%, 'M'=Medium 30%, 'H'=High 20%)
    
    -- Physical Process Parameters & Sensor Telemetry
    air_temp_k NUMERIC(5, 2) NOT NULL,           -- Ambient air temperature in Kelvin (generated via random walk)
    process_temp_k NUMERIC(5, 2) NOT NULL,       -- Process temperature in Kelvin (coupled to air temperature + 10 K)
    rotational_speed_rpm INT NOT NULL,           -- Spindle rotational speed in RPM (derived from 2860 W power)
    torque_nm NUMERIC(5, 2) NOT NULL,             -- Spindle torque in Nm (normally distributed around 40 Nm)
    tool_wear_min INT NOT NULL,                  -- Cumulative tool wear in minutes (+2/3/5 min per L/M/H variant)
    
    -- Target Label & Independent Failure Modes
    machine_failure INT NOT NULL,                -- Global failure target (1 if any independent failure mode is triggered)
    twf INT DEFAULT 0,                           -- Tool Wear Failure flag (tool replacement/failure between 200-240 min)
    hdf INT DEFAULT 0,                           -- Heat Dissipation Failure flag (temp diff < 8.6 K and speed < 1380 rpm)
    pwf INT DEFAULT 0,                           -- Power Failure flag (process power < 3500 W or > 9000 W)
    osf INT DEFAULT 0,                           -- Overstrain Failure flag (tool wear * torque exceeds variant threshold)
    rnf INT DEFAULT 0,                           -- Random Failure flag (0.1% chance independent process failure)
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Record creation timestamp in PostgreSQL
);

-- Index to optimize sequential and time-series analytical queries ordered by UDI
CREATE INDEX idx_process_telemetry_udi ON process_telemetry(udi);