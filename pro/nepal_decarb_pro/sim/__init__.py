"""
Process simulators — physics-based dynamic models of cement and brick equipment.

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
  process_flows    : PFD + P&ID generator (Plotly/SVG)
  cad_export       : DXF + FreeCAD macro output for fabrication

References:
  - Boateng, A.A. (2008). Rotary Kilns: Transport Phenomena and Transport Processes.
  - Sass, A. (1967). Computer model of a cement kiln.
  - Modigell, M. & Werther, J. (1997). Rotary kiln modeling.
  - Dhanjal, P. (2018). Cement plant process engineering.
"""
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
from nepal_decarb_pro.sim.process_flows import (
    generate_pfd_cement,
    generate_pfd_brick,
    generate_pid_cement,
)
from nepal_decarb_pro.sim.cad_export import (
    generate_dxf_kiln,
    generate_freecad_macro,
    generate_equipment_2d,
)

__all__ = [
    "KilnState", "KilnParameters", "simulate_kiln", "run_to_steady_state",
    "BrickKilnState",
    "simulate_brick_kiln_clamp", "simulate_brick_kiln_zigzag", "simulate_brick_kiln_tunnel",
    "Equipment", "EQUIPMENT_DATABASE", "get_equipment", "list_equipment", "equipment_by_category",
    "generate_pfd_cement", "generate_pfd_brick", "generate_pid_cement",
    "generate_dxf_kiln", "generate_freecad_macro", "generate_equipment_2d",
]
