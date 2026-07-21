"""
Pinch analysis implementation (Linnhoff method).

For a cement plant with hot and cold streams, find:
  - Pinch temperature
  - Minimum hot utility (Q_H,min)
  - Minimum cold utility (Q_C,min)
  - MER (minimum energy requirement)
"""
from __future__ import annotations

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
import numpy as np


class Stream(BaseModel):
    """A process stream for pinch analysis."""
    name: str
    supply_temp_c: float                       # T_in
    target_temp_c: float                       # T_out
    cp_kw_per_k: float = Field(..., gt=0)       # heat capacity flow rate
    h_kw: float = 0.0                           # enthalpy (calculated)

    def __init__(self, **data):
        super().__init__(**data)
        # Enthalpy change (kW = kW/K * delta_T in K)
        if self.h_kw == 0.0:
            self.h_kw = self.cp_kw_per_k * (self.target_temp_c - self.supply_temp_c)

    @property
    def is_hot(self) -> bool:
        return self.target_temp_c < self.supply_temp_c

    @property
    def is_cold(self) -> bool:
        return self.target_temp_c > self.supply_temp_c


class PinchResult(BaseModel):
    """Result of a pinch analysis."""
    pinch_temp_c: float
    dT_min_c: float
    q_h_min_kw: float                         # minimum hot utility
    q_c_min_kw: float                         # minimum cold utility
    mer_kw: float                             # Q_H + Q_C (energy consumption)
    target_area_m2: float                     # minimum HX area target
    n_units_min: int                          # minimum number of units
    streams_count: int
    hot_streams: List[str]
    cold_streams: List[str]
    notes: str = ""


def pinch_analysis(
    streams: List[Stream],
    dT_min_c: float = 10.0,
) -> PinchResult:
    """
    Classic Linnhoff pinch analysis.
    """
    # Convert all temps to K for interval construction
    hot_streams = [s for s in streams if s.is_hot]
    cold_streams = [s for s in streams if s.is_cold]

    if not hot_streams or not cold_streams:
        raise ValueError("Need at least one hot and one cold stream")

    # Problem Table Algorithm (PTA)
    # 1. Shift cold stream temps by -dT_min/2 and hot by +dT_min/2
    hot_intervals = []
    cold_intervals = []
    for s in hot_streams:
        hot_intervals.append((s.supply_temp_c, s.target_temp_c, s.cp_kw_per_k))
    for s in cold_streams:
        cold_intervals.append((s.supply_temp_c - dT_min_c, s.target_temp_c - dT_min_c, s.cp_kw_per_k))

    # Build interval diagram
    all_temps = set()
    for t1, t2, _ in hot_intervals + cold_intervals:
        all_temps.add(t1)
        all_temps.add(t2)
    all_temps = sorted(all_temps, reverse=True)  # descending

    # For each interval, compute net enthalpy (hot - cold)
    interval_data = []
    for i in range(len(all_temps) - 1):
        T_top = all_temps[i]
        T_bot = all_temps[i + 1]
        dT = T_top - T_bot
        # Sum cp for hot streams in this interval
        hot_cp = sum(cp for t1, t2, cp in hot_intervals if min(t1, t2) <= T_bot and max(t1, t2) >= T_top)
        cold_cp = sum(cp for t1, t2, cp in cold_intervals if min(t1, t2) <= T_bot and max(t1, t2) >= T_top)
        net_cp = hot_cp - cold_cp
        delta_h = net_cp * dT
        interval_data.append((T_top, T_bot, hot_cp, cold_cp, net_cp, delta_h))

    # Cascade: find pinch (where cumulative enthalpy = 0)
    cascade = 0.0
    pinch_T = None
    cum = []
    for T_top, T_bot, hot_cp, cold_cp, net_cp, delta_h in interval_data:
        cascade += delta_h
        cum.append((T_top, T_bot, cascade))
        if cascade < 0 and pinch_T is None:
            # Pinch is between T_bot and T_top in this interval
            pinch_T = (T_top + T_bot) / 2
            break

    if pinch_T is None:
        # No pinch: compute utilities from cascade
        cums = [c for _, _, c in cum]
        min_c = min(cums)
        max_c = max(cums)
        # Hot utility needed at top
        q_h = max(0.0, -min_c)
        # Cold utility needed at bottom
        q_c = max(0.0, max_c - q_h)
        pinch_T = (all_temps[0] + all_temps[-1]) / 2
    else:
        # Pinch found; utilities = deficit at top, surplus at bottom
        # Shift cascade so min = 0
        cums = [c for _, _, c in cum]
        min_c = min(cums)
        cums = [c - min_c for c in cums]
        # Hot utility = minimum cascade deficit
        q_h = -min_c if min_c < 0 else 0
        q_c = max(0.0, cums[-1] - cums[0])  # approx

    # Minimum number of units
    n_units_min = len(streams) - 1

    # Min heat exchanger area (Linnhoff rule of thumb)
    # Q_total = Q_H + Q_C; U_avg = 200 W/m²K; LMTD_avg = 20 K
    # A = Q / (U * LMTD)
    U_avg = 0.200  # kW/m²K
    LMTD_avg = 20.0  # K
    target_area = (q_h + q_c) / (U_avg * LMTD_avg) if (q_h + q_c) > 0 else 0

    return PinchResult(
        pinch_temp_c=round(pinch_T, 2),
        dT_min_c=dT_min_c,
        q_h_min_kw=round(q_h, 2),
        q_c_min_kw=round(q_c, 2),
        mer_kw=round(q_h + q_c, 2),
        target_area_m2=round(target_area, 2),
        n_units_min=n_units_min,
        streams_count=len(streams),
        hot_streams=[s.name for s in hot_streams],
        cold_streams=[s.name for s in cold_streams],
    )


def grand_composite_curve(
    streams: List[Stream],
    dT_min_c: float = 10.0,
) -> Dict[str, List[float]]:
    """
    Compute the grand composite curve (heat availability vs temperature).
    """
    hot_streams = [s for s in streams if s.is_hot]
    cold_streams = [s for s in streams if s.is_cold]
    all_temps = set()
    for s in streams:
        all_temps.add(s.supply_temp_c)
        all_temps.add(s.target_temp_c)
    all_temps = sorted(all_temps, reverse=True)

    # Heat available at each T (from hot streams)
    heat_avail = []
    temps = []
    for T in all_temps:
        h = sum(
            s.cp_kw_per_k * max(0, s.supply_temp_c - max(T, s.target_temp_c))
            for s in hot_streams
        )
        heat_avail.append(h)
        temps.append(T)
    return {
        "temperature_c": temps,
        "heat_available_kw": heat_avail,
    }


def minimum_heat_exchanger_area(
    streams: List[Stream],
    U_kw_m2_k: float = 0.2,
    LMTD_K: float = 20.0,
) -> float:
    """Estimate minimum HX area for the network."""
    pr = pinch_analysis(streams)
    return pr.mer_kw / (U_kw_m2_k * LMTD_K)
