from fastapi import APIRouter, HTTPException
from typing import List, Optional

from ml_model import forecaster

router = APIRouter()


@router.get("/", response_model=List[dict])
def all_predictions():
    """
    Return next-reading predictions for all devices that have
    accumulated enough history (minimum window size readings).
    """
    results = forecaster.predict_all()
    if not results:
        return []
    return results


@router.get("/{device_id}", response_model=dict)
def predict_device(device_id: str):
    """
    Predict the next glucose value for a specific device.

    Returns:
    - predicted_glucose_mg_dl / mmol_l
    - predicted_status  (normal / low / high / critical_low / critical_high)
    - trend             (stable / rising / rising_fast / falling / falling_fast)
    - slope_mg_dl_per_reading
    - confidence        (high / medium / low)
    - window_size_used
    """
    result = forecaster.predict(device_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Not enough readings yet for device '{device_id}'. "
                   f"Need at least {forecaster.window_size} readings.",
        )
    return result
