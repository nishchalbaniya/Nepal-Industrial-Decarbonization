"""
KPI band tests — assert the operator-facing KPIs from compute_outputs() land
in their engineering bands for each of the 4 Nepali plant presets.

Owner: Hiro Tanaka (data-scientist-uq)
Cross-check with: Ramesh (mech-eng-plant) — bands must be tight enough to
catch engineering errors but not so tight they fail on model uncertainty.

Source citations for the bands:
  - Peray & Waddell (1986) §6.4 — secondary-air T 600-900 C.
  - ECRA (2022) — cooler heat recuperation 75-80% BAT; total heat loss
    < 0.42 MJ/kg-cli.
  - ICCC 2006 §2.3 — f-CaO < 1.5% at cooler exit.
  - GCCA GNR 2022 — `cl_PM2` reporting convention: MJ/t-cli recovered.
  - Boateng (2008) Ch. 7 — clinker quench rate 150-300 K/min in the
    1300-900 C window for OPC.
  - KHD Pyrostep product literature — specific fan power 8-12 kW/(t/h).
  - Ramesh v0.3.0 review §4 (KPI gaps), §6 (Day-3 acceptance gate).

These tests are DIAGNOSTIC: the v0.3.0 model returns
    secondary_air_outlet_c = 5790.6 C
    clinker_outlet_c       = 403.7 C
which fail every band below. (Test conservatively tight bands reject
v0.3.0 with a clear error message — that is the point.)
"""
from __future__ import annotations

import pytest

from nepal_cooler_sim import (
    CoolerParameters,
    run_to_steady_state,
    compute_outputs,
)


# ---------------------------------------------------------------------------
# Plant preset parameters (4 Nepali plants). These are baseline configs
# that Ramesh will refine with altitude / RH / duty-case fields.
# Cite: Aanya's plants.py (to be built in v0.3.1); Ramesh §5.4 (Hetauda).
# ---------------------------------------------------------------------------

HETAUDA_PRESET = dict(
    length_m=28.0,
    width_m=3.5,
    bed_depth_m=0.70,
    n_compartments=5,
    n_cells=20,
    grate_speed_m_min=12.0,
    clinker_inlet_t_c=1400.0,
    clinker_outlet_t_c=150.0,
    under_grate_air_velocity_m_s=1.5,
    under_grate_air_temp_c=30.0,
    cp_clinker_kj_kg_k=1.05,
    emissivity=0.85,
    clinker_throughput_t_h=130.0,
    t_end_s=1800.0,
)

UDAYAPUR_PRESET = dict(HETAUDA_PRESET)  # UCIL is at ~300 m, similar duty

# 5000-tpd class, larger grate
HONGSHI_SHIVAM_PRESET = dict(
    HETAUDA_PRESET,
    length_m=32.0,
    width_m=3.8,
    grate_speed_m_min=14.0,
    clinker_throughput_t_h=208.0,
)

GHORAHI_PRESET = dict(HETAUDA_PRESET)


# ---------------------------------------------------------------------------
# Default-preset tests — these are the v0.3.0 default
# ---------------------------------------------------------------------------

def test_default_preset_secondary_air_in_realistic_band():
    """secondary_air_outlet_c in [600, 1000] C.
    Cite: Peray & Waddell §6.4; Hiro v0.3.0 review §2.4.
    v0.3.0 result: 5790.6 C — REJECTS.
    """
    p = CoolerParameters()
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert 600.0 <= state.secondary_air_outlet_c <= 1000.0, (
        f"secondary_air_outlet_c = {state.secondary_air_outlet_c:.1f} C "
        f"outside realistic band [600, 1000] C. "
        f"v0.3.0 reported 5790.6 C."
    )


def test_default_preset_clinker_outlet_in_realistic_band():
    """clinker_outlet_c in [120, 200] C (target 150 +/- 30 C).
    Cite: ECRA 2022 ("modern cooler < 100 C above ambient"); GCCA GNR 2022.
    v0.3.0 result: 403.7 C — REJECTS.
    """
    p = CoolerParameters()
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert 120.0 <= state.clinker_outlet_c <= 200.0, (
        f"clinker_outlet_c = {state.clinker_outlet_c:.1f} C "
        f"outside realistic band [120, 200] C."
    )


def test_default_preset_cooler_efficiency_in_band():
    """cooler_efficiency in [0.65, 0.85].
    Cite: ECRA 2022 BAT (75-80%); Peray & Waddell §6.4 (75-85%);
    GCCA GNR 2022 (Indian average 72-75%, BAT 78-80%).
    """
    p = CoolerParameters()
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert 0.65 <= state.cooler_efficiency <= 0.85, (
        f"cooler_efficiency = {state.cooler_efficiency:.3f} "
        f"outside [0.65, 0.85]. v0.3.0 reported 0.727 (in band, but for "
        f"the wrong reason — 5790 C air)."
    )


