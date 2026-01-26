"""
Run migration to add recommended_structure column
"""
from app.core.supabase import get_supabase_admin

def run_migration():
    print("🔄 Adding recommended_structure column to recharge_zones...")
    
    supabase = get_supabase_admin()
    
    sql_commands = [
        "ALTER TABLE recharge_zones ADD COLUMN IF NOT EXISTS recommended_structure TEXT;",
        "ALTER TABLE recharge_zones ADD COLUMN IF NOT EXISTS structure_cost_estimate FLOAT;",
        "ALTER TABLE recharge_zones DROP CONSTRAINT IF EXISTS recharge_zones_village_id_key;",
        "ALTER TABLE recharge_zones ADD CONSTRAINT recharge_zones_village_id_key UNIQUE (village_id);"
    ]
    
    for cmd in sql_commands:
        try:
            # Note: Direct SQL execution via RPC or psql is preferred, but here we simulate or skip
            # Since we don't have direct SQL access through python client easily without RPC, 
            # and the user environment has 'psql' missing, we'll try to check if we can use a helper or if we need to rely on the user.
            # However, for this environment, we will assume we might need to rely on the user running migration if Supabase client doesn't support raw SQL.
            # Wait, we have been using direct SQL via Psql in 'migrations'? No, psql command failed.
            # We need to use the 'rpc' method if a raw_sql function exists, or just tell the user. 
            # But wait, looking at project, there might be no raw_sql RPC.
            # Let's check if we can add it via a hack or just fail gracefully.
            pass
        except Exception as e:
            print(f"Error: {e}")

    print("⚠️ PLEASE RUN THE FOLLOWING SQL IN YOUR SUPABASE SQL EDITOR:")
    print("\n".join(sql_commands))

if __name__ == "__main__":
    run_migration()
