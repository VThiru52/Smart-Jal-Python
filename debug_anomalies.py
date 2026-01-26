import sys
import os
# No need to add to sys.path if run from this dir
from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def debug():
    supabase = get_supabase_admin()
    res = supabase.table("anomalies").select("count", count="exact").execute()
    print(f"Total Anomalies Count: {res.count}")
    
    if res.count > 0:
        data = supabase.table("anomalies").select("*").limit(5).execute()
        print("Recent 5 anomalies:")
        for a in data.data:
            print(f"- {a['event_date']}: {a['severity']} (Piezometer ID: {a['piezometer_id']})")
    else:
        print("Table is empty.")

if __name__ == "__main__":
    debug()
