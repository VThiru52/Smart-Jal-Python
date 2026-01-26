-- Migrate existing village data from JSONB fields to new columns
-- This extracts data from soil_profile, elevation_data, and total_area_ha

-- 1. Extract soil data from soil_profile JSONB
UPDATE villages 
SET 
    soil_type = soil_profile->>'soil_name',
    soil_texture = soil_profile->>'texture',
    soil_drainage = soil_profile->>'drainage_class'
WHERE soil_profile IS NOT NULL 
  AND (soil_type IS NULL OR soil_texture IS NULL OR soil_drainage IS NULL);

-- 2. Extract elevation from elevation_data JSONB
UPDATE villages 
SET 
    elevation_m = (elevation_data->>'elevation_m')::FLOAT
WHERE elevation_data IS NOT NULL 
  AND elevation_m IS NULL;

-- 3. Copy total_area_ha to land_area_ha if land_area_ha is NULL
UPDATE villages 
SET 
    land_area_ha = total_area_ha
WHERE total_area_ha IS NOT NULL 
  AND land_area_ha IS NULL;

-- 4. Calculate agricultural_area_ha from land_area_ha if it's 0 or NULL
-- Estimate 70% of total land as agricultural (typical for Krishna district)
UPDATE villages 
SET 
    agricultural_area_ha = ROUND((land_area_ha * 0.7)::NUMERIC, 2)
WHERE land_area_ha IS NOT NULL 
  AND land_area_ha > 0
  AND (agricultural_area_ha IS NULL OR agricultural_area_ha = 0);

-- Show migration statistics
SELECT 
    COUNT(*) as total_villages,
    COUNT(soil_type) as with_soil_type,
    COUNT(elevation_m) as with_elevation,
    COUNT(land_area_ha) as with_land_area,
    COUNT(agricultural_area_ha) as with_agri_area,
    COUNT(water_consumption_m3) as with_water_consumption
FROM villages;
