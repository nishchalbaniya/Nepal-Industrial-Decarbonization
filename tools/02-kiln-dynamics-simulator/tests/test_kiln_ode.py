"""
Tests for kiln_ode.py — physics and numerics.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from nepal_kiln_sim.kiln_ode import (
    KilnParameters, KilnState, simulate_kiln, run_to_steady_state,
    compute_outputs, initial_state, arrhenius_rate, convective_htc, radiative_flux,
)
from nepal_kiln_sim.plants import PLANT_PRESETS


# ---------------------------------------------------------------------------
# Pure physics
# ---------------------------------------------------------------------------

def test_arrhenius_increases_with_temperature():
    k_low = arrhenius_rate(800.0, 1e6, 110_000.0)
    k_high = arrhenius_rate(1200.0, 1e6, 110_000.0)
    assert k_high > k_low
    # At 1200 K, k should be on the order of 1e1
    assert 0.1 < k_high < 100.0


def test_arrhenius_zero_at_absolute_zero():
    assert arrhenius_rate(0.0, 1e6, 110_000.0) == 0.0


def test_convective_htc_stagnant_fallback():
    h = convective_htc(Re=0.5, Pr=0.7, k=0.05, D=4.0)
    assert h >= 1.0


def test_convective_htc_dittus_boelter():
    # Re=1e5, D=0.5, k=0.05: Nu ~128, h = Nu*k/D ~ 12.8 W/m²K
    h = convective_htc(Re=100_000.0, Pr=0.7, k=0.05, D=0.5)
    assert 5.0 < h < 100.0


def test_radiative_flux_sign():
    q = radiative_flux(1500.0, 800.0, eps=0.85)
    assert q > 0  # hot to cold
    q_rev = radiative_flux(800.0, 1500.0, eps=0.85)
    assert q_rev < 0


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------

def test_initial_state_shape():
    p = KilnParameters()
    y0 = initial_state(p)
    assert y0.shape == (6 * p.n_zones,)
    # All solid temps start at ambient
    assert np.all(y0[0::6] == p.ambient_temp_k)


def test_initial_state_in_bounds():
    p = KilnParameters(n_zones=10)
    y0 = initial_state(p)
    assert np.all(y0 > 0)
    assert np.all(y0 < 5000.0)


# ---------------------------------------------------------------------------
# Pydantic validators
# ---------------------------------------------------------------------------

def test_invalid_fuel_rejected():
    with pytest.raises(ValueError, match="Unknown fuel"):
        KilnParameters(fuel_type="unicornium")


def test_invalid_geometry_rejected():
    with pytest.raises(ValueError):
        KilnParameters(length_m=0.5)  # below ge=10


# ---------------------------------------------------------------------------
# Simulator
# ---------------------------------------------------------------------------

def test_simulate_runs_planta():
    p = PLANT_PRESETS["planta"].parameters
    t, y, x = simulate_kiln(p, t_end_s=120.0, n_time_points=10)
    assert t.shape == (10,)
    assert y.shape == (6 * p.n_zones, 10)
    assert x.shape == (p.n_zones,)


def test_steady_state_reaches_physically_reasonable_burning_zone():
    p = PLANT_PRESETS["plantb"].parameters
    state = run_to_steady_state(p, max_t_s=600.0)
    # Burning zone should be 1300-1700 K (well above calcination, well below melt)
    T_burning = state.t_solid_k[-1]
    assert 1000.0 < T_burning < 2000.0, f"Burning zone out of range: {T_burning} K"


def test_outputs_contain_required_kpis():
    p = PLANT_PRESETS["planta"].parameters
    state = run_to_steady_state(p, max_t_s=300.0)
    outs = compute_outputs(state, p)
    required = [
        "t_burning_zone_c", "sec_mj_per_t_clinker", "co2_intensity_kg_per_t_clinker",
        "avg_conversion", "co2_total_t_h",
    ]
    for k in required:
        assert k in outs, f"Missing output: {k}"
        assert isinstance(outs[k], float)
        assert math.isfinite(outs[k])


def test_biomass_lowers_co2_intensity():
    p_coal = PLANT_PRESETS["planta"].parameters
    p_bio = p_coal.model_copy(update={"fuel_type": "biomass_rice_husk"})
    s_coal = run_to_steady_state(p_coal, max_t_s=300.0)
    s_bio = run_to_steady_state(p_bio, max_t_s=300.0)
    o_coal = compute_outputs(s_coal, p_coal)
    o_bio = compute_outputs(s_bio, p_bio)
    # Biomass combustion CO2 should be lower (calcination CO2 stays same;
    # this is the fossil EF change captured by the model)
    assert o_bio["co2_fuel_t_h"] < o_coal["co2_fuel_t_h"]


def test_solver_handles_short_horizon():
    p = KilnParameters()
    t, y, x = simulate_kiln(p, t_end_s=30.0, n_time_points=5)
    assert t[0] == 0.0
    assert t[-1] == 30.0


def test_solver_recovers_from_lsoda():
    p = KilnParameters(solver_method="LSODA")
    t, y, x = simulate_kiln(p, t_end_s=30.0, n_time_points=5)
    assert y.shape[1] == 5
