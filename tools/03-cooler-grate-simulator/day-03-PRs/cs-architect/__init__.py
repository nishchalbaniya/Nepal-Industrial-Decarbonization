"""
nepal_cooler_sim — Day 3 v0.3.1 public API
===========================================

Day 3 of the 20-day Nepal Industrial Decarbonization Suite.

This module exposes the v0.3.1 grate-cooler simulator with an **explicit
shape contract** so the kiln model (Day 2) and downstream packages (Day 14
LLM advisor, Day 18 desktop shell) can integrate without the v0.3.0
spatial-vs-temporal shape mismatch.

Shape contract
--------------

* The cooler is **quasi-steady, spatial** — it does *not* integrate a
  time-dependent ODE. The v0.3.0 code's `simulate_cooler(p) -> (t, y, x)`
  was a band-aid that returned `t = [0.0]` and `y.shape = (2*n, 1)` so the
  kiln's I/O helpers would not crash; this is preserved for kiln-link
  compat but is no longer the canonical return type.

* The canonical return is :class:`CoolerResult` (a dataclass with typed
  spatial profile and KPI scalars).

* :func:`solve_steady_state` is the new canonical entry point. It
  accepts a :class:`CoolerParameters` (Pydantic v2) and returns a
  :class:`CoolerResult`.

* :func:`simulate_cooler` is the legacy shim. It calls
  ``solve_steady_state`` and reshapes the result into ``(t, y, x)`` for
  kiln-link compat. New code should use :func:`solve_steady_state`
  directly.

References
----------
  - McCabe, W.L., Smith, J.C. & Harriott, P. (2005). Unit Operations
    of Chemical Engineering, 7th ed. (Ch. 15 — Heat Exchangers).
  - Mujumdar, K.S. (2007). Grate cooler model. Ind. Eng. Chem. Res. 46(7).
  - Boateng, A.A. (2008). Rotary Kilns (Ch. 7 — Coolers).
  - Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.
  - Pydantic v2 docs — https://docs.pydantic.dev/latest/

License: MIT
"""
from __future__ import annotations

# Try a relative import first (production: the v0.3.1 module lives in
# the same package as `cooler_ode` and the rest of the upstream).
# Fall back to absolute (smoke tests, ad-hoc imports, pytest
# collection without a conftest). This pattern is repeated in
# `cooler_types.py`, `io.py`, and `cli.py`; all four files share the
# same import strategy so the PR works whether loaded standalone
# (e.g. from a verifier scratch dir) or as a sibling of the
# upstream package.
try:
    from .cooler_ode import (  # type: ignore[import-not-found]
        CoolerParameters,
        CoolerState,
        compute_outputs,
        run_to_steady_state,
        simulate_cooler,
        arrhenius_rate,
        convective_htc_cooler,
        radiative_flux_cooler,
    )
    from .kiln_link import (  # type: ignore[import-not-found]
        coupled_kiln_cooler_steady_state,
        CoupledResult,
    )
    from .cooler_types import (  # type: ignore[import-not-found]
        CoolerProfile,
        CoolerResult,
        CoolerOutputs,
        ShapeContractError,
        solve_steady_state,
    )
    from .io import (  # type: ignore[import-not-found]
        save_results_csv,
        load_results_csv,
        save_results_json,
        load_results_json,
        save_results_pickle,
        load_results_pickle,
        export_matlab_script,
        export_octave_script,
        to_pdd_json,
        to_natural_language,
    )
    from .sensitivity import sensitivity_sweep  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — smoke-test / pytest scratch path
    from nepal_cooler_sim.cooler_ode import (  # type: ignore[no-redef]
        CoolerParameters,
        CoolerState,
        compute_outputs,
        run_to_steady_state,
        simulate_cooler,
        arrhenius_rate,
        convective_htc_cooler,
        radiative_flux_cooler,
    )
    from nepal_cooler_sim.kiln_link import (  # type: ignore[no-redef]
        coupled_kiln_cooler_steady_state,
        CoupledResult,
    )
    from nepal_cooler_sim.cooler_types import (  # type: ignore[no-redef]
        CoolerProfile,
        CoolerResult,
        CoolerOutputs,
        ShapeContractError,
        solve_steady_state,
    )
    from nepal_cooler_sim.io import (  # type: ignore[no-redef]
        save_results_csv,
        load_results_csv,
        save_results_json,
        load_results_json,
        save_results_pickle,
        load_results_pickle,
        export_matlab_script,
        export_octave_script,
        to_pdd_json,
        to_natural_language,
    )
    from nepal_cooler_sim.sensitivity import (  # type: ignore[no-redef]
        sensitivity_sweep,
    )

__version__ = "0.3.1"

__all__ = [
    # Core domain
    "CoolerParameters",
    "CoolerState",
    "CoolerProfile",
    "CoolerResult",
    "CoolerOutputs",
    "ShapeContractError",
    "solve_steady_state",
    "run_to_steady_state",
    "simulate_cooler",
    "compute_outputs",
    "arrhenius_rate",
    "convective_htc_cooler",
    "radiative_flux_cooler",
    # Coupling
    "coupled_kiln_cooler_steady_state",
    "CoupledResult",
    # I/O
    "save_results_csv",
    "load_results_csv",
    "save_results_json",
    "load_results_json",
    "save_results_pickle",
    "load_results_pickle",
    "export_matlab_script",
    "export_octave_script",
    "to_pdd_json",
    "to_natural_language",
    # Sensitivity
    "sensitivity_sweep",
    # Meta
    "__version__",
]
