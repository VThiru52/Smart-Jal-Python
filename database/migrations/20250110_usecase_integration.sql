-- Migration: Integrate UseCase folder data
-- Date: 2025-01-10
-- Description: Add tables for Soils, Model Zones, MIT Zones, and Elevation Data

-- Soil Types Table
CREATE TABLE IF NOT EXISTS soil_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL DEFAULT 'Krishna',
    soil_code TEXT,
    soil_name TEXT,
    texture TEXT,
    drainage_class TEXT,
    area_ha FLOAT,
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model Zones Table (for groundwater modeling)
CREATE TABLE IF NOT EXISTS model_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL DEFAULT 'Krishna',
    zone_code TEXT,
    zone_name TEXT,
    description TEXT,
    model_type TEXT,
    area_ha FLOAT,
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- MIT Zones Table (intervention/monitoring zones)
CREATE TABLE IF NOT EXISTS mit_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL DEFAULT 'Krishna',
    mit_code TEXT,
    mit_name TEXT,
    category TEXT,
    priority_level INT,
    area_ha FLOAT,
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Elevation Data Table (processed from DEM)
CREATE TABLE IF NOT EXISTS elevation_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL DEFAULT 'Krishna',
    elevation_m FLOAT,
    slope_percent FLOAT,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Pumping/Extraction Data Table
CREATE TABLE IF NOT EXISTS pumping_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL DEFAULT 'Krishna',
    mandal TEXT,
    village TEXT,
    crop_type TEXT,
    area_acres FLOAT,
    pumping_hours_per_day FLOAT,
    pump_capacity_hp FLOAT,
    water_consumption_m3 FLOAT,
    season TEXT,
    year INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enhanced Villages table with UseCase data
ALTER TABLE villages ADD COLUMN IF NOT EXISTS village_code TEXT;
ALTER TABLE villages ADD COLUMN IF NOT EXISTS total_area_ha FLOAT;
ALTER TABLE villages ADD COLUMN IF NOT EXISTS census_code TEXT;
ALTER TABLE villages ADD COLUMN IF NOT EXISTS mandal TEXT;

-- Spatial indices for fast lookup
CREATE INDEX IF NOT EXISTS idx_soil_geom ON soil_types USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_model_zones_geom ON model_zones USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_mit_zones_geom ON mit_zones USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_elevation_geom ON elevation_data USING GIST (geom);

-- Additional indices
CREATE INDEX IF NOT EXISTS idx_soil_code ON soil_types (soil_code);
CREATE INDEX IF NOT EXISTS idx_model_zone_code ON model_zones (zone_code);
CREATE INDEX IF NOT EXISTS idx_mit_code ON mit_zones (mit_code);
CREATE INDEX IF NOT EXISTS idx_pumping_village ON pumping_data (village);
CREATE INDEX IF NOT EXISTS idx_pumping_year ON pumping_data (year);

-- Row Level Security
ALTER TABLE soil_types ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE mit_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE elevation_data ENABLE ROW LEVEL SECURITY;
ALTER TABLE pumping_data ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (to allow re-running migration)
DROP POLICY IF EXISTS "Public read access to soil_types" ON soil_types;
DROP POLICY IF EXISTS "Public read access to model_zones" ON model_zones;
DROP POLICY IF EXISTS "Public read access to mit_zones" ON mit_zones;
DROP POLICY IF EXISTS "Public read access to elevation_data" ON elevation_data;
DROP POLICY IF EXISTS "Public read access to pumping_data" ON pumping_data;

-- Create public read access policies for all new tables
CREATE POLICY "Public read access to soil_types" ON soil_types
    FOR SELECT USING (true);

CREATE POLICY "Public read access to model_zones" ON model_zones
    FOR SELECT USING (true);

CREATE POLICY "Public read access to mit_zones" ON mit_zones
    FOR SELECT USING (true);

CREATE POLICY "Public read access to elevation_data" ON elevation_data
    FOR SELECT USING (true);

CREATE POLICY "Public read access to pumping_data" ON pumping_data
    FOR SELECT USING (true);

