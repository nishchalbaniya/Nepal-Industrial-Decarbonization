"""
nepal_kiln_sim
==============

Day 2 of the 20-day Nepal Industrial Decarbonization Suite.

A standalone, installable dynamic simulator for rotary cement kilns and
clinker coolers, with:

  * 5-zone physics-based ODE model (drying, preheating, calcination,
    burning/sintering, cooling)
  * Mass + energy balance with Arrhenius calcination kinetics
  * Multiple fuels (coal, petcoke, biomass, TDF, RDF, natural gas)
  * Alternative fuel substitution impact on flame temperature and SEC
  * Steady-state solver and full transient simulation
  * Hetauda / Udayapur / Hongshi-Shivam plant parameter presets
  * MATLAB / Octave live scripts (.mlx + .m) for cross-language use
  * Streamlit UI + CLI + Python API
  * CSV / JSON / Excel I/O for plant historian integration

References
----------
  - Boateng, A.A. (2008). Rotary Kilns: Transport Phenomena and Transport Processes.
  - Mujumdar, K.S. & Ranade, V.V. (2006). Simulation of rotary cement kilns.
    Industrial & Engineering Chemistry Research, 45(9), 3027-3038.
  - Sass, A. (1967). Computer model of a cement kiln. IEEE Trans. Industry Apps.
  - Ghoshdastidar, P.S. (2017). Process Equipment Design (kiln chapter).
  - Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.

License: MIT
Authors: Nishchal Baniya, Mavis (Day 2 build)
"""
from __future__ import annotations

from .kiln_ode import (
    KilnParameters,
    KilnState,
    simulate_kiln,
    run_to_steady_state,
    compute_outputs,
    arrhenius_rate,
    convective_htc,
    radiative_flux,
)
from .fuels import (
    Fuel,
    FUEL_DATABASE,
    get_fuel,
    list_fuels,
    compute_blend_ef,
    compute_flame_temperature,
)
from .plants import (
    PlantPreset,
    PLANT_PRESETS,
    get_plant_preset,
    list_plants,
)
from .sensitivity import (
    sensitivity_sweep,
    morris_elementary_effects,
)
from .io import (
    save_results_csv,
    load_results_csv,
    save_results_json,
    save_state_pickle,
    load_state_pickle,
    export_matlab_script,
    export_octave_script,
)
from .calibration import (
    calibrate_to_plant,
    CalibrationResult,
)

__version__ = "0.2.0"

__all__ = [
    # ODE core
    "KilnParameters", "KilnState", "simulate_kiln", "run_to_steady_state",
    "compute_outputs",
    "arrhenius_rate", "convective_htc", "radiative_flux",
    # Fuels
    "Fuel", "FUEL_DATABASE", "get_fuel", "list_fuels",
    "compute_blend_ef", "compute_flame_temperature",
    # Plant presets
    "PlantPreset", "PLANT_PRESETS", "get_plant_preset", "list_plants",
    # Sensitivity / UQ
    "sensitivity_sweep", "morris_elementary_effects",
    # I/O
    "save_results_csv", "load_results_csv", "save_results_json",
    "save_state_pickle", "load_state_pickle",
    "export_matlab_script", "export_octave_script",
    # Calibration
    "calibrate_to_plant", "CalibrationResult",
    "__version__",
]
