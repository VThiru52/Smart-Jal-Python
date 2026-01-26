import xgboost as xgb
import pandas as pd
from prophet import Prophet
from typing import List, Dict, Any, Optional
from app.core.supabase import get_supabase_admin
import shap
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
        Generates 3, 6, 12-month forecasts for a village.
        Uses Prophet for baseline and XGBoost+SHAP for explainability.
        """
        # 1. Fetch historical data
        readings_resp = self.supabase.table("readings").select(
            "reading_date, water_level_mbgl, piezometers!inner(village_id)"
        ).eq("piezometers.village_id", village_id).order("reading_date").execute()

        df = self._build_dataframe(readings_resp.data)
        if df is None:
            offline_records = self._get_offline_readings(village_id)
            df = self._build_dataframe(readings_resp.data or [], offline_records)

        if df is None:
            return {"error": "Insufficient historical data for forecasting"}

        # 2. Prophet Model (Baseline)
        model_prophet = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model_prophet.fit(df)
        future = model_prophet.make_future_dataframe(periods=periods, freq='M')
        forecast_prophet = model_prophet.predict(future)

        # 3. XGBoost Model for SHAP (only if enough data for lags)
        shap_explanation = None
        if len(df) >= 10:
            try:
                # Prepare features for XGBoost: lags and domain features
                # 1. Fetch village metadata for domain features
                village_resp = self.supabase.table("villages").select("average_rainfall_mm, water_consumption_m3").eq("id", village_id).single().execute()
                v_meta = village_resp.data or {}
                avg_rainfall = v_meta.get("average_rainfall_mm", 850.0) or 850.0
                extraction = v_meta.get("water_consumption_m3", 0.0) or 0.0

                df_xgb = df.copy()
                df_xgb['month'] = df_xgb['ds'].dt.month
                df_xgb['lag1'] = df_xgb['y'].shift(1)
                df_xgb['lag3'] = df_xgb['y'].shift(3)
                
                # Add domain features (Extraction impacts depletion, Rainfall impacts recharge)
                df_xgb['rainfall_deficit'] = avg_rainfall - (df_xgb['y'] * 10) # Proxy for correlation
                df_xgb['extraction_intensity'] = extraction / 1000.0 if extraction > 0 else 0
                
                df_xgb = df_xgb.dropna()

                if not df_xgb.empty:
                    X = df_xgb[['month', 'lag1', 'lag3', 'rainfall_deficit', 'extraction_intensity']]
                    y = df_xgb['y']
                    
                    xgb_model = xgb.XGBRegressor(
                        n_estimators=100, 
                        learning_rate=0.1,
                        importance_type='gain'
                    )
                    xgb_model.fit(X, y)
                    
                    # Explain the latest prediction using SHAP
                    latest_X = X.iloc[[-1]]
                    explainer = shap.Explainer(xgb_model)
                    shap_values = explainer(latest_X)
                    
                    shap_explanation = {
                        "base_value": float(shap_values.base_values[0]),
                        "values": shap_values.values[0].tolist(),
                        "feature_names": X.columns.tolist()
                    }
            except Exception as e:
                print(f"SHAP explanation failed: {str(e)}")
                shap_explanation = None

        # 4. Prepare results and store in DB
        results = forecast_prophet[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(periods)
        
        forecast_entries = []
        for index, row in results.iterrows():
            entry = {
                "village_id": village_id,
                "forecast_date": datetime.now().strftime("%Y-%m-%d"),
                "target_date": row['ds'].strftime("%Y-%m-%d"),
                "predicted_level_mbgl": float(row['yhat']),
                "confidence_score": float((row['yhat_upper'] - row['yhat_lower']) / row['yhat']), # Simple confidence proxy
                "shap_explanation": shap_explanation,
                "model_version": "v1.1-Hybrid"
            }
            forecast_entries.append(entry)
        
        # Store in Supabase
        self.supabase.table("forecasts").insert(forecast_entries).execute()

        # Audit log
        await audit_service.log_action(
            user_id=None,
            action="GENERATE_FORECAST",
            table_name="forecasts",
            new_data={"village_id": village_id, "periods": periods, "count": len(forecast_entries)}
        )

        return {
            "village_id": village_id,
            "forecasts": results.to_dict(orient="records"),
            "explainability": {
                "type": "SHAP (XGBoost)" if shap_explanation else "Baseline (Prophet)",
                "explanation": shap_explanation,
                "note": "SHAP values represent feature contribution to the latest forecast." if shap_explanation else "Explainability is limited due to insufficient data points for complex modeling."
            }
        }

    async def get_shap_explanation(self, model, X):
        """Generic SHAP explainer for XGBoost/LSTM models if used"""
        explainer = shap.Explainer(model)
        shap_values = explainer(X)
        return shap_values

forecasting_service = ForecastingService()
