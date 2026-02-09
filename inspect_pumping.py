from app.core.supabase import get_supabase_admin
import pandas as pd

def debug():
    supabase = get_supabase_admin()
    
    print("Checking pumping_data summary...")
    res = supabase.table("pumping_data").select("village", "district").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        print("Pumping Data Villages (first 10):", df['village'].unique()[:10])
        print("Pumping Data District:", df['district'].unique())
    else:
        print("No pumping data found.")

    print("\nChecking villages table...")
    res = supabase.table("villages").select("name", "population", "district").execute()
    if res.data:
        df = pd.DataFrame(res.data)
        print("Villages Table Names (first 10):", df['name'].unique()[:10])
        print("Villages with population > 0:", len(df[df['population'] > 0]))
        print("Sample village with population:", df[df['population'] > 0].head(5).to_dict('records'))
    else:
        print("No villages found.")

if __name__ == "__main__":
    debug()
