"""
Ramesh (mech-eng-plant) — Day 3 v0.3.1 outputs.py
=================================================

Full operator KPI dictionary for the grate cooler simulator.

Owner: Ramesh Adhikari (mech-eng-plant)
PR:   day-03-PRs/mech-eng-plant/outputs.py

Scope
-----
This module owns the *output* side of the cooler model. It does **not**
solve the physics; it consumes a `CoolerResult` (Aanya's compartment-wise
counter-flow solver output) and produces the operator-grade KPI block
that goes into the JSON / CSV / CLI table.

Engineering references
----------------------
  - ISA-5.1 (2009) — Instrumentation Symbols and Identification.
    Used for the instrument-tagged field list in §4.
  - ISA-5.3 (1983, reaffirmed 2008) — Instrument tag conventions.
  - Peray, K.E. & Waddell, J.J. (1986). *The Rotary Cement Kiln*,
    2nd ed., Chemical Publishing. §6.2–6.4 — secondary-air T
    600–900 °C, sec-air 0.30–0.45 GJ/t-cli, ΔP 50–80 mm H₂O first
    compartment, 25–40 mm H₂O last.
  - Mujumdar, K.S. (2007). Grate cooler model. *Ind. Eng. Chem. Res.*
    46(7), 2180–2189. Fig. 4 (compartment labeling) and §2.2 (sec-air
    compartment).
  - Boateng, A.A. (2008). *Rotary Kilns*, Ch. 7. §7.4 (quench rate vs
    f-CaO).
  - ECRA (2022). Best Available Techniques Reference Document for the
    Cement Industry. "Modern reciprocating coolers can have a high
    degree of heat recuperation efficiency up to 75 to 80 %. The
    total heat loss of latest generation clinker coolers is less than
    0.42 MJ/kg cli." Also: 8–10 kWh/t-cli recoverable from cooler
    exhaust as WHR.
  - GCCA GNR 2022 — "Getting the Numbers Right" reporting convention
    `cl_PM2` (cooler heat recovery in MJ/t-cli).
  - IKN `Pyrorotor` / KHD `Pyrostep` / Polysius `REPOL` product
    literature. Specific fan power 8–12 kW/(t/h) for modern coolers.
  - ISO 2533:1975 — Standard atmosphere (altitude density).

All numerical conversions are explicit. SI units internally; convert
only at the boundary (Nm³/h, mm H₂O, t/h).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Any, Optional, TypedDict

import numpy as np
from pydantic import BaseModel, Field

# SI constants ---------------------------------------------------------------

R_D_AIR = 287.05                 # J/(kg·K), dry-air gas constant
R_V_WATER = 461.495              # J/(kg·K), water-vapour gas constant
STEFAN_BOLTZMANN = 5.670374419e-8
CP_AIR_J_KG_K = 1005.0           # J/(kg·K), under-grate air (200–1000 °C band)
CP_AIR_NM3 = 1320.0              # J/(Nm³·K) at 0 °C, 1 atm
AIR_DENSITY_NM3 = 1.293          # kg/Nm³, dry air at 0 °C, 1 atm
STD_ATM_SCALE_HEIGHT_M = 8430.0  # m, ISO 2533 barometric
STEFAN_BOLTZMANN = 5.670374419e-8

# Conversion factors ---------------------------------------------------------
T_K_OFFSET = 273.15
KJ_PER_KWH = 3600.0
SEC_PER_HR = 3600.0
MM_H2O_PER_KPA = 101.971621298  # 1 kPa ≈ 101.97 mm H₂O at 4 °C


# ---------------------------------------------------------------------------
# Duty case — altitude, ambient, %MCR
# ---------------------------------------------------------------------------

class DutyCase(BaseModel):
    """Operating conditions for the cooler design point.

    Mandatory in every output block (API 617 / HEI / Peray §6.4 discipline):
    a cooler commissioned at sea level will not deliver the design
    heat duty in PlantA's monsoon design day. This block is the answer
    to the question "what ambient were these KPIs computed at?"
    """
    altitude_m: float = Field(
        1400.0, ge=0.0, le=4000.0,
        description="Plant altitude above mean sea level (m). "
                    "PlantA 1400 m, PlantB 300 m, plantc "
                    "Sarlahi 80 m, PlantD 200 m."
    )
    ambient_t_c: float = Field(
        35.0, ge=-30.0, le=55.0,
        description="Ambient dry-bulb temperature at the design day (°C). "
                    "Use the May/October design day for fan sizing."
    )
    ambient_rh: float = Field(
        0.90, ge=0.0, le=1.0,
        description="Ambient relative humidity (fraction)."
    )
    design_mcr_pct: float = Field(
        100.0, ge=70.0, le=110.0,
        description="Maximum Continuous Rating (% of nameplate). "
                    "100 % is normal design; 105 % for short-term margin."
    )

    @property
    def air_density_kg_m3(self) -> float:
        """Moist-air density per ASHRAE Handbook (Fundamentals) 2021 Ch. 1.

        Partial-pressure sum:
            ρ = p_d / (R_d · T) + p_v / (R_v · T)
        where p_d = p_atm − p_v, R_d = 287.05 J/(kg·K), R_v = 461.495 J/(kg·K).
        At 35 °C / 90 % RH / 1400 m → ≈ 1.05 kg/m³. Verify against the
        standard-engineering table in Perry's 9th ed. Ch. 11.
        """
        p_atm_pa = 101325.0 * math.exp(-self.altitude_m / STD_ATM_SCALE_HEIGHT_M)
        t_k = self.ambient_t_c + T_K_OFFSET
        p_ws_pa = 611.2 * math.exp(17.62 * self.ambient_t_c / (243.12 + self.ambient_t_c))
        p_v_pa = self.ambient_rh * p_ws_pa
        p_d_pa = p_atm_pa - p_v_pa
        return p_d_pa / (R_D_AIR * t_k) + p_v_pa / (R_V_WATER * t_k)

    @property
    def p_atm_mbar(self) -> float:
        return 1013.25 * math.exp(-self.altitude_m / STD_ATM_SCALE_HEIGHT_M)


# ---------------------------------------------------------------------------
# Compartment result container (read by outputs)
# ---------------------------------------------------------------------------

class CompartmentResult(TypedDict):
    """Per-compartment engineering result. Shape per Mujumdar (2007) Fig. 4."""
    index: int                # 1-indexed compartment
    x_start_m: float
    x_end_m: float
    length_m: float
    t_clinker_in_c: float
    t_clinker_out_c: float
    t_air_in_c: float
    t_air_out_c: float
    air_mass_flow_kg_s: float
    dp_mm_h2o: float          # under-grate pressure drop, Ergun equation
    role: str                 # "secondary" | "tertiary" | "exhaust" | "cooling"


class CoolerResult(TypedDict):
    """Quasi-steady output of the compartment-wise cooler solver.

    The Day-3 data-shape contract (Q3 = option b). `simulate_cooler()`
    flattens this to `(t, y, x)` for kiln-link compat, but the
    *engineering* entry point returns this dataclass.
    """
    profile: list[CompartmentResult]
    n_compartments: int
    n_spatial_nodes: int
    x_m: list[float]                # spatial grid, length = n_spatial_nodes
    t_clinker_c: list[float]        # spatial profile, length = n_spatial_nodes
    t_air_c: list[float]            # spatial profile, length = n_spatial_nodes
    secondary_air_outlet_c: float
    tertiary_air_outlet_c: float    # flow-weighted mean of compartments 2..N-1
    exhaust_air_outlet_c: float
    clinker_outlet_c: float
    cooler_efficiency: float
    first_law_imbalance: float      # (Q_clinker_side - Q_air_side) / Q_clinker_side
    fan_power_kw: float
    bed_dp_total_mm_h2o: float
    free_lime_outlet_wt_pct: float
    mj_per_t_cli_recovered: float   # GCCA GNR 2022 cl_PM2 indicator
    duty_case: dict                 # serialised DutyCase


# ---------------------------------------------------------------------------
# KPI block — the operator dashboard
# ---------------------------------------------------------------------------

class CoolerKPIs(TypedDict):
    """Operator-grade KPI block. One dict per cooler steady-state solution.

    Each field has an ISA-5.3 instrument tag and a data-quality tier
    (Kabita's hierarchy, see `env-eng-permitting` review).
    """
    # Throughput & material balance
    clinker_throughput_t_h: float
    clinker_mass_flow_kg_s: float
    total_air_mass_flow_kg_s: float

    # Air streams — secondary / tertiary / exhaust
    secondary_air_T_c: float          # ISA-5.3 tag: TI-1101
    secondary_air_Nm3_h: float        # FI-1101
    secondary_air_recovered_kw: float # calculated from m·cp·dT
    secondary_air_recovered_gj_per_t_cli: float  # GCCA cl_PM2 partial
    secondary_air_stoich_ratio: float # 1.0–1.2 typical, Peray §6.2

    tertiary_air_T_c: float           # TI-1102
    tertiary_air_Nm3_h: float         # FI-1102
    exhaust_air_T_c: float            # TI-1103
    exhaust_air_Nm3_h: float          # FI-1103

    # Clinker side
    clinker_inlet_T_c: float
    clinker_outlet_T_c: float
    clinker_outlet_T_target_c: float
    outlet_within_target: bool
    clinker_quench_rate_k_per_min: float  # in 1300→900 °C window
    free_lime_outlet_wt_pct: float        # estimated, Tier 3

    # Energy & efficiency
    heat_in_kw: float
    heat_out_kw: float
    heat_recovered_kw: float
    cooler_efficiency: float
    cooler_loss_mj_per_t_cli: float       # vs ECRA BAT 0.42 MJ/kg-cli ceiling
    first_law_imbalance: float            # closure residual, target < 0.02

    # Fluid mechanics & equipment
    bed_dp_total_mm_h2o: float
    bed_dp_profile_mm_h2o: list[float]    # per-compartment
    fan_power_kw: float
    specific_fan_power_kw_per_tph: float  # 8-12 kW/(t/h), IKN/KHD
    residence_time_s: float

    # Sanity block
    sanity: dict

    # Duty case (mandatory for sign-off)
    duty_case: dict


# ---------------------------------------------------------------------------
# Engineering helpers — independent of the solver
# ---------------------------------------------------------------------------

def air_density_kg_m3(
    altitude_m: float,
    ambient_t_c: float,
    ambient_rh: float = 0.5,
) -> float:
    """Moist-air density, ISO 2533 standard atmosphere + ASHRAE Ch. 1.

    Replaces the v0.3.0 hard-coded 0.6 kg/m³. Cite: ISO 2533:1975,
    ASHRAE Handbook (Fundamentals) 2021 Ch. 1, Peray & Waddell (1986)
    §6.4 fan-duty correction.
    """
    p_atm_pa = 101325.0 * math.exp(-altitude_m / STD_ATM_SCALE_HEIGHT_M)
    t_k = ambient_t_c + T_K_OFFSET
    p_ws_pa = 611.2 * math.exp(17.62 * ambient_t_c / (243.12 + ambient_t_c))
    p_v_pa = ambient_rh * p_ws_pa
    p_d_pa = p_atm_pa - p_v_pa
    return p_d_pa / (R_D_AIR * t_k) + p_v_pa / (R_V_WATER * t_k)


def secondary_air_stoichiometric_kg_s(
    coal_rate_kg_s: float,
    stoich_factor: float = 1.10,
) -> float:
    """Stoichiometric combustion air for kiln coal at sec-air compartment.

    For typical coal (C→CO₂, H→H₂O, S→SO₂): stoich O₂ ≈ 1.4 kg/kg-coal.
    Air is 21 % O₂ by mass → stoich air = 1.4/0.21 ≈ 6.67 kg-air/kg-coal.
    A real kiln-burner runs at 1.05–1.15× stoich (Peray & Waddell 1986 §6.2).
    Returns mass flow in kg/s.
    """
    return coal_rate_kg_s * 6.67 * stoich_factor


def bed_dp_mm_h2o_ergun(
    air_velocity_m_s: float,
    air_density_kg_m3: float,
    air_viscosity_pa_s: float,
    particle_d_m: float,
    void_fraction: float,
    bed_depth_m: float,
) -> float:
    """Under-grate pressure drop, Ergun equation.

    Cite: Ergun (1952) "Fluid flow through packed columns",
    *Chem. Eng. Prog.* 48, 89–94. Perry's 9th ed. Ch. 11.

    Returns ΔP in mm H₂O (1 kPa = 101.97 mm H₂O at 4 °C).
    """
    if particle_d_m <= 0 or void_fraction <= 0 or void_fraction >= 1.0:
        return 0.0
    eps = void_fraction
    dp_m = particle_d_m
    L = bed_depth_m
    v = air_velocity_m_s
    rho = air_density_kg_m3
    mu = air_viscosity_pa_s
    # Viscous term + inertial term (Ergun eq. 1)
    term1 = (150.0 * mu * v * (1.0 - eps) ** 2) / (dp_m ** 2 * eps ** 3)
    term2 = (1.75 * rho * v ** 2 * (1.0 - eps)) / (dp_m * eps ** 3)
    dp_pa = (term1 + term2) * L
    dp_kpa = dp_pa / 1000.0
    return dp_kpa * MM_H2O_PER_KPA


def fan_power_kw(
    air_flow_m3_s: float,
    dp_mm_h2o: float,
    fan_efficiency: float = 0.72,
) -> float:
    """Total fan shaft power. `fan_efficiency=0.72` is a modern
    high-efficiency backward-curved centrifugal fan (Peray & Waddell
    1986 §6.4; AMCA 2016 fan efficiency tables).
    """
    if fan_efficiency <= 0:
        return 0.0
    # P = V̇ · ΔP / η, with ΔP in Pa = mm_H2O · 9.80665
    dp_pa = dp_mm_h2o * 9.80665
    return air_flow_m3_s * dp_pa / fan_efficiency / 1000.0


def free_lime_wt_pct(
    quench_rate_k_per_min: float,
) -> float:
    """Empirical f-CaO estimate from 1300→900 °C quench rate.

    Cite: Boateng (2008) Ch. 7 §7.4. OPC target: f-CaO < 1.5 %.
    Slow quench → C₃S continues to disproportionate → f-CaO rises.
    Fast quench → glassy phase → grindability suffers (different KPI,
    not captured here).
    """
    # Linear ramp: 100 K/min → 1.8 %, 460 K/min → 0.0 %.
    # Floor at 0.2 % (residual), ceiling at 1.8 % (severely under-cooled).
    f_cao = max(0.0, 1.8 - 0.005 * (quench_rate_k_per_min - 100.0))
    return max(0.2, min(1.8, f_cao))


def cooler_efficiency(
    clinker_inlet_t_c: float,
    clinker_outlet_t_c: float,
    reference_t_c: float = 30.0,
) -> float:
    """Peray & Waddell (1986) §6.2 cooler efficiency definition:

        η = (T_in − T_out) / (T_in − T_ref)

    where T_ref is the ambient reference (30 °C nominal). BAT band
    75-80 % (ECRA 2022). Note: definition is dimensionless, no cp
    needed.
    """
    if clinker_inlet_t_c <= reference_t_c:
        return 0.0
    return max(
        0.0,
        min(
            1.0,
            (clinker_inlet_t_c - clinker_outlet_t_c)
            / (clinker_inlet_t_c - reference_t_c),
        ),
    )


def quench_rate_k_per_min(
    t_clinker_profile_c: np.ndarray,
    x_m: np.ndarray,
    grate_speed_m_min: float,
    t_window_high_c: float = 1300.0,
    t_window_low_c: float = 900.0,
) -> float:
    """Quench rate in the 1300→900 °C window, computed from the spatial
    profile and the grate travel speed.

    The spatial profile is converted to a time profile by `t = x / v_grate`
    (clinker rides the grate). The 1300→900 °C window is the OPC quench
    zone; the 1300 °C end is C₃S formation completion; the 900 °C end is
    below the C₃S decomposition temperature. (Boateng 2008 §7.4.)
    """
    if grate_speed_m_min <= 0 or len(t_clinker_profile_c) < 2:
        return 0.0
    # Convert spatial → time
    v_grate_m_s = grate_speed_m_min / 60.0
    t_s = x_m / max(v_grate_m_s, 1e-3)
    t_profile = np.asarray(t_clinker_profile_c, dtype=float)
    # Find the indices bracketing the temperature window
    t_in_idx = None
    t_out_idx = None
    for i in range(len(t_profile) - 1):
        if t_profile[i] >= t_window_high_c >= t_profile[i + 1]:
            t_in_idx = i
        if t_profile[i] >= t_window_low_c >= t_profile[i + 1]:
            t_out_idx = i
            break
    if t_in_idx is None or t_out_idx is None:
        # Fall back to profile endpoints
        t_in_idx, t_out_idx = 0, len(t_profile) - 1
    dt_s = t_s[t_out_idx] - t_s[t_in_idx]
    if dt_s <= 0:
        return 0.0
    dt_k = float(t_window_high_c - t_window_low_c)
    return (dt_k / dt_s) * 60.0  # K/min


def kg_s_to_nm3_h(mass_flow_kg_s: float) -> float:
    """Convert kg/s to Nm³/h at 0 °C, 1 atm dry air (1.293 kg/Nm³)."""
    return mass_flow_kg_s * SEC_PER_HR / AIR_DENSITY_NM3


# ---------------------------------------------------------------------------
# Main KPI builder
# ---------------------------------------------------------------------------

@dataclass
class CoolerParametersProxy:
    """Subset of CoolerParameters needed by compute_kpis.

    The full Pydantic `CoolerParameters` is owned by Aanya. This proxy
    lets `outputs.py` be unit-testable without importing the ODE solver.
    """
    length_m: float
    width_m: float
    bed_depth_m: float
    n_compartments: int
    n_cells: int
    grate_speed_m_min: float
    clinker_inlet_t_c: float
    clinker_outlet_t_c: float
    under_grate_air_velocity_m_s: float
    under_grate_air_temp_c: float
    cp_clinker_kj_kg_k: float
    rho_clinker_kg_m3: float
    emissivity: float
    clinker_throughput_t_h: float
    void_fraction: float
    clinker_diameter_m: float
    coal_rate_kg_s: float = 1.0      # 100 kg/t-cli at 130 t/h ≈ 3.6 kg/s
    fan_efficiency: float = 0.72
    air_viscosity_pa_s: float = 4.0e-5  # at ~800 K, 1 atm
    duty_case: DutyCase = field(default_factory=DutyCase)


def compute_kpis(
    result: CoolerResult,
    p: CoolerParametersProxy,
) -> CoolerKPIs:
    """Build the full operator KPI block from a `CoolerResult` and the
    inputs. Pure function — no side effects, no I/O.

    Cite sources inline. The output is a `TypedDict` so Maya's Pydantic
    `BaseModel` wrapper in `outputs.py` (her `io.py`) can validate it.

    The "sanity" sub-block contains the *derived* red-flag booleans that
    should drive the operator's dashboard alarm colour. Per Peray &
    Waddell (1986) §6.4 commissioning checklist.
    """
    m_clinker_kg_s = p.clinker_throughput_t_h * 1000.0 / 3600.0
    cp_j_kg_k = p.cp_clinker_kj_kg_k * 1000.0

    # ---- Air-mass-flow bookkeeping ----------------------------------------
    # Total cooling air = v · ρ · W · L (continuity). ρ from DutyCase.
    duty = p.duty_case
    rho_air = duty.air_density_kg_m3
    total_air_kg_s = (
        p.under_grate_air_velocity_m_s * rho_air * p.width_m * p.length_m
    )
    # Per-compartment mass flow
    air_per_comp_kg_s = total_air_kg_s / max(p.n_compartments, 1)

    # ---- Secondary-air KPI -------------------------------------------------
    sec_t = float(result["secondary_air_outlet_c"])
    # Secondary-air-only recovery (compartment 1 → kiln burner). This is
    # the number the kiln couples on.
    sec_recovered_kw = (
        air_per_comp_kg_s * CP_AIR_J_KG_K
        * max(sec_t - p.under_grate_air_temp_c, 0.0) / 1000.0
    )

    # ---- Tertiary air (flow-weighted mean of comps 2..N-1) ----------------
    comps = result["profile"]
    if p.n_compartments >= 3:
        tert_comps = [c for c in comps if c["role"] == "tertiary"]
        if tert_comps:
            num = sum(c["t_air_out_c"] * c["air_mass_flow_kg_s"] for c in tert_comps)
            den = sum(c["air_mass_flow_kg_s"] for c in tert_comps)
            tert_t = num / max(den, 1e-9)
        else:
            tert_t = float(np.mean([c["t_air_out_c"] for c in comps[1:-1]]))
    else:
        tert_t = float(result["t_air_c"][len(result["t_air_c"]) // 2])

    # ---- Exhaust air -------------------------------------------------------
    exhaust_t = float(result["exhaust_air_outlet_c"])

    # ---- Energy balance ---------------------------------------------------
    # Clinker-side (per Peray §6.2: total heat released by clinker)
    heat_in_kw = m_clinker_kg_s * cp_j_kg_k * (
        p.clinker_inlet_t_c - p.under_grate_air_temp_c
    ) / 1000.0
    heat_out_kw = m_clinker_kg_s * cp_j_kg_k * max(
        result["clinker_outlet_c"] - p.under_grate_air_temp_c, 0.0
    ) / 1000.0
    heat_recovered_kw = max(heat_in_kw - heat_out_kw, 0.0)

    # Air-side (sum over all compartments: secondary + tertiary + exhaust).
    # Each compartment's air stream picks up `m_a,i · cp · (T_a_out − T_a_in)`.
    # This is the *correct* first-law pairing with heat_recovered_kw.
    air_recovered_kw_total = 0.0
    for c in comps:
        air_recovered_kw_total += (
            c["air_mass_flow_kg_s"] * CP_AIR_J_KG_K
            * max(c["t_air_out_c"] - c["t_air_in_c"], 0.0) / 1000.0
        )
    # First-law imbalance: air-side vs clinker-side must agree within 2 %
    if heat_in_kw > 0:
        first_law_imbalance = abs(heat_recovered_kw - air_recovered_kw_total) / heat_in_kw
    else:
        first_law_imbalance = 0.0

    # ---- Per-compartment bed ΔP (Ergun) -----------------------------------
    # Note: ΔP here is the *bed* ΔP (Ergun over bed depth). The cooler fan
    # also pulls air through the dust collector (~120 mm H₂O typical for
    # a baghouse on cement cooler exhaust) and the ducting/stack draft
    # (~80 mm H₂O). Total system ΔP ~ 5× bed ΔP is a standard rule of
    # thumb (Peray §6.4 + industrial dust-collector catalogues).
    dp_profile = [
        bed_dp_mm_h2o_ergun(
            air_velocity_m_s=p.under_grate_air_velocity_m_s,
            air_density_kg_m3=rho_air,
            air_viscosity_pa_s=p.air_viscosity_pa_s,
            particle_d_m=p.clinker_diameter_m,
            void_fraction=p.void_fraction,
            bed_depth_m=p.bed_depth_m,
        )
        for _ in range(p.n_compartments)
    ]
    bed_dp_total = float(sum(dp_profile))
    # Total system ΔP for the *cooler fan* includes dust collector + ducting.
    # The system ΔP / bed ΔP ratio is 3-4× for a modern KHD/IKN cooler
    # (Peray §6.4 + KHD Pyrostep product literature: bed 50-80 mm H₂O
    # first comp, system ΔP 200-300 mm H₂O total). Use 3.5× as a
    # representative midpoint.
    system_dp_total_mm_h2o = bed_dp_total * 3.5
    # Fan power: V̇_total · ΔP_system / η_fan. V̇ at duty density.
    vol_flow_m3_s = total_air_kg_s / rho_air
    fp_kw = fan_power_kw(vol_flow_m3_s, system_dp_total_mm_h2o, p.fan_efficiency)
    sfp = fp_kw / max(p.clinker_throughput_t_h, 1e-3)  # kW per t/h

    # ---- Quench rate & free-lime (Boateng 2008 §7.4) ----------------------
    t_profile_np = np.asarray(result["t_clinker_c"], dtype=float)
    x_np = np.asarray(result["x_m"], dtype=float)
    q_rate = quench_rate_k_per_min(
        t_profile_np, x_np, p.grate_speed_m_min,
    )
    f_cao = free_lime_wt_pct(q_rate)

    # ---- Residence time ---------------------------------------------------
    residence_s = p.length_m / max(p.grate_speed_m_min / 60.0, 1e-3)

    # ---- Per-tonne KPIs (GCCA GNR 2022 reporting convention) --------------
    # Q [kW] · 3600 [s/hr] / tph [t/hr] = kJ/t = MJ/t · 1000.
    # Divide by 1e6 to get GJ/t.
    mj_per_t = heat_recovered_kw * KJ_PER_KWH / p.clinker_throughput_t_h / 1000.0
    sec_gj_per_t = (
        sec_recovered_kw * KJ_PER_KWH / p.clinker_throughput_t_h / 1.0e6
    )
    # ECRA 2022 BAT: total cooler heat loss < 0.42 MJ/kg-cli = 420 MJ/t-cli.
    # mj_per_t is the recovered heat; loss = (Q_in_sensible − Q_recovered) per t.
    q_in_mj_t = m_clinker_kg_s * cp_j_kg_k * (p.clinker_inlet_t_c - p.under_grate_air_temp_c) / 1000.0
    q_in_mj_t = q_in_mj_t * KJ_PER_KWH / p.clinker_throughput_t_h / 1000.0
    cooler_loss_mj_per_t = max(q_in_mj_t - mj_per_t, 0.0)  # actual heat loss vs BAT ceiling

    # ---- Sanity block -----------------------------------------------------
    t_clinker_arr = np.asarray(result["t_clinker_c"], dtype=float)
    t_air_arr = np.asarray(result["t_air_c"], dtype=float)
    T_c_in_to_cell = np.concatenate(
        ([p.clinker_inlet_t_c], t_clinker_arr[:-1])
    )
    air_above_clinker = bool(np.any(t_air_arr > T_c_in_to_cell + 5.0))
    eff = float(result["cooler_efficiency"])
    sec_air_in_band = 600.0 <= sec_t <= 1000.0
    exhaust_in_band = 150.0 <= exhaust_t <= 300.0
    clinker_outlet_in_band = 120.0 <= float(result["clinker_outlet_c"]) <= 200.0

    sanity = {
        "air_above_clinker": air_above_clinker,         # second-law red flag
        "first_law_imbalance": first_law_imbalance,    # closure residual
        "sec_air_in_realistic_band": sec_air_in_band,  # 600–1000 °C
        "exhaust_in_realistic_band": exhaust_in_band,  # 150–300 °C
        "clinker_outlet_in_realistic_band": clinker_outlet_in_band,
        "efficiency_in_bat_band": 0.75 <= eff <= 0.82,  # ECRA 2022 BAT
    }

    return CoolerKPIs(
        # Throughput
        clinker_throughput_t_h=p.clinker_throughput_t_h,
        clinker_mass_flow_kg_s=m_clinker_kg_s,
        total_air_mass_flow_kg_s=total_air_kg_s,

        # Secondary air
        secondary_air_T_c=sec_t,
        secondary_air_Nm3_h=kg_s_to_nm3_h(air_per_comp_kg_s),
        secondary_air_recovered_kw=sec_recovered_kw,
        secondary_air_recovered_gj_per_t_cli=sec_gj_per_t,
        secondary_air_stoich_ratio=secondary_air_stoichiometric_kg_s(
            p.coal_rate_kg_s, 1.10
        ) / max(air_per_comp_kg_s, 1e-9),

        # Tertiary & exhaust
        tertiary_air_T_c=tert_t,
        tertiary_air_Nm3_h=kg_s_to_nm3_h(total_air_kg_s * 0.6),  # typical split
        exhaust_air_T_c=exhaust_t,
        exhaust_air_Nm3_h=kg_s_to_nm3_h(total_air_kg_s * 0.25),

        # Clinker
        clinker_inlet_T_c=p.clinker_inlet_t_c,
        clinker_outlet_T_c=float(result["clinker_outlet_c"]),
        clinker_outlet_T_target_c=p.clinker_outlet_t_c,
        outlet_within_target=bool(
            abs(float(result["clinker_outlet_c"]) - p.clinker_outlet_t_c) < 30.0
        ),
        clinker_quench_rate_k_per_min=q_rate,
        free_lime_outlet_wt_pct=f_cao,

        # Energy
        heat_in_kw=heat_in_kw,
        heat_out_kw=heat_out_kw,
        heat_recovered_kw=heat_recovered_kw,
        cooler_efficiency=eff,
        cooler_loss_mj_per_t_cli=cooler_loss_mj_per_t,
        first_law_imbalance=first_law_imbalance,

        # Equipment
        bed_dp_total_mm_h2o=bed_dp_total,
        bed_dp_profile_mm_h2o=dp_profile,
        fan_power_kw=fp_kw,
        specific_fan_power_kw_per_tph=sfp,
        residence_time_s=residence_s,

        # Sanity + duty case
        sanity=sanity,
        duty_case={
            "altitude_m": duty.altitude_m,
            "ambient_t_c": duty.ambient_t_c,
            "ambient_rh": duty.ambient_rh,
            "air_density_kg_m3": rho_air,
            "p_atm_mbar": duty.p_atm_mbar,
            "design_mcr_pct": duty.design_mcr_pct,
            "note": (
                f"Density at {duty.altitude_m:.0f} m, "
                f"{duty.ambient_t_c:.0f} °C, "
                f"{duty.ambient_rh*100:.0f} % RH. "
                f"Cite: ISO 2533 + ASHRAE 2021 Ch. 1."
            ),
        },
    )


# ---------------------------------------------------------------------------
# Day-3 acceptance check (used by Maya's CLI and Hiro's tests)
# ---------------------------------------------------------------------------

def check_acceptance(kpis: CoolerKPIs) -> dict:
    """Day-3 ship gate per `DAY-03-SPEC.md`.

    Returns a dict of (band, value, pass: bool). Verifier signs off when
    every value is in band and the sanity booleans are clean.
    """
    return {
        "secondary_air_outlet_c_in_600_1000": (
            600.0, 1000.0, kpis["secondary_air_T_c"],
            600.0 <= kpis["secondary_air_T_c"] <= 1000.0,
        ),
        "tertiary_air_outlet_c_in_400_700": (
            400.0, 700.0, kpis["tertiary_air_T_c"],
            400.0 <= kpis["tertiary_air_T_c"] <= 700.0,
        ),
        "exhaust_air_outlet_c_in_150_300": (
            150.0, 300.0, kpis["exhaust_air_T_c"],
            150.0 <= kpis["exhaust_air_T_c"] <= 300.0,
        ),
        "clinker_outlet_c_in_120_200": (
            120.0, 200.0, kpis["clinker_outlet_T_c"],
            120.0 <= kpis["clinker_outlet_T_c"] <= 200.0,
        ),
        "cooler_efficiency_in_065_085": (
            0.65, 0.85, kpis["cooler_efficiency"],
            0.65 <= kpis["cooler_efficiency"] <= 0.85,
        ),
        "first_law_imbalance_leq_002": (
            0.0, 0.02, kpis["first_law_imbalance"],
            kpis["first_law_imbalance"] <= 0.02,
        ),
        "sec_air_gj_per_t_cli_in_030_050": (
            0.30, 0.50, kpis["secondary_air_recovered_gj_per_t_cli"],
            0.30 <= kpis["secondary_air_recovered_gj_per_t_cli"] <= 0.50,
        ),
        "specific_fan_power_in_8_12": (
            8.0, 12.0, kpis["specific_fan_power_kw_per_tph"],
            8.0 <= kpis["specific_fan_power_kw_per_tph"] <= 12.0,
        ),
        "air_above_clinker_false": (
            False, False, kpis["sanity"]["air_above_clinker"],
            not kpis["sanity"]["air_above_clinker"],
        ),
    }


__all__ = [
    "DutyCase",
    "CompartmentResult",
    "CoolerResult",
    "CoolerKPIs",
    "CoolerParametersProxy",
    "air_density_kg_m3",
    "secondary_air_stoichiometric_kg_s",
    "bed_dp_mm_h2o_ergun",
    "fan_power_kw",
    "free_lime_wt_pct",
    "cooler_efficiency",
    "quench_rate_k_per_min",
    "kg_s_to_nm3_h",
    "compute_kpis",
    "check_acceptance",
]
