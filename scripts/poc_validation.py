import asyncio
from app.services.spatial_service import spatial_service
from app.services.forecasting_service import forecasting_service
from app.services.recharge_service import recharge_service
from app.core.supabase import get_supabase_admin

async def run_poc_validation():
    print("--- Starting PoC Validation for Krishna District ---")
    
    # 1. Test Spatial Mapping
    print("\n1. Running Spatial Interpolation (Kriging)...")
    mapping = await spatial_service.generate_village_mapping(district="Krishna")
    if mapping:
        print(f"✅ Mapping generated for {len(mapping)} villages.")
    else:
        print("❌ Mapping failed (check if piezometer data exists).")

    # 2. Test Forecasting
    print("\n2. Testing 12-month Forecasting...")
    # Get a sample village ID
    supabase = get_supabase_admin()
    village = supabase.table("villages").select("id").limit(1).execute()
    if village.data:
        v_id = village.data[0]['id']
        forecast = await forecasting_service.generate_forecast(v_id)
        if "error" not in forecast:
            print(f"✅ Forecast success for village {v_id}.")
        else:
            print(f"⚠️ Forecast skipped: {forecast['error']}")

    # 3. Test Recharge Recommendations
    print("\n3. Generating Recharge Priority Report...")
    recharge = await recharge_service.calculate_recharge_priorities(district="Krishna")
    if "error" not in recharge:
        print(f"✅ Ranked {len(recharge)} villages for recharge.")
    else:
        print(f"❌ Recharge logic failed: {recharge['error']}")

    print("\n--- PoC Validation Complete ---")

if __name__ == "__main__":
    asyncio.run(run_poc_validation())
