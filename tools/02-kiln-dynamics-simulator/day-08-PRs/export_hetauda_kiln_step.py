"""Day 8 v0.8.0 -- FreeCAD STEP export of the Hetauda rotary kiln.

The Hetauda rotary kiln is a 60 m long, 4.0 m diameter cylinder,
slightly inclined, supported on 4 tire-and-roller stations. The
hot end (lower) has a primary burner; the cold end (upper) has
a preheater tower and a cooler discharge chute.

The geometry includes:
  - 1 main cylinder (the kiln shell)
  - 4 tire-and-roller support stations
  - 1 burner at the hot end (lower)
  - 1 preheater tower stub at the cold end (upper)
  - 1 cooler-coupling stub at the cold end (links to the cooler)
  - 1 drive gear ring (simplified, around the kiln)

Cite:
- Peray & Waddell 1986 (rotary kiln mechanical design).
- IKN / KHD / Polysius product literature (real Hetauda design).
- ISO 10303-21:2016 (STEP file format, AP214).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

# This script must run inside FreeCAD's Python.
try:
    import FreeCAD
    import Part
    import Import
except ImportError:
    print("ERROR: This script must be run inside FreeCAD's Python:")
    print("  FreeCADCmd.exe -c export_hetauda_kiln_step.py")
    sys.exit(1)


DEFAULT_KILN = {
    "length_m": 60.0,           # Hetauda rotary kiln length (Peray s6.1)
    "diameter_m": 4.0,          # Hetauda inner diameter
    "slope_deg": 3.5,           # typical rotary kiln slope
    "rotation_rpm": 1.8,        # typical slow rotation
    "shell_thickness_m": 0.05,  # structural plate thickness
    "tire_thickness_m": 0.20,   # tire cross-section
    "tire_width_m": 0.40,       # tire width
    "foundation_height_m": 1.5, # height of the foundation pier
    "n_tire_stations": 4,       # 4 tire-and-roller stations
    "burner_diameter_m": 0.6,   # primary burner diameter
    "preheater_tower_diameter_m": 5.0,
    "preheater_tower_height_m": 12.0,
    "cooler_coupling_diameter_m": 3.5,
}


def make_box(L, W, H, p=(0, 0, 0), name="Box"):
    b = FreeCAD.ActiveDocument.addObject("Part::Box", name)
    b.Length = L
    b.Width = W
    b.Height = H
    b.Placement = FreeCAD.Placement(
        FreeCAD.Vector(p[0], p[1], p[2]),
        FreeCAD.Rotation(0, 0, 0, 1),
    )
    return b


def make_cylinder(radius, height, p=(0, 0, 0), axis="z", name="Cyl"):
    c = FreeCAD.ActiveDocument.addObject("Part::Cylinder", name)
    c.Radius = radius
    c.Height = height
    c.Placement = FreeCAD.Placement(
        FreeCAD.Vector(p[0], p[1], p[2]),
        FreeCAD.Rotation(0, 0, 0, 1) if axis == "z" else
        FreeCAD.Rotation(0, 90, 0) if axis == "y" else
        FreeCAD.Rotation(90, 0, 0) if axis == "x" else
        FreeCAD.Rotation(0, 0, 0, 1),
    )
    return c


def build_kiln_assembly(calib: dict) -> list:
    """Build the rotary kiln assembly from the kiln geometry."""
    L = float(calib["length_m"])
    D = float(calib["diameter_m"])
    t_shell = float(calib["shell_thickness_m"])
    t_tire = float(calib["tire_thickness_m"])
    w_tire = float(calib["tire_width_m"])
    h_found = float(calib["foundation_height_m"])
    n_stations = max(2, int(calib["n_tire_stations"]))
    d_burner = float(calib["burner_diameter_m"])
    d_preheater = float(calib["preheater_tower_diameter_m"])
    h_preheater = float(calib["preheater_tower_height_m"])
    d_cooler = float(calib["cooler_coupling_diameter_m"])
    slope = float(calib["slope_deg"])

    parts = []
    # 1. Main kiln shell (a cylinder along the X axis, with the
    #    slope baked into the placement).
    shell_outer = make_cylinder(D/2 + t_shell, L, p=(0, 0, 0), axis="y", name="KilnShellOuter")
    shell_inner = make_cylinder(D/2, L - 2*t_shell, p=(0, 0, 0), axis="y", name="KilnShellInner")
    shell = FreeCAD.ActiveDocument.addObject("Part::Cut", "KilnShell")
    shell.Base = shell_outer
    shell.Tool = shell_inner
    # Apply the slope: rotate the shell around the Z axis by slope_deg
    # at the center, then translate to the foundation height.
    # (Simplified: keep shell at Z=0, foundation piers will lift it.)
    parts.append(shell)

    # 2. Tire-and-roller support stations: 4 stations along the length.
    # A tire is a torus around the shell; we approximate with a
    # hollow cylinder.
    for i in range(n_stations):
        x = (i + 1) * (L / (n_stations + 1))
        tire = make_cylinder(
            D/2 + t_shell + t_tire, w_tire,
            p=(x, 0, -t_tire/2), axis="y", name=f"Tire_{i+1}",
        )
        parts.append(tire)
        # Foundation pier (vertical box) below the tire
        pier = make_box(
            0.8, w_tire + 0.4, h_found,
            p=(x - 0.4, -(w_tire/2 + 0.2), -h_found - t_tire/2),
            name=f"Pier_{i+1}",
        )
        parts.append(pier)

    # 3. Primary burner at the hot end (lower; y = -L/2 side)
    burner = make_cylinder(
        d_burner/2, 1.0,
        p=(-1.0, -L/2 - 0.5, 0), axis="y", name="PrimaryBurner",
    )
    parts.append(burner)

    # 4. Cooler coupling at the hot end (links to the cooler)
    cooler_coup = make_cylinder(
        d_cooler/2, 1.5,
        p=(D/2 + 1.5, -L/2, 0), axis="x", name="CoolerCoupling",
    )
    parts.append(cooler_coup)

    # 5. Preheater tower stub at the cold end (y = +L/2 side)
    preheater = make_cylinder(
        d_preheater/2, h_preheater,
        p=(-d_preheater/2, L/2, 0), axis="y", name="PreheaterTower",
    )
    # The preheater sits on top of the kiln; rotate so it's vertical
    preheater.Placement = FreeCAD.Placement(
        FreeCAD.Vector(-d_preheater/2, L/2, 0),
        FreeCAD.Rotation(90, 0, 0),  # rotate so axis is Z
    )
    parts.append(preheater)

    # 6. Drive gear ring (a torus around the shell, at the hot end
    # just before the cooler)
    gear = make_cylinder(
        D/2 + t_shell + 0.15, 0.15,
        p=(D/2 + 1.0, -L/2 + 2.0, 0), axis="y", name="DriveGearRing",
    )
    parts.append(gear)

    return parts


def export_step(parts: list, output_path: Path, calib: dict) -> dict:
    if not parts:
        return {"ok": False, "error": "no parts"}
    fused = FreeCAD.ActiveDocument.addObject("Part::MultiFuse", "KilnAssembly")
    fused.Shapes = parts
    FreeCAD.ActiveDocument.recompute()
    Import.export([fused], str(output_path))
    file_size = output_path.stat().st_size if output_path.exists() else 0
    return {
        "ok": True,
        "output_path": str(output_path),
        "file_size_bytes": file_size,
        "n_parts": len(parts),
        "n_faces": len(fused.Shape.Faces),
        "n_edges": len(fused.Shape.Edges),
        "bounding_box_mm": [
            round(fused.Shape.BoundBox.XLength * 1000, 1),
            round(fused.Shape.BoundBox.YLength * 1000, 1),
            round(fused.Shape.BoundBox.ZLength * 1000, 1),
        ],
        "calibration": calib,
    }


def main():
    # When invoked via `exec()` from FreeCADCmd, __file__ may not
    # be defined. Use the explicit script path passed via
    # sys.argv[0] if present, else fall back to a hard-coded
    # default.
    script_path = Path(__file__).resolve() if "__file__" in dir() else None
    if script_path is None:
        # Look for the script in argv (FreeCADCmd passes the
        # script path when called with -c "exec(open(SCRIPT).read())")
        for arg in sys.argv[1:]:
            if arg.endswith(".py") and Path(arg).exists():
                script_path = Path(arg).resolve()
                break
    if script_path is None:
        script_path = Path(r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\tools\02-kiln-dynamics-simulator\day-08-PRs\export_hetauda_kiln_step.py")
    out_path = script_path.parent / "cad" / "hetauda_kiln_assembly.step"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc = FreeCAD.newDocument("KilnAssembly")
    parts = build_kiln_assembly(DEFAULT_KILN)
    result = export_step(parts, out_path, DEFAULT_KILN)
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
