from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from models import GlucoseReading
from store import store
from database import get_db
from crud import get_readings, get_reading_by_id, get_latest_per_device, save_reading
from ml_model import forecaster
from users import current_active_user

router = APIRouter()


@router.get("/", response_model=List[GlucoseReading])
def list_readings(
    device_id: Optional[str] = Query(default=None, description="Filter by device ID"),
    status: Optional[str] = Query(default=None, description="Filter by status (normal, low, high, critical_low, critical_high)"),
    limit: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
    user=Depends(current_active_user),        # 🔒 JWT protected
):
    """Retrieve glucose readings from the database."""
    return get_readings(db, device_id=device_id, status=status, limit=limit)


@router.get("/latest", response_model=List[GlucoseReading])
def latest_readings(
    db: Session = Depends(get_db),
    user=Depends(current_active_user),        # 🔒 JWT protected
):
    """Return the most recent reading per device from the database."""
    return get_latest_per_device(db)


@router.get("/{reading_id}", response_model=GlucoseReading)
def get_reading(
    reading_id: str,
    db: Session = Depends(get_db),
    user=Depends(current_active_user),        # 🔒 JWT protected
):
    reading = get_reading_by_id(db, reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    return reading


@router.post("/", response_model=GlucoseReading, status_code=201)
def manual_reading(
    device_id: str,
    glucose_mg_dl: float = Query(..., ge=20, le=600),
    db: Session = Depends(get_db),
    user=Depends(current_active_user),        # 🔒 JWT protected
):
    """Manually push a glucose reading — persisted to the database."""
    if device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    reading = GlucoseReading.from_mg_dl(device_id, glucose_mg_dl)
    save_reading(db, reading)
    forecaster.ingest(reading)
    return reading
