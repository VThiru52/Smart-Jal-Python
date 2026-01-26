-- Migration to add unique constraints for data ingestion support
-- Required for upsert operations in ingestion scripts

-- 1. Villages Unique Constraint
-- Some ingestion scripts use name and district as a unique identifier
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'villages_name_district_key') THEN
        ALTER TABLE villages ADD CONSTRAINT villages_name_district_key UNIQUE (name, district);
    END IF;
END $$;

-- 2. Readings Unique Constraint
-- Prevent duplicate readings for the same piezometer and date
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'readings_piezo_date_key') THEN
        ALTER TABLE readings ADD CONSTRAINT readings_piezo_date_key UNIQUE (piezometer_id, reading_date);
    END IF;
END $$;

-- 3. Bore Wells Unique Constraint (Optional but good for idempotency)
-- Assuming district, mandal, village and geom (or at least location) but since it's massive, 
-- we might just stick to insert or add a unique constraint if we had a station code.
-- For now, we'll leave bore_wells as is since the script uses insert.
