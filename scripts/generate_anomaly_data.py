import os
import sys
import random
import datetime
import uuid
import time

# Add the parent directory to sys.path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase_admin
from dotenv import load_dotenv

load_dotenv()

def generate_anomaly_data():
    print("🚀 Starting Anomaly Data Generation...")
    supabase = get_supabase_admin()
    
    # 1. Get Piezometers
    print("📥 Fetching piezometers...")
    piezo_res = supabase.table("piezometers").select("id, location_name").limit(5).execute()
    
    if not piezo_res.data:
        print("❌ No piezometers found. Please run populate_sample_data.py first.")
        return

    piezometers = piezo_res.data
    print(f"✅ Found {len(piezometers)} piezometers for data injection.")

    # 2. Clear old anomalies for these piezometers to start fresh
    piezo_ids = [p['id'] for p in piezometers]
    supabase.table("anomalies").delete().in_("piezometer_id", piezo_ids).execute()
    
    all_readings = []
    anomaly_records = []
    
    current_date = datetime.datetime.now()
    
    # Define severity scenarios
    scenarios = [
        {"severity": "CRITICAL", "desc": "Sudden extreme drop in water level detected. Potential borehole collapse or extreme local extraction.", "drop": 25.0},
        {"severity": "HIGH", "desc": "Unusual water level rise detected during non-monsoon period. Potential sensor malfunction or local drainage issue.", "drop": -15.0},
        {"severity": "MEDIUM", "desc": "Multivariate anomaly detected in water level trend using Isolation Forest.", "drop": 10.0},
        {"severity": "LOW", "desc": "Minor deviation from seasonal baseline detected.", "drop": 5.0}
    ]

    for i, piezo in enumerate(piezometers):
        p_id = piezo['id']
        p_name = piezo['location_name']
        print(f"📊 Processing {p_name}...")
        
        # Base water level
        base_level = random.uniform(30.0, 50.0)
        
        # A. Inject 25 historical readings (Last 25 months)
        for month_offset in range(25, 0, -1):
            date = (current_date - datetime.timedelta(days=month_offset * 30)).strftime('%Y-%m-%d')
            # Add some natural variation
            level = base_level + random.uniform(-2.0, 2.0)
            
            all_readings.append({
                "piezometer_id": p_id,
                "water_level_mbgl": round(level, 2),
                "reading_date": date
            })

        # B. Inject the Anomaly Reading (Today)
        scenario = scenarios[i % len(scenarios)]
        anomaly_date = current_date.strftime('%Y-%m-%d')
        anomaly_level = base_level + scenario["drop"]
        
        all_readings.append({
            "piezometer_id": p_id,
            "water_level_mbgl": round(anomaly_level, 2),
            "reading_date": anomaly_date
        })
        
        # C. Create the Anomaly Record for the UI
        anomaly_records.append({
            "piezometer_id": p_id,
            "event_date": anomaly_date,
            "detected_value": round(anomaly_level, 2),
            "expected_value": round(base_level, 2),
            "severity": scenario["severity"],
            "description": scenario["desc"],
            "is_resolved": False
        })

    # 3. Batch Insert Readings
    print(f"🚀 Inserting {len(all_readings)} readings...")
    batch_size = 50
    for i in range(0, len(all_readings), batch_size):
        batch = all_readings[i:i+batch_size]
        try:
            supabase.table("readings").upsert(batch, on_conflict="piezometer_id,reading_date").execute()
            print(f"   Injected readings batch {i//batch_size + 1}")
        except Exception as e:
            print(f"   ⚠️ Error injecting readings: {e}")

    # 4. Batch Insert Anomalies
    print(f"🚨 Inserting {len(anomaly_records)} anomaly records...")
    try:
        supabase.table("anomalies").insert(anomaly_records).execute()
        print("✅ Anomaly records injected successfully.")
    except Exception as e:
        print(f"⚠️ Error injecting anomalies: {e}")

    print("\n" + "="*40)
    print("🎉 ANOMALY DATA POPULATION COMPLETE!")
    print("="*40)
    print("Please refresh the Anomaly Detection System dashboard.")

if __name__ == "__main__":
    generate_anomaly_data()
