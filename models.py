from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


# --- Device ---

class Device(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: str
    status: Literal["online", "offline", "error"] = "online"
    battery_level: int = Field(default=100, ge=0, le=100)  # percent
    firmware_version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)

class DeviceCreate(BaseModel):
    name: str
    location: str
    firmware_version: str = "1.0.0"

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[Literal["online", "offline", "error"]] = None
    battery_level: Optional[int] = Field(default=None, ge=0, le=100)


# --- Reading ---

class GlucoseReading(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    glucose_mg_dl: float = Field(..., ge=20, le=600)   # mg/dL — typical sensor range
    glucose_mmol_l: float                               # auto-derived
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    unit: Literal["mg/dL", "mmol/L"] = "mg/dL"
    status: Literal["normal", "low", "high", "critical_low", "critical_high"] = "normal"

    @staticmethod
    def derive_status(mg_dl: float) -> str:
        if mg_dl < 54:
            return "critical_low"
        elif mg_dl < 70:
            return "low"
        elif mg_dl <= 180:
            return "normal"
        elif mg_dl <= 250:
            return "high"
        else:
            return "critical_high"

    @classmethod
    def from_mg_dl(cls, device_id: str, mg_dl: float) -> "GlucoseReading":
        mmol = round(mg_dl / 18.0182, 2)
        status = cls.derive_status(mg_dl)
        return cls(
            device_id=device_id,
            glucose_mg_dl=round(mg_dl, 1),
            glucose_mmol_l=mmol,
            status=status,
        )


# --- Alert ---

class Alert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    reading_id: Optional[str] = None
    alert_type: Literal["critical_low", "critical_high", "high", "low", "device_offline", "low_battery"]
    message: str
    acknowledged: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class AlertAcknowledge(BaseModel):
    acknowledged: bool = True
