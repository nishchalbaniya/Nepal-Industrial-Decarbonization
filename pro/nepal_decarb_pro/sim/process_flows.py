"""
Process Flow Diagram (PFD) and P&ID Generator
=============================================

Generates SVG/Plotly process flow diagrams for cement and brick plants.
Used for:
  - Documentation
  - Operator training
  - Pilot plant commissioning
  - Process understanding
"""
from __future__ import annotations

# WP6: matplotlib is an optional dependency. Import it lazily so the
# module can be loaded (and the rest of the sim package can be used)
# on a minimal install. Functions in this module that need matplotlib
# check the global `_MATPLOTLIB_AVAILABLE` flag and raise a clear
# ImportError if matplotlib is not installed.
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from matplotlib.patches import (
        FancyArrowPatch, FancyBboxPatch, Rectangle, Circle,
    )
    _MATPLOTLIB_AVAILABLE = True
    _MATPLOTLIB_IMPORT_ERROR = None
except ImportError as _e:
    _MATPLOTLIB_AVAILABLE = False
    _MATPLOTLIB_IMPORT_ERROR = _e

import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from nepal_decarb_pro.sim.equipment_specs import Equipment, EQUIPMENT_DATABASE


def _require_matplotlib():
    """Raise a clear ImportError if matplotlib is not installed."""
    if not _MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for the PFD/P&ID generator "
            "(nepal_decarb_pro.sim.process_flows). Install it with: "
            "pip install matplotlib. (WP6 -- this dependency is optional "
            "because the core sim modules do not require it.)"
        ) from _MATPLOTLIB_IMPORT_ERROR


def _draw_box(ax, x, y, w, h, label, color="#E8F4F8", text_color="black", fontsize=9):
    """Draw a process box with label."""
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                            boxstyle="round,pad=0.02",
                            facecolor=color, edgecolor="black", linewidth=1.2)
    ax.add_patch(rect)
    ax.text(x, y, label, ha="center", va="center", fontsize=fontsize,
            color=text_color, fontweight="bold")


def _draw_arrow(ax, x1, y1, x2, y2, label="", color="black", style="-"):
    """Draw an arrow with optional label."""
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                              arrowstyle="->", mutation_scale=15,
                              color=color, linewidth=1.5, linestyle=style)
    ax.add_patch(arrow)
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, label,
                ha="center", va="bottom", fontsize=8, color=color)


def _draw_sensor(ax, x, y, label="", color="red"):
    """Draw a sensor/instrument."""
    circle = Circle((x, y), 0.3, facecolor=color, edgecolor="black", alpha=0.7)
    ax.add_patch(circle)
    if label:
        ax.text(x, y - 0.7, label, ha="center", va="top", fontsize=7, color=color)


