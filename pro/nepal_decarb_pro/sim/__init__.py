"""
Process simulators -- physics-based dynamic models of cement and brick equipment.

These are the actual engineering simulators used for:
  - Operator training
  - Process optimization (what-if scenarios)
  - Pilot plant commissioning
  - Troubleshooting
  - Real-time digital twin (when paired with IoT)

Modules:
  kiln_dynamics    : 5-zone rotary cement kiln (mass + energy + reactions)
  brick_dynamics   : Brick kiln firing curves (clamp/zigzag/tunnel)
  equipment_specs  : Database of 50+ cement & brick equipment
  process_flows    : PFD + P&ID generator (Plotly/SVG) -- REQUIRES matplotlib
  cad_export       : DXF + FreeCAD macro output for fabrication

WP6 fix: process_flows and cad_export are imported lazily because they
require optional dependencies (matplotlib for process_flows; FreeCAD
Python for cad_export). Importing the core sim modules
(kiln_dynamics, brick_dynamics, equipment_specs) no longer requires
these optional packages, so `from nepal_decarb_pro.sim import ...`
works on a minimal install. The lazy functions are exposed via
__getattr__ so `from nepal_decarb_pro.sim import generate_pfd_cement`
still works at call time -- but only if matplotlib is installed.

References:
  - Boateng, A.A. (2008). Rotary Kilns: Transport Phenomena and Transport Processes.
  - Sass, A. (1967). Computer model of a cement kiln.
  - Modigell, M. & Werther, J. (1997). Rotary kiln modeling.
  - Dhanjal, P. (2018). Cement plant process engineering.
"""
from __future__ import annotations

import importlib
from typing import Any

from nepal_decarb_pro.sim.kiln_dynamics import (
    KilnState,
    KilnParameters,
    simulate_kiln,
    run_to_steady_state,
)
from nepal_decarb_pro.sim.brick_dynamics import (
    BrickKilnState,
    simulate_brick_kiln_clamp,
    simulate_brick_kiln_zigzag,
    simulate_brick_kiln_tunnel,
)
from nepal_decarb_pro.sim.equipment_specs import (
    Equipment,
    EQUIPMENT_DATABASE,
    get_equipment,
    list_equipment,
    equipment_by_category,
)


# Lazy import map: process_flows requires matplotlib; cad_export may
# pull in FreeCAD's Python module on some installs. They are exposed
# via __getattr__ so `from nepal_decarb_pro.sim import generate_pfd_cement`
# still works, but does not fail at module-load time when the optional
# dependency is missing. See reviews/REMEDIATION_REPORT.md WP6.
_LAZY_IMPORTS = {
    "generate_pfd_cement": "nepal_decarb_pro.sim.process_flows",
    "generate_pfd_brick": "nepal_decarb_pro.sim.process_flows",
    "generate_pid_cement": "nepal_decarb_pro.sim.process_flows",
    "generate_dxf_kiln": "nepal_decarb_pro.sim.cad_export",
    "generate_freecad_macro": "nepal_decarb_pro.sim.cad_export",
    "generate_equipment_2d": "nepal_decarb_pro.sim.cad_export",
}


def __getattr__(name: str) -> Any:
    """PEP 562 lazy attribute access for modules with optional deps."""
    if name in _LAZY_IMPORTS:
        module = importlib.import_module(_LAZY_IMPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module 'nepal_decarb_pro.sim' has no attribute {name!r}")


__all__ = [
    "KilnState", "KilnParameters", "simulate_kiln", "run_to_steady_state",
    "BrickKilnState",
    "simulate_brick_kiln_clamp", "simulate_brick_kiln_zigzag", "simulate_brick_kiln_tunnel",
    "Equipment", "EQUIPMENT_DATABASE", "get_equipment", "list_equipment", "equipment_by_category",
    "generate_pfd_cement", "generate_pfd_brick", "generate_pid_cement",
    "generate_dxf_kiln", "generate_freecad_macro", "generate_equipment_2d",
]
