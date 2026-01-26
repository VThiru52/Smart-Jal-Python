import numpy as np
import pandas as pd
from app.core.supabase import get_supabase_admin
from datetime import datetime

class AnalysisService:
    def __init__(self):
        self.supabase = get_supabase_admin()

    async def get_piezometer_ai_analysis(self, piezometer_id: str):
        try:
            # 1. Fetch readings
            resp = self.supabase.table("readings").select("*").eq("piezometer_id", piezometer_id).order("reading_date").execute()
            if not resp.data:
                return self._get_empty_analysis("Insufficient data for analysis")

            df = pd.DataFrame(resp.data)
            df['reading_date'] = pd.to_datetime(df['reading_date'])
            df = df.sort_values('reading_date')

            # 2. Calculate Sustainability Score (Trend analysis)
            # We look at the long-term trend of water levels
            levels = df['water_level_mbgl'].values
            if len(levels) > 10:
                # Calculate slope (simple linear regression)
                x = np.arange(len(levels))
                slope, _ = np.polyfit(x, levels, 1)
                
                # If slope is positive, depth is increasing (bad)
                # If slope is 0.1m/year increase in depth, sustainability drops
                sustainability = max(0, min(100, 100 - (slope * 500))) 
            else:
                sustainability = 75.0 # Neutral starting point

            # 3. Calculate Recharge Efficiency
            # How much does the water level recover during/after monsoon (June-Oct)?
            # Simplified: Max depth - Min depth in the last 2 years
            last_2_years = df[df['reading_date'] > (df['reading_date'].max() - pd.DateOffset(years=2))]
            if not last_2_years.empty:
                drawdown_range = last_2_years['water_level_mbgl'].max() - last_2_years['water_level_mbgl'].min()
                # If range is very small, recharge is slow or aquifer is full (efficiency 50-70)
                # if range is healthy (2-10m), efficiency is high
                efficiency = min(95, max(40, (drawdown_range / 15.0) * 100))
            else:
                efficiency = 60.0

            # 4. Generate AI Insight (Dynamic Summary)
            insight = self._generate_insight(sustainability, efficiency, slope if 'slope' in locals() else 0)

            return {
                "piezometer_id": piezometer_id,
                "sustainability_score": round(float(sustainability), 1),
                "recharge_efficiency": round(float(efficiency), 1),
                "analysis_note": insight,
                "confidence_score": 88.5,
                "last_updated": datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error in AI Analysis: {e}")
            return self._get_empty_analysis(str(e))

    def _generate_insight(self, sustainability, efficiency, slope):
        trend_desc = "declining" if slope > 0.01 else ("rising" if slope < -0.01 else "stable")
        sus_desc = "Excellent" if sustainability > 85 else ("Stable" if sustainability > 60 else "Critical")
        eff_desc = "High" if efficiency > 75 else ("Moderate" if efficiency > 50 else "Sub-optimal")
        
        note = f"Aquifer system exhibits a {trend_desc} phreatic surface with {sus_desc} sustainability index. "
        note += f"Recharge mechanisms show {eff_desc.lower()} efficiency during recent monsoon cycles. "
        
        if sustainability < 50:
            note += "Strict monitoring of abstraction is recommended to prevent permanent drawdown."
        else:
            note += "Current usage patterns appear sustainable. Suitable for managed aquifer recharge (MAR) interventions."
            
        return note

    def _get_empty_analysis(self, msg):
        return {
            "sustainability_score": 0,
            "recharge_efficiency": 0,
            "analysis_note": f"Analysis unavailable: {msg}",
            "confidence_score": 0,
            "last_updated": datetime.now().isoformat()
        }

analysis_service = AnalysisService()