def generate_pfd_cement(out_path: Path, capacity_tpd: int = 5000) -> Path:
    """
    Generate a Process Flow Diagram (PFD) for a cement plant.

    Args:
        out_path: Path to save the PNG file
        capacity_tpd: Plant capacity in tonnes per day clinker

    Returns:
        Path to saved file
    """
    _require_matplotlib()
    fig, ax = plt.subplots(figsize=(20, 12))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"Process Flow Diagram — Cement Plant ({capacity_tpd} TPD Clinker)\n"
        f"nepal_decarb_pro v1.0 | 5-stage preheater, precalciner, grate cooler",
        fontsize=14, fontweight="bold", pad=20,
    )

    # Layout:
    # Row 1 (y=10): Raw material feed
    # Row 2 (y=8): Crushing & storage
    # Row 3 (y=6): Raw mill & preheater
    # Row 4 (y=4): Kiln
    # Row 5 (y=2): Clinker cooler & storage
    # Row 6 (y=0): Cement mill & dispatch

    # Raw material
    _draw_box(ax, 1, 11, 2.5, 0.8, "Limestone\nQuarry", "#FFE4B5")
    _draw_box(ax, 4, 11, 2.5, 0.8, "Clay/\nShale", "#FFE4B5")
    _draw_box(ax, 7, 11, 2.5, 0.8, "Iron Ore/\nSand", "#FFE4B5")

    # Crushing & storage
    _draw_box(ax, 1, 9, 1.5, 0.7, "Crusher", "#E8F4F8")
    _draw_box(ax, 4, 9, 1.5, 0.7, "Crusher", "#E8F4F8")
    _draw_box(ax, 7, 9, 1.5, 0.7, "Crusher", "#E8F4F8")
    _draw_box(ax, 4, 7.5, 4, 0.7, "Raw Material Storage Silos", "#E0E0E0")

    # Raw mill
    _draw_box(ax, 4, 6, 3, 0.9, "Vertical Roller Mill\n(Raw Mill)\n10-11 kWh/t", "#D0F0D0")

    # Preheater tower
    _draw_box(ax, 9, 7, 2.5, 3, "5-Stage\nCyclone\nPreheater\n+\nPrecalciner", "#FFE4B5", fontsize=8)
    _draw_box(ax, 9, 5.5, 2, 0.5, "Tertiary Air", "#FFB6C1", fontsize=7)

    # Rotary kiln
    _draw_box(ax, 13, 7, 4, 1.0, "Rotary Kiln (L=72m, D=4.6m)\n1450°C peak | 3.5° slope | 3.5 rpm",
              "#FFB6C1", fontsize=8)

    # Cooler
    _draw_box(ax, 13, 4, 4, 0.9, "Grate Cooler\nClinker 1450→1100°C\n75% heat recovery",
              "#B0D8FF", fontsize=8)
    _draw_box(ax, 16, 5.5, 1.5, 0.5, "Coal Mill", "#FFE4B5", fontsize=7)
    _draw_box(ax, 16, 6.5, 1.5, 0.5, "Coal Burner", "#FF6347", fontsize=7)

    # Clinker storage & cement mill
    _draw_box(ax, 13, 2, 4, 0.8, "Clinker Silo (50,000 t, ~30 days)", "#E0E0E0")
    _draw_box(ax, 10, 2, 2.5, 0.8, "Cement Mill\nVRM/Ball Mill", "#D0F0D0", fontsize=8)
    _draw_box(ax, 6, 2, 2.5, 0.8, "Gypsum &\nAdditives", "#FFE4B5", fontsize=8)
    _draw_box(ax, 3, 0.5, 2.5, 0.8, "Cement Silos\n(10,000 t)", "#E0E0E0", fontsize=8)
    _draw_box(ax, 1, 0.5, 1.5, 0.8, "Dispatch", "#D0F0D0", fontsize=7)

    # ESP / bag filter / stack
    _draw_box(ax, 16.5, 9, 1.5, 0.7, "Bag Filter\n<10 mg/Nm³", "#E8F4F8", fontsize=7)
    _draw_box(ax, 18.5, 9, 1.0, 0.7, "Stack\n(80m)", "#E0E0E0", fontsize=7)
    _draw_box(ax, 16.5, 11, 1.5, 0.5, "ID Fan", "#E0E0E0", fontsize=7)

    # Arrows — material flow
    _draw_arrow(ax, 1, 10.6, 1, 9.4, "Limestone")
    _draw_arrow(ax, 4, 10.6, 4, 9.4, "Clay")
    _draw_arrow(ax, 7, 10.6, 7, 9.4, "Iron")
    _draw_arrow(ax, 1, 8.6, 3, 7.9)
    _draw_arrow(ax, 4, 8.6, 4, 7.9)
    _draw_arrow(ax, 7, 8.6, 5, 7.9)
    _draw_arrow(ax, 4, 7.1, 4, 6.5, "Raw meal")
    _draw_arrow(ax, 5.5, 6, 8, 7, "Preheated\nmeal")
    _draw_arrow(ax, 10, 8, 12, 7.5, "Calcined\nmeal")
    _draw_arrow(ax, 15, 7, 15, 4.5, "Hot\nclinker")
    _draw_arrow(ax, 13, 4, 13, 2.5, "Cooled\nclinker")
    _draw_arrow(ax, 12, 2, 11, 2.4, "To mill")
    _draw_arrow(ax, 8, 2, 11, 2.4, "Gypsum")
    _draw_arrow(ax, 9.5, 1.5, 4, 1)
    _draw_arrow(ax, 2, 0.5, 1.7, 0.5, "Truck/\nrail")
    _draw_arrow(ax, 16, 7.0, 13.5, 7.0, "Coal")
    _draw_arrow(ax, 13.5, 6.5, 13, 4, "Air")
    _draw_arrow(ax, 10.5, 6.5, 10.5, 5.5, "Air")
    _draw_arrow(ax, 10, 8, 17, 9.3, "Hot\ngas")
    _draw_arrow(ax, 17, 9, 18.5, 9)

    # Sensors (CEMS points)
    _draw_sensor(ax, 18, 9, "CEMS")
    _draw_sensor(ax, 14, 7, "T_kiln")
    _draw_sensor(ax, 9, 7, "O2", color="blue")
    _draw_sensor(ax, 12, 4, "T_clinker", color="red")
    _draw_sensor(ax, 4, 6, "T_mill", color="red")

    # Legend
    legend_y = 11
    ax.text(10, legend_y - 0.3, "Legend:", ha="left", va="top", fontsize=9, fontweight="bold")
    ax.add_patch(Rectangle((11, legend_y - 0.4), 0.4, 0.3, facecolor="#FFE4B5", edgecolor="black"))
    ax.text(11.5, legend_y - 0.25, "Raw material", ha="left", va="top", fontsize=8)
    ax.add_patch(Rectangle((13, legend_y - 0.4), 0.4, 0.3, facecolor="#FFB6C1", edgecolor="black"))
    ax.text(13.5, legend_y - 0.25, "High temperature", ha="left", va="top", fontsize=8)
    ax.add_patch(Rectangle((15, legend_y - 0.4), 0.4, 0.3, facecolor="#B0D8FF", edgecolor="black"))
    ax.text(15.5, legend_y - 0.25, "Cooling", ha="left", va="top", fontsize=8)
    ax.add_patch(Rectangle((17, legend_y - 0.4), 0.4, 0.3, facecolor="#D0F0D0", edgecolor="black"))
    ax.text(17.5, legend_y - 0.25, "Processing", ha="left", va="top", fontsize=8)
    ax.add_patch(Circle((19, legend_y - 0.25), 0.15, facecolor="red", edgecolor="black"))
    ax.text(19.2, legend_y - 0.25, "Sensor", ha="left", va="top", fontsize=8)

    plt.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path


