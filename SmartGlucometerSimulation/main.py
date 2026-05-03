from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from routers import devices, readings, alerts, predictions
from routers.ws_router import router as ws_router
from simulator import start_simulator, stop_simulator
from mqtt_client import start_mqtt, stop_mqtt
from database import init_db
from users import (
    fastapi_users, auth_backend,
    UserRead, UserCreate, UserUpdate,
    current_active_user, init_user_db
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await init_user_db()
    # Run both simulator and MQTT side by side
    # Comment out start_simulator if you want MQTT-only
    sim_task  = asyncio.create_task(start_simulator())
    mqtt_task = asyncio.create_task(start_mqtt())
    yield
    await stop_simulator(sim_task)
    await stop_mqtt()
    mqtt_task.cancel()


app = FastAPI(
    title="IIoT Glucometer API",
    description="Simulated Industrial IoT Glucometer backend — device management, glucose readings, and alerts.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth routes (fastapi-users) ---
# POST /auth/jwt/login      → get JWT token
# POST /auth/jwt/logout     → invalidate token
# POST /auth/register       → create account
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["Users"],
)

# --- App routes ---
app.include_router(devices.router,     prefix="/devices",     tags=["Devices"])
app.include_router(readings.router,    prefix="/readings",    tags=["Readings"])
app.include_router(alerts.router,      prefix="/alerts",      tags=["Alerts"])
app.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
app.include_router(ws_router,          prefix="/ws",          tags=["WebSockets"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "service": "IIoT Glucometer API"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


# --- Protected route example ---
@app.get("/me", tags=["Auth"])
async def get_me(user=Depends(current_active_user)):
    return {"id": str(user.id), "email": user.email, "is_active": user.is_active}
