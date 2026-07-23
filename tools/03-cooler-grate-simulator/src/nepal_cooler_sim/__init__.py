"""
nepal_cooler_sim
================

Day 3 v0.3.2 — Aanya's structural fix for the grate cooler simulator.

This is the v0.3.2 entry point. The v0.3.0 / v0.3.1 files are kept in
``_v031_legacy/`` for one cycle so the kiln-link shim and the I/O
modules can be re-aligned in Day 4.

What changed v0.3.1 -> v0.3.2
-----------------------------
1. Per-compartment air inventory is now allocated by *physical demand*,
   not by uniform velocity-area. Compartment 1 (sec-air zone) is set
   by combustion-air stoichiometry (Peray & Waddell 1986 §6.2);
   compartments 2..N split the remainder by bed length.
2. The heat-transfer coefficient ``h_eff`` is now
   ``h_conv + h_rad_equiv`` with ``h_rad_equiv = 4·eps·sigma·T^3``
   (Incropera & DeWitt 2002 Ch. 12). The v0.3.1 constant 350 W/m^2K
   floor was a design-point floor, not a hot-end peak; v0.3.2 uses
   the temperature-dependent linearized radiation that Mujumdar 2007
   §2.2 Fig. 2 prescribes.
3. Moist-air density is computed from the ISA barometric formula with
   Magnus-form saturation vapour pressure (Cengel & Boles 2015).
   Hetauda at 1400 m / 35 °C / 90% RH: 0.95 kg/m^3 (was hard-coded
   0.6 in v0.3.0; 1.05 was the upper-bound estimate in v0.3.1).
4. First-law imbalance |Q_recovered - Q_air| / Q_in is now <= 0.02
   on the default Hetauda preset (was 4× in v0.3.1).

Honest disclosure (read this before claiming "ship")
-----------------------------------------------------
The 6 ship-gate bands defined in ``DAY-03-SPEC.md`` (secondary-air
600-1000 °C, tertiary 400-700 °C, exhaust 150-300 °C, clinker-outlet
120-200 °C, cooler efficiency 0.65-0.85, first-law <= 0.02) are NOT
all met on the default Hetauda preset. Only the first-law band and
the second-law invariant pass; the other bands fail because the
*prescribed geometry* (5 compartments × 28 m × 1.5 m/s) cannot deliver
the design-duty sec air (560 °C vs the 600 °C band floor) or the
clinker-outlet (532 °C vs the 200 °C band ceiling). The physical
ceiling at this geometry is ~ 1310 K air-side dT at 38 kg/s sec-air
and 52 MW clinker enthalpy drop. The Day 4 calibration work item
(see ``DAY-04-SPEC.md``, to be written) introduces plant-data
calibration (Hetauda clinker-outlet T time series, sec-air T time
series) and operating-handle freedom (air velocity, grate speed,
recuperator preheat) to bring the bands into spec.

Public API
----------
>>> from nepal_cooler_sim import (
...     CoolerParameters, CoolerState,
...     solve_steady_state, compute_outputs, simulate_cooler,
...     achenbach_nu, wakao_nu, effective_htc_cooler,
...     air_density_kg_m3, hetauda, udayapur, hongshi_shivam, ghorahi,
... )
>>> from nepal_cooler_sim.compartments import build_compartment_inventory
>>> p = hetauda()
>>> s = solve_steady_state(p)
>>> o = compute_outputs(s, p)
>>> o["secondary_air_outlet_c"], o["clinker_outlet_c"], o["cooler_efficiency"]

References
----------
- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192.
- Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.
- Cengel, Y.A. & Boles, M.A. (2015). Thermodynamics 8e.
- Incropera, F.P. & DeWitt, D.P. (2002). Fundamentals of Heat and Mass
  Transfer, 5e. Ch. 12.
- ICCC 2006 §2.3, §3.4.
- GCCA GNR 2022; ECRA 2022.
"""
from __future__ import annotations

from .cooler_ode import (
    # Constants
    STEFAN_BOLTZMANN,
    AIR_CP_J_KG_K,
    AIR_VISCOSITY_PA_S,
    AIR_K_W_M_K,
    PRANDTL_AIR,
    HOOD_RADIATION_MARGIN_K,
    ACHENBACH_RE_MAX,
    WAKAO_RE_MIN,
    # Ship-gate reference bands
    SEC_AIR_BAND_C,
    TERT_AIR_BAND_C,
    EXHAUST_AIR_BAND_C,
    CLINKER_OUTLET_BAND_C,
    COOLER_EFF_BAND,
    COOLER_LOSS_MJ_PER_T_CLI_BAT,
    # Pure-physics functions
    air_density_kg_m3,
    achenbach_nu,
    wakao_nu,
    convective_htc_cooler,
    radiative_htc_equiv_w_m2_k,
    effective_htc_cooler,
    radiative_flux_w_m2,
    ergun_pressure_drop_pa,
    fan_power_kw,
    # Pydantic / dataclass types
    CompartmentParameters,
    CoolerParameters,
    CoolerState,
    # Public API
    solve_steady_state,
    simulate_cooler,         # kiln-link back-compat shim, returns (t, y, x)
    compute_outputs,
)
from .compartments import (
    CompartmentAirInventory,
    build_compartment_inventory,
    check_second_law_compartments,
    achenbach_h_at_re1000,
)
from .plants import (
    hetauda,
    udayapur,
    hongshi_shivam,
    ghorahi,
    PRESETS,
)

__version__ = "0.3.2"

__all__ = [
    # Constants
    "STEFAN_BOLTZMANN", "AIR_CP_J_KG_K", "AIR_VISCOSITY_PA_S",
    "AIR_K_W_M_K", "PRANDTL_AIR", "HOOD_RADIATION_MARGIN_K",
    "ACHENBACH_RE_MAX", "WAKAO_RE_MIN",
    # Ship-gate reference bands
    "SEC_AIR_BAND_C", "TERT_AIR_BAND_C", "EXHAUST_AIR_BAND_C",
    "CLINKER_OUTLET_BAND_C", "COOLER_EFF_BAND",
    "COOLER_LOSS_MJ_PER_T_CLI_BAT",
    # Pure-physics functions
    "air_density_kg_m3",
    "achenbach_nu", "wakao_nu",
    "convective_htc_cooler",
    "radiative_htc_equiv_w_m2_k",
    "effective_htc_cooler",
    "radiative_flux_w_m2",
    "ergun_pressure_drop_pa",
    "fan_power_kw",
    # Pydantic / dataclass types
    "CompartmentParameters",
    "CoolerParameters",
    "CoolerState",
    # Public API
    "solve_steady_state",
    "simulate_cooler",
    "compute_outputs",
    # Compartment-wise helpers
    "CompartmentAirInventory",
    "build_compartment_inventory",
    "check_second_law_compartments",
    "achenbach_h_at_re1000",
    # Plant presets
    "hetauda", "udayapur", "hongshi_shivam", "ghorahi", "PRESETS",
    "__version__",
]
