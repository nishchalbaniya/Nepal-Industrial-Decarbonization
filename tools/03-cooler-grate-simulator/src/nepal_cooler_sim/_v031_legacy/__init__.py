"""
nepal_cooler_sim
================

Day 3 of the 20-day Nepal Industrial Decarbonization Suite.

1D cross-flow grate cooler simulator for cement clinker.

  - Discretized along grate (default 30 cells)
  - Convective + radiative heat transfer from hot clinker (T_in ~ 1400 C) to
    under-grate cooling air
  - Secondary-air temperature recovered (re-used in kiln calciner)
  - Grate speed / air flow / bed depth as parametric inputs
  - Validation against published cooler curves (Batty 1956, Peray 1986)
  - MATLAB / Octave export for cross-language use
  - Streamlit UI + CLI + Python API

This complements the kiln simulator (Day 2 / ``nepal_kiln_sim``). The
coupled picture is: kiln discharges hot clinker to cooler, cooler
recovers heat to secondary air, secondary air is blown back into the
kiln calciner.

References
----------
  - Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.
  - Boateng, A.A. (2008). Rotary Kilns (Ch. 7 — Coolers).
  - Mujumdar, K.S. (2007). Grate cooler model. *Ind. Eng. Chem. Res.* 46(7).
  - WBSCD/GCCA GNR 2022 (cooler efficiency benchmarks).

License: MIT
"""
from __future__ import annotations

from .cooler_ode import (
    CoolerParameters,
    CoolerState,
    simulate_cooler,
    run_to_steady_state,
    compute_outputs,
    arrhenius_rate,
    convective_htc_cooler,
    radiative_flux_cooler,
)
from .kiln_link import (
    coupled_kiln_cooler_steady_state,
    CoupledResult,
)
from .io import (
    save_results_csv,
    load_results_csv,
    save_results_json,
    export_matlab_script,
    export_octave_script,
)
from .sensitivity import (
    sensitivity_sweep,
)

__version__ = "0.3.0"

__all__ = [
    # Core
    "CoolerParameters", "CoolerState",
    "simulate_cooler", "run_to_steady_state", "compute_outputs",
    "arrhenius_rate", "convective_htc_cooler", "radiative_flux_cooler",
    # Coupling
    "coupled_kiln_cooler_steady_state", "CoupledResult",
    # I/O
    "save_results_csv", "load_results_csv", "save_results_json",
    "export_matlab_script", "export_octave_script",
    # Sensitivity
    "sensitivity_sweep",
    "__version__",
]
