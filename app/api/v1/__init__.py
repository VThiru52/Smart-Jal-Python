from fastapi import APIRouter
from app.api.v1.endpoints import ingest, village, anomalies, recharge, spatial, pumping, auth, drought, websocket

api_router = APIRouter()

api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(village.router, prefix="/village", tags=["village"])
api_router.include_router(anomalies.router, prefix="/anomalies", tags=["anomalies"])
api_router.include_router(recharge.router, prefix="/recharge", tags=["recharge"])
api_router.include_router(spatial.router, prefix="/spatial", tags=["spatial"])
api_router.include_router(pumping.router, prefix="/pumping", tags=["pumping"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(drought.router, prefix="/drought", tags=["drought"])
api_router.include_router(websocket.router, tags=["websocket"])

