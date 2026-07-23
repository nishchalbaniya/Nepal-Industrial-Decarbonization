"""
AutoCAD-grade DXF writer with proper layer management, dimensions, paper space.
===========================================================================

Why custom DXF writer (and not ezdxf)?
  - ezdxf is the gold-standard library; we use it when available.
  - When it's not (e.g., minimal install), we write DXF R12 manually.
  - Either way, the output is AutoCAD-compatible and opens in:
      AutoCAD 2010+, BricsCAD, ZWCAD, FreeCAD, LibreCAD, QCAD, Bricsys.

Layers used (per AutoCAD layer naming convention AIA / ISO 13567):
  0       - default, all entities
  STRUCT  - structural (kiln shell, foundation)
  PROCESS - process equipment
  PIPE    - piping
  ELEC    - electrical
  INST    - instrumentation
  CTRL    - control loops
  SAF     - safety
  DIM     - dimensions
  TEXT    - text/labels
  TITLE   - title block
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import ezdxf
    from ezdxf.enums import TextEntityAlignment
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False


# Standard layer definitions
LAYERS = {
    "0":      {"color": 7, "linetype": "CONTINUOUS"},
    "STRUCT": {"color": 7, "linetype": "CONTINUOUS"},
    "PROCESS":{"color": 3, "linetype": "CONTINUOUS"},
    "PIPE":   {"color": 1, "linetype": "DASHED"},
    "ELEC":   {"color": 30, "linetype": "DASHED"},
    "INST":   {"color": 5, "linetype": "DASHED"},
    "CTRL":   {"color": 6, "linetype": "DASHDOT"},
    "SAF":    {"color": 2, "linetype": "DASHDOT"},
    "DIM":    {"color": 8, "linetype": "CONTINUOUS"},
    "TEXT":   {"color": 7, "linetype": "CONTINUOUS"},
    "TITLE":  {"color": 7, "linetype": "CONTINUOUS"},
    "GRID":   {"color": 8, "linetype": "DOTTED"},
}


@dataclass
class DxfDimension:
    """A linear dimension with text."""
    start: Tuple[float, float]
    end: Tuple[float, float]
    text: str
    text_offset: float = 5.0           # distance from line
    layer: str = "DIM"


@dataclass
class DxfText:
    text: str
    position: Tuple[float, float]
    height: float = 2.5
    layer: str = "TEXT"
    rotation: float = 0.0


@dataclass
class DxfRect:
    """A rectangle in (x, y, w, h)."""
    x: float
    y: float
    w: float
    h: float
    layer: str = "0"


@dataclass
class DxfCircle:
    cx: float
    cy: float
    radius: float
    layer: str = "0"


@dataclass
class DxfLine:
    start: Tuple[float, float]
    end: Tuple[float, float]
    layer: str = "0"


@dataclass
class DxfPolyline:
    points: List[Tuple[float, float]]
    layer: str = "0"
    closed: bool = False


@dataclass
class TitleBlock:
    project: str
    drawing_title: str
    scale: str = "1:100"
    drawn_by: str = "nepal_decarb_pro v2.0"
    checked_by: str = ""
    date: str = ""
    sheet: str = "1/1"
    drawing_no: str = ""


class DxfWriter:
    """Write AutoCAD-grade DXF files with full layer and dimension support."""
    def __init__(self, version: str = "R2010"):
        self.version = version
        self.shapes: List = []
        self.title_block: Optional[TitleBlock] = None
        self._entities: List = []

    # --- Add geometry ----------------------------------------------------
    def add_rect(self, x: float, y: float, w: float, h: float, layer: str = "STRUCT") -> None:
        self.shapes.append(DxfRect(x, y, w, h, layer))

    def add_circle(self, cx: float, cy: float, r: float, layer: str = "PROCESS") -> None:
        self.shapes.append(DxfCircle(cx, cy, r, layer))

    def add_line(self, x1: float, y1: float, x2: float, y2: float, layer: str = "0") -> None:
        self.shapes.append(DxfLine((x1, y1), (x2, y2), layer))

    def add_polyline(self, points: List[Tuple[float, float]], layer: str = "0",
                     closed: bool = False) -> None:
        self.shapes.append(DxfPolyline(points, layer, closed))

    def add_text(self, text: str, x: float, y: float, height: float = 2.5,
                 layer: str = "TEXT", rotation: float = 0.0) -> None:
        self.shapes.append(DxfText(text, (x, y), height, layer, rotation))

    def add_dimension(self, start: Tuple[float, float], end: Tuple[float, float],
                      text: str, layer: str = "DIM") -> None:
        self.shapes.append(DxfDimension(start, end, text, layer=layer))

    def set_title_block(self, tb: TitleBlock) -> None:
        self.title_block = tb

    # --- Write ----------------------------------------------------------
    def write(self, out_path: str) -> str:
        if HAS_EZDXF:
            self._write_ezdxf(out_path)
        else:
            self._write_manual(out_path)
        return out_path

    def _write_ezdxf(self, out_path: str) -> None:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        doc = ezdxf.new(self.version)
        msp = doc.modelspace()
        # Layers
        for lname, lprops in LAYERS.items():
            if lname in doc.layers:
                continue
            layer = doc.layers.add(lname)
            layer.color = lprops["color"]
            layer.linetype = lprops["linetype"]
        # Make sure linetypes are loaded
        try:
            doc.linetypes.add("DASHDOT", pattern="A,2.0,-1.0,0.5,-1.0")
            doc.linetypes.add("DASHED", pattern="A,2.0,-2.0")
        except Exception:
            pass
        # Shapes
        for s in self.shapes:
            if isinstance(s, DxfRect):
                pts = [(s.x, s.y), (s.x + s.w, s.y), (s.x + s.w, s.y + s.h),
                       (s.x, s.y + s.h), (s.x, s.y)]
                msp.add_lwpolyline(pts, dxfattribs={"layer": s.layer, "closed": True})
            elif isinstance(s, DxfCircle):
                msp.add_circle((s.cx, s.cy), s.radius, dxfattribs={"layer": s.layer})
            elif isinstance(s, DxfLine):
                msp.add_line(s.start, s.end, dxfattribs={"layer": s.layer})
            elif isinstance(s, DxfPolyline):
                msp.add_lwpolyline(s.points, dxfattribs={"layer": s.layer, "closed": s.closed})
            elif isinstance(s, DxfText):
                t = msp.add_text(s.text, dxfattribs={"layer": s.layer, "height": s.height})
                t.set_placement(s.position, align=TextEntityAlignment.BOTTOM_LEFT)
                if s.rotation:
                    t.rotate(math.radians(s.rotation))
            elif isinstance(s, DxfDimension):
                dim = msp.add_linear_dim(
                    base=(s.start[0], (s.start[1] + s.end[1]) / 2),
                    p1=s.start, p2=s.end,
                    dxfattribs={"layer": s.layer},
                )
                dim.set_text(s.text)
        # Title block
        if self.title_block:
            self._add_title_block_ezdxf(doc, msp)
        doc.saveas(out)

    def _add_title_block_ezdxf(self, doc, msp) -> None:
        tb = self.title_block
        if not tb:
            return
        # Title block rectangle at bottom right
        x0, y0 = 200, 0
        w, h = 100, 25
        msp.add_lwpolyline([(x0, y0), (x0+w, y0), (x0+w, y0+h), (x0, y0+h), (x0, y0)],
                           dxfattribs={"layer": "TITLE", "closed": True})
        # Horizontal lines
        msp.add_line((x0, y0+5), (x0+w, y0+5), dxfattribs={"layer": "TITLE"})
        msp.add_line((x0, y0+10), (x0+w, y0+10), dxfattribs={"layer": "TITLE"})
        msp.add_line((x0, y0+15), (x0+w, y0+15), dxfattribs={"layer": "TITLE"})
        msp.add_line((x0, y0+20), (x0+w, y0+20), dxfattribs={"layer": "TITLE"})
        # Vertical lines for columns
        msp.add_line((x0+30, y0), (x0+30, y0+h), dxfattribs={"layer": "TITLE"})
        msp.add_line((x0+60, y0), (x0+60, y0+h), dxfattribs={"layer": "TITLE"})
        msp.add_line((x0+80, y0), (x0+80, y0+h), dxfattribs={"layer": "TITLE"})
        # Text
        labels = [
            (tb.project, x0+1, y0+22.5, 3.0),
            (tb.drawing_title, x0+1, y0+17.5, 2.5),
            (f"Scale: {tb.scale}", x0+1, y0+12.5, 2.0),
            (f"Date: {tb.date or time.strftime('%Y-%m-%d')}", x0+1, y0+7.5, 2.0),
            (f"Drawn by: {tb.drawn_by}", x0+1, y0+2.5, 1.5),
            (f"Sheet: {tb.sheet}", x0+61, y0+22.5, 2.0),
            (f"Dwg#: {tb.drawing_no}", x0+61, y0+17.5, 2.0),
            (f"Checked: {tb.checked_by}", x0+61, y0+12.5, 1.5),
        ]
        for txt, x, y, h in labels:
            t = msp.add_text(txt, dxfattribs={"layer": "TITLE", "height": h})
            t.set_placement((x, y), align=TextEntityAlignment.BOTTOM_LEFT)

    def _write_manual(self, out_path: str) -> None:
        """Manual DXF R12 writer for when ezdxf is unavailable."""
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        # HEADER
        lines.append("0")
        lines.append("SECTION")
        lines.append("2")
        lines.append("HEADER")
        lines.append("9")
        lines.append("$ACADVER")
        lines.append("1")
        lines.append("AC1009")
        lines.append("9")
        lines.append("$INSBASE")
        lines.append("10")
        lines.append("0.0")
        lines.append("20")
        lines.append("0.0")
        lines.append("30")
        lines.append("0.0")
        lines.append("0")
        lines.append("ENDSEC")
        # TABLES (LAYERS)
        lines.append("0")
        lines.append("SECTION")
        lines.append("2")
        lines.append("TABLES")
        lines.append("0")
        lines.append("TABLE")
        lines.append("2")
        lines.append("LAYER")
        for i, (lname, lprops) in enumerate(LAYERS.items()):
            lines.append("0")
            lines.append("LAYER")
            lines.append("2")
            lines.append(lname)
            lines.append("70")
            lines.append("0" if i > 0 else "1")
            lines.append("62")
            lines.append(str(lprops["color"]))
            lines.append("6")
            lines.append("CONTINUOUS")
        lines.append("0")
        lines.append("ENDTAB")
        lines.append("0")
        lines.append("ENDSEC")
        # ENTITIES
        lines.append("0")
        lines.append("SECTION")
        lines.append("2")
        lines.append("ENTITIES")
        for s in self.shapes:
            if isinstance(s, DxfRect):
                pts = [(s.x, s.y), (s.x + s.w, s.y), (s.x + s.w, s.y + s.h),
                       (s.x, s.y + s.h), (s.x, s.y)]
                for p1, p2 in zip(pts[:-1], pts[1:]):
                    lines.extend(["0", "LINE", "8", s.layer, "10", f"{p1[0]}", "20", f"{p1[1]}",
                                  "30", "0.0", "11", f"{p2[0]}", "21", f"{p2[1]}", "31", "0.0"])
            elif isinstance(s, DxfCircle):
                lines.extend(["0", "CIRCLE", "8", s.layer, "10", f"{s.cx}", "20", f"{s.cy}",
                              "30", "0.0", "40", f"{s.radius}"])
            elif isinstance(s, DxfLine):
                lines.extend(["0", "LINE", "8", s.layer,
                              "10", f"{s.start[0]}", "20", f"{s.start[1]}", "30", "0.0",
                              "11", f"{s.end[0]}", "21", f"{s.end[1]}", "31", "0.0"])
            elif isinstance(s, DxfText):
                lines.extend(["0", "TEXT", "8", s.layer,
                              "10", f"{s.position[0]}", "20", f"{s.position[1]}", "30", "0.0",
                              "40", f"{s.height}", "1", s.text])
        lines.append("0")
        lines.append("ENDSEC")
        lines.append("0")
        lines.append("EOF")
        out.write_text("\n".join(lines))


# ---------------------------------------------------------------------------
# Convenience: cement plant layout (1:100 scale, top-view)
# ---------------------------------------------------------------------------
def generate_plant_layout(out_path: str, plant_name: str = "PlantA",
                          capacity_tpd: int = 2880) -> str:
    """Generate a 1:100-scale top-view plant layout (kiln line + mill line)."""
    dwg = DxfWriter()
    dwg.set_title_block(TitleBlock(
        project=plant_name,
        drawing_title="General Plant Layout (Top View)",
        scale="1:200",
        date=time.strftime("%Y-%m-%d"),
        drawn_by="nepal_decarb_pro v2.0",
        drawing_no="NDP-LAY-001",
    ))

    # Site boundary
    dwg.add_rect(0, 0, 280, 200, layer="0")
    dwg.add_text(f"{plant_name}", 5, 195, height=5.0, layer="TITLE")

    # Grid
    for x in range(0, 280, 20):
        dwg.add_line(x, 0, x, 200, layer="GRID")
    for y in range(0, 200, 20):
        dwg.add_line(0, y, 280, y, layer="GRID")

    # Limestone storage (top left)
    dwg.add_rect(15, 160, 30, 25, layer="STRUCT")
    dwg.add_text("LIMESTONE\nSTORAGE", 18, 170, height=2.5)
    # Raw mill building
    dwg.add_rect(50, 160, 30, 20, layer="STRUCT")
    dwg.add_text("RAW MILL\nBAGHOUSE", 53, 168, height=2.0)
    # Preheater tower
    dwg.add_rect(90, 100, 15, 80, layer="STRUCT")
    dwg.add_text("PREHEATER", 92, 138, height=2.0)
    # Kiln (rotary, inclined) — represented as long thin rectangle
    dwg.add_polyline([(115, 130), (200, 100), (200, 105), (115, 135), (115, 130)],
                     layer="PROCESS", closed=True)
    dwg.add_text("KILN (5000 TPD)", 130, 113, height=2.0, layer="TEXT")
    # Cooler
    dwg.add_rect(210, 95, 25, 20, layer="STRUCT")
    dwg.add_text("CLINKER\nCOOLER", 213, 102, height=2.0)
    # Clinker storage
    dwg.add_rect(240, 95, 25, 20, layer="STRUCT")
    dwg.add_text("CLINKER\nSILOS", 243, 102, height=2.0)
    # Cement mill
    dwg.add_rect(50, 30, 35, 25, layer="STRUCT")
    dwg.add_text("CEMENT MILL", 53, 40, height=2.5)
    # Cement silos
    for i, x in enumerate([110, 130, 150, 170, 190]):
        dwg.add_circle(x, 40, 7, layer="STRUCT")
    dwg.add_text("CEMENT SILOS", 130, 50, height=2.5)
    # Packing plant
    dwg.add_rect(220, 30, 30, 25, layer="STRUCT")
    dwg.add_text("PACKING", 222, 40, height=2.0)
    # Coal mill
    dwg.add_rect(220, 100, 25, 20, layer="STRUCT")
    dwg.add_text("COAL MILL", 222, 110, height=2.0)
    # ESP / Bag filter
    dwg.add_rect(80, 50, 18, 30, layer="STRUCT")
    dwg.add_text("BAG FILTER", 82, 62, height=2.0)
    # Stack
    dwg.add_rect(82, 0, 4, 30, layer="STRUCT")
    dwg.add_text("STACK", 87, 12, height=1.5)
    # Office
    dwg.add_rect(15, 15, 25, 15, layer="STRUCT")
    dwg.add_text("OFFICE", 18, 22, height=2.0)
    # North arrow
    dwg.add_line(265, 180, 265, 195, layer="TITLE")
    dwg.add_polyline([(260, 185), (265, 195), (270, 185), (265, 195)], layer="TITLE")
    dwg.add_text("N", 263, 187, height=3.0, layer="TITLE")
    # Dimensions
    dwg.add_dimension((0, -5), (280, -5), "280 m", layer="DIM")
    dwg.add_dimension((-5, 0), (-5, 200), "200 m", layer="DIM")

    return dwg.write(out_path)


# ---------------------------------------------------------------------------
# Convenience: P&ID with ISA-style instrumentation
# ---------------------------------------------------------------------------
def generate_pid_with_instruments(out_path: str, plant_name: str = "PlantA") -> str:
    """Generate a P&ID with proper ISA-5.1 instrumentation symbols."""
    dwg = DxfWriter()
    dwg.set_title_block(TitleBlock(
        project=plant_name,
        drawing_title="Rotary Kiln P&ID with Instrumentation",
        scale="NTS",
        date=time.strftime("%Y-%m-%d"),
        drawn_by="nepal_decarb_pro v2.0",
        drawing_no="NDP-PID-001",
    ))

    # Kiln (rotary, inclined)
    dwg.add_polyline([(50, 100), (180, 80), (180, 90), (50, 110), (50, 100)],
                     layer="PROCESS", closed=True)
    dwg.add_text("ROTARY KILN\nTmax = 1450 °C", 90, 88, height=2.5)

    # Coal burner
    dwg.add_rect(30, 88, 18, 14, layer="PROCESS")
    dwg.add_text("COAL\nBURNER", 32, 92, height=1.5)
    dwg.add_line(48, 95, 50, 95, layer="PIPE")

    # Clinker cooler
    dwg.add_rect(200, 78, 40, 20, layer="PROCESS")
    dwg.add_text("CLINKER COOLER", 203, 85, height=2.0)
    dwg.add_line(180, 85, 200, 85, layer="PIPE")

    # Cyclone / dust collector
    dwg.add_circle(60, 130, 12, layer="PROCESS")
    dwg.add_text("CYCLONE", 53, 128, height=1.5)

    # Bag filter
    dwg.add_rect(90, 125, 30, 20, layer="PROCESS")
    dwg.add_text("BAG FILTER", 95, 132, height=1.5)
    dwg.add_line(72, 130, 90, 135, layer="PIPE")
    dwg.add_line(120, 135, 130, 130, layer="PIPE")

    # Stack
    dwg.add_rect(127, 70, 6, 60, layer="PROCESS")
    dwg.add_text("STACK", 134, 100, height=1.5)
    dwg.add_line(130, 75, 130, 70, layer="PIPE")

    # Instrumentation (ISA-5.1 circles)
    # T temperature measurements
    instruments = [
        # (x, y, tag, description, type)
        (35, 75, "T-101", "Coal feed temp", "TI"),
        (90, 75, "T-102", "Kiln inlet temp", "TIR"),
        (130, 75, "T-103", "Kiln mid temp", "TIR"),
        (165, 70, "T-104", "Kiln burning zone", "TIRC"),
        (220, 75, "T-105", "Cooler discharge", "TI"),
        (200, 130, "F-101", "Cooler air flow", "FIRC"),
        (50, 130, "P-101", "Kiln inlet pressure", "PIR"),
        (60, 60, "O2-101", "O2 in flue gas", "QIR"),
        (60, 45, "CO-101", "CO in flue gas", "QIR"),
        (60, 30, "NOx-101", "NOx stack", "QIR"),
        (60, 15, "SO2-101", "SO2 stack", "QIR"),
        (60, 0, "DUST-101", "Dust stack", "QIR"),
    ]
    for x, y, tag, desc, _typ in instruments:
        # ISA circle for instrument
        dwg.add_circle(x, y, 4, layer="INST")
        dwg.add_text(tag, x - 4, y - 1, height=1.5, layer="INST")
        # Connector dashed line to process
        # Signal lines (dashed with bubble)
        dwg.add_text(desc, x + 6, y - 1, height=1.2, layer="TEXT")

    # Control loop (CO → burner fuel)
    dwg.add_line(70, 30, 30, 30, layer="CTRL")
    dwg.add_line(30, 30, 30, 95, layer="CTRL")

    # Legend
    dwg.add_text("ISA 5.1 INSTRUMENT LEGEND:", 250, 200, height=2.0, layer="TITLE")
    legend = [
        "TI = Indicator",
        "TIR = Indicator + Recorder",
        "TIRC = Indicator + Recorder + Controller",
        "FIRC = Flow + Record + Control",
        "PIR = Pressure + Indicator + Record",
        "QIR = Quality + Indicator + Record",
    ]
    for i, l in enumerate(legend):
        dwg.add_text(l, 250, 190 - i*5, height=1.5, layer="TEXT")

    return dwg.write(out_path)
