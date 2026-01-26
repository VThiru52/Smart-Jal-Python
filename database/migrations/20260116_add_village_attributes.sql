-- Add comprehensive village attributes for evaluation
-- Migration: Add village land, soil, and consumption data
-- Date: 2026-01-16

-- Add new columns to villages table
ALTER TABLE villages 
ADD COLUMN IF NOT EXISTS land_area_ha FLOAT,
ADD COLUMN IF NOT EXISTS agricultural_area_ha FLOAT,
ADD COLUMN IF NOT EXISTS soil_type TEXT,
ADD COLUMN IF NOT EXISTS soil_texture TEXT,
ADD COLUMN IF NOT EXISTS soil_drainage TEXT,
ADD COLUMN IF NOT EXISTS elevation_m FLOAT,
ADD COLUMN IF NOT EXISTS water_consumption_m3 FLOAT,
ADD COLUMN IF NOT EXISTS agricultural_consumption_m3 FLOAT,
ADD COLUMN IF NOT EXISTS latitude FLOAT,
ADD COLUMN IF NOT EXISTS longitude FLOAT;

-- Add comments for documentation
COMMENT ON COLUMN villages.land_area_ha IS 'Total land area of village in hectares';
COMMENT ON COLUMN villages.agricultural_area_ha IS 'Agricultural land area in hectares';
COMMENT ON COLUMN villages.soil_type IS 'Soil type classification (e.g., Black Cotton Soil, Red Sandy Soil)';
COMMENT ON COLUMN villages.soil_texture IS 'Soil texture (e.g., Sandy Loam, Clay)';
COMMENT ON COLUMN villages.soil_drainage IS 'Drainage classification (e.g., Well Drained, Moderately Drained)';
COMMENT ON COLUMN villages.elevation_m IS 'Elevation above sea level in meters';
COMMENT ON COLUMN villages.water_consumption_m3 IS 'Total annual water consumption in cubic meters';
COMMENT ON COLUMN villages.agricultural_consumption_m3 IS 'Agricultural water consumption in cubic meters';
COMMENT ON COLUMN villages.latitude IS 'Latitude coordinate (decimal degrees)';
COMMENT ON COLUMN villages.longitude IS 'Longitude coordinate (decimal degrees)';

-- Create index for spatial queries on lat/lon
CREATE INDEX IF NOT EXISTS idx_villages_latlon ON villages (latitude, longitude);

-- Update existing villages to calculate centroid lat/lon if they have geometry
UPDATE villages 
SET 
    latitude = ST_Y(ST_Centroid(centroid)),
    longitude = ST_X(ST_Centroid(centroid))
WHERE centroid IS NOT NULL AND latitude IS NULL;
