"""
MQTT Device Simulator
----------------------
Simulates physical glucometer devices publishing readings to the broker.
Run this in a separate terminal to generate test data.

Usage: python3 mqtt_simulator.py

Each simulated device publishes to:
  glucometer/readings/{device_id}

Every 10 seconds, just like the original simulator.
"""

import asyncio
import json
import random
import aiomqtt

MQTT_BROKER = "127.0.0.1"
MQTT_PORT = 1883

DEVICES = [
    "GLU-001",
    "GLU-002",
    "GLU-003",
]

# Per-device glucose state
_glucose: dict[str, float] = {d: random.uniform(90, 130) for d in DEVICES}


def _next_glucose(device_id: str) -> float:
    current = _glucose[device_id]
    delta = random.uniform(-15, 15)
    new_val = max(55.0, min(350.0, current + delta))
    _glucose[device_id] = new_val
    return round(new_val, 1)


async def simulate():
    print(f"[SIM] Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
    async with aiomqtt.Client(MQTT_BROKER, MQTT_PORT) as client:
        print(f"[SIM] Publishing readings for devices: {DEVICES}")
        while True:
            for device_id in DEVICES:
                glucose = _next_glucose(device_id)
                payload = json.dumps({"glucose_mg_dl": glucose})
                topic = f"glucometer/readings/{device_id}"
                await client.publish(topic, payload)
                print(f"[SIM] {device_id} → {glucose} mg/dL")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(simulate())
