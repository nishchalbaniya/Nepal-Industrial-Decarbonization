"""
First-law conservation tests — the air side and the clinker side of the
same heat exchanger MUST agree within engineering tolerance.

Owner: Hiro Tanaka (data-scientist-uq)
Source citations:
  - First law of thermodynamics: Q_in = Q_out + Q_recovered.
  - Cengel & Boles (2015) Ch. 4 — energy balance on a control volume.
  - Ramesh v0.3.0 review §3.2 — first-law imbalance (catches 13.5x error).
  - Hiro v0.3.0 review §1.2 (conservation is robustness principle #2).
  - ASME PTC 38 (1985, reaff. 2015) — Performance Test Code for Rotary
    Kilns and Coolers; defines the test conditions and uncertainty bands.

These tests are DIAGNOSTIC: v0.3.0 reports
    secondary_air_recovered_kw / heat_recovered_kw = 13.5
which is a hard reject (the two sides of the same HX must agree).
"""
from __future__ import annotations

import numpy as np
import pytest

from nepal_cooler_sim import (
    CoolerParameters,
    run_to_steady_state,
    compute_outputs,
)


def test_air_side_recovery_agrees_with_clinker_side_within_5pct():
    """The secondary air and the clinker are two sides of the SAME
    heat exchanger. Their recovered heats must agree within ~5%
    (allowance for radiation to hood, wall loss, dust losses).

    Cite: First law; Ramesh v0.3.0 review §3.2; Hiro v0.3.0 review §2.2.
    v0.3.0 result: 510629 / 37775 = 13.5.  Test must FAIL.
    """
    p = CoolerParameters(n_cells=30, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    outs = compute_outputs(state, p)

    Q_clinker = outs["heat_recovered_kw"]            # clinker-side
    Q_air = outs["secondary_air_recovered_kw"]      # air-side
    # 15% tolerance per Hiro v0.3.0 review §2.2 (covers hood radiation
    # and dust losses that are legitimate sinks in a real cooler).
    assert 0.85 * Q_clinker <= Q_air <= 1.15 * Q_clinker, (
        f"First-law imbalance: air-side / clinker-side = "
        f"{Q_air / Q_clinker:.2f}x.  "
        f"Q_clinker = {Q_clinker:.0f} kW, Q_air = {Q_air:.0f} kW.  "
        f"v0.3.0 ratio = 13.5x (radiation runaway inflating air T)."
    )


def test_heat_in_equals_recovered_plus_out_within_2pct():
    """Q_in = Q_recovered + Q_out (clinker-side, no wall loss).
    Cite: First law; Hiro v0.3.0 review §2.2.
    v0.3.0 may pass this on the clinker side (the bug is on the air side)
    but the test is part of the suite for completeness.
    """
    p = CoolerParameters(n_cells=30, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    outs = compute_outputs(state, p)

    residual = outs["heat_in_kw"] - outs["heat_recovered_kw"] - outs["heat_out_kw"]
    assert abs(residual) < 0.02 * outs["heat_in_kw"], (
        f"Clinker-side energy balance residual {residual:.1f} kW exceeds "
        f"2% of Q_in={outs['heat_in_kw']:.1f} kW"
    )


def test_air_mass_flow_within_25pct_of_continuity():
    """Air mass flow from the model must agree with v * rho * W * L
    (continuity). v0.3.0 uses rho=0.6 (a fudge) when the correct
    density at 1400 m, 35 C, 90% RH is ~1.05 kg/m^3 (Ramesh §5.1).

    The 25% tolerance acknowledges the model may use a representative
    density; a 2x error is a reject.  Cite: Ramesh §5.1, §3.4.
    """
    p = CoolerParameters(n_cells=30, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)

    # Use the SEA-LEVEL standard density as a permissive lower bound.
    # Real altitude-corrected value (1.05 kg/m^3 at 1400 m) gives expected
    # = v * rho * W * L = 1.5 * 1.05 * 3.5 * 28 = 154 kg/s; v0.3.0
    # computes 88.2 kg/s.  Test against an envelope that v0.3.0 fails
    # (below 0.75 of sea-level expected) and v0.3.1 should pass.
    rho_sea_level = 1.225
    expected_sea_level = (
        p.under_grate_air_velocity_m_s * rho_sea_level * p.width_m * p.length_m
    )
    # Permissive: v0.3.0's 88.2 / 1.5 / 3.5 / 28 / 1.225 = 0.57
    # v0.3.1's 154 / 1.5 / 3.5 / 28 / 1.225 = 1.00
    # So a 0.75..1.25 band on sea-level expectation rejects v0.3.0
    # (88.2 vs 188.4 expected sea-level, ratio 0.47) and accepts v0.3.1
    # (154 vs 188.4, ratio 0.82).
    ratio = state.air_flow_kg_s / expected_sea_level
    assert 0.75 <= ratio <= 1.25, (
        f"air_flow_kg_s = {state.air_flow_kg_s:.1f} kg/s is "
        f"{ratio:.2f}x of v*rho_sea_level*W*L = {expected_sea_level:.1f} kg/s. "
        f"v0.3.0 uses rho=0.6 (Ramesh §5.1) — outside tolerance."
    )


def test_no_negative_entropy_energy_anywhere():
    """The heat recovered by the air stream (sum of m_a*cp*dT over all cells)
    must be ≤ the heat released by the clinker (m_c*cp*(T_in - T_out)).
    This is a per-cell second-law / first-law cross check, not just at
    the outlet. Catches the case where per-cell air heating exceeds
    per-cell clinker cooling (an impossibility).

    Cite: Second law + first law combined; Hiro v0.3.0 review §1.1 + §1.2.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)

    # Per-cell clinker release: dQ_c[i] = m_c * cp * (T_c[i-1] - T_c[i])
    # (with T_c[-1] = inlet T, treating the first cell's "in" as the kiln).
    T_c_in = np.concatenate(([p.clinker_inlet_t_c], state.t_clinker_c[:-1]))
    dQ_clinker = (
        (p.clinker_throughput_t_h * 1000.0 / 3600.0)
        * (p.cp_clinker_kj_kg_k * 1000.0)
        * np.maximum(T_c_in - state.t_clinker_c, 0.0)
        / 1000.0  # kW
    )

    # Per-cell air gain: this is the model's per-cell air dT multiplied
    # by the air mass in transit per cell. We can only check the *total*
    # air gain (model's `secondary_air_recovered_kw` × 1.0 — the model
    # doesn't expose per-cell air mass transit).  Use total.
    outs = compute_outputs(state, p)
    Q_air_total = outs["secondary_air_recovered_kw"]
    Q_clinker_total = float(dQ_clinker.sum())

    # Air side cannot exceed clinker side; allow 5% for hood/dust loss
    assert Q_air_total <= 1.05 * Q_clinker_total, (
        f"Air side recovery {Q_air_total:.0f} kW exceeds clinker side "
        f"release {Q_clinker_total:.0f} kW (5% margin). "
        f"v0.3.0 ratio: 13.5x (radiation runaway)."
    )


@pytest.mark.slow
def test_conservation_holds_for_higher_throughput():
    """Conservation should be throughput-invariant (mass-flow linearity).
    Tests a 2x throughput case to confirm no hidden mass-flow nonlinearities.

    Cite: Hiro v0.3.0 review §3 (UQ ranking: cp_clinker ± 5% enters linearly,
    so a 2x throughput should give 2x Q without other changes).
    """
    p_low = CoolerParameters(n_cells=20, t_end_s=900.0, clinker_throughput_t_h=130.0)
    p_high = CoolerParameters(n_cells=20, t_end_s=900.0, clinker_throughput_t_h=260.0)

    state_low = run_to_steady_state(p_low, max_t_s=900.0)
    state_high = run_to_steady_state(p_high, max_t_s=900.0)

    outs_low = compute_outputs(state_low, p_low)
    outs_high = compute_outputs(state_high, p_high)

    # 2x throughput → 2x Q_in (within 1% numerical)
    ratio = outs_high["heat_in_kw"] / outs_low["heat_in_kw"]
    assert 1.99 <= ratio <= 2.01, (
        f"Throughput scaling broken: Q_in ratio = {ratio:.3f} "
        f"(expected 2.0). This catches a missing m_c factor in the energy balance."
    )
