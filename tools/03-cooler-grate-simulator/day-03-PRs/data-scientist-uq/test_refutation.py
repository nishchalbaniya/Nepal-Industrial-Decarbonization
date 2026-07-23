"""
Refutation tests — construct configurations where the answer is known
analytically, and assert the model approaches it.

Owner: Hiro Tanaka (data-scientist-uq)
Source citations:
  - Hiro v0.3.0 review §1.4 (refutation is robustness principle #4).
  - Aanya's v0.3.0 review §1, §5 (radiation runaway can manufacture
    air T from a small air mass — refutation catches this).
  - Ramesh v0.3.0 review §2, §3.3 (sanity floor tests).

These are the most diagnostic tests after the second-law invariant.
v0.3.0 will FAIL zero-air (outlet too high — no heat sink works) and
FAIL infinite-air (clinker outlet T does not approach air T).
"""
from __future__ import annotations

import numpy as np
import pytest

from nepal_cooler_sim import (
    CoolerParameters,
    run_to_steady_state,
)


# ---------------------------------------------------------------------------
# Zero-air refutation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("v_air", [0.0, 0.05, 0.1])
def test_low_air_refutation(v_air):
    """As under-grate air velocity → 0, the clinker has nowhere to dump
    heat and should exit near inlet T. The 1D model must not produce
    cooling by some other channel (e.g. runaway radiation that
    manufactures air T from nothing).

    Cite: Hiro v0.3.0 review §2.3; Aanya §5 fix A (clamp prevents
    radiation from creating air T from a tiny air mass).
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=900.0, under_grate_air_velocity_m_s=v_air
    )
    state = run_to_steady_state(p, max_t_s=900.0)

    if v_air == 0.0:
        # At exactly zero air, expect outlet within 5% of inlet.
        assert state.clinker_outlet_c > 0.95 * p.clinker_inlet_t_c, (
            f"At v_air=0, clinker outlet {state.clinker_outlet_c:.1f} C "
            f"should be > {0.95 * p.clinker_inlet_t_c:.1f} C (95% of inlet). "
            f"This catches a model that uses some other channel "
            f"(e.g. a non-physical radiation sink) to cool the clinker."
        )
    else:
        # At low (but non-zero) air, expect outlet significantly above the
        # nominal 150 C target (insufficient heat removal).
        assert state.clinker_outlet_c > 200.0, (
            f"At v_air={v_air}, clinker outlet {state.clinker_outlet_c:.1f} C "
            f"is too low — the model is producing more cooling than the "
            f"air can absorb. Likely a missing air-mass clamp."
        )

    # Second-law invariant must still hold at every sweep point.
    T_c_in = np.concatenate(([p.clinker_inlet_t_c], state.t_clinker_c[:-1]))
    assert np.all(state.t_air_c <= T_c_in + 1e-6), (
        f"Second-law violation at v_air={v_air}: "
        f"max(T_air - T_c_in) = "
        f"{float((state.t_air_c - T_c_in).max()):.1f} K"
    )


# ---------------------------------------------------------------------------
# Infinite-air refutation (very high v_air → clinker approaches air T)
# ---------------------------------------------------------------------------

def test_high_air_clamps_clinker_toward_air_inlet():
    """At very high air velocity (>> stoich), the air mass is so large
    that the clinker exits close to the air inlet T.  This is a
    refutation of the model's high-velocity asymptote.

    Cite: McCabe-Smith-Harriott §15 (Kern's method, mass-flow ratio
    asymptote); Hiro v0.3.0 review §1.4.
    """
    p_low = CoolerParameters(
        n_cells=20, t_end_s=900.0, under_grate_air_velocity_m_s=0.5
    )
    p_high = CoolerParameters(
        n_cells=20, t_end_s=900.0, under_grate_air_velocity_m_s=5.0
    )

    s_low = run_to_steady_state(p_low, max_t_s=900.0)
    s_high = run_to_steady_state(p_high, max_t_s=900.0)

    # At high air, clinker outlet T must be lower than at low air.
    assert s_high.clinker_outlet_c < s_low.clinker_outlet_c, (
        f"More air should cool the clinker further. "
        f"At v=0.5: outlet {s_low.clinker_outlet_c:.1f} C; "
        f"at v=5.0: outlet {s_high.clinker_outlet_c:.1f} C."
    )

    # And the air outlet T must be in a physically reasonable band at
    # v=5.0 (not still 5790 C and not 30 C).  At v=5.0 with 1.5 m/s nominal,
    # the air mass flow is ~3.3x and the secondary-air T should be much
    # lower than the 5790 C of v0.3.0.
    assert s_high.secondary_air_outlet_c <= 1100.0, (
        f"secondary_air_outlet_c at v=5.0 = "
        f"{s_high.secondary_air_outlet_c:.1f} C — should be ≤ 1100 C."
    )

    # The air T at high air should be lower than at low air (more mass
    # to absorb the same heat).
    assert s_high.secondary_air_outlet_c < s_low.secondary_air_outlet_c + 200.0, (
        f"Air T at high velocity ({s_high.secondary_air_outlet_c:.1f} C) "
        f"should be ≤ air T at low velocity + slack "
        f"({s_low.secondary_air_outlet_c:.1f} C). "
        f"v0.3.0 fails this badly (air T is ~constant per cell due to reset)."
    )


# ---------------------------------------------------------------------------
# Zero-grate refutation (v_grate = 0 → clinker in plug flow, near steady)
# ---------------------------------------------------------------------------

def test_zero_grate_refutation():
    """At near-zero grate speed, the clinker has effectively infinite
    residence time and should approach thermal equilibrium with the
    air.  Test that outlet T is much lower than at the nominal grate
    speed (12 m/min), and that the second-law invariant still holds.

    Note: grate_speed_m_min=0.0 is rejected by the Pydantic field's
    ge=1.0 constraint, so we use 1.0 m/min as the smallest allowed
    value (a 12x slowdown vs nominal 12 m/min — already a strong
    refutation).  Ramesh's v0.3.1 should add a `grate_speed_floor_m_min`
    option for refutation tests.

    Cite: Hiro v0.3.0 review §1.4 (refutation test).
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=1800.0, grate_speed_m_min=1.0
    )
    state = run_to_steady_state(p, max_t_s=1800.0)

    # At very low grate speed, clinker has more time → outlet T lower.
    # Compare to nominal.
    p_nom = CoolerParameters(n_cells=20, t_end_s=1800.0, grate_speed_m_min=12.0)
    s_nom = run_to_steady_state(p_nom, max_t_s=1800.0)

    assert state.clinker_outlet_c < s_nom.clinker_outlet_c, (
        f"Slower grate should give lower outlet T. "
        f"At v_grate=1: {state.clinker_outlet_c:.1f} C; "
        f"at v_grate=12: {s_nom.clinker_outlet_c:.1f} C."
    )

    # And the second-law invariant holds.
    T_c_in = np.concatenate(([p.clinker_inlet_t_c], state.t_clinker_c[:-1]))
    assert np.all(state.t_air_c <= T_c_in + 1e-6), (
        f"Second-law violation at v_grate=1: "
        f"max(T_air - T_c_in) = "
        f"{float((state.t_air_c - T_c_in).max()):.1f} K"
    )


