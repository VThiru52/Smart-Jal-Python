-- Create pumping_data table
CREATE TABLE IF NOT EXISTS pumping_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    village TEXT,
    year INT,
    season TEXT, -- 'Kharif', 'Rabi', etc.
    crop_type TEXT,
    area_acres FLOAT,
    pumping_hours_per_day FLOAT,
    water_consumption_m3 FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for filtering
CREATE INDEX IF NOT EXISTS idx_pumping_district ON pumping_data (district);
CREATE INDEX IF NOT EXISTS idx_pumping_village ON pumping_data (village);
CREATE INDEX IF NOT EXISTS idx_pumping_year ON pumping_data (year);
CREATE INDEX IF NOT EXISTS idx_pumping_season ON pumping_data (season);

-- Add schema info
COMMENT ON TABLE pumping_data IS 'aggregated pumping/extraction data for analysis';

-- Enable RLS
ALTER TABLE pumping_data ENABLE ROW LEVEL SECURITY;

-- Allow read access to all
CREATE POLICY "Public read access to pumping_data" ON pumping_data
    FOR SELECT USING (true);
