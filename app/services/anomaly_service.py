from app.core.supabase import get_supabase_admin
from typing import List, Dict
import pandas as pd
from datetime import datetime, timedelta
import logging
from app.api.v1.endpoints.websocket import broadcast_alert

from sklearn.ensemble import IsolationForest
import numpy as np

class AnomalyService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def detect_anomalies(self, piezometer_id: str):
        """
        Detects anomalies using both domain-specific thresholds and ML (Isolation Forest).
        """
        # Fetch last 50 readings with station info
        resp = self.supabase.table("readings")\
            .select("reading_date, water_level_mbgl, piezometers(village_id, location_name)")\
            .eq("piezometer_id", piezometer_id)\
            .order("reading_date", desc=True)\
            .limit(50).execute()
        
        if not resp.data or len(resp.data) < 2:
            return None

        df = pd.DataFrame(resp.data)
        df = df.sort_values("reading_date")
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        latest_val = float(latest['water_level_mbgl'])
        prev_val = float(prev['water_level_mbgl'])
        delta = latest_val - prev_val
        
        # Access nested piezometer data
        p_data = latest.get('piezometers', {})
        village_id = p_data.get('village_id')
        location = p_data.get('location_name') or "Unknown Station"

        detected = False
        anomaly_type = "GENERAL"
        severity = "MEDIUM"
        desc = ""

        # 1. Domain-Specific Detection (Rule-based)
        # Sudden Drop (> 1.5m) - Serious concern for groundwater exhaustion
        if delta > 1.5:
            detected = True
            anomaly_type = "SUDDEN_DROP"
            severity = "CRITICAL"
            desc = f"Critical water level drop of {delta:.2f}m detected. Pattern suggests extreme seasonal over-extraction or local aquifer breach."
        
        # Sudden Rise (< -2.5m) - Potential sensor error or sudden flash flood
        elif delta < -2.5:
            detected = True
            anomaly_type = "SUDDEN_RISE"
            severity = "HIGH"
            desc = f"Unusual water level rise of {abs(delta):.2f}m noted. Requires inspection for soil saturation or sensor calibration issues."

        # 2. ML Detection (Isolation Forest) for complex trend deviations
        if not detected and len(df) >= 15:
            X = df[['water_level_mbgl']].values
            diff_feat = np.diff(X, axis=0, prepend=X[0])
            X_features = np.hstack([X, diff_feat])
            
            model = IsolationForest(contamination=0.04, random_state=42)
            model.fit(X_features)
            
            if model.predict(X_features)[-1] == -1:
                detected = True
                anomaly_type = "TREND_DEVIATION"
                severity = "HIGH"
                desc = "Advanced AI model detected a multivariate anomaly in the water level trend, deviating from historical baseline."

        if detected:
            history_mean = df['water_level_mbgl'].mean()
            
            # A. Log to Database
            await self.log_anomaly(
                piezometer_id=piezometer_id,
                date=latest['reading_date'],
                value=latest_val,
                expected=float(history_mean),
                severity=severity,
                desc=desc
            )

            # B. Real-time WebSocket Alert Broadcast
            await broadcast_alert(
                alert_type=anomaly_type,
                message=f"[{severity}] {desc} at station {location}",
                severity=severity.lower(),
                data={
                    "village_id": village_id,
                    "piezo_id": piezometer_id,
                    "location": location,
                    "detected_value": latest_val,
                    "deviation": delta
                }
            )

            # C. Propagate Risk Status to Village
            if village_id:
                await self.propagate_village_risk(village_id, severity)

    async def propagate_village_risk(self, village_id: str, severity: str):
        """Update village record with last anomaly activity and timestamp"""
        try:
            self.supabase.table("villages").update({
                "updated_at": datetime.now().isoformat()
            }).eq("id", village_id).execute()
        except Exception as e:
            logging.error(f"⚠️ Risk propagation error: {e}")

    async def log_anomaly(self, piezometer_id: str, date: str, value: float, expected: float, severity: str, desc: str):
        """Internal helper to insert anomaly record"""
        try:
            self.supabase.table("anomalies").insert({
                "piezometer_id": piezometer_id,
                "event_date": date,
                "detected_value": value,
                "expected_value": expected,
                "severity": severity,
                "description": desc,
                "is_resolved": False
            }).execute()
        except Exception as e:
            logging.error(f"⚠️ Failed to log anomaly: {e}")

anomaly_service = AnomalyService()
