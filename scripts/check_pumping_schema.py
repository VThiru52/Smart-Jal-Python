"""
Check database schema for pumping_data
"""
from app.core.supabase import get_supabase_admin

def check_schema():
    print("🔍 Checking pumping_data schema...")
    supabase = get_supabase_admin()
    
    # Fetch a single record to infer schema
    try:
        result = supabase.table("pumping_data").select("*").limit(1).execute()
        if result.data:
            print("\nColumns found:")
            for key in result.data[0].keys():
                print(f"- {key}")
            print(f"\nSample data: {result.data[0]}")
        else:
            print("Table is empty or not accessible")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()
