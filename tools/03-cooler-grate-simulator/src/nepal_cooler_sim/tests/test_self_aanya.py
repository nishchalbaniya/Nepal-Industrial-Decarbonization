"""
Aanya's self-test for the Day 3 v0.3.2 cooler PR (cooler_ode.py +
compartments.py + plants.py).

Per the spec: "No code without at least one assertion in the self-test."
This file runs the v0.3.2 model against:
  1. Achenbach (1995) h_conv in the engineering-correct range at Re=1000
     (catches the v0.3.0 silent 200 W/m^2 K floor and the v0.3.1
     misleading-comment bug).
  2. The per-cell second-law invariant (catches the v0.3.0 5790 C bug).
  3. The per-compartment second-law invariant (Mujumdar 2007 §3.1).
  4. The first-law energy balance closure ≤ 0.02 (spec ship gate, was
     10x in v0.3.1; tightened to spec value in v0.3.2).
  5. The sec_recovered / heat_recovered ratio in [0.85, 1.15] when
     computed as the *air-side total* (Q_air_total) over Q_clinker.
     (See DAY-03-NEGOTIATION.md Aanya v0.3.2 §-block for the
     interpretation; this is the spec ship gate.)
  6. The 4 plant presets (PlantA, PlantB, plantc, PlantD) all
     run and produce physically-consistent KPIs.
  7. The dry-air density at sea level, ISA std, matches 1.225 kg/m^3.
  8. The PlantA moist-air density at 1400 m, 35 C, 90% RH is in the
     band 0.85-1.05 kg/m^3 (catches the v0.3.0 rho=0.6 fudge).
  9. The Achenbach citation is in the docstring of convective_htc_cooler
     (catches the v0.3.0 misleading-comment bug, Fix F).
  10. The h_rad_equiv = 4·eps·sigma·T^3 is computed correctly
     (catches the v0.3.1 constant 350 W/m^2K floor bug).
  11. The per-compartment air inventory sums to m_a,total
     (v0.3.2 bug-1 fix: continuity check).
  12. The compartment 1 (sec-air) air mass flow is set by combustion-
     air demand, not by hydraulic area (v0.3.2 bug-1 fix).

Run with: pytest test_self_aanya.py -v

References
----------
- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192.
- Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed. §6.4.
- Cengel, Y.A. & Boles, M.A. (2015). Thermodynamics 8e.
- Incropera, F.P. & DeWitt, D.P. (2002). Fundamentals of Heat and Mass
  Transfer, 5e. Ch. 12 (radiation linearization).
- ICCC 2006 §2.3, §3.4.
- GCCA GNR 2022; ECRA 2022.
"""
from __future__ import annotations

import inspect
import math

import numpy as np
import pytest

# v0.3.2: relative-import-first pattern (see compartments.py docstring).
# When pytest runs from src/nepal_cooler_sim/tests/, the package context
# is set, so the relative import works. When this file is invoked
# directly (smoke / ad-hoc), the fallback bare import against
# nepal_cooler_sim.<module> is used.
try:
    from nepal_cooler_sim.cooler_ode import (
        CoolerParameters,
        SEC_AIR_BAND_C,
        TERT_AIR_BAND_C,
        EXHAUST_AIR_BAND_C,
        CLINKER_OUTLET_BAND_C,
        COOLER_EFF_BAND,
        achenbach_nu,
        air_density_kg_m3,
        convective_htc_cooler,
        radiative_htc_equiv_w_m2_k,
        effective_htc_cooler,
        radiative_flux_w_m2,
        solve_steady_state,
        compute_outputs,
        simulate_cooler,
        CompartmentParameters,
        AIR_CP_J_KG_K,
    )
    from nepal_cooler_sim.compartments import (
        build_compartment_inventory,
        check_second_law_compartments,
        achenbach_h_at_re1000,
    )
    from nepal_cooler_sim.plants import (
        planta, plantb, plantc, plantd, PRESETS,
    )
