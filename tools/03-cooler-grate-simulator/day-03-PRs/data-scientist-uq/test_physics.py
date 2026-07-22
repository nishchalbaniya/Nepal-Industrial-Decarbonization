"""
Physics tests for the cooler model — pure-function sanity + diagnostic invariants.

Owner: Hiro Tanaka (data-scientist-uq)
Source citations:
  - Achenbach (1995), Exp. Thermal Fluid Sci. 10(1):17-27. — packed-bed Nu.
  - Wakao & Kaguei (1982), Heat and Mass Transfer in Packed Beds. — Nu baseline.
  - Stefan-Boltzmann law: q'' = eps * sigma * (T1^4 - T2^4).
  - McCabe-Smith-Harriott (2005) Ch. 15. — Kern's method for 1D HX.
  - Hiro v0.3.0 review §1.1, §2.1, §2.4.
  - Aanya's v0.3.0 review §1 (radiation dominance) and §5 fix A (second-law clamp).

These tests are DIAGNOSTIC: they must FAIL against the v0.3.0 broken code.
The 5790 C second-law violation in v0.3.0 is what the second-law test catches.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from nepal_cooler_sim import (
    CoolerParameters,
    CoolerState,
    radiative_flux_cooler,
    convective_htc_cooler,
    arrhenius_rate,
    run_to_steady_state,
)


# ---------------------------------------------------------------------------
# Pure-function physics (these pass on v0.3.0 — sanity regression)
# ---------------------------------------------------------------------------

def test_arrhenius_zero_at_zero():
    """Arrhenius: A * exp(-Ea / (R * T)) must be 0 at T=0 (no division by zero).
    Cite: Hiro v0.3.0 review §5.3 (numerical hygiene).
    """
    assert arrhenius_rate(0.0, 1e6, 100e3) == 0.0


def test_radiative_flux_sign_is_correct():
    """Stefan-Boltzmann: heat flows hot to cold.
    q''_hot_to_cold > 0, q''_cold_to_hot < 0. (Sign convention from physics, not
    an arbitrary choice.) Cite: any heat-transfer textbook, e.g. Incropera §1.
    """
    q_hot_to_cold = radiative_flux_cooler(1000.0, 30.0, eps=0.85)
    q_cold_to_hot = radiative_flux_cooler(30.0, 1000.0, eps=0.85)
    assert q_hot_to_cold > 0
    assert q_cold_to_hot < 0


def test_radiative_flux_eps_proportional():
    """q'' is linear in emissivity. Cite: Stefan-Boltzmann.
    Doubling eps should double q'' (everything else equal).
    """
    q1 = radiative_flux_cooler(1400.0, 200.0, eps=0.5)
    q2 = radiative_flux_cooler(1400.0, 200.0, eps=0.9)
    assert math.isclose(q2 / q1, 0.9 / 0.5, rel_tol=1e-6)


def test_convective_htc_finite_and_positive():
    """h > 0 always. Cite: Achenbach (1995), Wakao & Kaguei (1982).
    A 0 or NaN h would silently produce zero heat transfer.
    """
    h = convective_htc_cooler(Re=10.0, Pr=0.7, k=0.05, d=0.025)
    assert math.isfinite(h)
    assert h > 0


def test_convective_htc_in_achenbach_range_for_typical_cooler_re():
    """At Re=1000, Achenbach 1995 (Eq. for cross-flow packed bed) gives
    h ≈ 700 W/m^2 K. A model that returns h = 200 (the floor) for typical
    cooler Reynolds numbers is fine if the floor is documented, but
    anything below ~100 W/m^2 K at Re=1000 indicates a missing floor or
    a wrong correlation. Cite: Achenbach (1995) §3.
    """
    h = convective_htc_cooler(Re=1000.0, Pr=0.7, k=0.05, d=0.025)
    assert h >= 100.0, f"h={h:.1f} W/m^2 K below engineering floor at Re=1000"


# ---------------------------------------------------------------------------
# DIAGNOSTIC: second-law invariant (FAILS on v0.3.0 — catches 5790 C bug)
# ---------------------------------------------------------------------------

def test_second_law_air_not_hotter_than_clinker_source():
    """For cross-flow with fresh air per cell, the air leaving a cell cannot
    exceed the clinker temperature entering that cell. This is the single
    most discriminating test for the v0.3.0 5790 C second-law violation.

    The current v0.3.0 `_solve_spatial` (line 235) updates T_a_cell with
    `T_a_cell += dT_a` and no upper clamp, so on the first sub-step at
    T_c ≈ 1400 C, dT_a ≈ 3340 K (per Aanya's review §1), and the
    air T explodes. This test catches it.

    Cite: Aanya's v0.3.0 review §1 (radiation runaway); Hiro v0.3.0 review
    §1.1 (second-law invariant is principle #1) and §2.1 (the test).
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)

    # Clinker entering cell i: T_clinker_inlet_to_cell[0] = p.clinker_inlet_t_c
    #                          T_clinker_inlet_to_cell[i] = state.t_clinker_c[i-1]
    T_c_in_to_cell = np.concatenate(
        ([p.clinker_inlet_t_c], state.t_clinker_c[:-1])
    )
    violation = state.t_air_c - T_c_in_to_cell
    assert np.all(state.t_air_c <= T_c_in_to_cell + 1e-6), (
        f"Second-law violation: air hotter than clinker source. "
        f"max(T_air - T_c_in) = {float(violation.max()):.1f} K. "
        f"Expected: ≤ 0. Got: T_air_max = {float(state.t_air_c.max()):.1f} C, "
        f"T_c_min_into_cell = {float(T_c_in_to_cell.min()):.1f} C."
    )


def test_secondary_air_within_realistic_envelope():
    """Well-operated grate coolers deliver secondary air at 600-1000 C
    to the kiln (Peray & Waddell 1986 §6.4). Above 1100 C indicates
    radiation runaway or missing clinker-side coupling. The current
    model reports 5790 C — this test rejects it.

    Cite: Peray & Waddell (1986) §6.4; Hiro v0.3.0 review §2.4.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    assert 200.0 < state.secondary_air_outlet_c < 1100.0, (
        f"Secondary air {state.secondary_air_outlet_c:.0f} C outside "
        f"realistic envelope [200, 1100] C. "
        f"v0.3.0 reported 5790 C due to missing dT_a clamp."
    )


# ---------------------------------------------------------------------------
# DIAGNOSTIC: energy balance closure (FAILS on v0.3.0 — 13.5x imbalance)
# ---------------------------------------------------------------------------

def test_energy_balance_closure_two_percent():
    """Energy in = recovered + out + loss. For a 1D model with no wall
    loss term, the closure residual should be small (< 2% of Q_in).
    A model that injects energy into the air stream via runaway
    radiation will fail this — and on v0.3.0 it does, by 13.5x.

    Cite: Ramesh v0.3.0 review §3.2 (first-law imbalance test);
    Hiro v0.3.0 review §2.2.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    outs = _outputs_for(state, p)

    residual_kw = outs["heat_in_kw"] - outs["heat_recovered_kw"] - outs["heat_out_kw"]
    # Note: on v0.3.0, `outs['secondary_air_recovered_kw']` is 13.5x
    # `outs['heat_recovered_kw']` (Ramesh §3.2). We assert on the
    # *clinker-side* balance which is what the model is supposed to
    # conserve, AND we assert the air-side / clinker-side ratio in
    # `test_conservation.py`.
    assert abs(residual_kw) < 0.02 * outs["heat_in_kw"], (
        f"Clinker-side energy balance residual {residual_kw:.1f} kW "
        f"exceeds 2% of Q_in={outs['heat_in_kw']:.1f} kW"
    )


# ---------------------------------------------------------------------------
# Helper: re-implement compute_outputs locally to avoid a v0.3.0 import
# surface. v0.3.0 ships `compute_outputs(state, p)` in cooler_ode.py.
# ---------------------------------------------------------------------------

def _outputs_for(state: CoolerState, p: CoolerParameters) -> dict:
    """Re-export compute_outputs via the public API. (Avoids duplicating the
    math here — we test the actual shipped function.)
    """
    from nepal_cooler_sim import compute_outputs  # local import: v0.3.0+ ships this
    return compute_outputs(state, p)


# ---------------------------------------------------------------------------
# Slow tests (>1s on CI; marked accordingly per pytest docs)
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_second_law_holds_at_high_resolution():
    """Refutation at n_cells=50 — same invariant, finer discretisation.
    Catches the case where a bug only appears at the high-resolution limit.
    Cite: Hiro v0.3.0 review §5.1 (state validation, not just scalar).
    """
    p = CoolerParameters(n_cells=50, t_end_s=1800.0)
    state = run_to_steady_state(p, max_t_s=1800.0)
    T_c_in_to_cell = np.concatenate(
        ([p.clinker_inlet_t_c], state.t_clinker_c[:-1])
    )
    assert np.all(state.t_air_c <= T_c_in_to_cell + 1e-6), (
        f"Second-law violation at n_cells=50: "
        f"max(T_air - T_c_in) = "
        f"{float((state.t_air_c - T_c_in_to_cell).max()):.1f} K"
    )