def generate_pfd_brick(out_path: Path, kiln_type: str = "zigzag", capacity_M: float = 10.0) -> Path:
    """
    Generate a PFD for a brick plant.

    Args:
        out_path: Path to save PNG
        kiln_type: 'clamp_traditional', 'hoffman', 'zigzag', 'tunnel', 'vertical_shaft'
        capacity_M: Capacity in million bricks per year
    """
    _require_matplotlib()
    fig, ax = plt.subplots(figsize=(18, 10))
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        f"Process Flow Diagram — Brick Plant ({kiln_type.replace('_', ' ').title()}, {capacity_M}M bricks/yr)\n"
        "nepal_decarb_pro v1.0",
        fontsize=14, fontweight="bold", pad=20,
    )

    # Clay preparation
    _draw_box(ax, 1.5, 9, 2, 0.7, "Clay Quarry", "#FFE4B5")
    _draw_box(ax, 1.5, 7.5, 1.5, 0.6, "Clay Prep", "#E8F4F8", fontsize=8)
    _draw_box(ax, 1.5, 6, 1.5, 0.6, "Pug Mill", "#D0F0D0", fontsize=8)

    # Molding & drying
    _draw_box(ax, 4, 7, 1.8, 0.7, "Molding\nMachine", "#D0F0D0", fontsize=8)
    _draw_box(ax, 4, 5, 1.8, 0.7, "Tunnel\nDryer", "#B0D8FF", fontsize=8)

    # Kiln (depending on type)
    if kiln_type == "clamp_traditional":
        _draw_box(ax, 8, 7, 4, 0.9, f"Clamp Kiln\n{capacity_M}M bricks/yr\n300 kg coal/1000",
                  "#FFB6C1", fontsize=8)
    elif kiln_type == "zigzag":
        _draw_box(ax, 8, 7, 4, 0.9, f"Zigzag Kiln\n{capacity_M}M bricks/yr\n110 kg coal/1000 | 70% eff",
                  "#FFB6C1", fontsize=8)
    elif kiln_type == "hoffman":
        _draw_box(ax, 8, 7, 4, 0.9, f"Hoffman Kiln\n{capacity_M}M bricks/yr\n155 kg coal/1000 | 60% eff",
                  "#FFB6C1", fontsize=8)
    elif kiln_type == "tunnel":
        _draw_box(ax, 8, 7, 4, 0.9, f"Tunnel Kiln\n{capacity_M}M bricks/yr\n120 kg coal/1000 | 75% eff",
                  "#FFB6C1", fontsize=8)
    elif kiln_type == "vertical_shaft":
        _draw_box(ax, 8, 7, 4, 0.9, f"Vertical Shaft Kiln\n{capacity_M}M bricks/yr\n90 kg coal/1000 | 80% eff",
                  "#FFB6C1", fontsize=8)

    # Cooling
    _draw_box(ax, 8, 5, 4, 0.7, "Natural Cooling (kiln integrated)", "#B0D8FF", fontsize=8)

    # Stack
    _draw_box(ax, 13, 7, 1.5, 0.7, "Cyclone\n+ Stack", "#E0E0E0", fontsize=8)

    # Storage & dispatch
    _draw_box(ax, 14, 5, 2.5, 0.8, "Brick Storage", "#E0E0E0", fontsize=8)
    _draw_box(ax, 16.5, 3, 1.5, 0.7, "Dispatch", "#D0F0D0", fontsize=7)
    _draw_box(ax, 14, 3, 1.5, 0.7, "Quality\nTest", "#E8F4F8", fontsize=7)

    # Arrows
    _draw_arrow(ax, 1.5, 8.6, 1.5, 7.9, "Clay")
    _draw_arrow(ax, 1.5, 7.1, 1.5, 6.4, "Mix")
    _draw_arrow(ax, 2.3, 6, 3.1, 7.0, "Column")
    _draw_arrow(ax, 4.9, 7, 6, 7, "Green\nbricks")
    _draw_arrow(ax, 4.9, 5, 6, 5, "Dried")
    _draw_arrow(ax, 6, 7, 6, 5)
    _draw_arrow(ax, 5, 4.6, 8, 6.8)
    _draw_arrow(ax, 10, 6.5, 10, 5.4, "Cooled\nbricks")
    _draw_arrow(ax, 10, 4.5, 14, 4.5, "Hot\nbricks")
    _draw_arrow(ax, 12, 7, 12.5, 7.2, "Hot gas")
    _draw_arrow(ax, 13, 5, 16, 3.5)

    # Sensors
    _draw_sensor(ax, 12, 7, "CEMS", color="red")
    _draw_sensor(ax, 10, 7, "T_kiln", color="red")
    _draw_sensor(ax, 4, 7, "P_mold", color="blue")

    plt.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path


