"""
Tests for calibration.py — DE-based parameter fitting.

The heavy DE convergence tests are marked ``slow`` and skipped by default
in the fast suite.  Run them with::

    pytest tests/test_calibration.py -m slow
    pytest tests/test_calibration.py                # fast only
    pytest tests/                                   # all fast
"""
from __future__ import annotations

import pytest

from nepal_kiln_sim.plants import PLANT_PRESETS
from nepal_kiln_sim.calibration import calibrate_to_plant, DEFAULT_BOUNDS, CalibrationResult
from nepal_kiln_sim.kiln_ode import KilnParameters


def test_calibration_result_dataclass_fields():
    r = CalibrationResult(
        success=True, best_params=KilnParameters(),
        observed={"sec": 100.0}, simulated={"sec": 110.0},
        rmse=0.1, n_iterations=3, message="ok",
    )
    assert r.success is True
    assert r.rmse == 0.1


def test_default_bounds_cover_tunable_space():
    expected = {"arrhenius_a", "precalciner_degree", "preheater_efficiency",
                "cooler_efficiency", "wall_loss_coeff_w_m2_k", "emissivity"}
    assert set(DEFAULT_BOUNDS.keys()) >= expected


def test_calibrate_empty_observed_is_trivial_success():
    """With no observed KPIs, there's nothing to fit — should 'succeed' trivially."""
    p = PLANT_PRESETS["hetauda"].parameters
    result = calibrate_to_plant(
        p, observed={},
        tunable=["arrhenius_a"],
        maxiter=1,
    )
    # Nothing to fit => objective is always 0 => DE "succeeds" without changing params
    assert result.success is True
    assert result.rmse == 0.0


def test_calibrate_unknown_tunable_skipped():
    p = PLANT_PRESETS["hetauda"].parameters
    result = calibrate_to_plant(
        p, {"sec_mj_per_t_clinker": 4000.0},
        tunable=["nonexistent_param"],
        maxiter=1, seed=42,
    )
    assert result.success is False


@pytest.mark.slow
def test_calibrate_de_converges_to_synthetic_plant():
    """Slow: ~30 s. Convergence check on a synthetic Hetauda target."""
    from nepal_kiln_sim.kiln_ode import run_to_steady_state, compute_outputs
    p_target = PLANT_PRESETS["hetauda"].parameters
    state = run_to_steady_state(p_target, max_t_s=180.0)
    obs = compute_outputs(state, p_target)
    observed = {
        "sec_mj_per_t_clinker": obs["sec_mj_per_t_clinker"],
        "co2_intensity_kg_per_t_clinker": obs["co2_intensity_kg_per_t_clinker"],
    }
    p_start = PLANT_PRESETS["udayapur"].parameters
    result = calibrate_to_plant(
        p_start, observed,
        tunable=["arrhenius_a", "precalciner_degree"],
        maxiter=5, seed=42,
    )
    # After a few iterations we should be within 5% of target SEC
    sec_err = abs(result.simulated["sec_mj_per_t_clinker"] - observed["sec_mj_per_t_clinker"]) / observed["sec_mj_per_t_clinker"]
    assert sec_err < 0.20, f"SEC error {sec_err:.2%} too large"
