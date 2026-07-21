"""
Rotary Kiln Dynamic Simulator
=============================

5-zone, transient, physics-based ODE model of a rotary cement kiln.

Zones (along kiln axis, x in [0, L]):
  1. Drying       (raw meal: 0 -> 100°C, free water evaporation)
  2. Preheating  (raw meal: 100 -> 600°C)
  3. Calcination (CaCO3 -> CaO + CO2, endothermic, ~600-900°C)
  4. Burning/sintering (clinker formation, 900 -> 1450°C peak)
  5. Cooling (clinker: 1450 -> 1100°C, partial reheat of secondary air)

Mass balance:
  dm_solid/dt = -r_reaction(t,x) * A_cross  (solid decreases as reaction proceeds)
  dm_gas/dt = +r_reaction(t,x) * A_cross + fuel_combustion
  dC_CO2/dt = r_reaction / m_solid  (concentration in gas phase)

Energy balance:
  m_solid * cp_solid * dT_s/dt = convective + radiative + reaction_heat
  m_gas * cp_gas * dT_g/dt = convective + radiative + combustion_heat

Reactions:
  CaCO3 -> CaO + CO2     (Arrhenius, A=1.0e6, Ea=110 kJ/mol)
  Fuel combustion         (Arrhenius, fast, assumed complete in burning zone)

Heat transfer:
  Convective:  h = Nu * k / D,  Nu ~ 0.023 * Re^0.8 * Pr^0.4
  Radiative:  q = ε * σ * (T_wall^4 - T_gas^4)
  Wall losses: q_loss = U * (T_wall - T_amb)

References
----------
  - Boateng, A.A. (2008). "Rotary Kilns: Transport Phenomena and Transport Processes."
  - Sass, A. (1967). "Computer model of a cement kiln." IEEE Trans. Industry Apps.
  - Mujumdar, K.S. & Ranade, V.V. (2006). "Simulation of rotary cement kilns."
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple
import numpy as np
from scipy.integrate import solve_ivp
from pydantic import BaseModel, Field


# ----------------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------------

class KilnParameters(BaseModel):
    """Rotary kiln physical and operating parameters."""
    # Geometry
    length_m: float = 60.0                          # typical: 50-90 m
    diameter_m: float = 4.5                          # typical: 3.5-6 m
    slope_deg: float = 3.5
    rotation_rpm: float = 3.5
    filling_fraction: float = 0.10                   # 8-15% typical

    # Operating
    raw_meal_throughput_t_h: float = 130.0          # t/h dry basis
    raw_meal_moisture_wt: float = 0.04              # 4% moisture
    raw_meal_lsf: float = 0.95
    raw_meal_sm: float = 2.5
    raw_meal_am: float = 1.6

    # Fuel (primary burner at discharge end)
    fuel_type: str = "coal_bituminous_NP"
    fuel_rate_t_h: float = 11.0
    secondary_air_temp_k: float = 800.0

    # Preheater (assumes 5-stage cyclone preheater + precalciner)
    preheater_stages: int = 5
    preheater_efficiency: float = 0.92
    precalciner_degree: float = 0.90                 # 90% of calcination happens in precalciner

    # Cooler (assumes grate cooler)
    cooler_type: str = "grate"
    cooler_efficiency: float = 0.75

    # Ambient
    ambient_temp_k: float = 298.15

    # Thermodynamic
    cao_frac_clinker: float = 0.65
    mgo_frac_clinker: float = 0.015
    cp_solid: float = 950.0                          # J/(kg K), raw meal
    cp_clinker: float = 1050.0                       # J/(kg K), clinker
    cp_gas: float = 1100.0                           # J/(kg K), gas
    coal_ncvc_gj_per_t: float = 25.5
    coal_ef_kgco2_per_gj: float = 94.6

    # Heat losses
    wall_loss_coeff_w_m2_k: float = 3.0              # W/(m² K)
    emissivity: float = 0.85
    stefan_boltzmann: float = 5.67e-8

    # Reaction kinetics (Arrhenius)
    arrhenius_a: float = 1.0e6                       # 1/s
    arrhenius_ea_j_per_mol: float = 110_000.0        # J/mol
    r_gas: float = 8.314                             # J/(mol K)

    # Simulation
    n_zones: int = 5
    n_time_steps: int = 1000
    t_end_s: float = 3600.0                          # 1 hour transient


@dataclass
class KilnState:
    """Dynamic state of the kiln along its axis."""
    x: np.ndarray                                   # position [m]
    t_solid_k: np.ndarray                           # solid temp [K]
    t_gas_k: np.ndarray                             # gas temp [K]
    t_wall_k: np.ndarray                            # wall temp [K]
    conversion: np.ndarray                          # CaCO3 conversion [0-1]
    co2_conc: np.ndarray                            # gas CO2 mass fraction
    o2_conc: np.ndarray                             # gas O2 mass fraction
    solid_mass: np.ndarray                          # solid mass per unit length [kg/m]
    gas_flow: np.ndarray                            # gas mass flow per unit length [kg/(m s)]
    time_s: float = 0.0


# ----------------------------------------------------------------------------
# Physics functions
# ----------------------------------------------------------------------------

def arrhenius_rate(T: float, A: float, Ea: float, R: float = 8.314) -> float:
    """Arrhenius rate constant."""
    return A * math.exp(-Ea / (R * T))


def convective_htc(Re: float, Pr: float, k: float, D: float) -> float:
    """Nusselt number for forced convection in a duct, then h."""
    if Re < 1:
        return 10.0   # stagnant fallback
    Nu = 0.023 * Re**0.8 * Pr**0.4
    return Nu * k / D


def radiative_flux(T1: float, T2: float, eps: float, sigma: float = 5.67e-8) -> float:
    """Net radiative heat flux between two surfaces (W/m²)."""
    return eps * sigma * (T1**4 - T2**4)


# ----------------------------------------------------------------------------
# ODE
# ----------------------------------------------------------------------------

def _kiln_rhs(t: float, y: np.ndarray, p: KilnParameters) -> np.ndarray:
    """
    Right-hand side of the kiln ODE system.

    State y is laid out as:
      [T_s(0), T_g(0), T_w(0), conv(0), CO2(0), O2(0),
       T_s(1), T_g(1), T_w(1), conv(1), CO2(1), O2(1),
       ...
       T_s(n-1), T_g(n-1), T_w(n-1), conv(n-1), CO2(n-1), O2(n-1)]
    Total: 6 * n state variables.

    Simplified: each zone is a lumped CSTR; mass/energy are not spatially
    distributed in detail (lower-fidelity than a full PDE but suitable for
    what-if, operator training, and pilot commissioning).
    """
    n = p.n_zones
    dx = p.length_m / n

    # Unpack state
    T_s = y[0::6]
    T_g = y[1::6]
    T_w = y[2::6]
    conv = np.clip(y[3::6], 0.0, 1.0)
    co2 = np.clip(y[4::6], 0.0, 0.5)
    o2 = np.clip(y[5::6], 0.0, 0.25)

    # Geometry
    A = math.pi * (p.diameter_m / 2) ** 2    # cross-section
    perimeter = math.pi * p.diameter_m

    # Solid flow (kg/s through the kiln, per unit cross-section)
    solid_flow_kg_s = (p.raw_meal_throughput_t_h * 1000.0) / 3600.0
    solid_per_m = solid_flow_kg_s * p.filling_fraction / (p.length_m * p.rotation_rpm / 60.0)
    # Approximate solid holdup

    # Gas flow
    air_for_combustion_kg_s = p.fuel_rate_t_h * 1000.0 / 3600.0 * 8.5  # ~8.5 kg air/kg coal
    co2_from_combustion_kg_s = p.fuel_rate_t_h * 1000.0 / 3600.0 * p.coal_ncvc_gj_per_t * p.coal_ef_kgco2_per_gj / 1000.0
    co2_from_calcination_kg_s = solid_flow_kg_s * p.cao_frac_clinker * 0.7857
    gas_flow_kg_s = air_for_combustion_kg_s + p.fuel_rate_t_h * 1000.0 / 3600.0 + co2_from_combustion_kg_s + co2_from_calcination_kg_s

    # Heat transfer coefficients
    # Re ~ gas mass flux
    gas_density = 0.6                                # kg/m³ at kiln temp
    gas_velocity = gas_flow_kg_s / (gas_density * A)
    Re = gas_density * gas_velocity * p.diameter_m / 4e-5
    Pr = 0.7
    k_gas = 0.05
    h_conv = convective_htc(Re, Pr, k_gas, p.diameter_m)

    # Wall temperature (quasi-steady, between T_s and T_g with losses)
    q_rad_internal = radiative_flux(T_w, T_g, p.emissivity, p.stefan_boltzmann) * perimeter
    q_wall_loss = p.wall_loss_coeff_w_m2_k * (T_w - p.ambient_temp_k) * perimeter
    # Wall thermal mass — not tracked dynamically; use algebraic form
    # Assume T_w is in quasi-steady state with radiation balance
    # T_w^4 = (T_g^4 + T_s^4) / 2 + q_wall_loss / (eps * sigma * perimeter)
    # Iteratively solve, but for our purposes, we treat it as lagged:
    T_w = ((T_g**4 + T_s**4) / 2.0 + q_wall_loss / (p.emissivity * p.stefan_boltzmann * perimeter + 1e-9)) ** 0.25

    # Reaction rate (CaCO3 -> CaO + CO2), Arrhenius
    # Most reaction happens in precalciner, but for kiln model, distributed
    r_react = np.zeros(n)
    for i in range(n):
        T_local = T_s[i]
        if T_local > 700.0:                                # calcination starts ~600°C
            k_react = arrhenius_rate(T_local, p.arrhenius_a, p.arrhenius_ea_j_per_mol, p.r_gas)
            r_react[i] = k_react * (1.0 - conv[i]) * solid_per_m
            r_react[i] = min(r_react[i], 0.5 * solid_per_m)   # cap

    # Heat of reaction (endothermic calcination)
    dH_react = 530_000.0                                   # J/kg CaCO3

    # Energy balances
    dT_s_dt = np.zeros(n)
    dT_g_dt = np.zeros(n)

    # Solid: convective from gas, radiative from wall, endothermic reaction
    for i in range(n):
        # Convective (gas -> solid)
        q_conv = h_conv * A * (T_g[i] - T_s[i]) / max(solid_per_m, 1e-3)
        # Radiative (wall -> solid, internal)
        q_rad = p.emissivity * p.stefan_boltzmann * A * (T_w[i]**4 - T_s[i]**4) / max(solid_per_m, 1e-3)
        # Reaction heat (endothermic, reduces solid temp)
        q_react = r_react[i] * dH_react / max(solid_per_m, 1e-3)
        dT_s_dt[i] = (q_conv + q_rad - q_react) / p.cp_solid

    # Gas: convective to solid, radiative, combustion heat (only in burning zone)
    # Cap gas temperature at physically reasonable value (2000 K)
    T_g_max = 2000.0
    for i in range(n):
        q_conv_g = h_conv * A * (T_s[i] - T_g[i]) / max(gas_flow_kg_s / n, 1e-3)
        q_combustion_zone = (i == n - 1)  # combustion at discharge end
        if q_combustion_zone:
            # NCV is in GJ/t = 1e9 J/t = 1e6 J/kg. fuel rate in t/h, so 1e9*1e3/3600 to get W
            Q_combustion = (p.fuel_rate_t_h * 1000.0 / 3600.0) * (p.coal_ncvc_gj_per_t * 1e6)  # W
            Q_combustion_zone = Q_combustion / n
        else:
            Q_combustion_zone = 0.0
        # In precalciner zone (assumed already done before kiln), we have
        # already released calcination CO2; here we just handle the kiln calcination
        dT_g_dt[i] = (q_conv_g + Q_combustion_zone / max(gas_flow_kg_s / n, 1e-3)) / p.cp_gas
        # Cap gas temperature to prevent runaway
        if T_g[i] > T_g_max:
            dT_g_dt[i] = min(dT_g_dt[i], 0)

    # Mass balances
    dconv_dt = np.zeros(n)
    for i in range(n):
        dconv_dt[i] = r_react[i] / max(solid_per_m, 1e-3)

    dco2_dt = np.zeros(n)
    for i in range(n):
        dco2_dt[i] = r_react[i] * 0.44 / max(gas_flow_kg_s / n, 1e-3)

    # O2: consumed by combustion in last zone
    do2_dt = np.zeros(n)
    o2_consumed = p.fuel_rate_t_h * 1000.0 / 3600.0 * 2.5 / max(gas_flow_kg_s / n, 1e-3)
    do2_dt[n - 1] = -o2_consumed

    # Repack
    dydt = np.zeros_like(y)
    dydt[0::6] = dT_s_dt
    dydt[1::6] = dT_g_dt
    dydt[2::6] = 0.0                                # T_w quasi-steady
    dydt[3::6] = dconv_dt
    dydt[4::6] = dco2_dt
    dydt[5::6] = do2_dt
    return dydt


# ----------------------------------------------------------------------------
# Simulator
# ----------------------------------------------------------------------------

def initial_state(p: KilnParameters) -> np.ndarray:
    """Initial state: solid enters cold at zone 0, gas hot at zone n-1."""
    n = p.n_zones
    T_s0 = p.ambient_temp_k                          # raw meal at ~25°C
    T_g0 = 800.0                                     # hot gas from preheater/precalciner
    T_w0 = 600.0
    conv0 = 0.5                                      # pre-calcination already done
    co20 = 0.25
    o20 = 0.10
    y0 = np.zeros(6 * n)
    for i in range(n):
        y0[6 * i + 0] = T_s0
        y0[6 * i + 1] = T_g0
        y0[6 * i + 2] = T_w0
        y0[6 * i + 3] = conv0
        y0[6 * i + 4] = co20
        y0[6 * i + 5] = o20
    return y0


def simulate_kiln(
    p: KilnParameters,
    y0: Optional[np.ndarray] = None,
    t_end_s: Optional[float] = None,
    n_time_points: int = 200,
    method: str = "Radau",
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simulate the rotary kiln transient.

    Returns: (t, y, x) where y is the state vector and x is the spatial
    coordinate along the kiln.
    """
    if y0 is None:
        y0 = initial_state(p)
    if t_end_s is None:
        t_end_s = p.t_end_s

    t_eval = np.linspace(0, t_end_s, n_time_points)
    sol = solve_ivp(
        fun=_kiln_rhs,
        t_span=(0, t_end_s),
        y0=y0,
        t_eval=t_eval,
        method=method,
        max_step=10.0,
        args=(p,),
    )
    if not sol.success:
        raise RuntimeError(f"ODE solver failed: {sol.message}")

    x = np.linspace(0, p.length_m, p.n_zones)
    return sol.t, sol.y, x


