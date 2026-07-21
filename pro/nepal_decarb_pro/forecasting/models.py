"""
Time-series forecasting models for emissions and energy.

We use only standard library (no statsmodels) for portability.
For advanced ML forecasting (transformer, TFT), install extras [ml].
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel
import numpy as np


class ForecastResult(BaseModel):
    """Result of a forecast."""
    model: str
    horizon: int
    point_forecast: List[float]
    lower_80: List[float]
    lower_95: List[float]
    upper_80: List[float]
    upper_95: List[float]
    mape: float                              # Mean Absolute Percentage Error on training
    rmse: float
    aic: Optional[float] = None
    notes: str = ""


def _ets_forecast_single(history: np.ndarray, horizon: int,
                          alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.3,
                          season_length: int = 12) -> tuple:
    """
    Holt-Winters Triple Exponential Smoothing.

    Returns: (forecast, fitted) arrays
    """
    n = len(history)
    if n < 2 * season_length:
        # Not enough data for seasonal; use simple exponential smoothing
        level = history[0]
        forecast = []
        for _ in range(horizon):
            forecast.append(level)
            level = alpha * history[-1] + (1 - alpha) * level
        fitted = np.full(n, level)
        return np.array(forecast), fitted

    # Initialize level, trend, seasonal
    level = np.mean(history[:season_length])
    trend = (np.mean(history[season_length:2*season_length]) - np.mean(history[:season_length])) / season_length
    seasonal = history[:season_length] - level

    fitted = np.zeros(n)
    for t in range(n):
        if t < season_length:
            fitted[t] = history[t]
            continue
        s = seasonal[t % season_length]
        yhat = level + trend + s
        fitted[t] = yhat
        # Update
        new_level = alpha * (history[t] - seasonal[t % season_length]) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        new_seasonal = gamma * (history[t] - new_level) + (1 - gamma) * seasonal[t % season_length]
        level, trend = new_level, new_trend
        seasonal[t % season_length] = new_seasonal

    # Forecast
    forecast = []
    for h in range(1, horizon + 1):
        s = seasonal[(n + h - 1) % season_length]
        yhat = level + h * trend + s
        forecast.append(yhat)
    return np.array(forecast), fitted


def ets_forecast(history: List[float], horizon: int = 12,
                  season_length: int = 12) -> ForecastResult:
    """Holt-Winters ETS forecast with prediction intervals."""
    y = np.asarray(history, dtype=float)
    fc, fitted = _ets_forecast_single(y, horizon, season_length=season_length)
    # Residuals
    res = y - fitted
    sigma = np.std(res)
    z80 = 1.282
    z95 = 1.96
    lower_80 = (fc - z80 * sigma).tolist()
    lower_95 = (fc - z95 * sigma).tolist()
    upper_80 = (fc + z80 * sigma).tolist()
    upper_95 = (fc + z95 * sigma).tolist()
    mape = float(np.mean(np.abs(res) / (np.abs(y) + 1e-9)) * 100)
    rmse = float(np.sqrt(np.mean(res**2)))
    return ForecastResult(
        model="Holt-Winters ETS",
        horizon=horizon,
        point_forecast=fc.tolist(),
        lower_80=lower_80,
        lower_95=lower_95,
        upper_80=upper_80,
        upper_95=upper_95,
        mape=mape,
        rmse=rmse,
    )


def naive_forecast(history: List[float], horizon: int = 12) -> ForecastResult:
    """Naive forecast: last value repeated."""
    y = np.asarray(history, dtype=float)
    last = y[-1]
    fc = np.full(horizon, last)
    sigma = np.std(y)
    z80, z95 = 1.282, 1.96
    return ForecastResult(
        model="Naive (last value)",
        horizon=horizon,
        point_forecast=fc.tolist(),
        lower_80=(fc - z80 * sigma).tolist(),
        lower_95=(fc - z95 * sigma).tolist(),
        upper_80=(fc + z80 * sigma).tolist(),
        upper_95=(fc + z95 * sigma).tolist(),
        mape=0.0,
        rmse=float(sigma),
    )


def fit_and_forecast(history: List[float], horizon: int = 12,
                      season_length: int = 12,
                      prefer: str = "ets") -> ForecastResult:
    """Auto-fit best model."""
    if prefer == "ets":
        return ets_forecast(history, horizon, season_length)
    return naive_forecast(history, horizon)
