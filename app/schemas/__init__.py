from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List, Dict, Any

# --- Reading Models ---
class ReadingBase(BaseModel):
    piezometer_id: str
    reading_date: datetime
    water_level_mbgl: float
    temperature_c: Optional[float] = None
    quality_index: Optional[str] = None

class ReadingCreate(ReadingBase):
    pass

class Reading(ReadingBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# --- Village Models ---
class VillageBase(BaseModel):
    name: str
    district: str = "Krishna"
    sub_district: Optional[str] = None
    mandal: Optional[str] = None
    population: Optional[int] = None
    average_rainfall_mm: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Land and area attributes
    land_area_ha: Optional[float] = None
    total_area_ha: Optional[float] = None
    agricultural_area_ha: Optional[float] = None
    # Soil attributes
    soil_type: Optional[str] = None
    soil_texture: Optional[str] = None
    soil_drainage: Optional[str] = None
    # Elevation
    elevation_m: Optional[float] = None
    # Water consumption
    water_consumption_m3: Optional[float] = None
    agricultural_consumption_m3: Optional[float] = None


class Village(VillageBase):
    id: str
    boundary: Optional[Any] = None
    centroid: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Forecast Models ---
class ForecastBase(BaseModel):
    village_id: str
    forecast_date: date
    target_date: date
    predicted_level_mbgl: float
    confidence_score: Optional[float] = None
    shap_explanation: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None

class Forecast(ForecastBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Anomaly Models ---
# --- Piezometer Models ---
class PiezometerSimple(BaseModel):
    id: str
    station_code: str
    location_name: str
    
    class Config:
        from_attributes = True

# --- Anomaly Models ---
class AnomalyBase(BaseModel):
    piezometer_id: str
    event_date: datetime
    detected_value: float
    expected_value: Optional[float] = None
    severity: str
    description: Optional[str] = None

class Anomaly(AnomalyBase):
    id: str
    is_resolved: bool
    created_at: datetime
    piezometers: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

# --- Recharge Zone Models ---
class RechargeZoneBase(BaseModel):
    village_id: str
    priority_score: float
    suitability_rank: int
    recommendation_logic: str

class RechargeZone(RechargeZoneBase):
    id: str
    geom: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
