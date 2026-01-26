from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.schemas import ReadingCreate, Reading
from app.core.supabase import get_supabase_admin
from typing import List
import pandas as pd
from io import StringIO

router = APIRouter()

from app.services.audit_service import audit_service
from app.services.anomaly_service import anomaly_service

@router.post("/readings", response_model=List[Reading])
async def ingest_readings(
    readings: List[ReadingCreate],
    background_tasks: BackgroundTasks,
    supabase = Depends(get_supabase_admin)
):
    """Ingest multiple piezometer readings"""
    data_to_insert = [r.model_dump(mode='json') for r in readings]
    
    result = supabase.table("readings").insert(data_to_insert).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to ingest readings")
    
    # Audit log
    background_tasks.add_task(
        audit_service.log_action, 
        user_id=None, # In production, get from auth
        action="BULK_INGEST_READINGS",
        table_name="readings",
        new_data={"count": len(data_to_insert)}
    )
    
    # Trigger background feature engineering/anomaly detection
    background_tasks.add_task(process_ingested_data, data_to_insert)
    
    return result.data

@router.post("/reading", response_model=Reading)
async def ingest_single_reading(
    reading: ReadingCreate,
    background_tasks: BackgroundTasks,
    supabase = Depends(get_supabase_admin)
):
    """Ingest a single piezometer reading"""
    data = reading.model_dump(mode='json')
    result = supabase.table("readings").insert(data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to ingest reading")
    
    # Audit log
    background_tasks.add_task(
        audit_service.log_action,
        user_id=None,
        action="SINGLE_INGEST_READING",
        table_name="readings",
        new_data=data
    )
    
    background_tasks.add_task(process_ingested_data, [data])
    return result.data[0]

@router.post("/bulk-csv")
async def ingest_bulk_csv(
    file_content: str,
    background_tasks: BackgroundTasks,
    supabase = Depends(get_supabase_admin)
):
    """Bulk ingest readings via CSV content"""
    try:
        df = pd.read_csv(StringIO(file_content))
        # Validate columns
        required_cols = {"piezometer_id", "reading_date", "water_level_mbgl"}
        if not required_cols.issubset(df.columns):
            raise HTTPException(status_code=400, detail=f"Missing required columns: {required_cols - set(df.columns)}")
        
        data = df.to_dict(orient="records")
        result = supabase.table("readings").insert(data).execute()
        
        # Audit log
        background_tasks.add_task(
            audit_service.log_action,
            user_id=None,
            action="CSV_INGEST_READINGS",
            table_name="readings",
            new_data={"count": len(data)}
        )
        
        background_tasks.add_task(process_ingested_data, data)
        return {"status": "success", "count": len(data)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

async def process_ingested_data(data: List[dict]):
    """Background task for feature engineering and anomaly detection"""
    for entry in data:
        if "piezometer_id" in entry:
            await anomaly_service.detect_anomalies(entry["piezometer_id"])
