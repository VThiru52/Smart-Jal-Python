import pandas as pd
from typing import List, Dict, Any, Optional
from app.core.supabase import get_supabase_admin
import numpy as np
from datetime import datetime
from pathlib import Path
from app.services.audit_service import audit_service
from postgrest.exceptions import APIError

class ForecastingService:
    def __init__(self):
        self.supabase = get_supabase_admin()
        self._offline_df: Optional[pd.DataFrame] = None
        self._offline_date_cols: Optional[list] = None
        self._offline_file = Path(__file__).resolve().parents[2] / "database" / "SmartJal" / "WaterLevels_Krishna" / "master data_updated.xlsx"

    def _load_offline_dataframe(self) -> Optional[pd.DataFrame]:
        if self._offline_df is not None:
            return self._offline_df

        if not self._offline_file.exists():
            return None

        try:
            df = pd.read_excel(self._offline_file, sheet_name="meta-historical")
            date_cols = []
            for col in df.columns:
                if isinstance(col, (datetime, pd.Timestamp)):
                    date_cols.append(col)
                else:
                    try:
                        parsed = pd.to_datetime(col)
                        if parsed.year >= 1990:
                            date_cols.append(col)
                    except Exception:
                        continue

            self._offline_df = df
            self._offline_date_cols = date_cols
            return self._offline_df
        except Exception:
            return None

    def _get_offline_readings(self, village_id: str) -> list:
        df = self._load_offline_dataframe()
        if df is None or not self._offline_date_cols:
            return []

        station_codes = []
        try:
            piezo_resp = self.supabase.table("piezometers").select("station_code").eq("village_id", village_id).execute()
            station_codes = [str(p["station_code"]) for p in (piezo_resp.data or []) if p.get("station_code")]
        except APIError:
            station_codes = []
        except Exception:
            station_codes = []

        subset = pd.DataFrame()
        if station_codes:
            subset = df[df["ID"].astype(str).isin(station_codes)]
        else:
            village_name = None
            try:
                village_resp = self.supabase.table("villages").select("name").eq("id", village_id).single().execute()
                village_name = (village_resp.data or {}).get("name")
            except Exception:
                village_name = None

            if village_name:
                target = village_name.strip().lower()
                village_cols = [col for col in df.columns if "Village" in str(col) and "Name" in str(col)]
                for col in village_cols or ["Village Name"]:
                    if col in df.columns:
                        subset = df[df[col].astype(str).str.strip().str.lower() == target]
                        if not subset.empty:
                            break

        if subset.empty:
            return []

        records = []
        for _, row in subset.iterrows():
            for col in self._offline_date_cols:
                value = row.get(col)
                if pd.isna(value):
                    continue

                ts = col
                if not isinstance(ts, (datetime, pd.Timestamp)):
                    try:
                        ts = pd.to_datetime(ts)
                    except Exception:
                        continue

                try:
                    records.append({
                        "ds": pd.to_datetime(ts).to_pydatetime(),
                        "y": float(value)
                    })
                except Exception:
                    continue
        return records

    def _build_dataframe(self, supabase_data: list, fallback_records: Optional[list] = None) -> Optional[pd.DataFrame]:
        rows = []
        for record in supabase_data or []:
            try:
                rows.append({
                    "ds": pd.to_datetime(record["reading_date"]).tz_localize(None),
                    "y": float(record["water_level_mbgl"])
                })
            except Exception:
                continue

        for record in fallback_records or []:
            try:
                rows.append({
                    "ds": pd.to_datetime(record["ds"]).tz_localize(None),
                    "y": float(record["y"])
                })
            except Exception:
                continue

        if len(rows) < 5:
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
            offline_records = self._get_offline_readings(village_id)
            df = self._build_dataframe(readings_resp.data or [], offline_records)

        if df is None or len(df) < 3:
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
