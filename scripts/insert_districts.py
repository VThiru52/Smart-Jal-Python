import asyncio
import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin

# SQL to run schema migration
schema_sql = """
-- Create districts table
CREATE TABLE IF NOT EXISTS districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    boundary GEOMETRY(MultiPolygon, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for spatial queries
CREATE INDEX IF NOT EXISTS idx_districts_boundary ON districts USING GIST (boundary);

-- RLS
ALTER TABLE districts ENABLE ROW LEVEL SECURITY;

-- Policy: Everyone can read districts
DROP POLICY IF EXISTS "Public read access to districts" ON districts;
CREATE POLICY "Public read access to districts" ON districts
    FOR SELECT USING (true);
"""

# Mock Data from frontend/src/data/districtData.js (converted to Python dict)
district_data = {
    'Krishna': {
        "type": "Feature",
        "properties": {
            "name": "Krishna"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [80.6, 16.5],
                    [80.7, 16.5],
                    [80.75, 16.6],
                    [80.8, 16.55],
                    [80.85, 16.5],
                    [80.9, 16.4],
                    [80.8, 16.3],
                    [80.7, 16.35],
                    [80.6, 16.4],
                    [80.5, 16.45],
                    [80.6, 16.5]
                ]
            ]
        }
    },
    'Guntur': {
        "type": "Feature",
        "properties": {
            "name": "Guntur"
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                 [
                    [80.4, 16.3],
                    [80.5, 16.35],
                    [80.55, 16.2],
                    [80.5, 16.1],
                    [80.4, 16.15],
                    [80.3, 16.2],
                    [80.35, 16.25],
                    [80.4, 16.3]
                ]
            ]
        }
    }
}

async def migrate_districts():
    supabase = get_supabase_admin()
    
    # 1. Run Schema Migration (RPC call if possible, or just ignore if user has to run SQL manually. 
    # Supabase-py doesn't support raw SQL execution easily unless via RPC 'exec_sql' or similar if configured.
    # Note: If no exec_sql RPC, we must rely on psql or manual execution. 
    # But let's assume the user might have missed the psql step due to error.
    # I will try to proceed with insertion. If table missing, it will fail.
    
    print("Starting district data insertion...")

    for name, feature in district_data.items():
        print(f"Processing {name}...")
        
        # Check if exists
        try:
            # This will fail if table doesn't exist
            existing = supabase.table("districts").select("id").eq("name", name).execute()
            if existing.data:
                print(f"District {name} already exists. Deleting to re-insert...")
                supabase.table("districts").delete().eq("name", name).execute()
        except Exception as e:
            print(f"Error checking {name} (Table might happen to be missing): {e}")
            print("Please ensure the 'districts' table is created using the SQL migration file.")
            continue

        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
             geometry["type"] = "MultiPolygon"
             geometry["coordinates"] = [geometry["coordinates"]]

        payload = {
            "name": name,
            "boundary": geometry
        }

        try:
            res = supabase.table("districts").insert(payload).execute()
            print(f"Inserted {name}: Success")
        except Exception as e:
            print(f"Failed to insert {name}: {e}")

    print("Migration complete (Data Insertion Phase).")

if __name__ == "__main__":
    asyncio.run(migrate_districts())
