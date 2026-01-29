import pandas as pd
from typing import List, Dict, Any, Optional
from app.core.supabase import get_supabase_admin
import numpy as np
from datetime import datetime
from pathlib import Path
from app.services.audit_service import audit_service
from postgrest.exceptions import APIError
import logging


logger = logging.getLogger(__name__)

class ForecastingService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    def _build_dataframe(self, supabase_data: list) -> Optional[pd.DataFrame]:
        rows = []
        for record in supabase_data or []:
            try:
                rows.append({
                    "ds": pd.to_datetime(record["reading_date"]).tz_localize(None),
                    "y": float(record["water_level_mbgl"])
                })
            except Exception:
                continue

        if len(rows) < 3:
            return None

        df = pd.DataFrame(rows).drop_duplicates(subset=["ds"]).sort_values("ds")
        return df

    async def generate_forecast(self, village_id: str, periods: int = 12):
        """
        Generates 3, 6, 12-month forecasts using lightweight Linear Regression.
        Replaces Prophet/XGBoost to stay under Heroku slug limits.
        """
        # 1. Fetch historical data
        readings_resp = self.supabase.table("readings").select(
            "reading_date, water_level_mbgl, piezometers!inner(village_id)"
        ).eq("piezometers.village_id", village_id).order("reading_date").execute()

        df = self._build_dataframe(readings_resp.data)

        if df is None:
            return {"error": "Insufficient historical data for forecasting"}

        # 2. Lightweight Linear Regression
        # Convert dates to numbers (days from start)
        df['ds_num'] = (df['ds'] - df['ds'].min()).dt.days
        
        # Simple slope & intercept
        x = df['ds_num'].values
        y = df['y'].values
        n = len(x)
        
        slope, intercept = 0, y.mean()
        if n > 1:
            slope = (n * np.sum(x*y) - np.sum(x)*np.sum(y)) / (n * np.sum(x**2) - (np.sum(x))**2)
            intercept = (np.sum(y) - slope * np.sum(x)) / n

        # 3. Generate future points
        last_date = df['ds'].max()
        forecast_entries = []
        
        for i in range(1, periods + 1):
            target_date = last_date + pd.DateOffset(months=i)
            target_num = (target_date - df['ds'].min()).days
            
            # Simple linear projection + seasonal hint (simple sine wave)
            seasonal_offset = 2.0 * np.sin(2 * np.pi * target_date.month / 12.0)
            predicted_value = slope * target_num + intercept + seasonal_offset
            
            # Ensure value is realistic (MBGL usually positive)
            predicted_value = max(0.1, predicted_value)

            forecast_entries.append({
                "village_id": village_id,
                "forecast_date": datetime.now().strftime("%Y-%m-%d"),
                "target_date": target_date.strftime("%Y-%m-%d"),
                "predicted_level_mbgl": float(predicted_value),
                "confidence_score": 0.85 - (i * 0.02), # Decaying confidence
                "shap_explanation": None,
                "model_version": "v1.2-Lightweight"
            })
        
        # Store in Supabase
        self.supabase.table("forecasts").insert(forecast_entries).execute()

        return {
            "village_id": village_id,
            "forecasts": forecast_entries,
            "explainability": {
                "type": "Trend Analysis (Linear)",
                "explanation": None,
                "note": "Forecasting uses a trend-based projection optimized for cloud deployment limits."
            }
        }


forecasting_service = ForecastingService()
