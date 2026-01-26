-- Migration: Insert Krishna District
-- Date: 2025-01-15
-- Description: Insert Krishna district data into districts table
-- This ensures the districts table has the required district for the application
-- 
-- Prerequisites: Run 20240114_add_districts_table.sql first to create the table structure

-- Ensure PostGIS extension is enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Ensure districts table exists (safe check - won't fail if already exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'districts') THEN
        CREATE TABLE districts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name TEXT UNIQUE NOT NULL,
            boundary GEOMETRY(MultiPolygon, 4326),
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        
        -- Create index
        CREATE INDEX idx_districts_boundary ON districts USING GIST (boundary);
        
        -- Enable RLS
        ALTER TABLE districts ENABLE ROW LEVEL SECURITY;
        
        -- Create policy
        CREATE POLICY "Public read access to districts" ON districts
            FOR SELECT USING (true);
    END IF;
END $$;

-- Insert Krishna district if it doesn't exist
-- Using approximate boundary coordinates for Krishna District, Andhra Pradesh
-- Coordinates: Latitude 15.7-17.2, Longitude 80.0-81.6
INSERT INTO districts (name, boundary, created_at, updated_at)
VALUES (
    'Krishna',
    ST_SetSRID(
        ST_GeomFromText(
            'MULTIPOLYGON(((
                80.0 15.7,
                81.6 15.7,
                81.6 17.2,
                80.0 17.2,
                80.0 15.7
            )))'
        ),
        4326
    ),
    NOW(),
    NOW()
)
ON CONFLICT (name) DO UPDATE 
SET 
    updated_at = NOW(),
    boundary = EXCLUDED.boundary;

-- Verify insertion
DO $$
DECLARE
    district_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO district_count FROM districts WHERE name = 'Krishna';
    IF district_count = 0 THEN
        RAISE EXCEPTION 'Failed to insert Krishna district';
    END IF;
    RAISE NOTICE 'Krishna district inserted successfully';
END $$;

-- Add comment
COMMENT ON TABLE districts IS 'Districts table containing all administrative districts in the system';
COMMENT ON COLUMN districts.name IS 'Unique district name (e.g., Krishna)';
COMMENT ON COLUMN districts.boundary IS 'PostGIS MultiPolygon geometry representing district boundary';
