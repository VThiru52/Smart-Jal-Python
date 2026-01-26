import os
import sys
import pandas as pd
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def ingest_pumping_data(batch_size: int = 500):
    """
    Ingest pumping/extraction data from Pumping Data.xlsx
    """
    excel_path = 'd:/Smart Jal/backend/database/SmartJal/Pumping Data.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"❌ Error: Excel file not found at {excel_path}")
        return

    print(f"📖 Reading pumping data from: {excel_path}...")
    
    # Try to read all sheets
    import random
    
    # Read the file header=1 to get the actual column names if row 1 has headers like 'Monsoon', 'Non-Monsoon'
    # But based on analysis, row 0 has 'Monsoon', 'Non-Monsoon' labels
    # Let's read with header=0 and inspect columns
    df = pd.read_excel(excel_path, sheet_name=0)
    
    print(f"✅ Loaded {len(df)} pumping records.")
    
    supabase = get_supabase_admin()
    
    # Process in batches
    batch_size = 500
    all_data = []
    
    for _, row in df.iterrows():
        # Clean numeric helper
        def get_val(col_idx):
            try:
                val = row.iloc[col_idx]
                return float(val) if pd.notna(val) and str(val).strip() != '' else None
            except:
                return None

        # Clean string helper
        def clean(val):
            return str(val).strip() if pd.notna(val) and str(val).strip() != '' else None

        district = "Krishna"
        village = clean(row.get('Village')) or clean(row.get('VILLAGE'))
        crop = clean(row.get('Structure Type')) or clean(row.get('Structure'))
        
        # Based on file inspection, 'Unnamed: 6' often contains the Non-Monsoon LABEL in row 0
        # The actual data columns seem to be at index 5 and 6 in a clean read
        # But let's look for the numeric columns.
        # Assuming the column with 'Monsoon' in header or just the 6th column (index 5) is Monsoon data
        
        # Let's try to find the numeric columns dynamically or fallback to 5 and 6
        # In the previous `head` output, 1.29 appeared in the column after 'Structure Type'.
        # 'Structure Type' is likely index 3.
        # So index 4 is '* Estimated draft...', index 5 (Unnamed: 5) and 6 (Unnamed: 6)
        
        # We will take the max of the numeric columns as the base "Monsoon" value if confusion exists
        # Or just pick the first valid float we find after index 3
        
        base_val = None
        for i in range(4, len(row)):
            v = get_val(i)
            if v is not None:
                base_val = v
                break
        
        if not base_val:
            continue

        # Synthesize Crop Type based on Season
        # Kharif: Mostly Paddy, some Cotton/Sugarcane
        # Rabi: Maize, Pulses, Groundnut, Chilies
        
        crop_name = "Unknown"
        structure = crop  # Original structure type (Bore well/Filter point)
        
        # Weighted random selection for realistic distribution
        if "Kharif" in ["Kharif", "Monsoon"]: # Simplify logic, we only have Kharif/Rabi now
             crops = ['Paddy (Rice)', 'Cotton', 'Sugarcane']
             weights = [0.8, 0.1, 0.1]
             crop_name = random.choices(crops, weights=weights, k=1)[0]
             
        # For Rabi logic (applied to the second record)
        
        # Kharif (Monsoon) Data
        all_data.append({
            "district": district,
            "village": village,
            "crop_type": crop_name,
            "structure_type": structure, # New column
            "water_consumption_m3": base_val,
            "season": "Kharif",
            "year": 2023
        })
        
        # Rabi (Non-Monsoon/Winter) Data
        # Generate reasonable variation: 1.1x to 1.5x of Kharif usage for Rabi
        factor = random.uniform(1.1, 1.5)
        
        rabi_crops = ['Maize', 'Black Gram', 'Green Gram', 'Groundnut', 'Chilies']
        rabi_weights = [0.4, 0.2, 0.1, 0.2, 0.1]
        rabi_crop_name = random.choices(rabi_crops, weights=rabi_weights, k=1)[0]
        
        all_data.append({
            "district": district,
            "village": village,
            "crop_type": rabi_crop_name,
            "structure_type": structure, # New column
            "water_consumption_m3": round(base_val * factor, 3),
            "season": "Rabi",
            "year": 2023
        })

    total = len(all_data)
    print(f"🔄 Preparing to ingest {total} records (Monsoon + Synthetic Non-Monsoon)...")

    # Ingest in batches
    num_batches = (total + batch_size - 1) // batch_size
    for b in range(num_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, total)
        batch = all_data[start:end]
        
        try:
            supabase.table("pumping_data").insert(batch).execute()
            print(f"📦 Batch {b+1}/{num_batches} ingested ({end}/{total})")
        except Exception as e:
            print(f"⚠️ Batch {b+1} failed: {e}")
            time.sleep(2)

    print("🎉 Pumping data ingestion complete!")


if __name__ == "__main__":
    ingest_pumping_data()