def generate_pid_cement(out_path: Path) -> Path:
    """Generate a simplified P&ID (Piping & Instrumentation Diagram)."""
    _require_matplotlib()
    fig, ax = plt.subplots(figsize=(20, 14))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 14)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(
        "P&ID — Cement Plant (Key Loops)\n"
        "TT = Temperature Transmitter, PT = Pressure, FT = Flow, AT = Analyzer, FC = Flow Controller",
        fontsize=14, fontweight="bold", pad=20,
    )

    # Kiln
    _draw_box(ax, 10, 7, 6, 1.2, "ROTARY KILN", "#FFB6C1", fontsize=11)

    # Sensors around kiln (ISA-style balloons)
    # TT 101 - Burning zone temperature
    _draw_sensor(ax, 13, 8, "TT-101", color="red")
    ax.text(13, 8.5, "Burning Zone T", ha="center", fontsize=8)
    # FT 101 - Coal flow
    _draw_sensor(ax, 8, 6, "FT-102", color="green")
    ax.text(8, 5.5, "Coal Flow", ha="center", fontsize=8)
    # AT 101 - O2
    _draw_sensor(ax, 8, 8, "AT-101", color="blue")
    ax.text(8, 8.5, "O2/CO/NOx", ha="center", fontsize=8)
    # PT 101 - Kiln inlet pressure
    _draw_sensor(ax, 7, 7, "PT-101", color="purple")
    # TT 102 - Clinker cooler discharge
    _draw_sensor(ax, 13, 6, "TT-102", color="red")
    ax.text(13, 5.5, "Clinker T", ha="center", fontsize=8)

    # Preheater
    _draw_box(ax, 4, 7, 3, 1.2, "PREHEATER", "#FFE4B5", fontsize=10)
    _draw_sensor(ax, 5.5, 8, "TT-103", color="red")
    ax.text(5.5, 8.5, "Cyclone T", ha="center", fontsize=8)
    _draw_sensor(ax, 5.5, 6, "PT-102", color="purple")
    ax.text(5.5, 5.5, "Cyclone ΔP", ha="center", fontsize=8)

    # Cooler
    _draw_box(ax, 10, 4, 6, 1, "GRATE COOLER", "#B0D8FF", fontsize=11)
    _draw_sensor(ax, 12, 4.5, "FT-103", color="green")
    ax.text(12, 5, "Cooler Air", ha="center", fontsize=8)

    # Control loops
    ax.annotate("", xy=(13, 8), xytext=(13, 9),
                arrowprops=dict(arrowstyle="->", color="red"))
    ax.text(13.3, 8.5, "→ DCS", fontsize=8, color="red")

    # Legend
    legend_text = (
        "ISA 5.1 Instrumentation:\n"
        "● Red = Temperature (TT)\n"
        "● Blue = Analyzer (AT)\n"
        "● Green = Flow (FT)\n"
        "● Purple = Pressure (PT)\n"
        "Lines → DCS for closed-loop control"
    )
    ax.text(17, 12, legend_text, ha="left", va="top", fontsize=9,
            bbox=dict(boxstyle="round", facecolor="lightyellow", edgecolor="black"))

    plt.tight_layout()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()
    return out_path
