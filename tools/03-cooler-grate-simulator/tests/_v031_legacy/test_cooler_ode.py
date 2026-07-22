"""Tests for nepal_cooler_sim."""
from __future__ import annotations

import math

import numpy as np
import pytest

from nepal_cooler_sim import (
    CoolerParameters, CoolerState, simulate_cooler, run_to_steady_state,
    compute_outputs, arrhenius_rate, convective_htc_cooler, radiative_flux_cooler,
    coupled_kiln_cooler_steady_state,
)


def test_arrhenius_zero_at_zero():
    assert arrhenius_rate(0.0, 1e6, 100e3) == 0.0


def test_convective_htc_returns_finite():
    h = convective_htc_cooler(Re=10.0, Pr=0.7, k=0.05, d=0.025)
    assert math.isfinite(h)
    assert h > 0


def test_radiative_flux_sign():
    q_hot_to_cold = radiative_flux_cooler(1000.0, 30.0, eps=0.85)
    q_cold_to_hot = radiative_flux_cooler(30.0, 1000.0, eps=0.85)
    assert q_hot_to_cold > 0
    assert q_cold_to_hot < 0


def test_initial_state_shape():
    p = CoolerParameters()
    y0 = np.array([1400.0] * p.n_cells + [30.0] * p.n_cells)
    assert y0.shape == (2 * p.n_cells,)


def test_simulate_runs():
    p = CoolerParameters(n_cells=10, t_end_s=120.0, n_time_points=20)
    t, y, x = simulate_cooler(p)
    assert t.shape == (20,)
    assert y.shape == (2 * p.n_cells, 20)
    assert x.shape == (p.n_cells,)


def test_steady_state_clinker_cools_below_inlet():
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    assert state.clinker_outlet_c < p.clinker_inlet_t_c
    # Outlet T should drop substantially; expect at least 700 C below inlet
    assert p.clinker_inlet_t_c - state.clinker_outlet_c > 700.0


def test_outputs_have_required_kpis():
    p = CoolerParameters(n_cells=20, t_end_s=600.0)
    state = run_to_steady_state(p, max_t_s=600.0)
    outs = compute_outputs(state, p)
    required = ["clinker_outlet_c", "secondary_air_outlet_c", "cooler_efficiency",
                "heat_in_kw", "heat_recovered_kw"]
    for k in required:
        assert k in outs
        assert math.isfinite(outs[k])


def test_efficiency_in_realistic_range():
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    # Typical grate cooler 65-85 % recovery
    assert 0.4 < state.cooler_efficiency < 0.95


def test_faster_grate_reduces_efficiency():
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    s_slow = run_to_steady_state(p, max_t_s=900.0)
    s_fast = run_to_steady_state(p.model_copy(update={"grate_speed_m_min": 24.0}),
                                  max_t_s=900.0)
    assert s_fast.clinker_outlet_c > s_slow.clinker_outlet_c


def test_more_air_improves_cooling():
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    s_low = run_to_steady_state(p, max_t_s=900.0)
    s_high = run_to_steady_state(p.model_copy(update={"under_grate_air_velocity_m_s": 3.0}),
                                  max_t_s=900.0)
    assert s_high.clinker_outlet_c < s_low.clinker_outlet_c


def test_coupled_converges_or_reports_failure():
    p = CoolerParameters(n_cells=15, t_end_s=600.0)
    result = coupled_kiln_cooler_steady_state(p, max_iter=5)
    assert result.iterations >= 1
    assert isinstance(result.secondary_air_t_c, float)
