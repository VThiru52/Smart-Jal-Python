-- Migration to add Geomorphology and Land Use layers
CREATE TABLE IF NOT EXISTS geomorphology_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    description TEXT, -- FIN_DESC
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS land_use_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district TEXT NOT NULL,
    grid_code INT,
    geom GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Spatial indices for fast lookup
CREATE INDEX IF NOT EXISTS idx_gm_geom ON geomorphology_zones USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_lulc_geom ON land_use_zones USING GIST (geom);
