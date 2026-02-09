
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append(os.getcwd())

from app.core.supabase import get_supabase_admin

async def debug_data():
    print("--- Checking Supabase Data ---")
    try:
        supabase = get_supabase_admin()
        
        # 1. Check Villages
        print("\nChecking 'villages' table...")
        villages = supabase.table("villages").select("*").limit(5).execute()
        if villages.data:
            print(f"Sample Village Data: {villages.data[0].keys()}")
            for v in villages.data:
                print(f"ID: {v['id']}, Name: {v['name']}, District: {v['district']}, Avg Rainfall: {v.get('average_rainfall_mm')}")
        else:
            print("No villages found.")

        # 2. Check Pumping Data
        print("\nChecking 'pumping_data' table...")
        pumping = supabase.table("pumping_data").select("*").limit(5).execute()
        if pumping.data:
            print(f"Sample Pumping Data: {pumping.data[0].keys()}")
        else:
            print("No pumping data found.")
            
        # 3. Check Drought Data
        print("\nChecking 'drought_assessments' or similar tables...")
        # (Assuming it might be under 'villages' or separate table)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_data())
