"""Day 9 v0.9.0 -- FreeCAD P&ID export of the v0.5.0 calibrated cooler.

A P&ID (Piping & Instrumentation Diagram) is the standard
engineering schematic for process control. It shows:
  - The process equipment (the cooler housing) as a simple
    box / outline
  - The process streams (clinker inlet, sec-air outlet, exhaust
    outlet, clinker outlet) as labelled arrows
  - The instrumentation (TI, PI, FT, FI tags) per ISA-5.1

The PlantA cooler P&ID includes:
  - 1 cooler housing (outline only)
  - 4 process streams with arrows and labels:
    - Clinker inlet (from kiln, ~1400 C)
    - Secondary air outlet (to kiln, ~715 C)
    - Tertiary air outlet (to calciner)
    - Exhaust air outlet (to dust collector / WHR)
    - Clinker outlet (to cement mill, ~150 C target)
  - 8 instrument loops per ISA-5.1:
    - TI-1101: sec-air T (Type-K TC at sec-air duct)
    - TI-1102: tert-air T (Type-K TC at tert-air duct)
    - TI-1103: exhaust T (TC in exhaust plenum)
    - TI-1104: clinker out T (IR spot pyrometer at cooler exit)
    - TI-1105: ambient T (met station)
    - PI-1101: cooler bed dP (delta-P transmitter)
    - FT-1101: sec-air flow (annubar)
    - SC-1101: grate speed (VFD Hz)

Output: an SVG file that renders the P&ID cleanly in any
browser, AND a FreeCAD document for the formal engineering
deliverable.

Cite:
- ISA-5.1-2009 (Instrumentation Symbols and Identification).
- ISA-5.3-1983 (Instrument Tag Conventions).
- Peray & Waddell 1986 s6.4 (cooler process streams and
  instrument conventions).
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
except ImportError:
    print("ERROR: This script must be run inside FreeCAD's Python.")
    sys.exit(1)


# ISA-5.1 instrument symbol mapping (text-based for SVG)
INSTRUMENT_SYMBOLS = {
    "TI": "circle",   # temperature indicator
    "PI": "circle",   # pressure indicator
    "FT": "circle",   # flow transmitter
    "FI": "circle",   # flow indicator
    "SC": "circle",   # speed controller
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


def build_pid_geometry() -> list:
    """Build the P&ID geometry. The P&ID is a 2D schematic on the
    X-Y plane; we build it in FreeCAD as thin extruded boxes for
    visual reference, then ALSO generate an SVG (separate path)
    for browser-friendly rendering.

    The P&ID's "geometry" is just labels and arrows on a canvas.
    The 3D FreeCAD representation is a thin (1 mm thick) base
    plate with the instrument tags as small raised boxes.

    Returns: list of FreeCAD objects.
    """
    parts = []
    # 1. Canvas (a thin base plate, 800 mm x 500 mm)
    canvas = make_box(800, 500, 1, p=(-400, -250, 0), name="PidCanvas")
    parts.append(canvas)

    # 2. Cooler housing outline (a 200 mm x 80 mm box, centered)
    housing = make_box(200, 80, 5, p=(-100, -40, 1), name="CoolerHousing")
    parts.append(housing)

    # 3. Process stream stubs (small cylinders representing pipes)
    # Clinker inlet (top-left, from kiln, 1400 C)
    inlet = make_box(10, 30, 3, p=(-200, -25, 1), name="ClinkerInlet")
    parts.append(inlet)
    # Sec-air outlet (top-right, to kiln, 715 C)
    sec_out = make_box(10, 30, 3, p=(200, -25, 1), name="SecAirOutlet")
    parts.append(sec_out)
    # Tert-air outlet (right, to calciner)
    tert_out = make_box(10, 30, 3, p=(250, 0, 1), name="TertAirOutlet")
    parts.append(tert_out)
    # Exhaust outlet (bottom-right, to dust collector)
    exh_out = make_box(10, 30, 3, p=(200, 25, 1), name="ExhaustOutlet")
    parts.append(exh_out)
    # Clinker outlet (bottom, to cement mill, 150 C target)
    cli_out = make_box(30, 10, 3, p=(-15, -200, 1), name="ClinkerOutlet")
    parts.append(cli_out)

    return parts


def render_svg(pid_data: dict, out_path: Path) -> str:
    """Render the P&ID as an SVG file. Pure Python, no FreeCAD needed
    for the SVG output -- this is the browser-friendly version.

    ISA-5.1 instrument tags: a circle (8 mm radius) with the
    tag letters (TI, PI, FT, etc.) inside, connected to a
    process pipe with a thin bubble line.
    """
    W, H = 1000, 700  # SVG canvas in mm (scaled at print time)
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W*3}" height="{H*3}" font-family="Arial, sans-serif" font-size="11">',
        '  <rect width="100%" height="100%" fill="#fafaf7"/>',
        '  <style>',
        '    .title { font-size: 18px; font-weight: bold; }',
        '    .stream { stroke: #1c1c1c; stroke-width: 2; fill: none; }',
        '    .arrow { fill: #1c1c1c; }',
        '    .label { font-size: 12px; fill: #1c1c1c; }',
        '    .label-small { font-size: 9px; fill: #555; }',
        '    .instrument { fill: white; stroke: #1c1c1c; stroke-width: 1.5; }',
        '    .instrument-text { font-size: 9px; text-anchor: middle; dominant-baseline: middle; }',
        '    .housing { fill: #e8e0d0; stroke: #1c1c1c; stroke-width: 1.5; }',
        '    .grid { stroke: #ddd; stroke-width: 0.3; }',
        '  </style>',
        # Title block
        '  <rect x="20" y="20" width="960" height="50" fill="white" stroke="#1c1c1c" stroke-width="1"/>',
        '  <text x="40" y="50" class="title">PlantA Industries Ltd. &mdash; Clinker Cooler P&amp;ID</text>',
        '  <text x="800" y="50" class="label-small">Drawing: NIDC-CLR-PID-001 Rev A</text>',
        '  <text x="40" y="65" class="label-small">v0.5.0 calibrated (Day 5 ship, commit 2aa918c)</text>',
        '  <text x="800" y="65" class="label-small">Date: 2026-07-22</text>',
        # Grid
        '  <g class="grid">',
    ]
    # Grid lines (10 mm spacing)
    for x in range(0, W + 1, 50):
        svg.append(f'    <line x1="{x}" y1="80" x2="{x}" y2="{H-20}"/>')
    for y in range(80, H + 1, 50):
        svg.append(f'    <line x1="0" y1="{y}" x2="{W}" y2="{y}"/>')
    svg.append('  </g>')

    # Cooler housing
    cx, cy = W / 2, H / 2
    svg.append(f'  <rect x="{cx-150}" y="{cy-50}" width="300" height="100" class="housing"/>')
    svg.append(f'  <text x="{cx}" y="{cy-30}" class="label" text-anchor="middle">CLINKER COOLER</text>')
    svg.append(f'  <text x="{cx}" y="{cy-12}" class="label-small" text-anchor="middle">5 compartments, 32.8 m grate, 0.78 m bed</text>')
    svg.append(f'  <text x="{cx}" y="{cy+5}" class="label-small" text-anchor="middle">130 t/h clinker, 1400 m altitude</text>')
    svg.append(f'  <text x="{cx}" y="{cy+22}" class="label-small" text-anchor="middle">PlantA, Nepal</text>')

    # Process streams (ISA-5.1 style: thick line + arrow + label)
    # 1. Clinker inlet (top-left, from kiln, 1400 C)
    svg.append(f'  <line x1="{cx-300}" y1="{cy-100}" x2="{cx-150}" y2="{cy-100}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx-225}" y="{cy-110}" class="label" text-anchor="middle">Clinker in (kiln discharge)</text>')
    svg.append(f'  <text x="{cx-225}" y="{cy-95}" class="label-small" text-anchor="middle">1400 °C, 36 kg/s</text>')

    # 2. Sec-air outlet (top-right, to kiln, 715 C)
    svg.append(f'  <line x1="{cx+150}" y1="{cy-100}" x2="{cx+300}" y2="{cy-100}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx+225}" y="{cy-110}" class="label" text-anchor="middle">Sec air out (to kiln burner)</text>')
    svg.append(f'  <text x="{cx+225}" y="{cy-95}" class="label-small" text-anchor="middle">715 °C, 26 kg/s</text>')

    # 3. Tert-air outlet (right, to calciner)
    svg.append(f'  <line x1="{cx+150}" y1="{cy-25}" x2="{cx+300}" y2="{cy-25}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx+225}" y="{cy-35}" class="label" text-anchor="middle">Tert air out (to calciner)</text>')
    svg.append(f'  <text x="{cx+225}" y="{cy-12}" class="label-small" text-anchor="middle">190 °C, 80 kg/s</text>')

    # 4. Exhaust outlet (right, to dust collector / WHR)
    svg.append(f'  <line x1="{cx+150}" y1="{cy+25}" x2="{cx+300}" y2="{cy+25}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx+225}" y="{cy+15}" class="label" text-anchor="middle">Exhaust out (to dust coll.)</text>')
    svg.append(f'  <text x="{cx+225}" y="{cy+38}" class="label-small" text-anchor="middle">149 °C, 53 kg/s</text>')

    # 5. Clinker outlet (bottom, to cement mill)
    svg.append(f'  <line x1="{cx}" y1="{cy+50}" x2="{cx}" y2="{cy+200}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx+10}" y="{cy+125}" class="label">Clinker out (to cement mill)</text>')
    svg.append(f'  <text x="{cx+10}" y="{cy+140}" class="label-small">351 °C, 36 kg/s (target 150 °C; v0.5.0 model)</text>')

    # 6. Under-grate air inlet (top, from primary air fan)
    svg.append(f'  <line x1="{cx}" y1="{cy-200}" x2="{cx}" y2="{cy-50}" class="stream" marker-end="url(#arrow)"/>')
    svg.append(f'  <text x="{cx+10}" y="{cy-180}" class="label">Under-grate air in (from PA fan)</text>')
    svg.append(f'  <text x="{cx+10}" y="{cy-165}" class="label-small">120 °C (recuperator preheat), 159 kg/s</text>')

    # Arrow marker definition
    svg.insert(2, '''  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" class="arrow"/>
    </marker>
  </defs>''')

    # Instrumentation (ISA-5.1 circles)
    # Define instrument positions
    instruments = [
        # (tag, x, y, label, full_loop_desc)
        ("TI-1101", cx+150, cy-100, "Sec air T", "Type-K TC, ±20 K at 800 °C"),
        ("TI-1102", cx+150, cy-25,  "Tert air T", "Type-K TC, ±20 K at 600 °C"),
        ("TI-1103", cx+150, cy+25,  "Exhaust T", "TC in plenum, ±10 K at 200 °C"),
        ("TI-1104", cx-30,  cy+200, "Clinker out T", "IR spot pyrometer, ±15 K at 200 °C"),
        ("TI-1105", cx+250, cy-180, "Ambient T", "PT100 RTD met station, ±2 K"),
        ("PI-1101", cx-150, cy-50,  "Bed dP", "Δ-P transmitter, ±0.5% span"),
        ("FT-1101", cx+150, cy-150, "Sec air flow", "Annubar, ±5% at 26 kg/s"),
        ("SC-1101", cx-150, cy+50,  "Grate speed", "VFD Hz, ±2%"),
    ]
    for tag, x, y, label, desc in instruments:
        svg.append(f'  <circle cx="{x}" cy="{y}" r="14" class="instrument"/>')
        svg.append(f'  <line x1="{x}" y1="{y+14}" x2="{x}" y2="{y+30}" stroke="#1c1c1c" stroke-width="1"/>')
        svg.append(f'  <text x="{x+18}" y="{y+34}" class="label-small">{tag}</text>')
        svg.append(f'  <text x="{x}" y="{y+3}" class="instrument-text">{tag.split("-")[0]}</text>')
        svg.append(f'  <text x="{x+18}" y="{y+4}" class="label-small">{label}</text>')

    # Legend (bottom-right)
    svg.append('  <rect x="700" y="500" width="280" height="180" fill="white" stroke="#1c1c1c" stroke-width="1"/>')
    svg.append('  <text x="840" y="520" class="label" text-anchor="middle">LEGEND</text>')
    svg.append('  <text x="710" y="540" class="label-small">TI = Temperature Indicator</text>')
    svg.append('  <text x="710" y="555" class="label-small">PI = Pressure Indicator</text>')
    svg.append('  <text x="710" y="570" class="label-small">FT = Flow Transmitter</text>')
    svg.append('  <text x="710" y="585" class="label-small">SC = Speed Controller</text>')
    svg.append('  <text x="710" y="605" class="label-small">Process stream (labelled arrow)</text>')
    svg.append('  <text x="710" y="620" class="label-small">Process equipment (housing)</text>')
    svg.append('  <text x="710" y="635" class="label-small">Instrument (ISA-5.1 circle)</text>')
    svg.append('  <text x="710" y="660" class="label-small" font-style="italic">NIDC-CLR-PID-001 Rev A</text>')
    svg.append('  <text x="710" y="673" class="label-small" font-style="italic">Cite: ISA-5.1-2009, ISA-5.3-1983</text>')

    # Footer
    svg.append(f'  <text x="{W/2}" y="{H-5}" class="label-small" text-anchor="middle">Source: nepal_decarb_pro v0.9.0 (commit in Day 9) | v0.5.0 calibration posterior (commit 2aa918c) | open source (MIT)</text>')

    svg.append('</svg>')
    return "\n".join(svg)


def main():
    # When invoked via `exec()` from FreeCADCmd, __file__ may not
    # be defined. Use the explicit script path passed via
    # sys.argv[0] if present, else fall back to a hard-coded
    # default.
    script_path = Path(__file__).resolve() if "__file__" in dir() else None
    if script_path is None:
        for arg in sys.argv[1:]:
            if arg.endswith(".py") and Path(arg).exists():
                script_path = Path(arg).resolve()
                break
    if script_path is None:
        script_path = Path(r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\tools\03-cooler-grate-simulator\day-09-PRs\export_pid_cooler.py")
    out_dir = script_path.parent / "cad"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Build the FreeCAD geometry (the formal P&ID for engineering)
    try:
        doc = FreeCAD.newDocument("CoolerPID")
        parts = build_pid_geometry()
        FreeCAD.ActiveDocument.recompute()
        # Export the formal P&ID as a FreeCAD document + as STEP
        freecad_step = out_dir / "planta_cooler_pid.step"
        try:
            import Import
            fused = FreeCAD.ActiveDocument.addObject("Part::MultiFuse", "PidAssembly")
            fused.Shapes = parts
            FreeCAD.ActiveDocument.recompute()
            Import.export([fused], str(freecad_step))
        except Exception as e:
            print(f"WARNING: could not export STEP: {e}")
    except Exception as e:
        print(f"WARNING: FreeCAD geometry step skipped: {e}")

    # 2. Render the browser-friendly SVG (no FreeCAD needed for this part)
    pid_data = {}
    svg_content = render_svg(pid_data, out_dir / "planta_cooler_pid.svg")
    (out_dir / "planta_cooler_pid.svg").write_text(svg_content, encoding="utf-8")

    # 3. Write the metadata JSON
    meta = {
        "model": "v0.9.0 cooler P&ID (Day 9 ship)",
        "drawing_number": "NIDC-CLR-PID-001 Rev A",
        "calibration_source": "Day 5 v0.5.0 commit 2aa918c",
        "free_geometry_step": "planta_cooler_pid.step",
        "browser_svg": "planta_cooler_pid.svg",
        "citations": [
            "ISA-5.1-2009 Instrumentation Symbols and Identification",
            "ISA-5.3-1983 Instrument Tag Conventions",
            "Peray & Waddell 1986 s6.4 cooler process streams",
            "Mujumdar 2007 compartment layout",
            "Achenbach 1995 h correlation",
        ],
        "instrument_tags": [
            {"tag": "TI-1101", "function": "sec-air T", "type": "Type-K TC", "uncertainty": "±20 K at 800 °C"},
            {"tag": "TI-1102", "function": "tert-air T", "type": "Type-K TC", "uncertainty": "±20 K at 600 °C"},
            {"tag": "TI-1103", "function": "exhaust T", "type": "TC in plenum", "uncertainty": "±10 K at 200 °C"},
            {"tag": "TI-1104", "function": "clinker out T", "type": "IR spot pyrometer", "uncertainty": "±15 K at 200 °C"},
            {"tag": "TI-1105", "function": "ambient T", "type": "PT100 RTD", "uncertainty": "±2 K"},
            {"tag": "PI-1101", "function": "bed dP", "type": "Δ-P transmitter", "uncertainty": "±0.5% span"},
            {"tag": "FT-1101", "function": "sec-air flow", "type": "Annubar", "uncertainty": "±5% at 26 kg/s"},
            {"tag": "SC-1101", "function": "grate speed", "type": "VFD Hz", "uncertainty": "±2%"},
        ],
        "process_streams": [
            {"id": "S1", "name": "Clinker in (kiln discharge)", "T_c": 1400, "m_kg_s": 36, "direction": "in"},
            {"id": "S2", "name": "Sec air out (to kiln burner)", "T_c": 715, "m_kg_s": 26, "direction": "out"},
            {"id": "S3", "name": "Tert air out (to calciner)", "T_c": 190, "m_kg_s": 80, "direction": "out"},
            {"id": "S4", "name": "Exhaust out (to dust collector)", "T_c": 149, "m_kg_s": 53, "direction": "out"},
            {"id": "S5", "name": "Clinker out (to cement mill)", "T_c": 351, "m_kg_s": 36, "direction": "out"},
            {"id": "S6", "name": "Under-grate air in (from PA fan)", "T_c": 120, "m_kg_s": 159, "direction": "in"},
        ],
    }
    (out_dir / "planta_cooler_pid.json").write_text(json.dumps(meta, indent=2, default=str))

    print(f"wrote {out_dir}/planta_cooler_pid.svg")
    print(f"wrote {out_dir}/planta_cooler_pid.json")
    if (out_dir / "planta_cooler_pid.step").exists():
        print(f"wrote {out_dir}/planta_cooler_pid.step")
    print()
    print(f"  drawing: {meta['drawing_number']}")
    print(f"  instrument tags: {len(meta['instrument_tags'])}")
    print(f"  process streams: {len(meta['process_streams'])}")


if __name__ == "__main__":
    main()
