from app.core.supabase import get_supabase_admin
import pandas as pd
from typing import List

class ETLService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def run_feature_engineering_pipeline(self, village_id: str):
        """
        Scheduled or triggered job to generate features:
        - Seasonal trends
        - Rainfall lag (1 month, 3 months)
        - Extraction stress indicators
        """
        # 1. Fetch Historical Readings & Rainfall
        readings = self.supabase.table("readings").select("*").eq("piezometer_id.village_id", village_id).execute()
        rainfall = self.supabase.table("rainfall").select("*").eq("village_id", village_id).execute()
        
        if not readings.data or not rainfall.data:
            return None

        df_readings = pd.DataFrame(readings.data)
        df_rainfall = pd.DataFrame(rainfall.data)

        # 2. Calculate Lags
        df_rainfall['reading_date'] = pd.to_datetime(df_rainfall['reading_date'])
        df_rainfall = df_rainfall.sort_values('reading_date')
        df_rainfall['rainfall_lag_1m'] = df_rainfall['rainfall_mm'].shift(1)
        df_rainfall['rainfall_lag_3m'] = df_rainfall['rainfall_mm'].rolling(window=3).mean()

        # 3. Store Processed Features (In a separate features table or JSONB in villages)
        # ... logic to update DB ...
        return {"status": "features_updated", "village_id": village_id}

etl_service = ETLService()