def run_to_steady_state(
    p: KilnParameters,
    max_t_s: float = 7200.0,
    tol: float = 1e-3,
) -> KilnState:
    """
    Run the kiln to steady state (default 2 hours simulated).
    """
    t, y, x = simulate_kiln(p, t_end_s=max_t_s, n_time_points=50, method="Radau")
    final = y[:, -1]
    n = p.n_zones
    state = KilnState(
        x=x,
        t_solid_k=final[0::6],
        t_gas_k=final[1::6],
        t_wall_k=final[2::6],
        conversion=final[3::6],
        co2_conc=final[4::6],
        o2_conc=final[5::6],
        solid_mass=np.full(n, 0.0),
        gas_flow=np.full(n, 0.0),
        time_s=t[-1],
    )
    return state


# ----------------------------------------------------------------------------
# Derived outputs
# ----------------------------------------------------------------------------

def compute_outputs(state: KilnState, p: KilnParameters) -> Dict[str, float]:
    """Compute engineering outputs from kiln state."""
    # Peak solid temperature (clinker)
    t_clinker_peak_k = float(np.max(state.t_solid_k))
    # Peak gas temperature
    t_gas_peak_k = float(np.max(state.t_gas_k))
    # Burning zone temperature
    t_burning = float(state.t_solid_k[-1])
    # Total conversion
    avg_conversion = float(np.mean(state.conversion))
    # Specific heat consumption (MJ / t clinker)
    # coal_kg_h = p.fuel_rate_t_h * 1000  (kg/h)
    # coal NCV = p.coal_ncvc_gj_per_t  (GJ/t = MJ/kg)
    # Energy input = coal_kg_h * NCV (MJ/h) (since 1 GJ/t = 1 MJ/kg)
    # raw_meal_throughput_t_h = t/h
    # SEC = energy / clinker production = (coal_kg_h * NCV) / (raw_meal * clinker_ratio)
    coal_kg_h = p.fuel_rate_t_h * 1000.0  # kg/h
    ncvc_mj_kg = p.coal_ncvc_gj_per_t     # MJ/kg (= GJ/t)
    energy_mj_h = coal_kg_h * ncvc_mj_kg  # MJ/h
    clinker_t_h = p.raw_meal_throughput_t_h * 0.78  # approx 78% of raw meal becomes clinker
    sec_mj_per_t_clinker = energy_mj_h / clinker_t_h
    # CO2 from calcination
    co2_calcination = p.raw_meal_throughput_t_h * p.cao_frac_clinker * 0.7857  # t CO2/h
    # CO2 from fuel combustion (11 t/h * 25.5 GJ/t * 94.6 kg/GJ = 26,535 kg/h = 26.5 t/h)
    co2_fuel = p.fuel_rate_t_h * p.coal_ncvc_gj_per_t * p.coal_ef_kgco2_per_gj / 1000.0  # t CO2/h
    return {
        "t_clinker_peak_k": t_clinker_peak_k,
        "t_clinker_peak_c": t_clinker_peak_k - 273.15,
        "t_gas_peak_k": t_gas_peak_k,
        "t_burning_zone_k": t_burning,
        "avg_conversion": avg_conversion,
        "sec_mj_per_t_clinker": sec_mj_per_t_clinker,
        "co2_calcination_t_h": co2_calcination,
        "co2_fuel_t_h": co2_fuel,
        "co2_total_t_h": co2_calcination + co2_fuel,
        "co2_total_kg_h": (co2_calcination + co2_fuel) * 1000,  # for backwards compat
        "thermal_efficiency": p.cooler_efficiency,
    }
