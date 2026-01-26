
import asyncio
import os
import sys

# Add the backend directory to sys.path
sys.path.append(os.path.abspath("d:/Smart Jal/backend"))

from app.core.supabase import get_supabase_admin

async def test_supabase():
    print("Testing Supabase connection...")
    try:
        supabase = get_supabase_admin()
        print("Supabase client created.")
        
        # Test districts query
        print("Querying districts table...")
        result = supabase.table("districts").select("id, name, created_at, updated_at").order("name").execute()
        print(f"Districts result: {result.data}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_supabase())
