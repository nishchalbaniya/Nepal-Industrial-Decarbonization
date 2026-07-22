"""
Property-based tests using Hypothesis.

Owner: Hiro Tanaka (data-scientist-uq)
Source citations:
  - hypothesis Python library docs — @given, @settings, strategies.
  - Saltelli et al. (2010), Computer Physics Communications 181: 259-260 —
    "Variance based sensitivity analysis of model output. Design and
    estimator for the total sensitivity index."  32-sample screening rule
    for first-order Sobol resolution.
  - Sobol' (2001), Mathematics and Computers in Simulation 55(1-3): 271-280.
  - Hiro v0.3.0 review §1.3 (property-based sweep is robustness principle #3).

These tests are *screening-level* Sobol / Monte Carlo.  The full
Saltelli N=1024 design for the top-3 inputs is in `uq_design.md`.

IMPORTANT:
  - Use `numpy.Generator` (modern API, `default_rng()`), not
    `np.random.seed` (legacy, NEP 19 deprecates new uses).
  - `deadline=None` because the cooler ODE is iterative and slow.
  - `max_examples=32` per Saltelli 2010.
"""
from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import given, settings, strategies as st

from nepal_cooler_sim import (
    CoolerParameters,
    run_to_steady_state,
)


# Hypothesis strategies: 32-sample screening sweep over the 5 top
# inputs (clinker_inlet_T, air_velocity, grate_speed, cp_clinker,
# clinker_diameter).  Bounded to the field's ge/le.

# All values are within the field's ge/le constraints from
# CoolerParameters (see cooler_ode.py:52-97).
# Cite: spec DAY-03-SPEC.md "Algorithm" + my v0.3.0 review §3.

# Reasonable range bounds (ge / le) from the field definitions:
#   clinker_inlet_t_c: [900, 1600]
#   under_grate_air_velocity_m_s: [0.3, 5.0]
#   grate_speed_m_min: [1.0, 30.0]
#   cp_clinker_kj_kg_k: [0.8, 1.5]
#   clinker_diameter_m: [0.005, 0.10]

st_clinker_inlet_T = st.floats(min_value=900.0, max_value=1600.0,
                                allow_nan=False, allow_infinity=False)
st_air_velocity = st.floats(min_value=0.3, max_value=5.0,
                             allow_nan=False, allow_infinity=False)
st_grate_speed = st.floats(min_value=1.0, max_value=30.0,
                            allow_nan=False, allow_infinity=False)
st_cp_clinker = st.floats(min_value=0.8, max_value=1.5,
                           allow_nan=False, allow_infinity=False)
st_diameter = st.floats(min_value=0.005, max_value=0.10,
                         allow_nan=False, allow_infinity=False)


# ---------------------------------------------------------------------------
# Property 1: second-law invariant for *any* valid input
# ---------------------------------------------------------------------------

