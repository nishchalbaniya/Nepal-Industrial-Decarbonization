"""Day 6 -- generate a JSON metadata file for the STEP export.

Output: day-06-PRs/cad/v050_cooler_assembly.json with the
calibrated geometry, the bounding box, the part list, and the
provenance (Day 5 v0.5.0 calibration posterior).
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

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

SITE_DEFAULTS = dict(
    width_m=3.5,
    shell_height_m=2.0,
    shell_thickness_m=0.20,
    sec_air_duct_diameter_m=1.0,
    exhaust_duct_diameter_m=0.8,
    kiln_coupling_diameter_m=1.5,
    clinker_chute_width_m=1.2,
    grate_plate_thickness_m=0.08,
)


def main():
    out_path = Path(__file__).parent / "cad" / "v050_cooler_assembly.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "model": "v0.5.0 calibrated cooler (Day 5 ship)",
        "calibration_source": "Day 5 v0.5.0 iterative two-stage L-BFGS-B (commit 2aa918c)",
        "calibration_target": "consistent synthetic Hetauda shift (synthetic_hetauda_v050_shift_4h.csv)",
        "calibration_loss_prior": 233.72,
        "calibration_loss_posterior": 5.00,
        "calibration_rmse_sec_air_K": 10.2,
        "calibration_rmse_clinker_K": 0.7,
        "calibration_rmse_exhaust_K": 24.0,
        "calibrated_posterior": DEFAULT_CALIBRATION,
        "geometry": {
            "grate_length_m":  DEFAULT_CALIBRATION["grate_length_m"],
            "bed_depth_m":     DEFAULT_CALIBRATION["bed_depth_m"],
            "n_compartments":  DEFAULT_CALIBRATION["n_compartments"],
            "width_m":         SITE_DEFAULTS["width_m"],
            "shell_height_m":  SITE_DEFAULTS["shell_height_m"],
            "shell_thickness_m": SITE_DEFAULTS["shell_thickness_m"],
            "grate_plate_thickness_m": SITE_DEFAULTS["grate_plate_thickness_m"],
            "sec_air_duct_diameter_m": SITE_DEFAULTS["sec_air_duct_diameter_m"],
            "exhaust_duct_diameter_m": SITE_DEFAULTS["exhaust_duct_diameter_m"],
            "kiln_coupling_diameter_m": SITE_DEFAULTS["kiln_coupling_diameter_m"],
        },
        "bounding_box_mm": [
            round((DEFAULT_CALIBRATION["grate_length_m"] + 2 * SITE_DEFAULTS["shell_thickness_m"]) * 1000, 1),
            round((SITE_DEFAULTS["width_m"] + 2 * SITE_DEFAULTS["shell_thickness_m"]) * 1000, 1),
            round((SITE_DEFAULTS["shell_height_m"] + SITE_DEFAULTS["shell_thickness_m"]) * 1000, 1),
        ],
        "n_parts": 11,
        "n_faces": 53,
        "step_file": "v050_cooler_assembly.step",
        "step_format": "ISO 10303-21 (STEP AP214)",
        "step_size_bytes": 62072,
        "citations": [
            "ISO 10303-21:2016 STEP file format",
            "Peray & Waddell 1986 s6.4 cooler geometry",
            "Mujumdar 2007 compartment layout",
            "Achenbach 1995 h correlation",
            "ICCC 2006 s2.3 emissivity",
            "GCCA GNR 2022 cooler efficiency BAT",
            "ECRA 2022 cooler heat loss BAT",
        ],
        "notes": [
            "Geometry is a simplified 1D-compartment model rendered as 3D",
            "compartment partitions, sec-air duct stub, exhaust duct stub,",
            "kiln-discharge coupling, clinker-discharge chute, grate plate.",
            "The bed material (clinker layer) is shown as a visual hint only;",
            "no solid is rendered for it (the model is for a 1D thermal sim,",
            "not a discrete-element simulation).",
            "The number of compartments is the calibrated v0.5.0 posterior,",
            "rounded to the nearest integer (Day 5 ship: 6 compartments",
            "at 32.797 m grate and 0.78 m bed depth).",
        ],
    }
    out_path.write_text(json.dumps(meta, indent=2, default=str))
    print(f"wrote {out_path}")
    print(f"  bounding box: {meta['bounding_box_mm']} mm")
    print(f"  grate length: {meta['geometry']['grate_length_m']} m")
    print(f"  bed depth: {meta['geometry']['bed_depth_m']} m")
    print(f"  compartments: {meta['geometry']['n_compartments']}")


if __name__ == "__main__":
    main()
