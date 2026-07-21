"""
Digital Twin: state estimation, anomaly detection, sensor fusion.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import numpy as np


class SensorReading(BaseModel):
    """A single sensor reading."""
    sensor_id: str
    sensor_type: str                          # temperature | pressure | flow | co2 | o2 | power
    value: float
    unit: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    quality: float = 1.0                       # 0-1, sensor health


class TwinState(BaseModel):
    """Estimated state of a process."""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    estimated: Dict[str, float]               # variable -> estimated value
    uncertainty: Dict[str, float]             # variable -> 1-sigma
    predictions: Dict[str, float]             # variable -> next-step prediction
    anomalies: List[str] = Field(default_factory=list)


class DigitalTwin:
    """
    A simplified digital twin for a cement plant or brick kiln.

    Maintains:
      - A Kalman filter per measured variable
      - Anomaly detection (z-score from rolling history)
      - Process historian (last N readings)
    """

    def __init__(self, plant_name: str, history_size: int = 1000) -> None:
        self.plant_name = plant_name
        self.history_size = history_size
        self.history: Dict[str, List[float]] = {}
        # Kalman state per variable: (x, P)
        self.kalman_state: Dict[str, tuple] = {}

    def update(self, readings: List[SensorReading]) -> TwinState:
        """Process new sensor readings, update Kalman filters and detect anomalies."""
        estimates: Dict[str, float] = {}
        uncertainties: Dict[str, float] = {}
        predictions: Dict[str, float] = {}
        anomalies: List[str] = []

        for r in readings:
            key = f"{r.sensor_id}_{r.sensor_type}"
            # Store in history
            self.history.setdefault(key, []).append(r.value)
            if len(self.history[key]) > self.history_size:
                self.history[key].pop(0)

            # Kalman update
            x_new, P_new = kalman_update(
                self.kalman_state.get(key, (r.value, 1.0)),
                r.value,
                r.quality,
            )
            self.kalman_state[key] = (x_new, P_new)
            estimates[key] = float(x_new)
            uncertainties[key] = float(np.sqrt(P_new))

            # Anomaly detection
            if detect_anomaly(self.history[key], r.value, threshold=3.5):
                anomalies.append(f"{key}={r.value} (z-score > 3.5)")

            # Next-step prediction (linear extrapolation)
            if len(self.history[key]) >= 2:
                dx = self.history[key][-1] - self.history[key][-2]
                predictions[key] = float(x_new + dx)
            else:
                predictions[key] = float(x_new)

        return TwinState(
            estimated=estimates,
            uncertainty=uncertainties,
            predictions=predictions,
            anomalies=anomalies,
        )

    def get_state(self) -> TwinState:
        """Get current state without updating."""
        estimates = {k: v[0] for k, v in self.kalman_state.items()}
        uncertainties = {k: float(np.sqrt(v[1])) for k, v in self.kalman_state.items()}
        predictions = {k: v[0] for k, v in self.kalman_state.items()}  # placeholder
        return TwinState(
            estimated=estimates,
            uncertainty=uncertainties,
            predictions=predictions,
        )


def kalman_update(state: tuple, measurement: float, quality: float = 1.0,
                   process_noise: float = 0.1, measurement_noise: float = 1.0) -> tuple:
    """
    Simple 1D Kalman filter update.

    State: (x, P) — estimate and its variance.
    """
    x, P = state
    # Predict (random walk)
    P = P + process_noise
    # Update
    R = measurement_noise / max(quality, 0.01)   # measurement noise
    K = P / (P + R)                              # Kalman gain
    x_new = x + K * (measurement - x)
    P_new = (1 - K) * P
    return x_new, P_new


def detect_anomaly(history: List[float], value: float, threshold: float = 3.0) -> bool:
    """
    Z-score based anomaly detection.

    Returns True if value is more than `threshold` std deviations from the
    rolling mean.
    """
    if len(history) < 10:
        return False
    arr = np.array(history[:-1])                 # exclude the new value
    mean = arr.mean()
    std = arr.std()
    if std < 1e-9:
        return False
    z = abs((value - mean) / std)
    return z > threshold
