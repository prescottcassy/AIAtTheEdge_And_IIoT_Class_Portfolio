"""
WebSocket Connection Manager
Tracks all active WebSocket connections and broadcasts messages to them.
"""

from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WS] Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"[WS] Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        """Send a message to all connected clients."""
        if not self.active_connections:
            return
        message = json.dumps(data, default=str)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        # Clean up dead connections
        for conn in dead:
            self.active_connections.remove(conn)


# Singleton — shared across the app
manager = ConnectionManager()
