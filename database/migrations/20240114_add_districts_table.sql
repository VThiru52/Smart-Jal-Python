-- Enable PostGIS extension (ensure it's available)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Drop existing table if any to ensure clean schema
DROP TABLE IF EXISTS districts CASCADE;

-- Create districts table
CREATE TABLE districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for spatial queries
CREATE INDEX IF NOT EXISTS idx_districts_boundary ON districts USING GIST (boundary);

-- RLS
ALTER TABLE districts ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can read districts
CREATE POLICY "Public read access to districts" ON districts
    FOR SELECT USING (true);
