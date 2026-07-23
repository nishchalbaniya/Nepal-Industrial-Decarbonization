"""
Tests for sensitivity.py — sweep monotonicity and Morris screening.
"""
from __future__ import annotations

import pytest

from nepal_kiln_sim.plants import PLANT_PRESETS
from nepal_kiln_sim.sensitivity import sensitivity_sweep, morris_elementary_effects


def test_sweep_increasing_fuel_rate_increases_sec():
    p = PLANT_PRESETS["planta"].parameters
    rows = sensitivity_sweep(p, "fuel_rate_t_h", [8.0, 10.0, 12.0, 14.0])
    secs = [r["output"] for r in rows]
    # SEC should be monotonically increasing in fuel rate (more fuel = more energy)
    for a, b in zip(secs, secs[1:]):
        assert b > a, f"SEC not monotonically increasing: {secs}"


def test_sweep_preserves_factor_label():
    p = PLANT_PRESETS["planta"].parameters
    rows = sensitivity_sweep(p, "raw_meal_throughput_t_h", [100.0, 130.0, 160.0])
    for r in rows:
        assert r["factor"] == "raw_meal_throughput_t_h"


def test_morris_returns_per_factor_dict():
    p = PLANT_PRESETS["planta"].parameters
    factors = ["fuel_rate_t_h", "raw_meal_throughput_t_h", "preheater_efficiency"]
    summary = morris_elementary_effects(p, factors, n_trajectories=2, seed=42)
    assert set(summary.keys()) == set(factors)
    for f, stats in summary.items():
        assert "mu_star" in stats
        assert "sigma" in stats
        assert stats["mu_star"] >= 0
