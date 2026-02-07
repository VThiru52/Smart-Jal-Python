
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import time

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"Connecting to: {url}")
supabase: Client = create_client(url, key)

start = time.time()
print("Executing query 'select * from villages limit 1'...")
try:
    # Use simple sync query for test
    res = supabase.table("villages").select("id").limit(1).execute()
    print(f"Success! Found ID: {res.data[0]['id']}")
except Exception as e:
    print(f"Error: {e}")
finally:
    print(f"Time taken: {time.time() - start:.2f}s")
