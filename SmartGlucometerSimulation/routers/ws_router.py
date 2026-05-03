"""
WebSocket endpoints for real-time glucose reading streaming.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from websocket_manager import manager

router = APIRouter()


@router.websocket("/readings")
async def websocket_readings(websocket: WebSocket):
    """
    Connect to receive real-time glucose readings from all devices.
    
    Every time the simulator emits a reading it is pushed here instantly.
    
    Example message:
    {
        "id": "uuid",
        "device_id": "uuid",
        "glucose_mg_dl": 142.3,
        "glucose_mmol_l": 7.9,
        "status": "normal",
        "timestamp": "2024-01-01T12:00:00"
    }
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive — listen for any client messages (e.g. ping)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    Connect to receive real-time alerts (critical highs, lows, low battery).
    Only alert-level events are pushed here, not every reading.
    """
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