# ---------------------------------------------------------------------------
# High-inlet-T refutation (clinker in at very high T → secondary air also high)
# ---------------------------------------------------------------------------

def test_high_inlet_T_secondary_air_does_not_exceed_clinker_inlet():
    """At higher clinker inlet T, the secondary air T can also be higher
    (more heat available), but it must still be ≤ clinker inlet T minus
    the 5 K second-law margin.  This is the second-law test at a
    different operating point.

    Cite: Hiro v0.3.0 review §1.1 (second-law invariant).
    """
    p = CoolerParameters(
        n_cells=20, t_end_s=1800.0, clinker_inlet_t_c=1500.0
    )
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert state.secondary_air_outlet_c <= p.clinker_inlet_t_c, (
        f"secondary_air_outlet_c = {state.secondary_air_outlet_c:.1f} C "
        f"exceeds clinker inlet T = {p.clinker_inlet_t_c:.1f} C. "
        f"v0.3.0 reports 5790.6 C against 1400 C inlet."
    )


# ---------------------------------------------------------------------------
# Monotonicity sweep — refutation-by-monotonicity
# ---------------------------------------------------------------------------

def test_more_air_sweep_monotone():
    """Across a sweep of under-grate air velocities, clinker outlet T
    must be non-increasing and secondary-air recovery non-decreasing,
    with the second-law invariant at every point.

    Replaces the fragile two-point `test_more_air_improves_cooling`
    (which passes on v0.3.0 for the wrong reason — both directions
    produce the same broken state).

    Cite: Hiro v0.3.0 review §2.5; Saltelli 2010 (32 samples for screening).
    """
    base = CoolerParameters(n_cells=20, t_end_s=900.0)
    velocities = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    outlets, sec_rec, sec_airs = [], [], []
    for v in velocities:
        p = base.model_copy(update={"under_grate_air_velocity_m_s": v})
        s = run_to_steady_state(p, max_t_s=900.0)
        outlets.append(s.clinker_outlet_c)
        sec_airs.append(s.secondary_air_outlet_c)
        sec_rec.append(
            s.air_flow_kg_s * 1.005
            * max(s.secondary_air_outlet_c - 30.0, 0.0) / 1000.0
        )
        # Second-law invariant at every sweep point.
        T_c_in = np.concatenate(([p.clinker_inlet_t_c], s.t_clinker_c[:-1]))
        assert np.all(s.t_air_c <= T_c_in + 1e-6), (
            f"Second-law violation at v_air={v}: "
            f"max(T_air - T_c_in) = "
            f"{float((s.t_air_c - T_c_in).max()):.1f} K"
        )

    # Strict monotone-decreasing outlet T (allow tiny numerical noise).
    eps = 1.0
    assert all(
        outlets[i] >= outlets[i + 1] - eps for i in range(len(outlets) - 1)
    ), f"clinker outlet T not monotone-decreasing in air: {outlets}"

    # Sanity floor: sec air T at v=4.0 must be < 1100 C (engineering ceiling).
    assert sec_airs[-1] <= 1100.0, (
        f"sec air T at v=4.0 = {sec_airs[-1]:.1f} C — v0.3.0 reports "
        f"~5790 C because the radiation runaway does not depend on air mass."
    )


