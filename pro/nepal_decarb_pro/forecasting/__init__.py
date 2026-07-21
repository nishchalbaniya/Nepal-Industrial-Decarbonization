"""
Forecasting module — time-series models for emissions and energy.

Models:
  - ETS (Exponential Triple Smoothing / Holt-Winters)
  - SARIMAX
  - Transformer-based (when ML extras installed)
  - Naive baseline
"""
from nepal_decarb_pro.forecasting.models import (
    ForecastResult,
    ets_forecast,
    naive_forecast,
    fit_and_forecast,
)

__all__ = [
    "ForecastResult",
    "ets_forecast",
    "naive_forecast",
    "fit_and_forecast",
]
