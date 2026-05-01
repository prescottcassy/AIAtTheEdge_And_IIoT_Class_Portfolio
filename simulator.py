"""
Background simulator: every 10 seconds each online device emits a glucose reading.
Readings follow a random walk within a realistic range so the data looks believable.
"""
import asyncio
import random
from datetime import datetime

from models import GlucoseReading, Alert
from store import store
from ml_model import forecaster
from database import SessionLocal
from crud import save_reading
from websocket_manager import manager

# Per-device current glucose level (simulated walk)
_current_glucose: dict[str, float] = {}
_running = True


def _next_glucose(device_id: str) -> float:
    """Random walk ±5–15 mg/dL per tick, clamped to [55, 350]."""
    current = _current_glucose.get(device_id, random.uniform(90, 130))
    delta = random.uniform(-15, 15)
    new_val = max(55.0, min(350.0, current + delta))
    _current_glucose[device_id] = new_val
    return new_val


def _maybe_raise_alert(reading: GlucoseReading):
    """Create an alert for out-of-range readings."""
    if reading.status in ("critical_low", "critical_high", "low", "high"):
        messages = {
            "critical_low": f"CRITICAL: Glucose dangerously low ({reading.glucose_mg_dl} mg/dL)",
            "low":          f"WARNING: Low glucose detected ({reading.glucose_mg_dl} mg/dL)",
            "high":         f"WARNING: High glucose detected ({reading.glucose_mg_dl} mg/dL)",
            "critical_high":f"CRITICAL: Glucose dangerously high ({reading.glucose_mg_dl} mg/dL)",
        }
        alert = Alert(
            device_id=reading.device_id,
            reading_id=reading.id,
            alert_type=reading.status,
            message=messages[reading.status],
        )
        store.alerts.append(alert)


async def start_simulator():
    global _running
    _running = True
    while _running:
        for device in list(store.devices.values()):
            if device.status != "online":
                continue

            # Simulate slight battery drain
            device.battery_level = max(0, device.battery_level - random.randint(0, 1))
            if device.battery_level < 15:
                # Raise low battery alert (once per cycle, avoid spamming)
                existing = [
                    a for a in store.alerts
                    if a.device_id == device.id
                    and a.alert_type == "low_battery"
                    and not a.acknowledged
                ]
                if not existing:
                    store.alerts.append(Alert(
                        device_id=device.id,
                        alert_type="low_battery",
                        message=f"Low battery on {device.name}: {device.battery_level}%",
                    ))

            mg_dl = _next_glucose(device.id)
            reading = GlucoseReading.from_mg_dl(device.id, mg_dl)

            # Persist to database
            db = SessionLocal()
            try:
                save_reading(db, reading)
            finally:
                db.close()

            _maybe_raise_alert(reading)

            # Feed reading into the forecasting model
            forecaster.ingest(reading)

            # Broadcast to all connected WebSocket clients
            await manager.broadcast({
                "event": "reading",
                "data": reading.model_dump(),
            })

            # Keep in-memory list for alerts (lightweight, no DB needed)
            store.readings.append(reading)
            store.readings = store.readings[-200:]

        await asyncio.sleep(10)


async def stop_simulator(task: asyncio.Task):
    global _running
    _running = False
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
