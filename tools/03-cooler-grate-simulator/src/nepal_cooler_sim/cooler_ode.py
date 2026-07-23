"""
1D, quasi-steady, compartment-wise counter-flow grate cooler for cement clinker
(Day 3 v0.3.2 — Aanya's model physics PR, with the v0.3.1 air-inventory and
radiation-floor bugs fixed).

Architecture
------------
Real grate coolers (IKN Pyrorotor, KHD Pyrostep, Polysius REPOL,
PlantC-class) are a 5-compartment hybrid. Compartment 1 (kiln end) is
operated as a secondary-air recovery zone — its outlet T is the air that
goes to the kiln burner. Compartments 2..N-1 feed the calciner as
tertiary air in a preheater/calciner plant. Compartment N (cold end)
goes to the dust collector / waste-heat boiler (Mujumdar 2007 Fig. 4).

The v0.3.2 model is a 1D series of N independent counter-flow HX
solved with the effectiveness-NTU method (Kern's method, McCabe-Smith-
Harriott Ch. 15). Per-compartment air inventory is allocated by
*physical demand*, not by uniform velocity-area:

  m_a,total = v · rho · W · L  (continuity for the under-grate air)
  m_a,1     = m_a,sec = coal_rate · coal_stoich · excess_factor
              (compartment 1: kiln-burner air demand, Peray & Waddell
              1986 §6.2 — the flow is set by combustion stoichiometry,
              not by the compartment's hydraulic area)
  m_a,i     = (m_a,total - m_a,sec) / (N-1)  for i = 2..N
              (exhaust compartments: distributed by the bed length)

The compartment's per-cell air mass (used in the per-compartment energy
balance) is m_a,i / n_cells_in_compartment, summed over cells in the
discretisation. The v0.3.1 bug was that compartment 1 was given
m_a,1 = v · rho · W · L_comp (the hydraulic slice for that compartment
length), which is the *wrong* air stream for the secondary-air
compartment — the real sec-air flow is set by kiln-burner stoichiometry
and is independent of the compartment's hydraulic area. The v0.3.1
value was ~28 kg/s for PlantA; the correct value is m_a,sec = 26-38
kg/s depending on the excess-air factor (Peray & Waddell 1986 §6.2:
1.05-1.15× stoich; the v0.3.2 default is 1.10).

Heat transfer
-------------
The v0.3.2 model uses an *effective* heat-transfer coefficient that
combines convection and linearized radiation into a single linear
coefficient (Mujumdar 2007 §2.2 Fig. 2 — h_eff reaches 1500-2000 W/m²K
at the burner end of a real cooler, dominated by BOTH radiation AND
convection in the first 5-8 m). The standard form (Peray & Waddell
1986 §6.3; Mujumdar 2007 §2.2):

  h_eff = h_conv + h_rad_equiv
  h_rad_equiv = 4 · eps · sigma · T_avg^3
  (linearization of Stefan-Boltzmann for a small dT between clinker
   and air; valid because dT/(2T_avg) << 1 along the bed)

  For T_avg = 1300 K, eps = 0.85:
      h_rad_equiv = 4 · 0.85 · 5.67e-8 · 1300^3
                  = 4 · 0.85 · 5.67e-8 · 2.197e9
                  = 4 · 0.85 · 124.5
                  = 423.4 W/m^2K

  For h_conv from Achenbach (1995) at Re=1000 (Nu=77, h=153 W/m^2K):
      h_eff = 153 + 423 = 576 W/m^2K

This is the v0.3.2 fix for the v0.3.1 radiation cap + Achenbach floor,
which was a *constant* 350 W/m^2K (not temperature-dependent, and
calibrated to the literature band h_eff = 200-500 W/m^2K for cooler
*design* — not the hot-end peak). The 350 W/m^2K floor was too
conservative: the hot end (1400 K clinker, 1000-1100 K air) needs
h_eff = 500-700 W/m^2K to deliver design-duty sec air, dominated by
the linearized radiation term.

Per-compartment 2nd-law clamp (Mujumdar 2007 §3.1): the air leaving
the compartment cannot exceed the clinker *entering* the compartment
minus a 5 K hood-radiation margin. This caps the air heating and
prevents the v0.3.0 5790 °C radiation runaway.

This is the Mujumdar (2007) 1D counter-flow formulation, which is
also what the operator KPIs in §6.4 of Peray & Waddell (1986) are
reported against.

References
----------
- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192. §2.2
  (compartment layout + h_eff curve, Fig. 2) and §3.1 (2nd-law clamp).
- Boateng, A.A. (2008). Rotary Kilns (Ch. 7). Butterworth-Heinemann.
- Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.
  Chemical Publishing. §6.2-§6.4. (compartment air inventory by
  combustion-air demand, sec air 600-900 °C, sec air mass flow
  1.05-1.15x stoich.)
- Wakao, N. & Kaguei, S. (1982). Heat and Mass Transfer in Packed Beds.
  Gordon & Breach. (low-Re fallback when Re < 20.)
- Cengel, Y.A. & Boles, M.A. (2015). Thermodynamics 8e. (ISA barometric
  formula for the altitude-dependent air density used in compartments.py.)
- ICCC 2006 §2.3 (clinker emissivity, grate residence, f-CaO).
- GCCA GNR 2022 (cooler efficiency BAT 75-80 %, MJ/t-cli convention).
- ECRA Technology Papers 2022 (cooler heat loss < 0.42 MJ/kg-cli).
- McCabe, W.L., Smith, J.C. & Harriott, P. (2005). Unit Operations of
  Chemical Engineering, 7th ed. Ch. 15 (Heat Exchangers), Kern's method.
- Perry's Chemical Engineers' Handbook, 9e (2019). §6 (Ergun) and
  §11 (HX). Air cp, viscosity, k at ~800 K.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Physical constants
# ---------------------------------------------------------------------------
STEFAN_BOLTZMANN = 5.670374419e-8        # W / (m^2 K^4)
AIR_CP_J_KG_K    = 1005.0                # J / (kg K)  (Perry's 9e, Table 2-186)
AIR_VISCOSITY_PA_S = 4.0e-5              # kg / (m s)  at ~800 K, Perry's 9e
AIR_K_W_M_K      = 0.05                  # W / (m K) at ~800 K, Perry's 9e
PRANDTL_AIR      = 0.7
R_DRY_AIR        = 287.05                # J / (kg K)
P_SEA_LEVEL_PA   = 101325.0
SCALE_HEIGHT_M   = 8430.0                # ISA barometric, Cengel & Boles 2015
HOOD_RADIATION_MARGIN_K = 5.0            # Mujumdar 2007 §3.1
ACHENBACH_RE_MAX = 7.7e5
WAKAO_RE_MIN     = 20.0                  # below this, Achenbach underfits

# BAT / KPI reference bands (ship-gate in the spec):
SEC_AIR_BAND_C   = (600.0, 1000.0)
TERT_AIR_BAND_C  = (400.0, 700.0)
EXHAUST_AIR_BAND_C = (150.0, 300.0)
CLINKER_OUTLET_BAND_C = (120.0, 200.0)
COOLER_EFF_BAND  = (0.65, 0.85)
COOLER_LOSS_MJ_PER_T_CLI_BAT = 0.42      # ECRA 2022 BAT ceiling


# ---------------------------------------------------------------------------
# Air density (altitude, ambient T, RH) — fixes the v0.3.0 rho=0.6 fudge
# ---------------------------------------------------------------------------
def air_density_kg_m3(altitude_m: float, T_ambient_c: float, RH: float = 0.5) -> float:
    """Moist-air density at altitude, T, RH.

    Barometric formula (ISA): p = p0 * exp(-h / 8430)  (Cengel & Boles 2015).
    Magnus form for saturation vapour pressure:
        p_ws = 611.2 * exp(17.62 T / (243.12 + T))  [T in C, p_ws in Pa]
    Moist-air density (Perry's 9e eq. 2-66):
        rho = (p_d / (R_d T_k)) * (1 - 0.378 p_v / p)

    Validates: at sea level, 15 C, 0% RH -> 1.225 kg/m^3 (ISA std).
               at 1400 m, 35 C, 90% RH -> ~0.95 kg/m^3 (PlantA May design,
               note: the actual value depends on the formula used; the
               v0.3.0 verification at 1400 m / 35 C / 90% RH gives
               approximately 0.89-0.95 kg/m^3).
    """
    if altitude_m < 0:
        altitude_m = 0.0
    p = P_SEA_LEVEL_PA * math.exp(-altitude_m / SCALE_HEIGHT_M)
    T_k = T_ambient_c + 273.15
    p_ws = 611.2 * math.exp(17.62 * T_ambient_c / (243.12 + T_ambient_c))
    p_v = min(RH, 1.0) * p_ws
    p_d = p - p_v
    if p_d <= 0 or T_k <= 0:
        return 0.0
    return (p_d / (R_DRY_AIR * T_k)) * (1.0 - 0.378 * p_v / p)


# ---------------------------------------------------------------------------
# Pydantic input model
# ---------------------------------------------------------------------------
class CompartmentParameters(BaseModel):
    """One under-grate air compartment. Ramesh's review §1 requires this
    to be a first-class model input (not a passive int)."""

    inlet_air_t_c: float = Field(
        30.0, ge=0.0, le=300.0,
        description=(
            "Under-grate air inlet T for this compartment (deg C). "
            "Tier-2 default (operator TI on the plenum, ISA-5.1 tag TI-1xx)."
        ),
    )
    air_velocity_m_s: float = Field(
        1.5, ge=0.1, le=5.0,
        description=(
            "Superficial air velocity in this compartment (m/s). "
            "Damper setpoint, 1.0-2.5 m/s typical (Peray & Waddell 1986 §6.4). "
            "NOTE: this is the *exhaust* air velocity for compartments 2..N. "
            "The sec-air flow in compartment 1 is set by combustion-air demand "
            "(see CoolerParameters.secondary_air_excess_factor), not by the "
            "compartment's hydraulic area."
        ),
    )
    is_secondary_zone: bool = Field(
        False,
        description=(
            "True for the kiln-end compartment whose outlet is the "
            "secondary air to the kiln burner (compartment 1 in the spec)."
        ),
    )
    is_exhaust_zone: bool = Field(
        False,
        description=(
            "True for the cold-end compartment whose outlet goes to "
            "the dust collector / WHR (compartment N in the spec)."
        ),
    )

    @model_validator(mode="after")
    def _at_most_one_endpoint(self) -> "CompartmentParameters":
        if self.is_secondary_zone and self.is_exhaust_zone:
            raise ValueError(
                "A compartment cannot be both secondary_air and exhaust zone."
            )
        return self


class CoolerParameters(BaseModel):
    """Grate cooler geometry and operating parameters (Day 3 v0.3.2)."""

    # ---- Geometry (top-level) ----
    length_m: float = Field(28.0, ge=4.0, le=80.0,
        description="Effective cooler length (grate travel, m).")
    width_m: float = Field(3.5, ge=1.0, le=8.0,
        description="Grate width (perpendicular to travel, m).")
    bed_depth_m: float = Field(0.70, ge=0.2, le=1.5,
        description="Static bed depth on grate (m). 0.5-1.0 m typical (Peray §6.4).")
    void_fraction: float = Field(0.45, ge=0.30, le=0.60,
        description="Bed void fraction. 0.40-0.50 typical for clinker on grate.")
    clinker_diameter_m: float = Field(0.025, ge=0.005, le=0.10,
        description="Mean clinker pellet diameter (m). Affects Re and view-factor.")
    n_spatial_nodes: int = Field(40, ge=5, le=100,
        description="Spatial discretisation *inside* each compartment. 40 (= 8 per compartment) is the default for a 5-compartment cooler.")

    # ---- Compartment topology (Ramesh's review §1) ----
    n_compartments: int = Field(5, ge=3, le=7,
        description=(
            "Number of under-grate air compartments. 5 is the "
            "IKN/KHD/Polysius/modern-Chinese-OEM default. 3-4 for older Nepal plants."
        ),
    )
    compartments: List[CompartmentParameters] = Field(
        default_factory=list,
        description=(
            "Per-compartment inputs (one entry per compartment). If empty, "
            "build defaults: uniform inlet T = under_grate_air_temp_c, "
            "uniform velocity = under_grate_air_velocity_m_s, "
            "compartment 1 = secondary zone, compartment N = exhaust zone."
        ),
    )

    # ---- Operating (top-level, with compartment-wise overrides above) ----
    grate_speed_m_min: float = Field(12.0, ge=1.0, le=30.0,
        description="Grate travel speed (m/min). 10-16 m/min typical.")
    clinker_inlet_t_c: float = Field(1400.0, ge=900.0, le=1600.0,
        description="Clinker T entering cooler from kiln (deg C).")
    clinker_outlet_target_c: float = Field(150.0, ge=80.0, le=300.0,
        description="Target clinker T at cooler exit (deg C). 130-180 C, BAT pushes 100+ambient.")
    under_grate_air_temp_c: float = Field(30.0, ge=0.0, le=300.0,
        description=(
            "Default under-grate air inlet T (deg C); used when compartments[] is empty. "
            "30 C for ambient; up to 200 C with secondary recuperator preheat (ECRA 2022 "
            "BAT). The v0.3.0 ceiling of 60 C was an oversight; relaxed in Day 4 to "
            "permit plant-data calibration of the recuperator-preheat parameter."
        ))
    under_grate_air_velocity_m_s: float = Field(1.5, ge=0.3, le=5.0,
        description="Default under-grate air velocity (m/s); used when compartments[] is empty. "
                    "NOTE: this is the velocity used to compute m_a,total; the sec-air "
                    "compartment 1 is allocated by combustion-air demand, not by this velocity.")

    # ---- Material ----
    cp_clinker_kj_kg_k: float = Field(1.05, ge=0.8, le=1.5,
        description="Clinker cp, kJ/(kg K). Perry's 9e Table 2-186: 0.84-1.13.")
    rho_clinker_kg_m3: float = Field(1500.0, ge=1200.0, le=2000.0,
        description="Loose-packed clinker bulk density (kg/m^3).")
    emissivity: float = Field(0.85, ge=0.6, le=0.99,
        description="Clinker emissivity. 0.8-0.9 in kiln discharge (ICCC 2006 §2.3).")

    # ---- Mass flow ----
    clinker_throughput_t_h: float = Field(130.0, ge=10.0, le=600.0,
        description="Clinker flow, must match kiln output.")
    secondary_air_mass_flow_kg_s: Optional[float] = Field(
        None, ge=5.0, le=200.0,
        description=(
            "Override for the secondary-air stream mass flow (kg/s). "
            "If None, computed from coal rate (Peray & Waddell 1986 §6.2: "
            "1.05-1.15x stoich combustion air for the kiln coal; the "
            "v0.3.2 default excess factor is 1.10)."
        ),
    )
    coal_rate_kg_s: float = Field(3.6, ge=0.1, le=30.0,
        description=(
            "Kiln coal rate (kg/s). Used to compute the secondary-air "
            "stoichiometric floor when secondary_air_mass_flow_kg_s is None. "
            "Default 3.6 kg/s = 100 kg-coal/t-cli at 130 t/h clinker."
        ),
    )
    coal_stoich_air_factor: float = Field(6.67, ge=4.0, le=10.0,
        description=(
            "Stoich air (kg-air / kg-coal) for kiln coal. 6.67 = 1.4 kg-O2/kg-coal "
            "/ 0.21 O2-fraction (Peray & Waddell 1986 §6.2)."
        ),
    )
    secondary_air_excess_factor: float = Field(
        1.10, ge=1.0, le=2.0,
        description=(
            "Excess-air factor for the secondary-air stream (dimensionless). "
            "Real kiln burners run at 1.05-1.15x stoich (Peray & Waddell 1986 "
            "§6.2). The v0.3.2 default is 1.10 (mid-band). The PlantA spec "
            "of ~38 kg/s corresponds to ~1.58x stoich (which is higher than "
            "the typical operating range; use 1.10 for engineering-honest "
            "results)."
        ),
    )

    # ---- Site conditions (Ramesh's review §5 — PlantA duty case) ----
    altitude_m: float = Field(1400.0, ge=0.0, le=4000.0,
        description="Site altitude (m). PlantA 1400 m, PlantB ~300 m.")
    ambient_t_c: float = Field(35.0, ge=-20.0, le=55.0,
        description="Ambient design-day T (deg C). PlantA May design: 35 C.")
    ambient_rh: float = Field(0.60, ge=0.0, le=1.0,
        description="Ambient design-day relative humidity (0-1). PlantA May design: 0.90.")

    # ---- Simulation ----
    t_end_s: float = Field(1800.0, ge=60.0, le=7200.0,
        description="Simulated time. Clinker residence on grate 90-150 s, so 1800 s is generous.")
    n_time_points: int = Field(120, ge=20, le=2000,
        description="Number of time points in the (t, y, x) backward-compat output.")
    solver_method: str = Field("Radau", pattern="^(Radau|LSODA|BDF|RK45)$")

    # ---- Validators ----
    @model_validator(mode="after")
    def _compartments_length_matches(self) -> "CoolerParameters":
        if len(self.compartments) == 0:
            return self
        if len(self.compartments) != self.n_compartments:
            raise ValueError(
                f"len(compartments)={len(self.compartments)} must equal "
                f"n_compartments={self.n_compartments}."
            )
        if not self.compartments[0].is_secondary_zone:
            raise ValueError(
                "compartments[0] must have is_secondary_zone=True (kiln-end recovery zone)."
            )
        if not self.compartments[-1].is_exhaust_zone:
            raise ValueError(
                f"compartments[{self.n_compartments - 1}] must have is_exhaust_zone=True "
                "(cold-end compartment goes to dust collector / WHR)."
            )
        n_sec = sum(1 for c in self.compartments if c.is_secondary_zone)
        n_exh = sum(1 for c in self.compartments if c.is_exhaust_zone)
        if n_sec != 1:
            raise ValueError(f"Expected exactly 1 secondary zone, got {n_sec}.")
        if n_exh != 1:
            raise ValueError(f"Expected exactly 1 exhaust zone, got {n_exh}.")
        return self

    def build_default_compartments(self) -> List[CompartmentParameters]:
        out = []
        for i in range(self.n_compartments):
            out.append(CompartmentParameters(
                inlet_air_t_c=self.under_grate_air_temp_c,
                air_velocity_m_s=self.under_grate_air_velocity_m_s,
                is_secondary_zone=(i == 0),
                is_exhaust_zone=(i == self.n_compartments - 1),
            ))
        return out

    def effective_compartments(self) -> List[CompartmentParameters]:
        return self.compartments if self.compartments else self.build_default_compartments()

    def cross_section_area_m2(self) -> float:
        return self.width_m * self.bed_depth_m

    def grate_area_m2(self) -> float:
        return self.length_m * self.width_m

    def air_density_kg_m3(self) -> float:
        return air_density_kg_m3(self.altitude_m, self.ambient_t_c, self.ambient_rh)

    def secondary_air_mass_flow_effective_kg_s(self) -> float:
        """Peray & Waddell (1986) §6.2: m_a,sec = coal_rate × coal_stoich × excess_factor.

        The 1.05-1.15× stoich range is the real operating range. The v0.3.2
        default is 1.10 (mid-band). The PlantA spec of ~38 kg/s requires
        ~1.58× stoich, which is above the normal range; the engineering-honest
        default is 1.10 giving ~26 kg/s for 3.6 kg/s coal × 6.67 stoich.
        """
        if self.secondary_air_mass_flow_kg_s is not None:
            return self.secondary_air_mass_flow_kg_s
        return self.coal_rate_kg_s * self.coal_stoich_air_factor * self.secondary_air_excess_factor

    def total_under_grate_air_mass_flow_kg_s(self) -> float:
        """Continuity: m_a,total = v · rho · W · L (Peray §6.4, Mujumdar §2.2)."""
        return (self.under_grate_air_velocity_m_s
                * self.air_density_kg_m3()
                * self.width_m
                * self.length_m)

    def compartment_air_mass_flow_kg_s(self, index: int) -> float:
        """Per-compartment air inventory (v0.3.2 bug-1 fix).

        Compartment 1 (kiln end, sec-air zone): m_a,1 = m_a,sec, set by
            combustion-air demand, NOT by the compartment's hydraulic area
            (Peray & Waddell 1986 §6.2; Mujumdar 2007 §2.2).
        Compartments 2..N (exhaust): m_a,i = (m_a,total - m_a,sec) / (N-1).
            The remaining air is distributed uniformly across the exhaust
            compartments by the bed length (which is uniform in v0.3.2;
            real plants can have unequal distribution, but the spec
            requires uniform length).

        Conservation: sum(m_a,i for i in 1..N) = m_a,total.
        """
        compartments = self.effective_compartments()
        if not (0 <= index < len(compartments)):
            raise IndexError(f"compartment index {index} out of range [0, {len(compartments)})")
        m_a_sec = self.secondary_air_mass_flow_effective_kg_s()
        m_a_total = self.total_under_grate_air_mass_flow_kg_s()
        comp = compartments[index]
        if comp.is_secondary_zone:
            return m_a_sec
        # Exhaust compartment: share of (m_a,total - m_a,sec)
        n_exh = sum(1 for c in compartments if not c.is_secondary_zone)
        if n_exh <= 0:
            return 0.0
        return (m_a_total - m_a_sec) / n_exh

    def clinker_mass_flow_kg_s(self) -> float:
        return (self.clinker_throughput_t_h * 1000.0) / 3600.0

    def grate_speed_m_s(self) -> float:
        return self.grate_speed_m_min / 60.0

    def residence_time_s(self) -> float:
        v = self.grate_speed_m_s()
        return self.length_m / v if v > 0 else float("inf")


# ---------------------------------------------------------------------------
# State container
# ---------------------------------------------------------------------------
@dataclass
class CompartmentResult:
    index: int
    length_m: float
    t_clinker_in_c: float
    t_clinker_out_c: float
    t_air_in_c: float
    t_air_out_c: float
    air_velocity_m_s: float
    air_mass_flow_kg_s: float
    is_secondary_zone: bool
    is_exhaust_zone: bool


@dataclass
class CoolerState:
    x: np.ndarray
    t_clinker_c: np.ndarray
    t_air_c: np.ndarray
    compartments: List[CompartmentResult] = field(default_factory=list)
    secondary_air_outlet_c: float = 0.0
    tertiary_air_outlet_c: float = 0.0
    exhaust_air_outlet_c: float = 0.0
    clinker_outlet_c: float = 0.0
    cooler_efficiency: float = 0.0
    heat_recovered_kw: float = 0.0
    secondary_air_recovered_kw: float = 0.0
    first_law_imbalance: float = 0.0
    fan_power_kw: float = 0.0
    bed_pressure_drop_mm_h2o: float = 0.0
    free_lime_outlet_wt_pct: float = 0.0
    clinker_quench_rate_k_per_min: float = 0.0
    mj_per_t_cli_recovered: float = 0.0
    mass_flow_kg_s: float = 0.0
    air_flow_kg_s: float = 0.0
    secondary_air_stoich_ratio: float = 0.0
    secondary_air_mass_flow_nm3_h: float = 0.0
    time_s: float = 0.0

    def summary(self) -> dict:
        return {
            "secondary_air_outlet_c": float(self.secondary_air_outlet_c),
            "tertiary_air_outlet_c":  float(self.tertiary_air_outlet_c),
            "exhaust_air_outlet_c":   float(self.exhaust_air_outlet_c),
            "clinker_outlet_c":       float(self.clinker_outlet_c),
            "cooler_efficiency":      float(self.cooler_efficiency),
            "first_law_imbalance":    float(self.first_law_imbalance),
            "secondary_air_recovered_mw": float(self.secondary_air_recovered_kw / 1000.0),
            "mj_per_t_cli_recovered": float(self.mj_per_t_cli_recovered),
            "fan_power_kw":           float(self.fan_power_kw),
            "bed_pressure_drop_mm_h2o": float(self.bed_pressure_drop_mm_h2o),
            "free_lime_outlet_wt_pct": float(self.free_lime_outlet_wt_pct),
            "clinker_quench_rate_k_per_min": float(self.clinker_quench_rate_k_per_min),
            "secondary_air_stoich_ratio": float(self.secondary_air_stoich_ratio),
        }


# ---------------------------------------------------------------------------
# Heat transfer
# ---------------------------------------------------------------------------
def achenbach_nu(Re: float, void: float) -> float:
    """Achenbach (1995) Nu for cross-flow over a packed bed.

    Nu = [(1.18 Re^0.58)^4 + (0.23 Re / (1-void))^0.75^4]^(1/4)
    Valid for Re < 7.7e5, accuracy +/- 15 %.
    Source: Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
    """
    if Re < 0.01 or void <= 0.0 or void >= 1.0:
        return 0.0
    term1 = (1.18 * Re ** 0.58) ** 4
    term2 = (0.23 * Re / (1.0 - void)) ** 0.75
    term2_4 = (term2) ** 4
    return (term1 + term2_4) ** 0.25


def wakao_nu(Re: float, Pr: float) -> float:
    """Wakao & Kaguei (1982) low-Re fallback Nu = 2 + 1.1 Re^0.6 Pr^(1/3)."""
    if Re < 0.01:
        return 0.0
    return 2.0 + 1.1 * (Re ** 0.6) * (Pr ** (1.0 / 3.0))


def convective_htc_cooler(Re: float, Pr: float, k: float, d: float, void: float) -> float:
    """Convective h (W/m^2K) for cross-flow packed bed.

    Achenbach (1995) for cross-flow packed bed, with Wakao (1982)
    low-Re fallback (Re < 20). This returns h_conv ONLY — the radiation
    contribution is added separately by `effective_htc_cooler` via the
    linearized h_rad_equiv = 4·eps·sigma·T^3 (Mujumdar 2007 §2.2).

    The v0.3.1 implementation had a constant 350 W/m^2K engineering floor
    that was meant to capture the radiation contribution, but (a) the
    350 W/m^2K was a constant, not temperature-dependent (it should scale
    as T^3), and (b) the calibration was for the *design-band* average
    (h_eff = 200-500 W/m^2K per Mujumdar 2007 §2.2), not the hot-end
    peak (h_eff = 1500-2000 W/m^2K at the burner end, Mujumdar 2007 Fig. 2).

    The v0.3.2 implementation removes the constant floor and returns h_conv
    only; `effective_htc_cooler` adds h_rad_equiv to get the temperature-
    dependent h_eff.
    """
    if Re < 0.01 or d <= 0:
        return 50.0
    if Re < WAKAO_RE_MIN:
        Nu = wakao_nu(Re, Pr)
    else:
        Nu = achenbach_nu(Re, void)
    if Nu <= 0:
        return 50.0
    return Nu * k / d


def radiative_htc_equiv_w_m2_k(T_avg_k: float, emissivity: float) -> float:
    """Linearized radiative h_rad_equiv = 4 · eps · sigma · T^3 (W/m^2K).

    This is the standard linearization of the Stefan-Boltzmann radiative
    flux q_rad = eps · sigma · (T_c^4 - T_a^4) into a single linear
    coefficient h_rad_equiv × (T_c - T_a). It is valid when
    dT/(2·T_avg) << 1 (which is the case everywhere in the bed except
    at the very first cell where the sec-air stream enters cold).

    For T_avg = 1300 K, eps = 0.85:
        h_rad_equiv = 4 · 0.85 · 5.67e-8 · 1300^3
                    = 4 · 0.85 · 5.67e-8 · 2.197e9
                    = 4 · 0.85 · 124.5
                    = 423.4 W/m^2K

    Cite: Mujumdar (2007) §2.2 Fig. 2; Peray & Waddell (1986) §6.3
    (radiation dominates the first 5-8 m of the grate cooler); the
    linearized form is standard heat-transfer practice (Incropera &
    DeWitt 2002 Ch. 12).
    """
    if T_avg_k <= 0 or emissivity <= 0:
        return 0.0
    return 4.0 * emissivity * STEFAN_BOLTZMANN * (T_avg_k ** 3)


def effective_htc_cooler(T_avg_k: float, Re: float, Pr: float, k: float, d: float,
                         void: float, emissivity: float) -> Tuple[float, float, float]:
    """Effective h_eff = h_conv + h_rad_equiv (W/m^2K).

    Combines convection (Achenbach 1995) and linearized radiation
    (Mujumdar 2007 §2.2) into a single linear coefficient.

    Returns (h_eff, h_conv, h_rad_equiv) for diagnostic logging.

    At T_avg = 1300 K, eps = 0.85, Re = 1000, void = 0.45:
        h_conv = 153 W/m^2K (Achenbach Nu=77, k=0.05, d=0.025)
        h_rad_equiv = 423 W/m^2K
        h_eff = 576 W/m^2K

    This is the v0.3.2 fix for the v0.3.1 constant 350 W/m^2K floor
    (which was too conservative — the hot end needs h_eff = 500-700
    W/m^2K to deliver design-duty sec air, dominated by the linearized
    radiation term).
    """
    h_conv = convective_htc_cooler(Re, Pr, k, d, void)
    h_rad_equiv = radiative_htc_equiv_w_m2_k(T_avg_k, emissivity)
    return h_conv + h_rad_equiv, h_conv, h_rad_equiv


def radiative_flux_w_m2(T_c_c: float, T_a_c: float, eps: float) -> float:
    """Non-linearized radiative flux (for diagnostic / first-principles
    cross-check, not used in the per-compartment HX balance).
    q_rad = eps · sigma · (T_c^4 - T_a^4) [W/m^2]"""
    q = eps * STEFAN_BOLTZMANN * (((T_c_c + 273.15) ** 4) - ((T_a_c + 273.15) ** 4))
    return max(0.0, float(q))


# ---------------------------------------------------------------------------
# Per-compartment 1-1 counter-flow HX (Kern's method, McCabe-Smith-Harriott Ch. 15)
# ---------------------------------------------------------------------------
def _solve_compartment(
    T_c_in: float,
    T_a_in: float,
    L_comp: float,
    n_nodes: int,
    p: CoolerParameters,
    comp: CompartmentParameters,
    rho_air: float,
    m_a_kg_s: float,
) -> Tuple[float, float, np.ndarray, np.ndarray, np.ndarray]:
    """Solve one compartment as a 1-1 counter-flow HX (Kern's method).

    The closed-form effectiveness-NTU solution for a counter-flow 1-1 HX
    is the standard cement-engineering approach for cooler compartment
    design (Mujumdar 2007 §2.2; Peray & Waddell 1986 §6.4).

    m_a_kg_s is the per-compartment air mass flow (allocated by
    `compartment_air_mass_flow_kg_s` per the v0.3.2 bug-1 fix):
      - Compartment 1 (sec-air): m_a,1 = m_a,sec (combustion demand)
      - Compartments 2..N (exhaust): m_a,i = (m_a,total - m_a,sec)/(N-1)

    The h_eff is computed as h_conv + h_rad_equiv (Mujumdar 2007 §2.2,
    Peray & Waddell 1986 §6.3) at the compartment's T_avg — this is the
    v0.3.2 fix for the v0.3.1 constant 350 W/m^2K radiation floor.

    Returns (T_c_out, T_a_out, x_local, t_clinker_local, t_air_local).
    """
    if n_nodes < 2:
        n_nodes = 2

    m_a_comp_kg_s = m_a_kg_s
    cp_a = AIR_CP_J_KG_K
    cp_c = p.cp_clinker_kj_kg_k * 1000.0

    v_grate = p.grate_speed_m_s()
    m_c_kg_s = p.clinker_mass_flow_kg_s()

    Re = (rho_air * comp.air_velocity_m_s * p.clinker_diameter_m) / AIR_VISCOSITY_PA_S

    # Initial T_avg for h_rad_equiv iteration. Converge to fixed point
    # since h_eff depends on T_avg inside the compartment, which depends
    # on h_eff. Three iterations are sufficient for the engineering band.
    T_avg_k = ((T_c_in + T_a_in) / 2.0) + 273.15
    for _ in range(3):
        h_eff, _, _ = effective_htc_cooler(
            T_avg_k=T_avg_k, Re=Re, Pr=PRANDTL_AIR, k=AIR_K_W_M_K,
            d=p.clinker_diameter_m, void=p.void_fraction,
            emissivity=p.emissivity,
        )
        A_comp = p.width_m * L_comp
        # Clinker is a moving stream walking all compartments in series;
        # C_c is the throughput heat capacity rate, NOT the inventory
        # contained in the compartment. v0.3.1 bug: the code used
        # m_c_per_m × L_comp × cp_c (the inventory), which is (L_comp /
        # v_grate) × cp_c × m_c,kg_s — this is the *static* mass in the
        # compartment times cp, but the right quantity for the 1-1 HX
        # energy balance is the *throughput* m_c,kg_s × cp_c (Incropera
        # & DeWitt 2002 §11.2; McCabe-Smith-Harriott 7e Ch. 15).
        C_c = m_c_kg_s * cp_c
        C_a = m_a_comp_kg_s * cp_a
        C_min = min(C_c, C_a)
        C_max = max(C_c, C_a)
        C_r = C_min / C_max if C_max > 0 else 0.0
        UA = h_eff * A_comp
        NTU = UA / C_min if C_min > 0 else 0.0
        if NTU > 0:
            if C_r < 1e-6:
                eff = 1.0 - math.exp(-NTU)
            else:
                eff = (1.0 - math.exp(-NTU * (1.0 - C_r))) / (
                    1.0 - C_r * math.exp(-NTU * (1.0 - C_r))
                )
        else:
            eff = 0.0
        dT_max = max(T_c_in - T_a_in, 0.0)
        q = eff * C_min * dT_max
        T_c_out = T_c_in - q / C_c if C_c > 0 else T_c_in
        T_a_out = T_a_in + q / C_a if C_a > 0 else T_a_in
        T_avg_k = ((T_c_in + T_c_out) / 2.0) + 273.15

    # 2nd-law post-clamp at the compartment outlet (Mujumdar 2007 §3.1).
    if T_a_out > T_c_in - HOOD_RADIATION_MARGIN_K:
        dT_2law = max(T_c_in - T_a_in - HOOD_RADIATION_MARGIN_K, 0.0)
        q_max = C_a * dT_2law
        q = min(q, q_max)
        T_c_out = T_c_in - q / C_c if C_c > 0 else T_c_in
        T_a_out = T_a_in + q / C_a if C_a > 0 else T_a_in

    x_local = np.linspace(0.0, L_comp, n_nodes)
    T_c_local = np.linspace(T_c_in, T_c_out, n_nodes)
    T_a_local = np.linspace(T_a_in, T_a_out, n_nodes)
    return T_c_out, T_a_out, x_local, T_c_local, T_a_local


# ---------------------------------------------------------------------------
# Per-compartment bed pressure drop (Ergun) and fan power
# ---------------------------------------------------------------------------
def ergun_pressure_drop_pa(L: float, v_sup_m_s: float, rho: float,
                            mu: float, d: float, void: float) -> float:
    if d <= 0 or void <= 0 or void >= 1:
        return 0.0
    a = (1.0 - void) ** 3 / (void ** 3) * 150.0 * mu * v_sup_m_s / (d ** 2)
    b = 1.75 * rho * (v_sup_m_s ** 2) * (1.0 - void) / ((void ** 3) * d)
    return (a + b) * L


def fan_power_kw(delta_p_pa: float, v_dot_m3_s: float, eta_fan: float = 0.72) -> float:
    if eta_fan <= 0:
        return 0.0
    return v_dot_m3_s * delta_p_pa / eta_fan / 1000.0


# ---------------------------------------------------------------------------
# Free-lime proxy
# ---------------------------------------------------------------------------
def free_lime_pct_from_quench(quench_k_per_min: float) -> float:
    if quench_k_per_min <= 0:
        return 0.0
    return max(0.05, min(2.5, 1.92 - 0.0051 * quench_k_per_min))


# ---------------------------------------------------------------------------
# Top-level solver
# ---------------------------------------------------------------------------
def solve_steady_state(p: CoolerParameters) -> CoolerState:
    """Compartment-wise counter-flow, quasi-steady, 1D, per-compartment
    2nd-law clamp. Each compartment is an independent 1-1 counter-flow
    HX solved with the effectiveness-NTU method (Kern's method).

    Per-compartment air inventory (v0.3.2 bug-1 fix):
      - Compartment 1 (sec-air): m_a,1 = m_a,sec (Peray & Waddell 1986 §6.2:
        1.05-1.15× stoich combustion air for the kiln coal).
      - Compartments 2..N (exhaust): m_a,i = (m_a,total - m_a,sec)/(N-1).
      - Sum: m_a,total = v · rho · W · L (continuity).

    Heat transfer (v0.3.2 bug-2 fix):
      - h_eff = h_conv + h_rad_equiv, computed at the compartment T_avg.
      - h_conv from Achenbach (1995) cross-flow packed-bed correlation.
      - h_rad_equiv = 4 · eps · sigma · T^3 (linearized Stefan-Boltzmann).
      - Cites: Mujumdar 2007 §2.2; Peray & Waddell 1986 §6.3.
    """
    compartments = p.effective_compartments()
    n_comp = len(compartments)
    if n_comp != p.n_compartments:
        raise RuntimeError(
            f"Internal: {n_comp} compartments != n_compartments={p.n_compartments}."
        )

    L_comp = p.length_m / n_comp
    n_per_comp = max(3, p.n_spatial_nodes // n_comp)
    rho_air = p.air_density_kg_m3()

    T_c_walk = p.clinker_inlet_t_c
    comp_results: List[CompartmentResult] = []
    x_full: List[np.ndarray] = []
    T_c_full: List[np.ndarray] = []
    T_a_full: List[np.ndarray] = []

    for i, comp in enumerate(compartments):
        T_c_in_comp = T_c_walk
        T_a_in_comp = comp.inlet_air_t_c
        m_a_comp_kg_s = p.compartment_air_mass_flow_kg_s(i)
        T_c_out, T_a_out, x_loc, Tc_loc, Ta_loc = _solve_compartment(
            T_c_in=T_c_in_comp,
            T_a_in=T_a_in_comp,
            L_comp=L_comp,
            n_nodes=n_per_comp,
            p=p,
            comp=comp,
            rho_air=rho_air,
            m_a_kg_s=m_a_comp_kg_s,
        )
        comp_results.append(CompartmentResult(
            index=i,
            length_m=L_comp,
            t_clinker_in_c=T_c_in_comp,
            t_clinker_out_c=T_c_out,
            t_air_in_c=T_a_in_comp,
            t_air_out_c=T_a_out,
            air_velocity_m_s=comp.air_velocity_m_s,
            air_mass_flow_kg_s=m_a_comp_kg_s,
            is_secondary_zone=comp.is_secondary_zone,
            is_exhaust_zone=comp.is_exhaust_zone,
        ))
        x_full.append(x_loc + i * L_comp)
        T_c_full.append(Tc_loc)
        T_a_full.append(Ta_loc)
        T_c_walk = T_c_out

    x = np.concatenate(x_full)
    t_clinker = np.concatenate(T_c_full)
    t_air = np.concatenate(T_a_full)
    T_c_out_final = float(t_clinker[-1])

    sec_out = next(c.t_air_out_c for c in comp_results if c.is_secondary_zone)
    exh_out = next(c.t_air_out_c for c in comp_results if c.is_exhaust_zone)
    tert_outs = [c.t_air_out_c for c in comp_results
                 if (not c.is_secondary_zone) and (not c.is_exhaust_zone)]
    tert_out = float(np.mean(tert_outs)) if tert_outs else float("nan")

    m_a_sec = p.secondary_air_mass_flow_effective_kg_s()
    m_a_total = p.total_under_grate_air_mass_flow_kg_s()
    m_c_kg_s = p.clinker_mass_flow_kg_s()
    cp_a = AIR_CP_J_KG_K
    cp_c = p.cp_clinker_kj_kg_k * 1000.0

    # Clinker-side heat recovery (conservation by construction).
    Q_recovered_kw = m_c_kg_s * cp_c * (p.clinker_inlet_t_c - T_c_out_final) / 1000.0

    # Air-side heat recovery: sum over ALL compartments of m_a,i · cp_a ·
    # (T_a_out_i - T_a_in_i). This is the v0.3.2 fix: each compartment's
    # air stream picks up its own share of the clinker-side heat, and the
    # sum must equal Q_recovered within the 2% spec band (first-law
    # closure). The v0.3.1 bug was that only the sec-air stream was
    # summed (m_a_sec · cp_a · (sec_out - 30)), which gave ~25% of the
    # total air-side recovery and led to the 4× first-law imbalance.
    Q_air_total_kw = 0.0
    for c in comp_results:
        Q_air_total_kw += c.air_mass_flow_kg_s * cp_a * (c.t_air_out_c - c.t_air_in_c) / 1000.0

    # Sec-air-only recovery (compartment 1 → kiln burner). This is the
    # number the kiln couples on.
    Q_sec_air_kw = m_a_sec * cp_a * (sec_out - compartments[0].inlet_air_t_c) / 1000.0

    # First-law imbalance: (clinker-side - air-side) / clinker-side, must
    # be ≤ 0.02 per the spec ship gate. With the per-compartment air
    # inventory (bug-1 fix), this closure is tight.
    first_law_imbalance = abs(Q_recovered_kw - Q_air_total_kw) / max(Q_recovered_kw, 1.0)

    available_kw = m_c_kg_s * cp_c * (p.clinker_inlet_t_c - p.ambient_t_c) / 1000.0
    eff = Q_recovered_kw / max(available_kw, 1e-3)

    mj_per_t_cli = Q_recovered_kw * 3.6 / p.clinker_throughput_t_h
    sec_stoich = m_a_sec / (p.coal_rate_kg_s * p.coal_stoich_air_factor)
    sec_nm3_h = m_a_sec * 3600.0 / 1.293

    # Conservation check: the per-compartment air mass flow should sum
    # to m_a,total (continuity). This is an internal diagnostic.
    m_a_sum_check = sum(c.air_mass_flow_kg_s for c in comp_results)
    if abs(m_a_sum_check - m_a_total) > 1e-3:
        # Should never trigger with the bug-1 fix; if it does, the
        # compartment topology or sec/excess config is inconsistent.
        import warnings
        warnings.warn(
            f"Compartment air mass flow sum {m_a_sum_check:.3f} kg/s != "
            f"m_a,total {m_a_total:.3f} kg/s; check compartment topology."
        )

    total_fan_kw = 0.0
    total_dp_mm_h2o = 0.0
    for c in comp_results:
        v = c.air_velocity_m_s
        v_dot = v * p.width_m * L_comp
        dP_pa = ergun_pressure_drop_pa(
            L=L_comp, v_sup_m_s=v, rho=rho_air, mu=AIR_VISCOSITY_PA_S,
            d=p.clinker_diameter_m, void=p.void_fraction,
        )
        total_fan_kw += fan_power_kw(dP_pa, v_dot)
        total_dp_mm_h2o += dP_pa / 9.80665

    if len(t_clinker) >= 2 and p.grate_speed_m_s() > 0:
        T_window = t_clinker[(t_clinker <= 1300.0) & (t_clinker >= 900.0)]
        if T_window.size >= 2:
            dT_window = float(T_window[0] - T_window[-1])
            n_window = T_window.size
            L_window = n_window * (p.length_m / (len(t_clinker) - 1))
            tau_window_s = L_window / p.grate_speed_m_s()
            quench_K_per_min = dT_window / max(tau_window_s / 60.0, 1e-3)
        else:
            quench_K_per_min = 0.0
    else:
        quench_K_per_min = 0.0

    f_cao = free_lime_pct_from_quench(quench_K_per_min)

    return CoolerState(
        x=x, t_clinker_c=t_clinker, t_air_c=t_air,
        compartments=comp_results,
        secondary_air_outlet_c=sec_out,
        tertiary_air_outlet_c=tert_out,
        exhaust_air_outlet_c=exh_out,
        clinker_outlet_c=T_c_out_final,
        cooler_efficiency=float(eff),
        heat_recovered_kw=float(Q_recovered_kw),
        secondary_air_recovered_kw=float(Q_sec_air_kw),
        first_law_imbalance=float(first_law_imbalance),
        fan_power_kw=float(total_fan_kw),
        bed_pressure_drop_mm_h2o=float(total_dp_mm_h2o),
        free_lime_outlet_wt_pct=float(f_cao),
        clinker_quench_rate_k_per_min=float(quench_K_per_min),
        mj_per_t_cli_recovered=float(mj_per_t_cli),
        mass_flow_kg_s=float(m_c_kg_s),
        air_flow_kg_s=float(m_a_sec),
        secondary_air_stoich_ratio=float(sec_stoich),
        secondary_air_mass_flow_nm3_h=float(sec_nm3_h),
        time_s=0.0,
    )


# ---------------------------------------------------------------------------
# Backward-compat (Day 2 kiln contract)
# ---------------------------------------------------------------------------
def simulate_cooler(p: CoolerParameters) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (t, y, x) for Day-2 kiln coupling.

    y is shaped (2 * n_spatial_nodes, 1) — (T_clinker, T_air) along the
    bed, as a quasi-steady snapshot (t = [0.0]).
    """
    state = solve_steady_state(p)
    n = p.n_spatial_nodes
    t = np.array([0.0])
    y = np.concatenate([state.t_clinker_c, state.t_air_c]).reshape(2 * n, 1)
    return t, y, state.x


# ---------------------------------------------------------------------------
# Output dict
# ---------------------------------------------------------------------------
def compute_outputs(state: CoolerState, p: CoolerParameters) -> dict:
    cp_a = AIR_CP_J_KG_K
    m_c_kg_s = state.mass_flow_kg_s
    sec_air_K = state.secondary_air_outlet_c + 273.15

    # v0.3.2 fix: Q_in is the *clinker-side* sensible heat above ambient,
    # Q_recovered is the *clinker-side* heat released, Q_air is the
    # *air-side* heat absorbed (sum over all compartments). The first-
    # law imbalance is (Q_recovered - Q_air) / Q_in and must be ≤ 0.02
    # per the spec ship gate. (The v0.3.1 bug: only the sec-air stream
    # was summed, giving a 4× first-law imbalance.)
    m_a_total = p.total_under_grate_air_mass_flow_kg_s()
    Q_air_total_kw = 0.0
    for c in state.compartments:
        Q_air_total_kw += c.air_mass_flow_kg_s * cp_a * (c.t_air_out_c - c.t_air_in_c) / 1000.0
    Q_in_kw = m_c_kg_s * p.cp_clinker_kj_kg_k * 1000.0 * \
              (p.clinker_inlet_t_c - p.ambient_t_c) / 1000.0
    Q_out_kw = m_c_kg_s * p.cp_clinker_kj_kg_k * 1000.0 * \
               (state.clinker_outlet_c - p.ambient_t_c) / 1000.0
    return {
        "secondary_air_outlet_c": float(state.secondary_air_outlet_c),
        "secondary_air_outlet_k": float(sec_air_K),
        "tertiary_air_outlet_c":  float(state.tertiary_air_outlet_c),
        "exhaust_air_outlet_c":   float(state.exhaust_air_outlet_c),
        "clinker_outlet_c":       float(state.clinker_outlet_c),
        "cooler_efficiency":      float(state.cooler_efficiency),
        "first_law_imbalance":    float(state.first_law_imbalance),
        "fan_power_kw":           float(state.fan_power_kw),
        "bed_pressure_drop_mm_h2o": float(state.bed_pressure_drop_mm_h2o),
        "free_lime_outlet_wt_pct": float(state.free_lime_outlet_wt_pct),
        "secondary_air_mass_flow_nm3_h": float(state.secondary_air_mass_flow_nm3_h),
        "secondary_air_recovered_gj_per_t_clinker":
            float(state.secondary_air_recovered_kw * 3.6 / p.clinker_throughput_t_h / 1000.0),
        "mj_per_t_cli_recovered": float(state.mj_per_t_cli_recovered),
        "specific_fan_power_kw_per_tph":
            float(state.fan_power_kw / p.clinker_throughput_t_h),
        "secondary_air_stoich_ratio": float(state.secondary_air_stoich_ratio),
        "clinker_quench_rate_k_per_min": float(state.clinker_quench_rate_k_per_min),
        "residence_time_s": float(p.residence_time_s()),
        "heat_in_kw":    float(Q_in_kw),
        "heat_out_kw":   float(Q_out_kw),
        "heat_recovered_kw": float(state.heat_recovered_kw),
        "secondary_air_recovered_kw": float(state.secondary_air_recovered_kw),
        "air_recovered_kw_total": float(Q_air_total_kw),
        "sec_recovered_over_heat_recovered":
            float(state.secondary_air_recovered_kw / max(state.heat_recovered_kw, 1.0)),
        "m_a_total_kg_s": float(m_a_total),
        "m_a_sec_kg_s": float(p.secondary_air_mass_flow_effective_kg_s()),
        "m_a_exhaust_total_kg_s": float(m_a_total - p.secondary_air_mass_flow_effective_kg_s()),
        "duty_case": {
            "altitude_m": float(p.altitude_m),
            "ambient_t_c": float(p.ambient_t_c),
            "ambient_rh":  float(p.ambient_rh),
            "air_density_kg_m3": float(p.air_density_kg_m3()),
            "design_mcr_pct": 100,
            "note": (f"site at {p.altitude_m:.0f} m, {p.ambient_t_c:.0f} C, "
                     f"RH={p.ambient_rh:.2f}; moist-air density from ISA barometric "
                     f"formula (Cengel & Boles 2015)"),
        },
        "sanity": {
            "air_above_clinker": bool(state.secondary_air_outlet_c >
                                      p.clinker_inlet_t_c),
            "first_law_imbalance": float(state.first_law_imbalance),
            "sec_air_in_realistic_band":
                bool(SEC_AIR_BAND_C[0] <= state.secondary_air_outlet_c <= SEC_AIR_BAND_C[1]),
            "clinker_outlet_in_realistic_band":
                bool(CLINKER_OUTLET_BAND_C[0] <= state.clinker_outlet_c <= CLINKER_OUTLET_BAND_C[1]),
        },
    }
