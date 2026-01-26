"""
Master Ingestion Script
Orchestrates all data ingestion in the correct order
"""
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all ingestion modules
from scripts.ingest_usecase_villages import ingest_usecase_villages
from scripts.ingest_smartjal_aquifers import ingest_aquifers
from scripts.ingest_smartjal_gm import ingest_geomorphology
from scripts.ingest_smartjal_lulc import ingest_lulc
from scripts.ingest_usecase_soils import ingest_usecase_soils
from scripts.ingest_usecase_model_zones import ingest_usecase_model_zones
from scripts.ingest_usecase_mit import ingest_usecase_mit
from scripts.ingest_usecase_dem import ingest_usecase_dem
from scripts.ingest_smartjal_bore_wells import ingest_bore_wells
from scripts.ingest_historical_readings import ingest_historical_readings
from scripts.ingest_pumping_data import ingest_pumping_data

def main():
    print("=" * 80)
    print("SMART JAL - MASTER DATA INGESTION")
    print("=" * 80)
    print()
    
    ingestion_steps = [
        ("1. Villages (UseCase)", ingest_usecase_villages),
        ("2. Aquifers", ingest_aquifers),
        ("3. Geomorphology", ingest_geomorphology),
        ("4. Land Use (LULC)", ingest_lulc),
        ("5. Soil Types", ingest_usecase_soils),
        ("6. Model Zones", ingest_usecase_model_zones),
        ("7. MIT Zones", ingest_usecase_mit),
        ("8. Elevation Data (DEM)", ingest_usecase_dem),
        ("9. Bore Wells", ingest_bore_wells),
        ("10. Historical Readings", ingest_historical_readings),
        ("11. Pumping Data", ingest_pumping_data),
    ]
    
    print(f"📋 Total steps: {len(ingestion_steps)}")
    print()
    
    for step_name, ingest_func in ingestion_steps:
        print("=" * 80)
        print(f"▶️  {step_name}")
        print("=" * 80)
        
        try:
            ingest_func()
            print(f"✅ {step_name} completed successfully!")
        except Exception as e:
            print(f"❌ {step_name} failed: {e}")
            print("⚠️  Continuing with remaining steps...")
        
        print()
    
    print("=" * 80)
    print("🎉 MASTER INGESTION COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Verify data in Supabase dashboard")
    print("2. Test API endpoints")
    print("3. Run spatial queries to validate geometry data")

if __name__ == "__main__":
    main()
