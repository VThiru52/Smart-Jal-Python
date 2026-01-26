-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Villages Table
CREATE TABLE IF NOT EXISTS villages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    district TEXT NOT NULL DEFAULT 'Krishna',
    sub_district TEXT,
    boundary GEOMETRY(MultiPolygon, 4326),
    centroid GEOMETRY(Point, 4326),
    population INT,
    average_rainfall_mm FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was already created
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='villages' AND column_name='district') THEN
        ALTER TABLE villages ADD COLUMN district TEXT NOT NULL DEFAULT 'Krishna';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='villages' AND column_name='boundary') THEN
        ALTER TABLE villages ADD COLUMN boundary GEOMETRY(MultiPolygon, 4326);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='villages' AND column_name='centroid') THEN
        ALTER TABLE villages ADD COLUMN centroid GEOMETRY(Point, 4326);
    END IF;
END $$;

-- 2. Aquifers Table
CREATE TABLE IF NOT EXISTS aquifers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL, -- e.g., Alluvial, Hard Rock
    permeability_factor FLOAT,
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was already created
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='aquifers' AND column_name='boundary') THEN
        ALTER TABLE aquifers ADD COLUMN boundary GEOMETRY(MultiPolygon, 4326);
    END IF;
END $$;

-- 3. Piezometers Table
CREATE TABLE IF NOT EXISTS piezometers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    station_code TEXT UNIQUE NOT NULL,
    location_name TEXT NOT NULL,
    village_id UUID REFERENCES villages(id) ON DELETE SET NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    depth_m FLOAT,
    is_active BOOLEAN DEFAULT TRUE,
    last_reading_date DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was already created
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='piezometers' AND column_name='geom') THEN
        ALTER TABLE piezometers ADD COLUMN geom GEOMETRY(Point, 4326);
    END IF;
END $$;

-- 4. Groundwater Readings (Time-series)
CREATE TABLE IF NOT EXISTS readings (
    id BIGSERIAL PRIMARY KEY,
    piezometer_id UUID REFERENCES piezometers(id) ON DELETE CASCADE,
    reading_date TIMESTAMPTZ NOT NULL,
    water_level_mbgl FLOAT NOT NULL, -- Meters Below Ground Level
    temperature_c FLOAT,
    quality_index TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Rainfall Data
CREATE TABLE IF NOT EXISTS rainfall (
    id BIGSERIAL PRIMARY KEY,
    village_id UUID REFERENCES villages(id) ON DELETE CASCADE,
    reading_date DATE NOT NULL,
    rainfall_mm FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. Forecasts Table
CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    village_id UUID REFERENCES villages(id) ON DELETE CASCADE,
    forecast_date DATE NOT NULL,
    target_date DATE NOT NULL,
    predicted_level_mbgl FLOAT NOT NULL,
    confidence_score FLOAT,
    shap_explanation JSONB, -- Store SHAP explainability data
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. Anomalies Table
CREATE TABLE IF NOT EXISTS anomalies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    piezometer_id UUID REFERENCES piezometers(id) ON DELETE CASCADE,
    event_date TIMESTAMPTZ NOT NULL,
    detected_value FLOAT,
    expected_value FLOAT,
    severity TEXT CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    description TEXT,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 8. Recharge Zones
CREATE TABLE IF NOT EXISTS recharge_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    village_id UUID REFERENCES villages(id) ON DELETE CASCADE,
    priority_score FLOAT,
    suitability_rank INT,
    recommendation_logic TEXT,
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ensure columns exist if table was already created
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='recharge_zones' AND column_name='geom') THEN
        ALTER TABLE recharge_zones ADD COLUMN geom GEOMETRY(MultiPolygon, 4326);
    END IF;
END $$;

-- 9. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id),
    action TEXT NOT NULL,
    table_name TEXT,
    record_id UUID,
    old_data JSONB,
    new_data JSONB,
    ip_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- indices for spatial queries
CREATE INDEX IF NOT EXISTS idx_villages_boundary ON villages USING GIST (boundary);
CREATE INDEX IF NOT EXISTS idx_piezometers_geom ON piezometers USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_readings_date ON readings (reading_date DESC);
CREATE INDEX IF NOT EXISTS idx_readings_piezometer ON readings (piezometer_id);

