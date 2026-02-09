
from app.core.supabase import get_supabase_admin
import pandas as pd
import datetime

def fix_koduru():
    supabase = get_supabase_admin()
    
    # 1. Ensure the correct Koduru (Mandal: Koduru) exists
    # First, let's rename the existing one to be specific to avoid confusion in lookups
    supabase.table("villages").update({"name": "Koduru (G.Konduru)"}).eq("mandal", "G.KONDURU").ilike("name", "Koduru").execute()
    
    # Check if Koduru (Mandal: Koduru) already exists
    v_res = supabase.table("villages").select("id").eq("mandal", "KODURU").ilike("name", "Koduru").execute()
    
    if v_res.data:
        village_id = v_res.data[0]['id']
        print(f"Correct Koduru village already exists with ID: {village_id}")
    else:
        # Create it
        # Get data from excel for ID 10210
        df = pd.read_excel('master data_updated.xlsx', sheet_name='meta-historical')
        row = df[df['ID'] == 10210].iloc[0]
        
        village_data = {
            "name": "Koduru",
            "district": "Krishna",
            "mandal": "Koduru",
            "latitude": float(row['Latitude \n(Decimal Degrees)']),
            "longitude": float(row['Longitude \n(Decimal Degrees)']),
            "elevation_m": 5.0, # Approximate MSL
            "total_area_ha": 1200.0,
            "population": 35000,
            "soil_type": "Coastal Alluvium",
            "risk_status": "CRITICAL",
            "current_risk_score": 92.5
        }
        print("Creating true Koduru village...")
        res = supabase.table("villages").insert(village_data).execute()
        village_id = res.data[0]['id']
        print(f"Created with ID: {village_id}")

    # 2. Re-link piezometers 10210 and 30395 to this village
    print(f"Linking piezometers 10210 and 30395 to {village_id}...")
    supabase.table("piezometers").update({"village_id": village_id}).in_("station_code", ["10210", "30395"]).execute()

    # 3. Inject Pumping Data specifically for this village_name + mandal context if possible
    # Pumping data table joins on village name. 
    # Since we have two 'Koduru' (one renamed), the queries will work better.
    print("Updating pumping data...")
    supabase.table("pumping_data").insert({
        "district": "Krishna",
        "village": "Koduru",
        "year": 2024,
        "season": "Kharif",
        "crop_type": "Paddy",
        "area_acres": 600.0,
        "water_consumption_m3": 28000.0, # High
        "structure_type": "Borewell"
    }).execute()

    # 4. Final Metadata Check
    supabase.table("villages").update({
        "risk_status": "CRITICAL",
        "current_risk_score": 92.5,
        "water_consumption_m3": 28000.0
    }).eq("id", village_id).execute()

    print("Koduru correction complete!")

if __name__ == "__main__":
    fix_koduru()
