import asyncio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

from app.services.anomaly_service import anomaly_service
from app.services.forecasting_service import forecasting_service
from app.services.recharge_service import recharge_service
from app.core.supabase import get_supabase_admin

async def verify_systems():
    supabase = get_supabase_admin()
    
    # 1. Test Anomaly Detection
    print("Testing Anomaly Detection (Isolation Forest)...")
    # Fetch a piezometer with some data
    piezo_resp = supabase.table("piezometers").select("id").limit(1).execute()
    if piezo_resp.data:
        p_id = piezo_resp.data[0]['id']
        await anomaly_service.detect_anomalies(p_id)
        print(f"✅ Anomaly detection triggered for {p_id}")
    else:
        print("❌ No piezometers found for testing")

    # 2. Test Forecasting with SHAP
    print("\nTesting Forecasting (SHAP)...")
    village_resp = supabase.table("villages").select("id").limit(1).execute()
    if village_resp.data:
        v_id = village_resp.data[0]['id']
        forecast = await forecasting_service.generate_forecast(v_id, periods=3)
        if "error" not in forecast:
            print(f"✅ Forecast generated for {v_id}")
            print(f"SHAP Explanation: {forecast['explainability']['type']}")
        else:
            print(f"⚠️ Forecast skipped: {forecast['error']}")
    else:
        print("❌ No villages found for testing")

    # 3. Test Recharge persistence and Audit
    print("\nTesting Recharge and Audit...")
    recharge_res = await recharge_service.calculate_recharge_priorities(district="Krishna")
    if recharge_res:
        print(f"✅ Recharge priorities calculated: {len(recharge_res)} villages")
    
    # Check audit logs
    audit_resp = supabase.table("audit_logs").select("*").order("created_at", desc=True).limit(5).execute()
    if audit_resp.data:
        print(f"✅ Audit logs found: {len(audit_resp.data)} recent entries")
        for log in audit_resp.data:
            print(f" - {log['action']} at {log['created_at']}")
    else:
        print("❌ No audit logs found")

if __name__ == "__main__":
    asyncio.run(verify_systems())
