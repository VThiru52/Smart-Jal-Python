import os
import psycopg2
from urllib.parse import urlparse

def run_migration():
    # Try different common env var names for DB URL
    db_url = os.getenv("DATABASE_URL") or os.getenv("SUPABASE_DB_URL") or "postgresql://postgres:postgres@localhost:5432/postgres"
    
    print(f"Attempting to connect to DB...")
    
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        sql_commands = [
            "ALTER TABLE recharge_zones ADD COLUMN IF NOT EXISTS recommended_structure TEXT;",
            "ALTER TABLE recharge_zones ADD COLUMN IF NOT EXISTS structure_cost_estimate FLOAT;",
            "ALTER TABLE recharge_zones DROP CONSTRAINT IF EXISTS recharge_zones_village_id_key;",
            "ALTER TABLE recharge_zones ADD CONSTRAINT recharge_zones_village_id_key UNIQUE (village_id);"
        ]
        
        for cmd in sql_commands:
            print(f"Executing: {cmd}")
            cursor.execute(cmd)
            
        print("✅ Migration applied successfully!")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # If psycopg2 fails, we might be on a system without it or valid creds
        # In that case, we must modify the code to be resilient

if __name__ == "__main__":
    run_migration()