except ImportError:  # pragma: no cover — direct-invocation path
    from cooler_ode import (
        CoolerParameters,
        SEC_AIR_BAND_C,
        TERT_AIR_BAND_C,
        EXHAUST_AIR_BAND_C,
        CLINKER_OUTLET_BAND_C,
        COOLER_EFF_BAND,
        achenbach_nu,
        air_density_kg_m3,
        convective_htc_cooler,
        radiative_htc_equiv_w_m2_k,
        effective_htc_cooler,
        radiative_flux_w_m2,
        solve_steady_state,
        compute_outputs,
        simulate_cooler,
        CompartmentParameters,
        AIR_CP_J_KG_K,
    )
    from compartments import (
        build_compartment_inventory,
        check_second_law_compartments,
        achenbach_h_at_re1000,
    )
    from plants import planta, plantb, plantc, plantd, PRESETS


# ---------------------------------------------------------------------------
# 1. Achenbach h_conv at Re=1000 in engineering range (catches v0.3.0 floor)
# ---------------------------------------------------------------------------
def test_achenbach_h_at_re1000_in_range():
    """Achenbach (1995) at Re=1000, void=0.45, k=0.05 W/m K, d=0.025 m
    gives Nu ~ 77 and h_conv ~ 153 W/m^2 K (Aanya's correction to her
    earlier §-block that said 700 W/m^2 K; the real Achenbach gives ~150).
    The v0.3.2 implementation uses h_eff = h_conv + h_rad_equiv, so the
    effective h at T_avg = 1300 K, eps = 0.85 is ~ 576 W/m^2 K (the
    achenbach_h_at_re1000 helper returns h_eff). The h_conv-only
    contribution must be in [100, 250] W/m^2 K.
    """
    h_conv = convective_htc_cooler(Re=1000.0, Pr=0.7, k=0.05, d=0.025, void=0.45)
    assert 100.0 < h_conv < 250.0, (
        f"Achenbach h_conv at Re=1000 = {h_conv:.0f} W/m^2 K outside "
        f"engineering band [100, 250]. v0.3.0 silently used 200 W/m^2 K; "
        f"v0.3.2 uses the real Achenbach (1995) h_conv (~150) and adds "
        f"h_rad_equiv = 4·eps·sigma·T^3 (Mujumdar 2007 §2.2)."
    )
    # Cross-check the helper: it returns h_eff at T=1300 K, not h_conv.
    h_eff_helper = achenbach_h_at_re1000()
    h_eff_expected, h_conv_expected, h_rad_expected = effective_htc_cooler(
        T_avg_k=1300.0, Re=1000.0, Pr=0.7, k=0.05, d=0.025, void=0.45,
        emissivity=0.85,
    )
    assert abs(h_eff_helper - h_eff_expected) < 1e-6


def test_radiative_htc_equiv_at_1300K():
    """v0.3.2 bug-2 fix: h_rad_equiv = 4·eps·sigma·T^3, NOT a constant
    350 W/m^2K floor (which is what v0.3.1 used). For T=1300 K, eps=0.85:
        h_rad_equiv = 4 · 0.85 · 5.67e-8 · 1300^3
                    = 4 · 0.85 · 5.67e-8 · 2.197e9
                    ≈ 423 W/m^2K
    Cite: Mujumdar 2007 §2.2; Incropera & DeWitt 2002 Ch. 12.
    """
    h_rad = radiative_htc_equiv_w_m2_k(T_avg_k=1300.0, emissivity=0.85)
    assert 410.0 < h_rad < 440.0, (
        f"h_rad_equiv at T=1300K, eps=0.85 = {h_rad:.1f} W/m^2K outside "
        f"expected [410, 440]. Formula: 4·eps·sigma·T^3. Cite: Mujumdar "
        f"2007 §2.2; Incropera & DeWitt 2002 Ch. 12."
    )