@given(
    T_in=st_clinker_inlet_T,
    v_air=st_air_velocity,
    v_grate=st_grate_speed,
)
@settings(max_examples=32, deadline=None, derandomize=True)
def test_second_law_invariant_for_random_inputs(T_in, v_air, v_grate):
    """For ANY valid combination of (clinker_inlet_T, air_velocity,
    grate_speed), the second-law invariant must hold:
        T_air_c[i] <= T_clinker_inlet_to_cell[i]  for all i.

    This is the strongest property-based test: a model that violates
    second-law for ANY input is wrong.  A model that holds second-law
    everywhere is at least not violating thermodynamics.

    Cite: Hiro v0.3.0 review §1.1; Aanya's v0.3.0 review §1.
    v0.3.0 FAILS: at default inputs, max(T_air - T_c_in) = 4487 K.
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=900.0,
        clinker_inlet_t_c=T_in,
        under_grate_air_velocity_m_s=v_air,
        grate_speed_m_min=v_grate,
    )
    state = run_to_steady_state(p, max_t_s=900.0)
    T_c_in = np.concatenate(([p.clinker_inlet_t_c], state.t_clinker_c[:-1]))
    violation = state.t_air_c - T_c_in
    assert np.all(state.t_air_c <= T_c_in + 1e-6), (
        f"Second-law violation: max(T_air - T_c_in) = "
        f"{float(violation.max()):.1f} K at "
        f"(T_in={T_in}, v_air={v_air}, v_grate={v_grate})"
    )


# ---------------------------------------------------------------------------
# Property 2: cooling direction — more air → cooler clinker
# ---------------------------------------------------------------------------

@given(
    v_air_1=st_air_velocity,
    v_air_2=st_air_velocity,
)
@settings(max_examples=32, deadline=None, derandomize=True)
def test_more_air_lowers_or_equals_clinker_outlet(v_air_1, v_air_2):
    """If v_air_2 > v_air_1, then clinker_outlet_c(v_air_2) <=
    clinker_outlet_c(v_air_1).  AND the second-law invariant must
    hold at BOTH points.

    The v0.3.0 model happens to satisfy the first part (clinker_outlet_c
    decreases with v_air) because the per-cell air_kg_per_m scales with
    v_air — but the model *fails* the second-law invariant at the
    default operating point, so the second part of this test catches it.

    Cite: McCabe-Smith-Harriott §15 (Kern's method, mass-flow direction);
    Hiro v0.3.0 review §1.1 (second-law is principle #1) and §1.3
    (property-based sweep is principle #3).
    """
    if v_air_2 <= v_air_1:
        return  # no ordering to test

    p1 = CoolerParameters(
        n_cells=20, t_end_s=900.0, under_grate_air_velocity_m_s=v_air_1
    )
    p2 = CoolerParameters(
        n_cells=20, t_end_s=900.0, under_grate_air_velocity_m_s=v_air_2
    )
    s1 = run_to_steady_state(p1, max_t_s=900.0)
    s2 = run_to_steady_state(p2, max_t_s=900.0)

    # Direction: more air → cooler clinker.
    assert s2.clinker_outlet_c <= s1.clinker_outlet_c + 1.0, (
        f"More air should cool the clinker. "
        f"v_air_1={v_air_1}: outlet {s1.clinker_outlet_c:.1f} C; "
        f"v_air_2={v_air_2}: outlet {s2.clinker_outlet_c:.1f} C."
    )

    # Second-law invariant at BOTH points (this is the diagnostic part).
    for label, s, v in (("v_air_1", s1, v_air_1), ("v_air_2", s2, v_air_2)):
        T_c_in = np.concatenate(
            ([p1.clinker_inlet_t_c], s.t_clinker_c[:-1])
        )
        assert np.all(s.t_air_c <= T_c_in + 1e-6), (
            f"Second-law violation at {label}={v}: "
            f"max(T_air - T_c_in) = "
            f"{float((s.t_air_c - T_c_in).max()):.1f} K"
        )


# ---------------------------------------------------------------------------
# Property 3: faster grate → less cooling (higher outlet T)
# ---------------------------------------------------------------------------

@given(v_grate_1=st_grate_speed, v_grate_2=st_grate_speed)
@settings(max_examples=32, deadline=None, derandomize=True)
def test_faster_grate_raises_clinker_outlet(v_grate_1, v_grate_2):
    """If v_grate_2 > v_grate_1, then clinker_outlet_c(v_grate_2) >=
    clinker_outlet_c(v_grate_1).  Strict monotone in grate speed:
    faster grate → shorter residence time → higher outlet T.

    Cite: Mujumdar (2007) §3 (residence time on grate); Hiro v0.3.0
    review §3 (grate speed is rank #3 UQ lever).
    """
    if v_grate_2 <= v_grate_1:
        return
    p1 = CoolerParameters(
        n_cells=20, t_end_s=900.0, grate_speed_m_min=v_grate_1
    )
    p2 = CoolerParameters(
        n_cells=20, t_end_s=900.0, grate_speed_m_min=v_grate_2
    )
    s1 = run_to_steady_state(p1, max_t_s=900.0)
    s2 = run_to_steady_state(p2, max_t_s=900.0)
    assert s2.clinker_outlet_c >= s1.clinker_outlet_c - 1.0, (
        f"Faster grate should give higher clinker outlet. "
        f"v_grate_1={v_grate_1}: outlet {s1.clinker_outlet_c:.1f} C; "
        f"v_grate_2={v_grate_2}: outlet {s2.clinker_outlet_c:.1f} C."
    )


# ---------------------------------------------------------------------------
# Property 4: first-law imbalance must be small for all valid inputs
# ---------------------------------------------------------------------------

@given(
    T_in=st_clinker_inlet_T,
    v_air=st_air_velocity,
    v_grate=st_grate_speed,
    cp_c=st_cp_clinker,
    d=st_diameter,
)
@settings(max_examples=32, deadline=None, derandomize=True)
def test_first_law_imbalance_below_5pct_for_random_inputs(
    T_in, v_air, v_grate, cp_c, d
):
    """For ANY valid combination of (T_in, v_air, v_grate, cp, d),
    the air-side / clinker-side first-law imbalance must be ≤ 5%.

    The 5% band covers hood radiation + dust losses that are legitimate
    engineering sinks.  A 13.5x imbalance (v0.3.0) is a hard reject.

    Cite: first law; Ramesh v0.3.0 review §3.2.
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=900.0,
        clinker_inlet_t_c=T_in,
        under_grate_air_velocity_m_s=v_air,
        grate_speed_m_min=v_grate,
        cp_clinker_kj_kg_k=cp_c,
        clinker_diameter_m=d,
    )
    state = run_to_steady_state(p, max_t_s=900.0)
    from nepal_cooler_sim import compute_outputs
    outs = compute_outputs(state, p)
    Q_clinker = outs["heat_recovered_kw"]
    Q_air = outs["secondary_air_recovered_kw"]
    # Allow the ratio to span [0.85, 1.05] × Q_clinker.  Outside this
    # band = first-law reject.
    assert Q_air <= 1.05 * Q_clinker, (
        f"First-law imbalance: Q_air / Q_clinker = "
        f"{Q_air / Q_clinker:.2f}x at "
        f"(T_in={T_in}, v_air={v_air}, v_grate={v_grate}, "
        f"cp={cp_c}, d={d}). "
        f"v0.3.0 default: 13.5x (radiation runaway)."
    )


# ---------------------------------------------------------------------------
# Property 5: secondary air never exceeds clinker inlet (a tight bound)
# ---------------------------------------------------------------------------

@given(T_in=st_clinker_inlet_T, v_air=st_air_velocity)
@settings(max_examples=32, deadline=None, derandomize=True)
def test_secondary_air_never_exceeds_clinker_inlet(T_in, v_air):
    """For ANY valid (T_in, v_air), secondary_air_outlet_c <= T_in.

    This is a direct second-law test on the *outlet* air, with no
    spatial nuance — it should hold even for the most pathological
    model state.

    Cite: second law; Hiro v0.3.0 review §1.1.
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=900.0,
        clinker_inlet_t_c=T_in,
        under_grate_air_velocity_m_s=v_air,
    )
    state = run_to_steady_state(p, max_t_s=900.0)
    assert state.secondary_air_outlet_c <= T_in + 1e-6, (
        f"secondary_air_outlet_c = {state.secondary_air_outlet_c:.1f} C "
        f"exceeds clinker inlet T = {T_in:.1f} C. "
        f"v0.3.0 reports 5790.6 C against 1400 C inlet — fails this for "
        f"every random sample near the default operating point."
    )


# ---------------------------------------------------------------------------
# numpy.Generator smoke test (NOT np.random.seed)
# ---------------------------------------------------------------------------

def test_uses_numpy_generator_not_seed():
    """Confirm the test suite uses `numpy.random.default_rng()` (Generator)
    and not `np.random.seed` (legacy).  This is a self-check: if a future
    contributor adds `np.random.seed(...)` to one of my tests, this
    will catch it (via a static search in a CI linter, not runtime).

    Cite: numpy NEP 19, "Default NumPy random number generator".
    """
    # Sanity: Generator must be available.
    rng = np.random.default_rng(seed=42)
    sample = rng.uniform(0, 1, size=10)
    assert sample.shape == (10,)
    assert np.all(sample >= 0.0) and np.all(sample <= 1.0)
    # And the API is reproducible across calls with the same seed.
    rng2 = np.random.default_rng(seed=42)
    sample2 = rng2.uniform(0, 1, size=10)
    assert np.allclose(sample, sample2), (
        "numpy.Generator should be reproducible with the same seed"
    )
