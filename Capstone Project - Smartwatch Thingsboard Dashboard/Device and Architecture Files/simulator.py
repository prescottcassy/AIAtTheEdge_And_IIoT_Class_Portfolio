import glob
import json
import time
import requests
import pandas as pd
import paho.mqtt.client as mqtt

ACCESS_TOKEN = "fWbkN4E14PAjBnwoFDrz"
HTTP_URL = f"http://thingsboard.cloud/api/v1/{ACCESS_TOKEN}/telemetry"

# MQTT client setup
client = mqtt.Client()
client.tls_set(ca_certs=None)
client.tls_insecure = False
client.username_pw_set(ACCESS_TOKEN)
client.connect("mqtt.thingsboard.cloud", 8883, 60)

# ---------------------------------------------------------
# TELEMETRY MAPPERS
# ---------------------------------------------------------

def map_daily_row(row):
    return {
        "steps": row.get("TotalSteps"),
        "calories": row.get("Calories"),
        "distance": row.get("TotalDistance"),
        "activeMinutes": row.get("VeryActiveMinutes"),
    }

def map_heartrate_row(row):
    return {
        "heartRate": row["Value"]
    }

# ---------------------------------------------------------
# STREAM DAILY FILES IN CHUNKS
# ---------------------------------------------------------

daily_files = [
    f for f in glob.glob("dataset/**/*.csv", recursive=True)
    if "heartrate_seconds_merged.csv" not in f.lower()
]

for file_path in daily_files:
    print(f"Streaming: {file_path}")

    for chunk in pd.read_csv(file_path, chunksize=500):
        for _, row in chunk.iterrows():

            payload = map_daily_row(row)

            # Skip empty rows
            if not any(payload.values()):
                continue

            # Latency fields
            device_ts = int(time.time() * 1000)
            latency = int(time.time() * 1000) - device_ts

            payload["deviceTimestamp"] = device_ts
            payload["latency"] = latency

            # Send HTTP
            requests.post(HTTP_URL, json=payload)

            # Send MQTT
            client.publish("v1/devices/me/telemetry", json.dumps(payload), qos=1)

            time.sleep(1)

# ---------------------------------------------------------
# STREAM HEARTRATE FILES IN CHUNKS
# ---------------------------------------------------------

heartrate_files = glob.glob("dataset/**/heartrate_seconds_merged.csv", recursive=True)

for file_path in heartrate_files:
    print(f"Streaming HR: {file_path}")

    for chunk in pd.read_csv(file_path, chunksize=500, usecols=["Id", "Time", "Value"]):
        for _, row in chunk.iterrows():

            payload = map_heartrate_row(row)

            device_ts = int(time.time() * 1000)
            latency = int(time.time() * 1000) - device_ts

            payload["deviceTimestamp"] = device_ts
            payload["latency"] = latency

            ts = int(pd.to_datetime(row["Time"]).timestamp() * 1000)

            # HTTP
            requests.post(HTTP_URL, json={"ts": ts, "values": payload})

            # MQTT
            client.publish(
                "v1/devices/me/telemetry",
                json.dumps([{"ts": ts, "values": payload}]),
                qos=1
            )

            time.sleep(0.1)
