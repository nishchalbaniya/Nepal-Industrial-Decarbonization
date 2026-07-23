"""
Day 12 demo -- write the cooler STEP file via FreeCAD.
Standalone script (no FreeCAD import path issues).
"""
import json
import os
import sys
import time
from pathlib import Path

# Must run inside FreeCAD
import FreeCAD
import Part
import Import

# NOTE: FreeCAD 1.1's CLI hijacks the first non-flag arg as a file
# to OPEN, so we look at sys.argv carefully. The actual command
# is:  FreeCADCmd 05_export_cooler_step.py  output.step  calib.json
# FreeCAD sees argv = [script, output.step, calib.json] AND
# simultaneously tries to open output.step. We work around by
# writing to a temp file inside the script, then renaming.

OUT_FINAL = Path("C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/05_cooler_v050_calibrated.step")
CALIB_PATH = Path("C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/json/01_calibration.json")
OUT_TMP = Path("C:/Users/TG/.mavis/workspace/nepal-decarb-build/demo-e2e/cad/05_cooler_v050_calibrated.tmp.step")
OUT_FINAL.parent.mkdir(parents=True, exist_ok=True)
if OUT_TMP.exists():
    OUT_TMP.unlink()

# Load calibration
with open(CALIB_PATH, encoding="utf-8") as f:
    cal = json.load(f)
posterior = cal.get("posterior", {})
L = float(posterior.get("grate_length_m", 32.797))
B = float(posterior.get("bed_depth_m", 0.78))
N = max(3, min(7, int(round(posterior.get("n_compartments", 6)))))
W = 3.5
H = 2.0
T_shell = 0.20
T_part = 0.05
T_grate = 0.08
D_sec = 1.0
D_exh = 0.8
D_kiln = 1.5

# Create doc
doc = FreeCAD.newDocument("CoolerAssembly")
FreeCAD.setActiveDocument(doc.Name)

parts = []

# 1. Outer shell (hollow box made of 6 plates)
shell = doc.addObject("Part::Box", "Shell")
shell.Length = L; shell.Width = W; shell.Height = H
shell.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0), FreeCAD.Rotation(0, 0, 0))
parts.append(shell)

# 2. Grate plate at the bottom
grate = doc.addObject("Part::Box", "Grate")
grate.Length = L; grate.Width = W; grate.Height = T_grate
grate.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, B), FreeCAD.Rotation(0, 0, 0))
parts.append(grate)

# 3. Compartment partitions (N-1 internal walls)
for i in range(1, N):
    p = doc.addObject("Part::Box", f"Partition_{i}")
    p.Length = T_part; p.Width = W; p.Height = H - B
    p.Placement = FreeCAD.Placement(FreeCAD.Vector((i * L / N) - T_part/2, 0, B), FreeCAD.Rotation(0, 0, 0))
    parts.append(p)

# 4. Sec-air duct (compartment 1, top)
sec = doc.addObject("Part::Cylinder", "SecAirDuct")
sec.Radius = D_sec/2; sec.Height = 1.5
sec.Placement = FreeCAD.Placement(FreeCAD.Vector(-1.0, W/2, H + 0.3), FreeCAD.Rotation(0, -90, 0))
parts.append(sec)

# 5. Exhaust duct (compartment N, side)
exh = doc.addObject("Part::Cylinder", "ExhaustDuct")
exh.Radius = D_exh/2; exh.Height = 1.5
exh.Placement = FreeCAD.Placement(FreeCAD.Vector(L + 0.3, W/2, B + 0.5), FreeCAD.Rotation(0, -90, 90))
parts.append(exh)

# 6. Kiln coupling
kc = doc.addObject("Part::Cylinder", "KilnCoupling")
kc.Radius = D_kiln/2; kc.Height = 1.0
kc.Placement = FreeCAD.Placement(FreeCAD.Vector(-0.5, W/2 - D_kiln/2, H - 0.1), FreeCAD.Rotation(0, -90, 0))
parts.append(kc)

# 7. Clinker discharge chute
chute = doc.addObject("Part::Box", "ClinkerDischargeChute")
chute.Length = 1.0; chute.Width = 1.2; chute.Height = B
chute.Placement = FreeCAD.Placement(FreeCAD.Vector(L, W/2 - 0.6, 0), FreeCAD.Rotation(0, 0, 0))
parts.append(chute)

# Recompute
FreeCAD.ActiveDocument.recompute()

# Fuse all
fused = doc.addObject("Part::MultiFuse", "CoolerAssemblyFused")
fused.Shapes = parts
FreeCAD.ActiveDocument.recompute()

# Export STEP
try:
    Import.export([fused], str(OUT_TMP).replace("\\", "/"))
    print("STEP export OK (fused)", file=sys.stderr)
except Exception as e:
    print(f"STEP export fused FAILED: {e}", file=sys.stderr)
    Import.export(parts, str(OUT_TMP).replace("\\", "/"))
    print("STEP export OK (unfused)", file=sys.stderr)

# Rename
if OUT_TMP.exists() and OUT_TMP.stat().st_size > 0:
    if OUT_FINAL.exists():
        OUT_FINAL.unlink()
    OUT_TMP.rename(OUT_FINAL)
    size = OUT_FINAL.stat().st_size
    OUT = OUT_FINAL
else:
    size = 0
    OUT = None
bb = fused.Shape.BoundBox
result = {
    "ok": OUT is not None,
    "output": str(OUT) if OUT else None,
    "size_bytes": size,
    "n_parts": len(parts),
    "n_faces": len(fused.Shape.Faces),
    "bounding_box_mm": [
        round(bb.XLength * 1000, 1),
        round(bb.YLength * 1000, 1),
        round(bb.ZLength * 1000, 1),
    ],
    "calibration_posterior": posterior,
    "n_compartments_used": N,
    "grate_length_m": L,
    "bed_depth_m": B,
}
print(json.dumps(result, indent=2, default=str))
