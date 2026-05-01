from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from models import Alert, AlertAcknowledge
from store import store

router = APIRouter()


@router.get("/", response_model=List[Alert])
def list_alerts(
    device_id: Optional[str] = Query(default=None),
    acknowledged: Optional[bool] = Query(default=None, description="Filter by acknowledgement state"),
    limit: int = Query(default=50, le=500),
):
    """List alerts, optionally filtered."""
    results = store.alerts

    if device_id:
        results = [a for a in results if a.device_id == device_id]
    if acknowledged is not None:
        results = [a for a in results if a.acknowledged == acknowledged]

    return results[-limit:]


@router.get("/{alert_id}", response_model=Alert)
def get_alert(alert_id: str):
    for a in store.alerts:
        if a.id == alert_id:
            return a
    raise HTTPException(status_code=404, detail="Alert not found")


@router.patch("/{alert_id}/acknowledge", response_model=Alert)
def acknowledge_alert(alert_id: str, payload: AlertAcknowledge):
    """Acknowledge (or un-acknowledge) an alert."""
    for i, a in enumerate(store.alerts):
        if a.id == alert_id:
            updated = a.model_copy(update={"acknowledged": payload.acknowledged})
            store.alerts[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="Alert not found")


@router.delete("/acknowledged", status_code=204)
def clear_acknowledged():
    """Delete all acknowledged alerts."""
    store.alerts = [a for a in store.alerts if not a.acknowledged]