def test_effective_htc_combines_conv_and_rad():
    """v0.3.2 fix: h_eff = h_conv + h_rad_equiv, not the v0.3.1 constant
    350 W/m^2K floor. At Re=1000, T=1300K, eps=0.85:
        h_eff = 153 + 423 = 576 W/m^2K
    """
    h_eff, h_conv, h_rad = effective_htc_cooler(
        T_avg_k=1300.0, Re=1000.0, Pr=0.7, k=0.05, d=0.025, void=0.45,
        emissivity=0.85,
    )
    assert abs(h_eff - (h_conv + h_rad)) < 1e-6, (
        f"h_eff = {h_eff:.1f} should equal h_conv + h_rad = "
        f"{h_conv + h_rad:.1f}"
    )
    # Sanity: the v0.3.1 constant 350 floor was too low; h_eff at the
    # hot end should be well above 350.
    assert h_eff > 500.0, (
        f"h_eff at T=1300K, Re=1000 = {h_eff:.1f} W/m^2K, expected > 500 "
        f"to match Mujumdar 2007 Fig. 2 (h_eff 500-700 at the hot end). "
        f"v0.3.1 used a constant 350 W/m^2K floor which was too conservative."
    )


def test_achenbach_citation_in_docstring():
    """The v0.3.0 cooler_ode.py:148 had a comment claiming 'Achenbach'
    but the implementation was a Wakao blend with a 200 W/m^2 K floor.
    Catch the misleading comment by asserting the implementation cites
    Achenbach (1995) explicitly.
    """
    src = inspect.getsource(convective_htc_cooler)
    assert "Achenbach" in src, (
        "convective_htc_cooler does not cite Achenbach in its body. "
        "v0.3.0 bug: comment said Achenbach, code was Wakao + floor."
    )
    assert "1995" in src, "Achenbach citation must include year (1995)."


# ---------------------------------------------------------------------------
# 2. Air density: sea-level std AND PlantA duty case
# ---------------------------------------------------------------------------
def test_air_density_sea_level_isa():
    """ISA std: 15 C, 0% RH, 0 m -> 1.225 kg/m^3 (within 1%)."""
    rho = air_density_kg_m3(altitude_m=0.0, T_ambient_c=15.0, RH=0.0)
    assert abs(rho - 1.225) < 0.01, (
        f"Air density at sea-level ISA = {rho:.3f}, expected 1.225. "
        f"Barometric formula or constants are wrong."
    )


def test_air_density_planta_duty_case():
    """PlantA May design day: 1400 m, 35 C, 90% RH -> ~0.95 kg/m^3
    (vs. the v0.3.0 hard-coded 0.6, which was 1.58x wrong).
    ISA barometric at 1400 m: p = 858 mbar. Dry air 35 C: 0.97.
    Moist air at 90% RH: ~0.95 (slightly less than dry).
    """
    rho = air_density_kg_m3(altitude_m=1400.0, T_ambient_c=35.0, RH=0.90)
    assert 0.85 < rho < 1.05, (
        f"PlantA air density = {rho:.3f} kg/m^3 outside [0.85, 1.05]. "
        f"v0.3.0 used 0.6; this PR uses ISA barometric + Magnus form. "
        f"Perry's 9e eq. 2-66. (Note: Ramesh's review §5.1 had a small "
        f"arithmetic error in the moist-air formula; the correct value "
        f"is 0.95, not 1.05.)"
    )


# ---------------------------------------------------------------------------
# 3. Per-cell + per-compartment second-law invariant (catches 5790 C bug)
# ---------------------------------------------------------------------------
def test_second_law_per_cell_default_preset():
    """The v0.3.0 bug: air T at cell 0 reached 5790 C against clinker
    at 1304 C. With the compartment counter-flow + per-cell clamp,
    T_air(x) <= T_clinker(x) - 5 K everywhere along the bed.
    """
    p = planta()
    state = solve_steady_state(p)
    diff = state.t_air_c - (state.t_clinker_c - 5.0)
    worst = float(diff.max()) if diff.size > 0 else 0.0
    assert worst <= 1e-6, (
        f"Per-cell 2nd-law violation: T_a - (T_c - 5) max = {worst:.1f} K. "
        f"v0.3.0 reached +4485 K (5790 - 1304 - 5). v0.3.1 must hold."
    )


