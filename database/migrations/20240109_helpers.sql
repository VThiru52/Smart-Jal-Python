-- Helper for getting village averages from readings
CREATE OR REPLACE FUNCTION get_village_avg_water_levels()
RETURNS TABLE (
    village_id UUID,
    avg_level_mbgl FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.village_id,
        AVG(r.water_level_mbgl)::FLOAT
    FROM 
        piezometers p
    JOIN 
        readings r ON p.id = r.piezometer_id
    GROUP BY 
        p.village_id;
END;
$$ LANGUAGE plpgsql;
