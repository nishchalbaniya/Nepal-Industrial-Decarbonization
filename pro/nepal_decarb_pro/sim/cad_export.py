"""
CAD/parametric output — DXF and FreeCAD macros.

Generates 2D CAD drawings of major equipment for fabrication and engineering.
Outputs:
  - DXF (AutoCAD R12) — universally readable
  - FreeCAD Python macro — parametric 3D models
  - SVG — web viewable

These are useful for:
  - Pilot plant fabrication drawings
  - Modification/retrofit engineering
  - Stakeholder communication
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

from nepal_decarb_pro.sim.equipment_specs import Equipment, get_equipment


# ----------------------------------------------------------------------------
# DXF output (using simple text format if ezdxf not available)
# ----------------------------------------------------------------------------

def _write_minimal_dxf(entities: List[Dict], out_path: Path) -> Path:
    """
    Write a minimal DXF file (AutoCAD R12 format) without dependencies.
    entities: list of {"type": "LINE"|"CIRCLE"|"ARC", ...}
    """
    lines = [
        "0", "SECTION", "2", "ENTITIES",
    ]
    for e in entities:
        if e["type"] == "LINE":
            lines.extend([
                "0", "LINE",
                "8", "0",  # layer
                "10", str(e["x1"]), "20", str(e["y1"]), "30", "0",
                "11", str(e["x2"]), "21", str(e["y2"]), "31", "0",
            ])
        elif e["type"] == "CIRCLE":
            lines.extend([
                "0", "CIRCLE",
                "8", "0",
                "10", str(e["cx"]), "20", str(e["cy"]), "30", "0",
                "40", str(e["r"]),
            ])
        elif e["type"] == "ARC":
            lines.extend([
                "0", "ARC",
                "8", "0",
                "10", str(e["cx"]), "20", str(e["cy"]), "30", "0",
                "40", str(e["r"]),
                "50", str(e["start_angle"]), "51", str(e["end_angle"]),
            ])
        elif e["type"] == "TEXT":
            lines.extend([
                "0", "TEXT",
                "8", "0",
                "10", str(e["x"]), "20", str(e["y"]), "30", "0",
                "40", str(e.get("size", 5)),
                "1", e["text"],
            ])
    lines.extend(["0", "ENDSEC", "0", "EOF"])

    out_path.write_text("\n".join(lines))
    return out_path


def generate_dxf_kiln(equipment_id: str = "rotary_kiln_5000tpd", out_path: Path = None) -> Path:
    """
    Generate a 2D DXF drawing of a rotary kiln (side view + end view).
    """
    eq = get_equipment(equipment_id)
    L = eq.length_m
    D = eq.diameter_m
    R = D / 2.0

    entities: List[Dict] = []

    # Side view: tilted cylinder
    slope_deg = 3.5
    slope = math.tan(math.radians(slope_deg))
    # Two end-circles connected by tangent lines
    # Cylinder axis from (0,0) to (L, -L*slope)
    end1_x, end1_y = 0, 0
    end2_x, end2_y = L, -L * slope

    # Direction along axis
    dx = end2_x - end1_x
    dy = end2_y - end1_y
    L_axis = math.sqrt(dx**2 + dy**2)
    ux, uy = dx / L_axis, dy / L_axis
    # Perpendicular
    px, py = -uy, ux

    # Cylinder top line
    entities.append({
        "type": "LINE",
        "x1": end1_x + px * R, "y1": end1_y + py * R,
        "x2": end2_x + px * R, "y2": end2_y + py * R,
    })
    # Cylinder bottom line
    entities.append({
        "type": "LINE",
        "x1": end1_x - px * R, "y1": end1_y - py * R,
        "x2": end2_x - px * R, "y2": end2_y - py * R,
    })
    # End circles (in 2D, just the silhouette = lines)
    # First end (left): tangent lines already drawn; the actual end is curved but in 2D side view it's a line
    # Use a CIRCLE for end view reference
    entities.append({
        "type": "CIRCLE",
        "cx": end1_x, "cy": end1_y, "r": R,
    })
    entities.append({
        "type": "CIRCLE",
        "cx": end2_x, "cy": end2_y, "r": R,
    })

    # Center line (axis)
    entities.append({
        "type": "LINE",
        "x1": end1_x, "y1": end1_y,
        "x2": end2_x, "y2": end2_y,
    })

    # Annotations
    entities.append({"type": "TEXT", "x": L / 2 - 5, "y": R + 2, "text": f"{eq.name}"})
    entities.append({"type": "TEXT", "x": L / 2 - 5, "y": R + 0.5, "text": f"L={L}m, D={D}m"})
    entities.append({"type": "TEXT", "x": -2, "y": -3, "text": "Feed end"})
    entities.append({"type": "TEXT", "x": L + 1, "y": -L * slope - 3, "text": "Discharge end"})
    entities.append({"type": "TEXT", "x": L / 2 - 5, "y": -L * slope - R - 2, "text": f"Slope: {slope_deg}°"})
    entities.append({"type": "TEXT", "x": L / 2 - 5, "y": -L * slope - R - 3.5, "text": f"Power: {eq.power_kw:.0f} kW"})

    # Support rings (typical 2-3 supports)
    for i, x_pos in enumerate([0.15, 0.5, 0.85]):
        sx = end1_x + (end2_x - end1_x) * x_pos
        sy = end1_y + (end2_y - end1_y) * x_pos
        entities.append({
            "type": "CIRCLE", "cx": sx, "cy": sy, "r": R * 1.08,
        })

    if out_path is None:
        out_path = Path(f"reports/{equipment_id}.dxf")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    return _write_minimal_dxf(entities, out_path)


def generate_dxf_cyclone_preheater(out_path: Path = None) -> Path:
    """Generate a 2D DXF of a cyclone (used in preheater)."""
    entities: List[Dict] = []
    R = 4.0  # cyclone radius in m
    entities.append({"type": "CIRCLE", "cx": 0, "cy": 0, "r": R})
    # Inlet duct (rectangular)
    entities.append({
        "type": "LINE", "x1": -R, "y1": 1,
        "x2": R * 0.5, "y2": 1.5,
    })
    entities.append({
        "type": "LINE", "x1": -R, "y1": 1.5,
        "x2": R * 0.5, "y2": 2,
    })
    # Gas outlet (top)
    entities.append({
        "type": "LINE", "x1": -1.5, "y1": R,
        "x2": 1.5, "y2": R,
    })
    entities.append({
        "type": "LINE", "x1": -1.5, "y1": R + 0.5,
        "x2": 1.5, "y2": R + 0.5,
    })
    # Dust outlet (bottom)
    entities.append({
        "type": "LINE", "x1": -0.5, "y1": -R,
        "x2": 0.5, "y2": -R,
    })
    entities.append({
        "type": "LINE", "x1": -0.5, "y1": -R - 0.4,
        "x2": 0.5, "y2": -R - 0.4,
    })
    entities.append({"type": "TEXT", "x": -3, "y": R + 2, "text": "Cyclone (single stage, R=4m)"})
    entities.append({"type": "TEXT", "x": -3, "y": R + 1, "text": "Refractory-lined steel"})
    if out_path is None:
        out_path = Path("reports/cyclone_preheater.dxf")
    return _write_minimal_dxf(entities, Path(out_path))


def generate_equipment_2d(equipment_id: str, out_path: Path) -> Path:
    """Generate a 2D representation of any equipment."""
    eq = get_equipment(equipment_id)
    if "kiln" in equipment_id.lower() and "rotary" in equipment_id.lower():
        return generate_dxf_kiln(equipment_id, out_path)
    elif "cyclone" in equipment_id.lower():
        return generate_dxf_cyclone_preheater(out_path)
    elif "preheater" in equipment_id.lower():
        return generate_dxf_cyclone_preheater(out_path)
    else:
        # Generic — draw a rectangle representing the equipment
        entities = [
            {"type": "LINE", "x1": 0, "y1": 0, "x2": eq.length_m, "y2": 0},
            {"type": "LINE", "x1": eq.length_m, "y1": 0, "x2": eq.length_m, "y2": eq.diameter_m or 1.0},
            {"type": "LINE", "x1": eq.length_m, "y1": eq.diameter_m or 1.0, "x2": 0, "y2": eq.diameter_m or 1.0},
            {"type": "LINE", "x1": 0, "y1": eq.diameter_m or 1.0, "x2": 0, "y2": 0},
            {"type": "TEXT", "x": 0, "y": (eq.diameter_m or 1.0) + 0.5, "text": f"{eq.name}"},
            {"type": "TEXT", "x": 0, "y": (eq.diameter_m or 1.0) + 0.1, "text": f"L={eq.length_m}m, D={eq.diameter_m}m"},
        ]
        return _write_minimal_dxf(entities, out_path)


# ----------------------------------------------------------------------------
# FreeCAD macro
# ----------------------------------------------------------------------------

def generate_freecad_macro(
    equipment_id: str = "rotary_kiln_5000tpd",
    out_path: Path = None,
) -> Path:
    """
    Generate a FreeCAD Python macro for parametric 3D model.

    Usage: Open FreeCAD, Macro > Macros > Run, select this file.
    """
    eq = get_equipment(equipment_id)
    L = eq.length_m
    D = eq.diameter_m
    R = D / 2.0

    macro = f'''# FreeCAD Macro: Parametric model of {eq.name}
# Generated by nepal_decarb_pro v1.0
# Open in FreeCAD: Macro > Macros > Run this file

import FreeCAD
import Part
import Sketcher
import math

# Parameters (all in mm)
L = {L * 1000}        # length, converted from m
D = {D * 1000}        # diameter
R = D / 2
T = 50                 # shell thickness
slope_deg = 3.5
slope = math.tan(math.radians(slope_deg))

# Create a new document
doc = FreeCAD.newDocument("KilnModel")
FreeCAD.setActiveDocument("KilnModel")

# Outer cylinder (tilted)
# FreeCAD's Part.makeCylinder takes (radius, height, direction)
# We rotate the cylinder to be tilted
outer = Part.makeCylinder(R, L)
outer.rotate([0, 0, 0], [0, 1, 0], slope_deg)
outer.translate(FreeCAD.Vector(0, 0, 0))
Part.show(outer, "Kiln_Shell_Outer")

# Inner cylinder (refractory inside)
inner = Part.makeCylinder(R - T, L - 50)
inner.rotate([0, 0, 0], [0, 1, 0], slope_deg)
Part.show(inner, "Kiln_Shell_Inner")

# Subtract inner from outer to get hollow shell
shell = outer.cut(inner)
Part.show(shell, "Kiln_Shell")

# Refractory layer
ref_outer = Part.makeCylinder(R - 5, L - 25)
ref_outer.rotate([0, 0, 0], [0, 1, 0], slope_deg)
refractory = ref_outer.cut(Part.makeCylinder(R - T - 5, L - 25).rotate([0, 0, 0], [0, 1, 0], slope_deg))
Part.show(refractory, "Refractory_Lining")

# Tires (riding rings) — 2 supports
for i, x_pos in enumerate([0.15, 0.85]):
    x = L * x_pos
    tire = Part.makeCylinder(R * 1.08, 200)
    tire.rotate([0, 0, 0], [0, 1, 0], slope_deg)
    tire.translate(FreeCAD.Vector(x, 0, 0))
    Part.show(tire, f"Tire_{{i+1}}")

# Recompute
doc.recompute()
FreeCAD.Gui.SendMsgToActiveView("ViewFit")
FreeCAD.Console.PrintMessage("Kiln model generated.\\nL = {{}} m\\nD = {{}} m\\n".format({L}, {D}))
'''
    if out_path is None:
        out_path = Path(f"reports/{equipment_id}.FCMacro")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(macro)
    return out_path


# ----------------------------------------------------------------------------
# SVG output (web-viewable)
# ----------------------------------------------------------------------------

def generate_svg_kiln(equipment_id: str = "rotary_kiln_5000tpd", out_path: Path = None) -> Path:
    """Generate an SVG of the rotary kiln (web viewable)."""
    eq = get_equipment(equipment_id)
    L = eq.length_m
    D = eq.diameter_m
    R = D / 2.0
    slope = math.tan(math.radians(3.5))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="-10 -8 {L + 20} {L*slope + D + 16}" font-family="sans-serif">
  <defs>
    <linearGradient id="kilnGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#FFB6C1;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#FF6347;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect x="-10" y="-8" width="{L + 20}" height="{L*slope + D + 16}" fill="white" stroke="none"/>
  <!-- Kiln body (tilted) -->
  <g transform="translate(0, 0)">
    <ellipse cx="0" cy="0" rx="{R}" ry="{R}" fill="url(#kilnGrad)" stroke="black" stroke-width="2"/>
    <ellipse cx="{L}" cy="{-L*slope}" rx="{R}" ry="{R}" fill="url(#kilnGrad)" stroke="black" stroke-width="2"/>
    <line x1="0" y1="{-R}" x2="{L}" y2="{-L*slope - R}" stroke="black" stroke-width="2"/>
    <line x1="0" y1="{R}" x2="{L}" y2="{-L*slope + R}" stroke="black" stroke-width="2"/>
    <line x1="0" y1="0" x2="{L}" y2="{-L*slope}" stroke="black" stroke-width="1" stroke-dasharray="5,5"/>
    <!-- Tires -->
    <ellipse cx="{L*0.15}" cy="{-L*slope*0.15}" rx="{R*1.08}" ry="{R*1.08}" fill="none" stroke="black" stroke-width="2"/>
    <ellipse cx="{L*0.85}" cy="{-L*slope*0.85}" rx="{R*1.08}" ry="{R*1.08}" fill="none" stroke="black" stroke-width="2"/>
  </g>
  <!-- Annotations -->
  <text x="{L/2 - 5}" y="{-L*slope - R - 3}" font-size="14" font-weight="bold">{eq.name}</text>
  <text x="{L/2 - 5}" y="{-L*slope - R - 1.5}" font-size="10">L = {L} m, D = {D} m</text>
  <text x="{L/2 - 5}" y="{-L*slope - R - 0.3}" font-size="10">Slope 3.5° | Power {eq.power_kw:.0f} kW</text>
  <text x="-9" y="{R + 1}" font-size="9" fill="gray">Feed end</text>
  <text x="{L + 1}" y="{-L*slope + R - 1}" font-size="9" fill="gray">Discharge end</text>
  <!-- Title -->
  <text x="{L/2 - 6}" y="{-L*slope - R - 5}" font-size="16" font-weight="bold">Rotary Kiln — Side View</text>
  <text x="{L/2 - 6}" y="{-L*slope - R - 4}" font-size="9" fill="gray">nepal_decarb_pro v1.0</text>
</svg>'''
    if out_path is None:
        out_path = Path(f"reports/{equipment_id}.svg")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(svg)
    return out_path
