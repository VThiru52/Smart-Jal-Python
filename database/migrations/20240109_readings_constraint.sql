-- Migration to add unique constraint for historical ingestion
-- This ensures that we don't have multiple readings for the same piezometer on the same day
ALTER TABLE readings 
ADD CONSTRAINT unique_piezometer_reading_date UNIQUE (piezometer_id, reading_date);

-- Ensure we have indices for common queries
CREATE INDEX IF NOT EXISTS idx_readings_water_level ON readings (water_level_mbgl);
