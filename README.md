# IIoT Glucometer — FastAPI Backend

A simulated Industrial IoT glucometer backend featuring device management, real-time glucose readings, JWT authentication, WebSocket streaming, MQTT integration, a machine learning forecasting model, and full Docker support.

## Quickstart (local)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
sudo mosquitto -c /etc/mosquitto/mosquitto.conf -v
```

Interactive docs at http://localhost:8000/docs

## Quickstart (Docker)

```bash
docker compose up --build
```

Services started:
- FastAPI app at http://localhost:8000
- Mosquitto MQTT broker at localhost:1883

---

## Project Structure

```
.
├── main.py                 # App entry point, lifespan, middleware, route registration
├── models.py               # Pydantic models (Device, GlucoseReading, Alert)
├── database.py             # Sync SQLAlchemy engine, glucose_readings table, get_db
├── store.py                # In-memory store for devices and alerts
├── crud.py                 # DB helpers: save/query glucose readings
├── users.py                # FastAPI Users setup - JWT auth, user table, schemas
├── simulator.py            # Background task - random walk glucose readings every 10s
├── mqtt_client.py          # MQTT subscriber - processes device readings from broker
├── mqtt_simulator.py       # Standalone MQTT device simulator for testing
├── ml_model.py             # Linear regression forecaster - predicts next glucose value
├── websocket_manager.py    # WebSocket connection manager - broadcasts to all clients
├── create_tables.py        # One-time script to initialise database tables
├── loader.py               # CSV loader - imports real glucose datasets into the DB
├── Dockerfile              # Container definition for the FastAPI app
├── docker-compose.yml      # Orchestrates FastAPI + Mosquitto broker
├── mosquitto.conf          # Mosquitto broker configuration
├── .env                    # Local environment variable defaults
├── .dockerignore           # Files excluded from the Docker build context
├── requirements.txt        # Python dependencies
└── routers/
    ├── __init__.py
    ├── devices.py          # CRUD endpoints for glucometer devices
    ├── readings.py         # Glucose reading endpoints (DB-backed, JWT protected)
    ├── alerts.py           # Alert management and acknowledgement
    ├── predictions.py      # ML forecast endpoints
    └── ws_router.py        # WebSocket endpoints for real-time streaming
```

---

## API Overview

### Auth
All protected routes require: Authorization: Bearer <token>

| Method | Endpoint              | Description                    |
|--------|-----------------------|--------------------------------|
| POST   | /auth/register        | Create a new user account      |
| POST   | /auth/jwt/login       | Login and receive a JWT token  |
| POST   | /auth/jwt/logout      | Invalidate token               |
| GET    | /me                   | Current authenticated user     |

### Devices
| Method | Endpoint          | Description                        |
|--------|-------------------|------------------------------------|
| GET    | /devices/         | List all registered devices        |
| POST   | /devices/         | Register a new device              |
| PATCH  | /devices/{id}     | Update device status or battery    |
| DELETE | /devices/{id}     | Remove a device                    |

### Readings
| Method | Endpoint              | Description                                      |
|--------|-----------------------|--------------------------------------------------|
| GET    | /readings/            | List readings (filter by device, status, limit)  |
| GET    | /readings/latest      | Latest reading per device                        |
| GET    | /readings/{id}        | Single reading by ID                             |
| POST   | /readings/            | Manually push a reading                          |

### Alerts
| Method | Endpoint                     | Description                          |
|--------|------------------------------|--------------------------------------|
| GET    | /alerts/                     | List alerts                          |
| PATCH  | /alerts/{id}/acknowledge     | Acknowledge an alert                 |
| DELETE | /alerts/acknowledged         | Clear all acknowledged alerts        |

### Predictions (ML)
| Method | Endpoint                  | Description                          |
|--------|---------------------------|--------------------------------------|
| GET    | /predictions/             | Forecast for all devices             |
| GET    | /predictions/{device_id}  | Forecast for a specific device       |

### WebSockets
| Endpoint                            | Description                     |
|-------------------------------------|---------------------------------|
| ws://localhost:8000/ws/readings     | Real-time glucose reading stream|
| ws://localhost:8000/ws/alerts       | Real-time alert stream          |

---

## Glucose Status Thresholds

| Status        | Range (mg/dL) |
|---------------|---------------|
| critical_low  | < 54          |
| low           | 54 to 69      |
| normal        | 70 to 180     |
| high          | 181 to 250    |
| critical_high | > 250         |

---

## MQTT

Devices publish to topic: glucometer/readings/{device_id}

Payload: {"glucose_mg_dl": 134.5}

Test with mosquitto_pub:
  mosquitto_pub -h 127.0.0.1 -t "glucometer/readings/GLU-001" -m '{"glucose_mg_dl": 145}'

Run the simulator:
  python3 mqtt_simulator.py

---

## Machine Learning Model

Linear regression over a rolling window of 6 readings per device.
Predicts next glucose value and classifies trend direction.

Trend labels: stable, rising, rising_fast, falling, falling_fast
Confidence: high, medium, low (based on reading window variance)

---

## Real Glucose Datasets

| Dataset             | Source           | Access          |
|---------------------|------------------|-----------------|
| Diabetes 130-US     | UCI ML Repo      | Free, no signup |
| OpenAPS Commons     | openhumans.org   | Free            |
| OhioT1DM            | ohio.edu         | Request access  |
| Tidepool            | tidepool.org     | Request access  |

---

## Environment Variables

| Variable            | Default                               | Description                          |
|---------------------|---------------------------------------|--------------------------------------|
| MQTT_BROKER         | 127.0.0.1                             | Broker host (use "mosquitto" Docker) |
| SYNC_DATABASE_URL   | sqlite:///./glucometer.db             | Sync SQLAlchemy DB URL               |
| DATABASE_URL        | sqlite+aiosqlite:///./glucometer.db   | Async DB URL for fastapi-users       |
| SECRET_KEY          | change-me                             | JWT signing secret                   |

---

## Dependencies

| Package             | Purpose                          |
|---------------------|----------------------------------|
| fastapi             | Web framework                    |
| uvicorn             | ASGI server                      |
| pydantic            | Data validation                  |
| sqlalchemy          | ORM and DB access                |
| aiosqlite           | Async SQLite driver              |
| fastapi-users       | Auth, JWT, user management       |
| aiomqtt             | Async MQTT client                |
| numpy               | ML model (linear regression)     |
| websockets          | WebSocket test client            |
| python-multipart    | OAuth2 form login support        |

---

## Next Steps

- Swap SQLite for PostgreSQL by updating DATABASE_URL
- Add role-based access control (admin vs read-only)
- Connect a real CGM device via MQTT
- Build a React/Vue dashboard consuming the WebSocket feed
- Add Alembic for database migrations