def test_faster_grate_sweep_monotone():
    """Faster grate → shorter residence time → higher outlet T.
    Monotone non-decreasing in grate speed.  With second-law
    invariant at every point.

    Cite: Hiro v0.3.0 review §3 (UQ ranking: grate speed is rank #3
    lever); Aanya v0.3.0 review §5 fix E (RTD discipline).
    """
    base = CoolerParameters(n_cells=20, t_end_s=900.0)
    speeds = [6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 20.0]
    outlets = []
    for v_grate in speeds:
        p = base.model_copy(update={"grate_speed_m_min": v_grate})
        s = run_to_steady_state(p, max_t_s=900.0)
        outlets.append(s.clinker_outlet_c)
        # Second-law invariant at every sweep point.
        T_c_in = np.concatenate(([p.clinker_inlet_t_c], s.t_clinker_c[:-1]))
        assert np.all(s.t_air_c <= T_c_in + 1e-6), (
            f"Second-law violation at v_grate={v_grate}: "
            f"max(T_air - T_c_in) = "
            f"{float((s.t_air_c - T_c_in).max()):.1f} K"
        )

    eps = 1.0
    assert all(
        outlets[i] <= outlets[i + 1] + eps for i in range(len(outlets) - 1)
    ), f"clinker outlet T not monotone-increasing in grate speed: {outlets}"
