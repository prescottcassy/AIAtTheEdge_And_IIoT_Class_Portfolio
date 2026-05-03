"""
Glucose Forecasting Model
--------------------------
Uses a rolling window of recent readings per device to predict the next
glucose value via linear regression (numpy least-squares).

No heavy ML framework needed — scikit-learn is optional and only used
if you want to swap to a richer model later.

Window size: last N readings → predict reading N+1.
"""

import numpy as np
from collections import defaultdict
from typing import Optional

from models import GlucoseReading

WINDOW_SIZE = 6  # number of past readings used to forecast


class GlucoseForecaster:
    """
    Per-device linear regression forecaster.
    Fits on the last WINDOW_SIZE readings and predicts the next value.
    """

    def __init__(self, window_size: int = WINDOW_SIZE):
        self.window_size = window_size
        # device_id -> list of recent mg/dL values (capped at window_size)
        self._history: dict[str, list[float]] = defaultdict(list)

    def ingest(self, reading: GlucoseReading):
        """Feed a new reading into the model's history."""
        buf = self._history[reading.device_id]
        buf.append(reading.glucose_mg_dl)
        # Keep only the last window_size + a little buffer
        if len(buf) > self.window_size * 3:
            self._history[reading.device_id] = buf[-(self.window_size * 3):]

    def predict(self, device_id: str) -> Optional[dict]:
        """
        Predict the next glucose value for a device.
        Returns None if there are not enough readings yet.
        """
        buf = self._history.get(device_id, [])
        if len(buf) < self.window_size:
            return None

        window = np.array(buf[-self.window_size:], dtype=float)
        x = np.arange(self.window_size, dtype=float)

        # Least-squares linear fit: y = mx + b
        coeffs = np.polyfit(x, window, deg=1)
        slope, intercept = coeffs

        # Predict the next step (index = window_size)
        predicted_mg_dl = float(slope * self.window_size + intercept)
        # Clamp to physiologically plausible range
        predicted_mg_dl = round(max(20.0, min(600.0, predicted_mg_dl)), 1)
        predicted_mmol_l = round(predicted_mg_dl / 18.0182, 2)

        predicted_status = GlucoseReading.derive_status(predicted_mg_dl)

        return {
            "device_id": device_id,
            "predicted_glucose_mg_dl": predicted_mg_dl,
            "predicted_glucose_mmol_l": predicted_mmol_l,
            "predicted_status": predicted_status,
            "trend": _trend_label(slope),
            "slope_mg_dl_per_reading": round(slope, 2),
            "window_size_used": self.window_size,
            "confidence": _confidence(window),
        }

    def predict_all(self) -> list[dict]:
        """Return predictions for all devices that have enough history."""
        results = []
        for device_id in self._history:
            pred = self.predict(device_id)
            if pred:
                results.append(pred)
        return results


# --- Helpers ---

def _trend_label(slope: float) -> str:
    if slope > 5:
        return "rising_fast"
    elif slope > 1.5:
        return "rising"
    elif slope < -5:
        return "falling_fast"
    elif slope < -1.5:
        return "falling"
    else:
        return "stable"


def _confidence(window: np.ndarray) -> str:
    """
    Simple confidence heuristic based on variance in the window.
    Low variance → high confidence in the linear trend.
    """
    std = float(np.std(window))
    if std < 8:
        return "high"
    elif std < 20:
        return "medium"
    else:
        return "low"


# Singleton instance shared across the app
forecaster = GlucoseForecaster()
