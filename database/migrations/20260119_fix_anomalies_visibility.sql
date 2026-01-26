-- Ensure anomalies table has public read access for both anon and authenticated roles
DROP POLICY IF EXISTS "Public read access to anomalies" ON anomalies;
CREATE POLICY "Public read access to anomalies" ON anomalies 
    FOR SELECT TO anon, authenticated 
    USING (true);

-- Ensure piezometers table also has public read access (it might be needed for the join)
DROP POLICY IF EXISTS "Public read access to piezometers" ON piezometers;
CREATE POLICY "Public read access to piezometers" ON piezometers 
    FOR SELECT TO anon, authenticated 
    USING (true);

-- Explicitly ensure the foreign key relationship is solid (PostgREST sometimes needs this hint)
ALTER TABLE anomalies 
    DROP CONSTRAINT IF EXISTS anomalies_piezometer_id_fkey,
    ADD CONSTRAINT anomalies_piezometer_id_fkey 
    FOREIGN KEY (piezometer_id) 
    REFERENCES piezometers(id) 
    ON DELETE CASCADE;

-- Grant usage on the table to anon and authenticated
GRANT SELECT ON anomalies TO anon, authenticated;
GRANT SELECT ON piezometers TO anon, authenticated;
