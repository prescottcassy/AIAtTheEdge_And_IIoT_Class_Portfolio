"""
MQTT Integration
-----------------
Subscribes to glucometer/readings/# and processes incoming messages.
Each device publishes to: glucometer/readings/{device_id}

Message format (JSON):
{
    "glucose_mg_dl": 134.5
}
"""

import asyncio
import json
import os

import aiomqtt

from models import GlucoseReading, Alert
from store import store
from database import SessionLocal
from crud import save_reading
from ml_model import forecaster
from websocket_manager import manager

import os
MQTT_BROKER = os.getenv("MQTT_BROKER", "127.0.0.1")
MQTT_PORT   = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC  = "glucometer/readings/#"


def _maybe_raise_alert(reading: GlucoseReading):
    if reading.status in ("critical_low", "critical_high", "low", "high"):
        messages = {
            "critical_low":  f"CRITICAL: Glucose dangerously low ({reading.glucose_mg_dl} mg/dL)",
            "low":           f"WARNING: Low glucose detected ({reading.glucose_mg_dl} mg/dL)",
            "high":          f"WARNING: High glucose detected ({reading.glucose_mg_dl} mg/dL)",
            "critical_high": f"CRITICAL: Glucose dangerously high ({reading.glucose_mg_dl} mg/dL)",
        }
        store.alerts.append(Alert(
            device_id=reading.device_id,
            alert_type=reading.status,
            message=messages[reading.status],
        ))


async def _process(device_id: str, glucose_mg_dl: float):
    reading = GlucoseReading.from_mg_dl(device_id, glucose_mg_dl)

    # 1. Save to DB
    db = SessionLocal()
    try:
        save_reading(db, reading)
    finally:
        db.close()

    # 2. Alerts
    _maybe_raise_alert(reading)

    # 3. ML model
    forecaster.ingest(reading)

    # 4. Broadcast via WebSocket
    await manager.broadcast({
        "event": "reading",
        "source": "mqtt",
        "data": reading.model_dump(),
    })

    # 5. Keep in-memory
    store.readings.append(reading)
    store.readings = store.readings[-200:]

    print(f"[MQTT] {device_id} → {reading.glucose_mg_dl} mg/dL ({reading.status})")


async def _listener():
    print(f"[MQTT] Connecting to {MQTT_BROKER}:{MQTT_PORT}")
    try:
        async with aiomqtt.Client(MQTT_BROKER, MQTT_PORT) as client:
            await client.subscribe(MQTT_TOPIC)
            print(f"[MQTT] Subscribed to {MQTT_TOPIC}")
            async for message in client.messages:
                try:
                    topic = str(message.topic)
                    device_id = topic.split("/")[-1]
                    payload = json.loads(message.payload.decode())
                    glucose_mg_dl = float(payload["glucose_mg_dl"])

                    # Auto-register unknown devices
                    if device_id not in store.devices:
                        from models import Device
                        store.devices[device_id] = Device(
                            id=device_id,
                            name=f"MQTT-{device_id[:8]}",
                            location="unknown",
                        )

                    await _process(device_id, glucose_mg_dl)

                except Exception as e:
                    print(f"[MQTT] Error processing message: {e}")
    except Exception as e:
        print(f"[MQTT] Connection error: {e}")


async def start_mqtt():
    """Start the MQTT listener (called from lifespan)."""
    await _listener()


async def stop_mqtt():
    """Graceful shutdown (called from lifespan)."""
    print("[MQTT] Shutting down listener")
