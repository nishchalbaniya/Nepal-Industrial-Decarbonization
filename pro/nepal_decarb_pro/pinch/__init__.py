"""
Pinch analysis — process integration for cement and brick plants.

Implements:
  - Composite curves (hot + cold)
  - Grand composite curve
  - Minimum Energy Requirement (MER) targeting
  - Heat Exchanger Network (HEN) minimum utilities
  - Capital cost targeting
"""
from nepal_decarb_pro.pinch.analysis import (
    Stream,
    PinchResult,
    pinch_analysis,
    grand_composite_curve,
    minimum_heat_exchanger_area,
)

__all__ = [
    "Stream", "PinchResult", "pinch_analysis", "grand_composite_curve",
    "minimum_heat_exchanger_area",
]
