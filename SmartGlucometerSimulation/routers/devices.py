from fastapi import APIRouter, HTTPException
from typing import List

from models import Device, DeviceCreate, DeviceUpdate
from store import store

router = APIRouter()


@router.get("/", response_model=List[Device])
def list_devices():
    """Return all registered devices."""
    return list(store.devices.values())


@router.get("/{device_id}", response_model=Device)
def get_device(device_id: str):
    device = store.devices.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.post("/", response_model=Device, status_code=201)
def create_device(payload: DeviceCreate):
    """Register a new simulated glucometer device."""
    device = Device(name=payload.name, location=payload.location, firmware_version=payload.firmware_version)
    store.devices[device.id] = device
    return device


@router.patch("/{device_id}", response_model=Device)
def update_device(device_id: str, payload: DeviceUpdate):
    device = store.devices.get(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    update_data = payload.model_dump(exclude_none=True)
    updated = device.model_copy(update=update_data)
    store.devices[device_id] = updated
    return updated


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: str):
    if device_id not in store.devices:
        raise HTTPException(status_code=404, detail="Device not found")
    del store.devices[device_id]
