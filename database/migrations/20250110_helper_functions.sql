-- Helper Functions for Spatial Queries
-- These RPC functions enable efficient spatial lookups from the API

-- Function: Get soil type at a specific point
CREATE OR REPLACE FUNCTION get_soil_at_point(lat FLOAT, lon FLOAT)
RETURNS TABLE (
    id UUID,
    soil_code TEXT,
    soil_name TEXT,
    texture TEXT,
    drainage_class TEXT,
    area_ha FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.id,
        s.soil_code,
        s.soil_name,
        s.texture,
        s.drainage_class,
        s.area_ha
    FROM soil_types s
    WHERE ST_Contains(s.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326))
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Get nearest elevation point
CREATE OR REPLACE FUNCTION get_elevation_near_point(lat FLOAT, lon FLOAT, radius_km FLOAT DEFAULT 1.0)
RETURNS TABLE (
    elevation_m FLOAT,
    distance_km FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.elevation_m,
        ST_Distance(
            e.geom::geography,
            ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
        ) / 1000.0 AS distance_km
    FROM elevation_data e
    WHERE ST_DWithin(
        e.geom::geography,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography,
        radius_km * 1000
    )
    ORDER BY ST_Distance(
        e.geom::geography,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
    )
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Function: Get village average water levels (helper for recharge service)
CREATE OR REPLACE FUNCTION get_village_avg_water_levels()
RETURNS TABLE (
    village_id UUID,
    avg_level_mbgl FLOAT,
    reading_count INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.village_id,
        AVG(r.water_level_mbgl) AS avg_level_mbgl,
        COUNT(r.id)::INT AS reading_count
    FROM piezometers p
    INNER JOIN readings r ON r.piezometer_id = p.id
    WHERE r.reading_date >= NOW() - INTERVAL '6 months'
    GROUP BY p.village_id
    HAVING p.village_id IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Function: Find zones (model/MIT) containing a point
CREATE OR REPLACE FUNCTION get_zones_at_point(lat FLOAT, lon FLOAT)
RETURNS TABLE (
    zone_type TEXT,
    zone_code TEXT,
    zone_name TEXT,
    description TEXT
) AS $$
BEGIN
    -- Return model zones
    RETURN QUERY
    SELECT 
        'model'::TEXT AS zone_type,
        m.zone_code,
        m.zone_name,
        m.description
    FROM model_zones m
    WHERE ST_Contains(m.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326));
    
    -- Return MIT zones
    RETURN QUERY
    SELECT 
        'mit'::TEXT AS zone_type,
        i.mit_code AS zone_code,
        i.mit_name AS zone_name,
        i.category AS description
    FROM mit_zones i
    WHERE ST_Contains(i.geom, ST_SetSRID(ST_MakePoint(lon, lat), 4326));
END;
$$ LANGUAGE plpgsql;