-- Row Level Security (RLS) Policies

ALTER TABLE villages ENABLE ROW LEVEL SECURITY;
ALTER TABLE readings ENABLE ROW LEVEL SECURITY;
ALTER TABLE piezometers ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE anomalies ENABLE ROW LEVEL SECURITY;
ALTER TABLE recharge_zones ENABLE ROW LEVEL SECURITY;
ALTER TABLE aquifers ENABLE ROW LEVEL SECURITY;
ALTER TABLE rainfall ENABLE ROW LEVEL SECURITY;

-- 1. ADMIN Policy: Full Access
DROP POLICY IF EXISTS "Admins have full access" ON villages;
CREATE POLICY "Admins have full access" ON villages FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
DROP POLICY IF EXISTS "Admins have full access" ON readings;
CREATE POLICY "Admins have full access" ON readings FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
DROP POLICY IF EXISTS "Admins have full access" ON piezometers;
CREATE POLICY "Admins have full access" ON piezometers FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
DROP POLICY IF EXISTS "Admins have full access" ON forecasts;
CREATE POLICY "Admins have full access" ON forecasts FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
DROP POLICY IF EXISTS "Admins have full access" ON anomalies;
CREATE POLICY "Admins have full access" ON anomalies FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');
DROP POLICY IF EXISTS "Admins have full access" ON recharge_zones;
CREATE POLICY "Admins have full access" ON recharge_zones FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'admin');

-- 2. SCIENTIST Policy: Read/Write access to core data
DROP POLICY IF EXISTS "Scientists can manage readings" ON readings;
CREATE POLICY "Scientists can manage readings" ON readings FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'scientist');
DROP POLICY IF EXISTS "Scientists can manage piezometers" ON piezometers;
CREATE POLICY "Scientists can manage piezometers" ON piezometers FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'scientist');
DROP POLICY IF EXISTS "Scientists can manage forecasts" ON forecasts;
CREATE POLICY "Scientists can manage forecasts" ON forecasts FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'scientist');
DROP POLICY IF EXISTS "Scientists can manage anomalies" ON anomalies;
CREATE POLICY "Scientists can manage anomalies" ON anomalies FOR ALL TO authenticated USING (auth.jwt() ->> 'role' = 'scientist');

-- 3. DISTRICT OFFICER Policy: Read access to their district
-- We assume the JWT contains a 'district' claim
DROP POLICY IF EXISTS "District officers can view their district villages" ON villages;
CREATE POLICY "District officers can view their district villages" ON villages
    FOR SELECT TO authenticated USING (
        auth.jwt() ->> 'role' = 'district_officer' AND 
        name = (auth.jwt() ->> 'district')
    );

DROP POLICY IF EXISTS "District officers can view their district piezometers" ON piezometers;
CREATE POLICY "District officers can view their district piezometers" ON piezometers
    FOR SELECT TO authenticated USING (
        auth.jwt() ->> 'role' = 'district_officer' AND 
        village_id IN (SELECT id FROM villages WHERE district = (auth.jwt() ->> 'district'))
    );

-- 4. PUBLIC/VIEWER Policy: Read only access
DROP POLICY IF EXISTS "Public read access to villages" ON villages;
CREATE POLICY "Public read access to villages" ON villages FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to piezometers" ON piezometers;
CREATE POLICY "Public read access to piezometers" ON piezometers FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to readings" ON readings;
CREATE POLICY "Public read access to readings" ON readings FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to forecasts" ON forecasts;
CREATE POLICY "Public read access to forecasts" ON forecasts FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to anomalies" ON anomalies;
CREATE POLICY "Public read access to anomalies" ON anomalies FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to recharge_zones" ON recharge_zones;
CREATE POLICY "Public read access to recharge_zones" ON recharge_zones FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "Public read access to aquifers" ON aquifers;
CREATE POLICY "Public read access to aquifers" ON aquifers FOR SELECT TO authenticated USING (true);
