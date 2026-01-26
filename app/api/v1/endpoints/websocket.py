from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import logging

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"WebSocket connected. Active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a JSON message to all active connections.
        Useful for real-time alerts and water level updates.
        """
        payload = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception as e:
                logging.error(f"Error broadcasting to client: {e}")
                # Potentially remove dead connection here
                pass

manager = ConnectionManager()

@router.websocket("/ws/realtime-data")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection open and listen for client messages if needed
            data = await websocket.receive_text()
            # Echo back for heartbeat/testing
            await manager.send_personal_message(f"ACK: {data}", websocket)
    except WebSocketDisconnect:
        print("WebSocket client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        # logging.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# Helper function to be called from other parts of the application
async def broadcast_alert(alert_type: str, message: str, severity: str = "info", data: Dict = None):
    """
    Broadcast an alert to all connected clients.
    """
    payload = {
        "type": "ALERT",
        "alert_type": alert_type, # e.g., "WATER_LEVEL_DROP", "SENSOR_FAILURE"
        "message": message,
        "severity": severity, # "critical", "moderate", "low", "info"
        "data": data or {}
    }
    await manager.broadcast(payload)
