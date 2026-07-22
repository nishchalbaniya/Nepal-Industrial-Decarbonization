"""
nepal_decarb_pro
================

Unified entry point for the Nepal Industrial Decarbonization
v1.0 product (per ADR-001). Wraps:

  - nepal_kiln_sim      (Day 2 ship; v0.2.0)
  - nepal_cooler_sim   (Day 3 v0.3.2 + Day 4 v0.4.0 + Day 5 v0.5.0)
  - nepal_decarb_pro.mrv  (Day 1 baseline MRV; v1.3.4 already in repo)
  - nepal_decarb_pro.api  (Day 10 FastAPI; dispatched to Hiro)
  - nepal_decarb_pro.cad  (Day 6 v0.6.0 FreeCAD STEP export)
  - nepal_decarb_pro.sim  (Day 14 LLM advisor; deferred)

The `nepal-decarb` CLI (nepal_decarb_pro.cli) is the single user-
facing entry point. It dispatches to the right module and returns
JSON / CSV / STEP outputs.

References
----------
- ADR-001: docs/ADR-001-v1-ARCHITECTURE.md
- v0.5.0 calibrated cooler: commit 2aa918c
- v0.6.0 STEP export: commit 55f14e2
- Mujumdar 2007; Peray & Waddell 1986; Achenbach 1995;
  Boateng 2008; Mujumdar & Ranade 2006; Sass 1967.

License: MIT
"""
from __future__ import annotations

__version__ = "0.6.0"
