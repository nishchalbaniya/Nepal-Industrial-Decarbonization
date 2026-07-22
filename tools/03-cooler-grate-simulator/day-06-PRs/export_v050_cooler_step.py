"""Day 6 v0.6.0 -- FreeCAD STEP export of the v0.5.0 calibrated cooler.

Takes the v0.5.0 calibrated CoolerParameters (grate_length, bed_depth,
n_compartments, etc.) and produces a real 3D STEP file (.step) that
can be opened in FreeCAD, Onshape, Fusion 360, or any STEP-compliant
CAD viewer.

The geometry is a simplified 1D-compartment model rendered as 3D
geometry, with:
  - 1 main cooler housing (a rectangular box for the grate + air
    plenums)
  - N compartment partitions (vertical plates dividing the housing
    into N compartments)
  - 1 sec-air duct stub (at the kiln-end, compartment 1)
  - 1 exhaust duct stub (at the cold-end, compartment N)
  - 1 kiln-discharge coupling face (at the hot end)
  - 1 clinker-discharge chute (at the cold end)
  - 1 grate (slotted plate at the bed depth, full length)
  - Bed material indicator (the clinker layer between grate and
    top of housing) -- not a solid, just a visual hint

Cites:
- ISO 10303-21:2016 (STEP AP214 file format).
- ISA-5.1 (instrument symbols and identification).
- Peray & Waddell (1986) s6.4 (cooler geometry conventions).
- IKN Pyrorotor / KHD Pyrostep / Polysius REPOL product literature
  (the real cooler geometries this approximates).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

# This script must run inside FreeCAD's Python (FreeCADCmd.exe -c).
# We import FreeCAD lazily so the file can be syntax-checked without
# FreeCAD installed.
try:
    import FreeCAD
    import Part
    import Import
except ImportError:
    print("ERROR: This script must be run inside FreeCAD's Python:")
    print("  C:\\Users\\TG\\AppData\\Local\\Programs\\FreeCAD 1.1\\bin\\FreeCADCmd.exe -c export_v050_cooler_step.py -- <calibration.json>")
    sys.exit(1)


# ---------------------------------------------------------------------------
# v0.5.0 calibrated posterior (default; can be overridden by -- <json>)
# ---------------------------------------------------------------------------
DEFAULT_CALIBRATION = {
    "grate_length_m": 32.797,
    "bed_depth_m": 0.78,
    "n_compartments": 6,
    "grate_speed_m_min": 9.7,
    "under_grate_air_velocity_m_s": 4.0,
    "coal_rate_kg_s": 2.5,
    "secondary_air_excess_factor": 1.59,
    "emissivity": 0.95,
    "void_fraction": 0.55,
    "recuperator_preheat_c": 90.0,
    "clinker_throughput_t_h": 130.0,
    "clinker_inlet_t_c": 1400.0,
    "altitude_m": 1400.0,
}

# Other engineering defaults (not calibrated; Hetauda site)
SITE_DEFAULTS = dict(
    width_m=3.5,                 # grate width
    shell_height_m=2.0,           # total cooler housing height
    shell_thickness_m=0.20,        # structural plate thickness
    partition_thickness_m=0.05,    # compartment partition thickness
    sec_air_duct_diameter_m=1.0,   # sec-air duct at compartment 1
    exhaust_duct_diameter_m=0.8,   # exhaust duct at compartment N
    kiln_coupling_diameter_m=1.5,   # rotary kiln discharge coupling
    clinker_chute_width_m=1.2,     # clinker discharge chute width
    grate_plate_thickness_m=0.08,  # grate plate thickness
)


def make_box(L, W, H, p=(0, 0, 0), name="Box"):
    """Create a box primitive at position p with size (L, W, H)."""
    b = FreeCAD.ActiveDocument.addObject("Part::Box", name)
    b.Length = L
    b.Width = W
    b.Height = H
    b.Placement = FreeCAD.Placement(
        FreeCAD.Vector(p[0], p[1], p[2]),
        FreeCAD.Rotation(0, 0, 0, 1),
    )
    return b


def make_cylinder(radius, height, axis="z", p=(0, 0, 0), name="Cyl"):
    """Create a cylinder primitive."""
    c = FreeCAD.ActiveDocument.addObject("Part::Cylinder", name)
    c.Radius = radius
    c.Height = height
    c.Placement = FreeCAD.Placement(
        FreeCAD.Vector(p[0], p[1], p[2]),
        FreeCAD.Rotation(0, 0, 0, 1) if axis == "z" else
        FreeCAD.Rotation(0, 0, 0, 1),
    )
    return c


def build_cooler_assembly(calib: dict, site: dict) -> list:
    """Build the cooler assembly from the calibrated geometry.

    Coordinate system:
      - X axis: grate travel (kiln end at X=0, cold end at X=L)
      - Y axis: grate width (Y=0 to Y=W)
      - Z axis: vertical (Z=0 at the grate level, Z=H at the top)
    """
    L = float(calib["grate_length_m"])
    W = float(site["width_m"])
    H = float(site["shell_height_m"])
    H_bed = float(calib["bed_depth_m"])
    n = max(1, int(round(calib["n_compartments"])))
    th_shell = float(site["shell_thickness_m"])
    th_part = float(site["partition_thickness_m"])
    th_grate = float(site["grate_plate_thickness_m"])
    D_sec = float(site["sec_air_duct_diameter_m"])
    D_exh = float(site["exhaust_duct_diameter_m"])
    D_kiln = float(site["kiln_coupling_diameter_m"])
    W_chute = float(site["clinker_chute_width_m"])

    parts = []

    # 1. Main cooler housing (outer shell, hollowed out by inner shell)
    outer = make_box(L + 2 * th_shell, W + 2 * th_shell, H + th_shell,
                     p=(-th_shell, -th_shell, 0), name="CoolerOuter")
    inner = make_box(L, W, H, p=(0, 0, th_shell), name="CoolerInner")
    shell = FreeCAD.ActiveDocument.addObject("Part::Cut", "CoolerShell")
    shell.Base = outer
    shell.Tool = inner
    parts.append(shell)

    # 2. Grate plate (slotted, at Z = H_bed - th_grate)
    grate = make_box(L, W, th_grate, p=(0, 0, H_bed - th_grate), name="GratePlate")
    parts.append(grate)

    # 3. N compartment partitions (vertical plates, perpendicular to X axis)
    for i in range(1, n):
        x = i * (L / n)
        part = make_box(th_part, W, H - H_bed,
                        p=(x - th_part/2, 0, H_bed), name=f"Partition_{i}")
        parts.append(part)

    # 4. Sec-air duct stub (at compartment 1, kiln end)
    # A horizontal cylinder entering the housing at the top, at X=0
    sec_air_duct = make_cylinder(
        D_sec / 2, 1.5,
        p=(-1.0, W/2, H + 0.3),
        name="SecAirDuctStub",
    )
    # Rotate to be horizontal (Y axis)
    sec_air_duct.Placement = FreeCAD.Placement(
        FreeCAD.Vector(-1.0, W/2, H + 0.3),
        FreeCAD.Rotation(0, -90, 0),
    )
    parts.append(sec_air_duct)

    # 5. Exhaust duct stub (at compartment N, cold end)
    exh_duct = make_cylinder(
        D_exh / 2, 1.5,
        p=(L + 0.3, W/2, H_bed + 0.5),
        name="ExhaustDuctStub",
    )
    exh_duct.Placement = FreeCAD.Placement(
        FreeCAD.Vector(L + 0.3, W/2, H_bed + 0.5),
        FreeCAD.Rotation(0, -90, 90),
    )
    parts.append(exh_duct)

    # 6. Kiln-discharge coupling (at X=0, vertical)
    kiln_coup = make_cylinder(
        D_kiln / 2, 1.0,
        p=(-1.0, W/2 - D_kiln/2, H - 0.1),
        name="KilnCoupling",
    )
    kiln_coup.Placement = FreeCAD.Placement(
        FreeCAD.Vector(-0.5, W/2 - D_kiln/2, H - 0.1),
        FreeCAD.Rotation(0, -90, 0),
    )
    parts.append(kiln_coup)

    # 7. Clinker-discharge chute (at X=L, vertical)
    chute = make_box(1.0, W_chute, H_bed,
                    p=(L, W/2 - W_chute/2, 0), name="ClinkerDischargeChute")
    parts.append(chute)

    # 8. Compartment labels (cosmetic; FreeCAD can also render the
    #    labels as DatumLabel objects, but for STEP export they're
    #    not visible — just included for the part tree)
    for i in range(n):
        x = (i + 0.5) * (L / n)
        # Skip actual geometry; just metadata.

    return parts


def export_step(parts: list, output_path: Path, calib: dict) -> dict:
    """Fuse all parts into a single shape and export as STEP."""
    if not parts:
        return {"ok": False, "error": "no parts"}

    # Fuse
    fused = FreeCAD.ActiveDocument.addObject("Part::MultiFuse", "CoolerAssembly")
    fused.Shapes = parts
    FreeCAD.ActiveDocument.recompute()

    # Export as STEP
    Import.export([fused], str(output_path))

    # Compute file size
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
    """Main entry point for FreeCAD -c invocation."""
    import argparse
    parser = argparse.ArgumentParser(description="Export v0.5.0 cooler as STEP")
    parser.add_argument("--calibration", type=str, default=None,
                        help="Path to calibration JSON; default uses DEFAULT_CALIBRATION")
    parser.add_argument("--output", type=str, default=None,
                        help="Output .step path; default: <repo>/cad/v050_cooler.step")
    args = parser.parse_args()

    # Load calibration
    if args.calibration and Path(args.calibration).exists():
        with open(args.calibration, encoding="utf-8") as f:
            calib = json.load(f)["posterior"]
    else:
        calib = DEFAULT_CALIBRATION

    # Output path
    if args.output:
        out_path = Path(args.output)
    else:
        out_path = Path(__file__).parent.parent / "cad" / "v050_cooler_assembly.step"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Create a fresh document
    doc = FreeCAD.newDocument("CoolerAssembly")
    parts = build_cooler_assembly(calib, SITE_DEFAULTS)
    result = export_step(parts, out_path, calib)

    # FreeCADGui isn't available in FreeCADCmd; just print summary
    print(json.dumps(result, indent=2, default=str))
    return result


if __name__ == "__main__":
    main()
