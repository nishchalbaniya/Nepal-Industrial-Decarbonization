"""
Day 12 demo -- write the Hetauda rotary kiln STEP file via FreeCAD.
Geometry per IKN / KHD / Polysius product literature, sized to a
typical 5000 tpd Nepal cement plant (Hetauda 60m × 4.6m).
"""
import json
import math
import sys
from pathlib import Path

import FreeCAD
import Part
import Import

OUT_TMP = Path("C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/06_hetauda_kiln.tmp.step")
OUT_FINAL = Path("C:/Users/TG/.mavis\workspace/nepal-decarb-build/demo-e2e/cad/06_hetauda_kiln.step".replace("C:\\Users\\TG\\.mavis", "C:/Users/TG/.mavis"))
OUT_FINAL = Path("C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/06_hetauda_kiln.step")
if OUT_TMP.exists(): OUT_TMP.unlink()
OUT_FINAL.parent.mkdir(parents=True, exist_ok=True)

# Hetauda kiln dimensions (per IKN/Pyrorotor literature; Mujumdar 2007 Ch.4)
KILN_LENGTH_M = 60.0
KILN_DIAM_M = 4.6
SHELL_THK_M = 0.05
TIRE_OD_M = 5.0    # tire outside diameter
TIRE_W_M = 0.8     # tire width
ROLLER_OD_M = 1.2
ROLLER_W_M = 0.5
BURNER_LEN_M = 3.0
BURNER_OD_M = 0.6
GEAR_OD_M = 5.4    # girth gear
GEAR_W_M = 0.5
PREHEATER_H_M = 25.0
PREHEATER_DIA_M = 6.0
COOLER_DX_M = 33.0  # mating cooler length

doc = FreeCAD.newDocument("HetaudaKiln")
FreeCAD.setActiveDocument(doc.Name)

parts = []

# 1. Main shell (cylinder, axis along X)
shell = doc.addObject("Part::Cylinder", "KilnShell")
shell.Radius = KILN_DIAM_M / 2
shell.Height = KILN_LENGTH_M
shell.Placement = FreeCAD.Placement(
    FreeCAD.Vector(0, 0, 0),
    FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)  # rotate to lie along X
)
parts.append(shell)

# 2. Four tire-and-roller stations (at x=12, 24, 36, 48)
tire_positions = [12, 24, 36, 48]
for i, x in enumerate(tire_positions):
    # Tire (ring around shell)
    tire = doc.addObject("Part::Cylinder", f"Tire_{i+1}")
    tire.Radius = TIRE_OD_M / 2
    tire.Height = TIRE_W_M
    tire.Placement = FreeCAD.Placement(
        FreeCAD.Vector(x, 0, 0),
        FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
    )
    parts.append(tire)
    # Two support rollers per tire (below, at z=-(KILN_DIAM/2+ROLLER_OD/2))
    for j, yoff in enumerate([-KILN_DIAM_M/2 - ROLLER_OD_M/2, KILN_DIAM_M/2 + ROLLER_OD_M/2]):
        roller = doc.addObject("Part::Cylinder", f"Roller_{i+1}_{j+1}")
        roller.Radius = ROLLER_OD_M / 2
        roller.Height = ROLLER_W_M
        roller.Placement = FreeCAD.Placement(
            FreeCAD.Vector(x, yoff, 0),
            FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
        )
        parts.append(roller)

# 3. Primary burner (at cold end, x=0)
burner = doc.addObject("Part::Cylinder", "PrimaryBurner")
burner.Radius = BURNER_OD_M / 2
burner.Height = BURNER_LEN_M
burner.Placement = FreeCAD.Placement(
    FreeCAD.Vector(-BURNER_LEN_M/2, 0, KILN_DIAM_M/2 + 0.5),
    FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
)
parts.append(burner)

# 4. Preheater tower (at hot end, x=KILN_LENGTH)
preheater = doc.addObject("Part::Cylinder", "PreheaterTower")
preheater.Radius = PREHEATER_DIA_M / 2
preheater.Height = PREHEATER_H_M
preheater.Placement = FreeCAD.Placement(
    FreeCAD.Vector(KILN_LENGTH_M + 0.5, 0, 0),
    FreeCAD.Rotation(0, 0, 0)
)
parts.append(preheater)

# 5. Girth gear (around shell, mid-kiln)
gear = doc.addObject("Part::Cylinder", "GirthGear")
gear.Radius = GEAR_OD_M / 2
gear.Height = GEAR_W_M
gear.Placement = FreeCAD.Placement(
    FreeCAD.Vector(KILN_LENGTH_M/2, 0, 0),
    FreeCAD.Rotation(FreeCAD.Vector(0, 0, 1), 90)
)
parts.append(gear)

# 6. Discharge end coupling (to cooler)
coupling = doc.addObject("Part::Box", "DischargeCoupling")
coupling.Length = 1.0; coupling.Width = KILN_DIAM_M + 0.5; coupling.Height = KILN_DIAM_M + 0.5
coupling.Placement = FreeCAD.Placement(
    FreeCAD.Vector(-0.5, -(KILN_DIAM_M+0.5)/2, 0),
    FreeCAD.Rotation(0, 0, 0)
)
parts.append(coupling)

FreeCAD.ActiveDocument.recompute()

# Export STEP
try:
    Import.export(parts, str(OUT_TMP).replace("\\", "/"))
    print("Kiln STEP export OK", file=sys.stderr)
except Exception as e:
    print(f"Kiln STEP export FAILED: {e}", file=sys.stderr)
    raise

# Rename
if OUT_TMP.exists() and OUT_TMP.stat().st_size > 0:
    if OUT_FINAL.exists():
        OUT_FINAL.unlink()
    OUT_TMP.rename(OUT_FINAL)
    size = OUT_FINAL.stat().st_size
else:
    size = 0
    OUT_FINAL = None

# Stats
bb_min_x = min(p.Shape.BoundBox.XMin for p in parts)
bb_max_x = max(p.Shape.BoundBox.XMax for p in parts)
bb_min_y = min(p.Shape.BoundBox.YMin for p in parts)
bb_max_y = max(p.Shape.BoundBox.YMax for p in parts)
bb_min_z = min(p.Shape.BoundBox.ZMin for p in parts)
bb_max_z = max(p.Shape.BoundBox.ZMax for p in parts)

result = {
    "ok": OUT_FINAL is not None,
    "output": str(OUT_FINAL) if OUT_FINAL else None,
    "size_bytes": size,
    "n_parts": len(parts),
    "bounding_box_mm": [
        round((bb_max_x - bb_min_x) * 1000, 1),
        round((bb_max_y - bb_min_y) * 1000, 1),
        round((bb_max_z - bb_min_z) * 1000, 1),
    ],
    "kiln_length_m": KILN_LENGTH_M,
    "kiln_diam_m": KILN_DIAM_M,
    "throughput_tpd": 5000,
    "n_tires": len(tire_positions),
    "n_rollers": 2 * len(tire_positions),
}
print(json.dumps(result, indent=2))