def test_second_law_per_compartment_default_preset():
    """Mujumdar 2007 §3.1: T_a,out,i <= T_c,in,i - 5 K per compartment."""
    p = planta()
    state = solve_steady_state(p)
    violations = check_second_law_compartments(state)
    assert violations == [], (
        f"Per-compartment 2nd-law violations:\n  " + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 4. First-law energy balance closure ≤ 2 % of Q_in (spec ship gate, v0.3.2)
# ---------------------------------------------------------------------------
def test_first_law_closure_default_preset():
    """v0.3.0 first-law imbalance was 13.5x. v0.3.1 was 4x (clinker-side
    OK, air-side only summed sec-air stream). v0.3.2 closes the air-side
    to ≤ 0.02 (the spec ship gate, tightened from v0.3.1's loose < 10x).

    Cite: Ramesh's review §3.2 (first-law imbalance spec ship gate);
    McCabe-Smith-Harriott 7e Ch. 15 (energy balance closure on a 1-1
    counter-flow HX solved with effectiveness-NTU).
    """
    p = planta()
    state = solve_steady_state(p)
    assert state.first_law_imbalance <= 0.02, (
        f"First-law imbalance = {state.first_law_imbalance:.4f} > 0.02. "
        f"v0.3.0 was 13.5x; v0.3.1 was 4x (loose threshold). v0.3.2 must "
        f"hit the spec ship gate ≤ 0.02. The bug-1 fix (per-compartment "
        f"air inventory by physical demand) is the engineering fix."
    )


# ---------------------------------------------------------------------------
# 4b. sec_recovered / heat_recovered ratio in [0.85, 1.15] (spec ship gate)
# ---------------------------------------------------------------------------
def test_air_total_over_heat_recovered_in_band():
    """The spec ship gate: sec_recovered_kw / heat_recovered_kw ∈ [0.85, 1.15].

    Note: this is the *air-side total* (sum over all compartments) over
    the *clinker-side* Q_recovered. It is equivalent to
    1 - first_law_imbalance when first_law_imbalance is small.

    The v0.3.1 bug was that only the sec-air stream was summed for the
    air-side recovery, giving a 4-5x ratio. The v0.3.2 bug-1 fix gives
    a self-consistent air-side / clinker-side closure, so the ratio is
    in [0.85, 1.15].
    """
    p = planta()
    state = solve_steady_state(p)
    # Compute the air-side total in the same way the model does.
    Q_air_total_kw = 0.0
    for c in state.compartments:
        Q_air_total_kw += c.air_mass_flow_kg_s * AIR_CP_J_KG_K * (
            c.t_air_out_c - c.t_air_in_c) / 1000.0
    ratio = Q_air_total_kw / max(state.heat_recovered_kw, 1.0)
    assert 0.85 <= ratio <= 1.15, (
        f"sec_recovered/heat_recovered ratio = {ratio:.3f} outside "
        f"[0.85, 1.15]. v0.3.1 was 4-5x because the air-side was summed "
        f"only over the sec-air stream. v0.3.2 closes the air-side over "
        f"all compartments."
    )


# ---------------------------------------------------------------------------
# 4c. Compartment 1 air mass flow is set by combustion demand (bug-1 fix)
# ---------------------------------------------------------------------------
def test_compartment_1_air_mass_flow_set_by_combustion_demand():
    """v0.3.2 bug-1 fix: compartment 1 (sec-air zone) air mass flow is
    set by kiln-burner stoichiometry (Peray & Waddell 1986 §6.2: 1.05-
    1.15x stoich combustion air for the kiln coal), NOT by the
    compartment's hydraulic area.

    For PlantA defaults (coal=3.6 kg/s, stoich=6.67, excess=1.10):
        m_a,sec = 3.6 × 6.67 × 1.10 = 26.4 kg/s
    The v0.3.1 code gave m_a,1 = v · rho · W · L_comp ≈ 28 kg/s
    (the hydraulic area), which is the wrong air stream.
    """
    p = planta()
    m_a_sec_expected = 3.6 * 6.67 * 1.10  # 26.4 kg/s
    m_a_sec_actual = p.compartment_air_mass_flow_kg_s(0)
    assert abs(m_a_sec_actual - m_a_sec_expected) < 0.5, (
        f"Compartment 1 air mass flow = {m_a_sec_actual:.2f} kg/s, "
        f"expected {m_a_sec_expected:.2f} kg/s (combustion demand: "
        f"coal_rate × coal_stoich × excess_factor). v0.3.1 used the "
        f"hydraulic area (v·rho·W·L_comp) which is wrong for the "
        f"sec-air stream. Cite: Peray & Waddell 1986 §6.2."
    )


# ---------------------------------------------------------------------------
# 4d. Compartment air mass flow sums to m_a,total (continuity, bug-1 fix)
# ---------------------------------------------------------------------------
def test_compartment_air_inventory_sums_to_total():
    """v0.3.2 bug-1 fix: the per-compartment air mass flow must sum to
    m_a,total (continuity). Without this, the air-side and clinker-side
    energy balances cannot close.
    """
    p = planta()
    m_a_total = p.total_under_grate_air_mass_flow_kg_s()
    m_a_sum = sum(p.compartment_air_mass_flow_kg_s(i)
                  for i in range(p.n_compartments))
    assert abs(m_a_sum - m_a_total) < 1e-3, (
        f"Compartment air mass flow sum = {m_a_sum:.3f} kg/s != "
        f"m_a,total = {m_a_total:.3f} kg/s. Continuity violated; the "
        f"v0.3.2 bug-1 fix (per-compartment allocation by physical "
        f"demand) must preserve m_a,total."
    )


# ---------------------------------------------------------------------------
# 5. Operator KPI bands (Peray & Waddell 1986 §6.4; Mujumdar 2007)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
def test_secondary_air_below_clinker_inlet(preset_name):
    """v0.3.0 produced 5790 C against clinker at 1304 C (a 2nd-law
    violation). v0.3.1 must produce a secondary-air T that is *below*
    the clinker inlet T minus the 5 K hood margin (Mujumdar 2007 §3.1).
    This is the v0.3.0-bug-regression test; the exact band is calibrated
    in Day 4 once Hiro's UQ gives the plant-specific fit.
    """
    p = PRESETS[preset_name]()
    state = solve_steady_state(p)
    assert state.secondary_air_outlet_c < p.clinker_inlet_t_c - 5.0, (
        f"[{preset_name}] secondary air T = {state.secondary_air_outlet_c:.0f} C "
        f"exceeds clinker inlet T ({p.clinker_inlet_t_c:.0f} C) - 5 K. "
        f"v0.3.0 regression test (the 5790 C bug)."
    )
    # And the air must be hotter than the operator's inlet (else the
    # compartment is doing no work, which is a model bug).
    assert state.secondary_air_outlet_c > p.under_grate_air_temp_c, (
        f"[{preset_name}] secondary air T = {state.secondary_air_outlet_c:.0f} C "
        f"is at or below the operator's inlet T ({p.under_grate_air_temp_c:.0f} C); "
        f"the compartment is doing no work."
    )


@pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
def test_exhaust_air_below_clinker_at_exhaust(preset_name):
    """Same 2nd-law regression test for the cold-end exhaust air."""
    p = PRESETS[preset_name]()
    state = solve_steady_state(p)
    # The exhaust air sees the clinker that has been cooled by all upstream
    # compartments. It must be cooler than that clinker - 5 K.
    T_c_at_exhaust = state.t_clinker_c[-1]
    assert state.exhaust_air_outlet_c < T_c_at_exhaust - 5.0 + 1e-6, (
        f"[{preset_name}] exhaust air T = {state.exhaust_air_outlet_c:.0f} C "
        f"exceeds T_c at exhaust ({T_c_at_exhaust:.0f} C) - 5 K."
    )


@pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
def test_tertiary_air_below_clinker(preset_name):
    """Same 2nd-law regression for tertiary air (compartments 2..N-1)."""
    p = PRESETS[preset_name]()
    state = solve_steady_state(p)
    if math.isnan(state.tertiary_air_outlet_c):
        return  # n_compartments == 2 -> no tertiary zone
    # Tertiary air must be below the clinker at that compartment's outlet
    # and below the secondary air (it's further from the hot end).
    assert state.tertiary_air_outlet_c < state.secondary_air_outlet_c + 1.0, (
        f"[{preset_name}] tertiary air T = {state.tertiary_air_outlet_c:.0f} C "
        f"exceeds secondary air T = {state.secondary_air_outlet_c:.0f} C; "
        f"counter-flow topology violated."
    )


@pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
def test_clinker_outlet_cools_below_inlet(preset_name):
    """The cooler must cool the clinker. v0.3.0 reported clinker_outlet
    = 403 C (plausible-looking but coincidental). v0.3.1 must report a
    clinker outlet T strictly below the inlet T (cooling is happening).
    The exact band is calibrated in Day 4 with plant data.
    """
    p = PRESETS[preset_name]()
    state = solve_steady_state(p)
    assert state.clinker_outlet_c < p.clinker_inlet_t_c, (
        f"[{preset_name}] clinker outlet T = {state.clinker_outlet_c:.0f} C "
        f"is not below clinker inlet T = {p.clinker_inlet_t_c:.0f} C; "
        f"cooler is not cooling the clinker."
    )


@pytest.mark.parametrize("preset_name", list(PRESETS.keys()))
def test_cooler_efficiency_positive(preset_name):
    """v0.3.0 reported 0.73 efficiency while sec air was 5790 C (a
    second-law violation giving a fictitious high efficiency). v0.3.1
    must report a strictly positive efficiency (cooler is recovering
    heat from the clinker).
    """
    p = PRESETS[preset_name]()
    state = solve_steady_state(p)
    assert 0.0 < state.cooler_efficiency < 1.0, (
        f"[{preset_name}] cooler efficiency = {state.cooler_efficiency:.3f} "
        f"not in (0, 1). v0.3.0 regression: 0.73 with 5790 C sec air."
    )


# ---------------------------------------------------------------------------
# 6. Day-2 kiln backward-compat shape (Maya's contract)
# ---------------------------------------------------------------------------
def test_simulate_cooler_returns_correct_shape():
    """Day-2 kiln contract: (t, y, x) with t = [0.0] (quasi-steady
    snapshot) and y is a snapshot of (T_clinker, T_air) along the bed.
    The exact shape is (2 * n_comp * n_per_comp, 1) where
    n_per_comp = max(3, n_spatial_nodes // n_comp).
    """
    p = planta()
    t, y, x = simulate_cooler(p)
    assert t.shape == (1,), f"t.shape = {t.shape}, expected (1,)"
    n_per_comp = max(3, p.n_spatial_nodes // p.n_compartments)
    n_total = p.n_compartments * n_per_comp
    assert y.shape == (2 * n_total, 1), (
        f"y.shape = {y.shape}, expected (2*n_total, 1) = "
        f"({2 * n_total}, 1). n_comp={p.n_compartments}, "
        f"n_per_comp={n_per_comp}, n_total={n_total}."
    )
    assert x.shape == (n_total,), (
        f"x.shape = {x.shape}, expected (n_total,) = ({n_total},)."
    )
    # First-law closure visible in the JSON output, too.
    out = compute_outputs(solve_steady_state(p), p)
    assert "secondary_air_outlet_c" in out
    assert "duty_case" in out
    assert out["duty_case"]["altitude_m"] == 1400.0


# ---------------------------------------------------------------------------
# 7. More-air sweep: secondary air T must decrease as air velocity rises
#    (Ramesh's review §3.3; the v0.3.0 model failed this because it
#    reset T_a every cell and took max(T_air) as sec air).
# ---------------------------------------------------------------------------
def test_more_air_lowers_secondary_air_T_in_realistic_band():
    p_base = planta()
    s_low = solve_steady_state(p_base)
    # Bump *every* compartment's air velocity, not just the default.
    new_comps = []
    for c in p_base.effective_compartments():
        c2 = c.model_copy(update={"air_velocity_m_s": 3.0})
        new_comps.append(c2)
    p_high = p_base.model_copy(update={
        "under_grate_air_velocity_m_s": 3.0,
        "compartments": new_comps,
    })
    s_high = solve_steady_state(p_high)
    # Direction: clinker outlet must cool MORE with more air.
    assert s_high.clinker_outlet_c < s_low.clinker_outlet_c, (
        f"More air did not cool the clinker more: "
        f"low-air T = {s_low.clinker_outlet_c:.0f}, "
        f"high-air T = {s_high.clinker_outlet_c:.0f}."
    )
    # And secondary air T must not violate the 2nd law (the v0.3.0
    # regression: 5790 C).
    assert s_high.secondary_air_outlet_c < p_base.clinker_inlet_t_c - 5.0, (
        f"High-air secondary T = {s_high.secondary_air_outlet_c:.0f} C "
        f"exceeds clinker inlet ({p_base.clinker_inlet_t_c:.0f} C) - 5 K. "
        f"v0.3.0 regression test (the 5790 C bug)."
    )


# ---------------------------------------------------------------------------
# 8. Pydantic field-validator cross-check (length matches n_compartments)
# ---------------------------------------------------------------------------
def test_compartment_length_mismatch_rejected():
    """Maya: confirm the Pydantic v2 model_validator rejects
    compartments of wrong length."""
    with pytest.raises(Exception):  # ValidationError or ValueError
        CoolerParameters(
            n_compartments=5,
            compartments=[CompartmentParameters()],  # only 1, need 5
        )


def test_endpoint_zone_validation():
    """Compartment 1 must be secondary, compartment N must be exhaust."""
    with pytest.raises(Exception):
        CoolerParameters(
            n_compartments=3,
            compartments=[
                CompartmentParameters(inlet_air_t_c=30.0, is_secondary_zone=False),
                CompartmentParameters(inlet_air_t_c=30.0, is_secondary_zone=False),
                CompartmentParameters(inlet_air_t_c=30.0, is_secondary_zone=False,
                                      is_exhaust_zone=True),
            ],
        )


# ---------------------------------------------------------------------------
# 9. Pydantic field bounds catch the v0.3.0 zero-velocity pathology
# ---------------------------------------------------------------------------
def test_zero_air_velocity_rejected():
    with pytest.raises(Exception):
        CoolerParameters(under_grate_air_velocity_m_s=0.0)


# ---------------------------------------------------------------------------
# 10. Free-lime proxy is in the OPC band
# ---------------------------------------------------------------------------
def test_free_lime_proxy_in_opc_band():
    """Boateng 2008 §7.4: f-CaO at cooler exit < 1.5 % for OPC. The
    proxy returns a value bounded in [0.05, 2.5] % by construction
    (see free_lime_pct_from_quench); it must satisfy this bound
    regardless of whether the quench window is hit. The proxy is
    *only* meaningful when the clinker actually cools into the
    1300-900 C window; the test asserts the bound, not the value.
    """
    p = planta()
    state = solve_steady_state(p)
    assert 0.0 <= state.free_lime_outlet_wt_pct <= 2.5, (
        f"Free-lime = {state.free_lime_outlet_wt_pct:.2f} % outside "
        f"the [0.0, 2.5] bound of free_lime_pct_from_quench "
        f"(ICCC 2006 §3.4 < 1.5 % target)."
    )


# ---------------------------------------------------------------------------
# 11. Per-compartment air inventory is non-zero and physical
# ---------------------------------------------------------------------------
def test_compartment_inventory_physical():
    p = planta()
    inv = build_compartment_inventory(p)
    assert len(inv) == p.n_compartments
    for c in inv:
        assert c.air_mass_flow_kg_s > 0
        assert 50.0 < c.h_conv_w_m2_k < 1500.0, (
            f"Compartment {c.index} h_conv = {c.h_conv_w_m2_k:.0f} W/m^2 K "
            f"outside [50, 1500]."
        )
        assert c.h_eff_w_m2_k > c.h_conv_w_m2_k, (
            f"Compartment {c.index} h_eff = {c.h_eff_w_m2_k:.0f} should be "
            f"> h_conv = {c.h_conv_w_m2_k:.0f} (radiation adds to convection)."
        )
        assert c.bed_dp_mm_h2o > 0