# ---------------------------------------------------------------------------
# Per-preset parametrized tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "preset_name,preset_kwargs",
    [
        ("hetauda", HETAUDA_PRESET),
        ("udayapur", UDAYAPUR_PRESET),
        ("hongshi_shivam", HONGSHI_SHIVAM_PRESET),
        ("ghorahi", GHORAHI_PRESET),
    ],
)
def test_preset_secondary_air_in_band(preset_name, preset_kwargs):
    p = CoolerParameters(**preset_kwargs)
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert 500.0 <= state.secondary_air_outlet_c <= 1100.0, (
        f"[{preset_name}] secondary_air_outlet_c = "
        f"{state.secondary_air_outlet_c:.1f} C outside [500, 1100] C. "
        f"Peray & Waddell §6.4 gives 600-900 C for a well-operated cooler."
    )


@pytest.mark.parametrize(
    "preset_name,preset_kwargs",
    [
        ("hetauda", HETAUDA_PRESET),
        ("udayapur", UDAYAPUR_PRESET),
        ("hongshi_shivam", HONGSHI_SHIVAM_PRESET),
        ("ghorahi", GHORAHI_PRESET),
    ],
)
def test_preset_clinker_outlet_in_band(preset_name, preset_kwargs):
    p = CoolerParameters(**preset_kwargs)
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert 100.0 <= state.clinker_outlet_c <= 250.0, (
        f"[{preset_name}] clinker_outlet_c = {state.clinker_outlet_c:.1f} C "
        f"outside [100, 250] C. ECRA 2022 BAT: < 100 C above ambient."
    )


@pytest.mark.parametrize(
    "preset_name,preset_kwargs",
    [
        ("hetauda", HETAUDA_PRESET),
        ("udayapur", UDAYAPUR_PRESET),
        ("hongshi_shivam", HONGSHI_SHIVAM_PRESET),
        ("ghorahi", GHORAHI_PRESET),
    ],
)
def test_preset_heat_in_kw_finite_and_positive(preset_name, preset_kwargs):
    """heat_in_kw must be finite & positive (clinker is hot at the inlet).
    Cite: first law; sanity check.
    """
    p = CoolerParameters(**preset_kwargs)
    state = run_to_steady_state(p, max_t_s=1800.0)
    outs = compute_outputs(state, p)
    import math
    assert math.isfinite(outs["heat_in_kw"])
    assert outs["heat_in_kw"] > 0.0
    # And it must be in a plausible engineering range:
    # For 130 t/h at 1400 C inlet, 30 C ref, cp=1.05 kJ/kg/K:
    #   Q_in = (130/3.6) * 1.05 * (1400-30) = 36.1 * 1.05 * 1370 = 51,946 kW
    # For 208 t/h (Hongshi-Shivam 5000-tpd class):
    #   Q_in = (208/3.6) * 1.05 * 1370 = 83,113 kW
    # Cite: heat balance, first law.
    if "hongshi" in preset_name:
        assert 70_000.0 <= outs["heat_in_kw"] <= 100_000.0
    else:
        assert 40_000.0 <= outs["heat_in_kw"] <= 65_000.0


# ---------------------------------------------------------------------------
# Per-preset fragility: tighter bands for the v0.3.0 5790 C bug
# ---------------------------------------------------------------------------

def test_hetauda_secondary_air_does_not_exceed_1100c():
    """Hard ceiling at 1100 C for Hetauda.
    v0.3.0 result: 5790.6 C — REJECTS. Cite: Peray & Waddell §6.4.
    """
    p = CoolerParameters(**HETAUDA_PRESET)
    state = run_to_steady_state(p, max_t_s=1800.0)
    assert state.secondary_air_outlet_c <= 1100.0, (
        f"secondary_air_outlet_c = {state.secondary_air_outlet_c:.1f} C "
        f"exceeds engineering ceiling 1100 C. v0.3.0 reported 5790.6 C."
    )


# ---------------------------------------------------------------------------
# Outputs dict structure (cross-checks for compute_outputs)
# ---------------------------------------------------------------------------

def test_outputs_dict_contains_required_kpis():
    """compute_outputs must include the operator KPIs.
    Cite: Ramesh v0.3.0 review §4 (KPI gaps).
    """
    p = CoolerParameters()
    state = run_to_steady_state(p, max_t_s=1800.0)
    outs = compute_outputs(state, p)
    required = [
        "clinker_outlet_c", "secondary_air_outlet_c", "cooler_efficiency",
        "heat_in_kw", "heat_out_kw", "heat_recovered_kw",
        "secondary_air_recovered_kw",
    ]
    for k in required:
        assert k in outs, f"compute_outputs missing required KPI: {k}"
        import math
        assert math.isfinite(outs[k]), f"{k} is not finite: {outs[k]}"
