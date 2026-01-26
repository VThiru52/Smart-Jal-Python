-- Add recommended_structure column to recharge_zones table
ALTER TABLE recharge_zones 
ADD COLUMN IF NOT EXISTS recommended_structure TEXT,
ADD COLUMN IF NOT EXISTS structure_cost_estimate FLOAT;

-- Ensure unique constraint for UPSERT
ALTER TABLE recharge_zones
DROP CONSTRAINT IF EXISTS recharge_zones_village_id_key;

ALTER TABLE recharge_zones
ADD CONSTRAINT recharge_zones_village_id_key UNIQUE (village_id);
