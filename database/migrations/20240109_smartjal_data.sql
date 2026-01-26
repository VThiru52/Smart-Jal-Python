-- Migration to add bore_wells and update aquifers for SmartJal data
-- Enable PostGIS if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Update Aquifers table to match shapefile if necessary
-- Existing: code, type, permeability_factor, boundary
-- Shapefile: AQUI_CODE, Geo_Class
-- We will keep the existing structure but ensure 'code' maps to 'AQUI_CODE' and 'type' to 'Geo_Class'.

-- 2. New Bore Wells Table for the massive 88k dataset
CREATE TABLE IF NOT EXISTS bore_wells (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    mandal TEXT,
    village TEXT,
    well_status TEXT, -- Working/Not Working
    well_type TEXT,
    depth_m FLOAT,
    pump_capacity_hp FLOAT,
    crop_type TEXT,
    irrigation_type TEXT,
    land_extent_acres FLOAT,
    geom GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for spatial queries
CREATE INDEX IF NOT EXISTS idx_bore_wells_geom ON bore_wells USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_bore_wells_village ON bore_wells (village);
CREATE INDEX IF NOT EXISTS idx_bore_wells_mandal ON bore_wells (mandal);
