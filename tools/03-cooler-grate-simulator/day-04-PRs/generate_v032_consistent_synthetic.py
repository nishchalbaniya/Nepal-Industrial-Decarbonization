"""Day 5 -- generate a v0.3.2-model-consistent synthetic PlantA
plant-data CSV.

The Day 4 generator (generate_synthetic_plant_data.py) produced
synthetic data from a hand-coded additive design-duty function
that does NOT match the v0.3.2 model output. As a result, the
synthetic target is infeasible for the v0.3.2 model: the design-
duty operating point gives loss 512 with the v0.3.2 model, not
~0 as expected.

This Day 5 generator runs the v0.3.2 model with the v0.5.0
operating-handle freedom (longer grate, deeper bed, more
compartments, etc.) and produces synthetic data that IS
consistent with the model. The Day 5 calibration can then
recover the parameters from this data without the infeasibility
issue.

The generator runs the v0.5.0 model at a known operating point
and records the KPIs as the synthetic data target. The target
is what the v0.5.0 model can actually deliver.
"""
from __future__ import annotations

import csv
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nepal_cooler_sim.cooler_ode import (
    CoolerParameters, solve_steady_state, compute_outputs,
)

# Deterministic seed
random.seed(20260722)

# Anchor time: 2026-07-15, 14:00 NPT
ANCHOR_UTC = datetime(2026, 7, 15, 8, 15, 0, tzinfo=timezone.utc)
DURATION_MIN = 240
SAMPLE_EVERY_MIN = 1

# v0.5.0 operating point (with operating-handle freedom)
# This is the "design-duty" that the v0.5.0 model can actually
# deliver. The target means (sec_air, clinker, exhaust) come from
# running the v0.5.0 model with this operating point, NOT from
# a hand-coded function.
DESIGN_DUTY = dict(
    grate_length_m=42.0,           # longer grate (50 m at upper)
    bed_depth_m=1.0,                # deeper bed (1.0 m at upper)
    n_compartments=7,               # 7 compartments (max allowed in v0.3.2; box [3, 7])
    grate_speed_m_min=11.0,
    under_grate_air_velocity_m_s=3.5,
    recuperator_preheat_c=120.0,
    coal_rate_kg_s=3.4,
    secondary_air_excess_factor=1.15,
    emissivity=0.88,
    void_fraction=0.45,
    altitude_m=1400.0,
    ambient_t_c=32.0,
    ambient_rh=0.75,
)

# Per-field 1-sigma measurement noise (Kabita's data_quality_tiers.py)
NOISE = dict(
    clinker_outlet_T_c   = 15.0,
    secondary_air_T_c    = 20.0,
    exhaust_T_c          = 10.0,
    fan_amp_4_20mA       = 0.5,
    grate_speed_hz       = 2.0,
    ambient_T_c          = 1.0,
    ambient_rh_pct       = 5.0,
)

# Per-field sinusoid amplitude for the operator-tuning cycle
TREND_AMP = dict(
    clinker_outlet_T_c   = 6.0,
    secondary_air_T_c    = 20.0,
    exhaust_T_c          = 5.0,
    fan_amp_4_20mA       = 1.0,
    grate_speed_hz       = 0.5,
    ambient_T_c          = 1.0,
    ambient_rh_pct       = 2.0,
)


def run_model_at(t_min: float) -> dict:
    """Run the v0.5.0 model at minute t_min with the design-duty
    operating point. Returns the KPIs as a dict."""
    import math
    # Sinusoid on grate_speed and air_velocity (operator tuning cycle)
    sin_t = math.sin(2.0 * math.pi * t_min / 60.0)
    cos_t = math.cos(2.0 * math.pi * t_min / 60.0)
    p = CoolerParameters(
        length_m=DESIGN_DUTY["grate_length_m"],
        bed_depth_m=DESIGN_DUTY["bed_depth_m"],
        n_compartments=DESIGN_DUTY["n_compartments"],
        grate_speed_m_min=DESIGN_DUTY["grate_speed_m_min"] + 0.5 * sin_t,
        under_grate_air_velocity_m_s=DESIGN_DUTY["under_grate_air_velocity_m_s"] + 0.1 * cos_t,
        coal_rate_kg_s=DESIGN_DUTY["coal_rate_kg_s"],
        secondary_air_excess_factor=DESIGN_DUTY["secondary_air_excess_factor"],
        emissivity=DESIGN_DUTY["emissivity"],
        void_fraction=DESIGN_DUTY["void_fraction"],
        under_grate_air_temp_c=DESIGN_DUTY["recuperator_preheat_c"] + DESIGN_DUTY["ambient_t_c"] + 5.0 * sin_t,
        ambient_t_c=DESIGN_DUTY["ambient_t_c"],
        ambient_rh=DESIGN_DUTY["ambient_rh"],
    )
    state = solve_steady_state(p)
    out = compute_outputs(state, p)
    return out


def observed_value(field: str, t_min: float) -> float:
    """Observed = design duty + measurement noise (Gaussian, 1-sigma)."""
    import math
    out = run_model_at(t_min)
    field_to_model = {
        "clinker_outlet_T_c": "clinker_outlet_c",
        "secondary_air_T_c":  "secondary_air_outlet_c",
        "exhaust_T_c":        "exhaust_air_outlet_c",
    }
    if field in field_to_model:
        true_val = float(out[field_to_model[field]])
    elif field == "fan_amp_4_20mA":
        true_val = 72.0
    elif field == "grate_speed_hz":
        true_val = 33.0
    elif field == "ambient_T_c":
        true_val = DESIGN_DUTY["ambient_t_c"]
    elif field == "ambient_rh_pct":
        true_val = DESIGN_DUTY["ambient_rh"] * 100.0
    else:
        true_val = 0.0
    sigma = NOISE[field]
    return round(true_val + random.gauss(0.0, sigma), 2)


def main() -> None:
    here = Path(__file__).parent
    out = here / "data" / "synthetic_planta_v050_shift_4h.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    n = DURATION_MIN // SAMPLE_EVERY_MIN
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "timestamp_utc",
            "clinker_outlet_T_c",
            "secondary_air_T_c",
            "exhaust_T_c",
            "fan_amp_4_20mA",
            "grate_speed_hz",
            "ambient_T_c",
            "ambient_rh_pct",
        ])
        for i in range(n):
            ts = ANCHOR_UTC + timedelta(minutes=i * SAMPLE_EVERY_MIN)
            w.writerow([
                ts.isoformat(),
                observed_value("clinker_outlet_T_c",   i),
                observed_value("secondary_air_T_c",    i),
                observed_value("exhaust_T_c",         i),
                observed_value("fan_amp_4_20mA",       i),
                observed_value("grate_speed_hz",       i),
                observed_value("ambient_T_c",          i),
                observed_value("ambient_rh_pct",       i),
            ])

    # Get the model output at the design-duty point (i=0, no sinusoid)
    p = CoolerParameters(
        length_m=DESIGN_DUTY["grate_length_m"],
        bed_depth_m=DESIGN_DUTY["bed_depth_m"],
        n_compartments=DESIGN_DUTY["n_compartments"],
        grate_speed_m_min=DESIGN_DUTY["grate_speed_m_min"],
        under_grate_air_velocity_m_s=DESIGN_DUTY["under_grate_air_velocity_m_s"],
        coal_rate_kg_s=DESIGN_DUTY["coal_rate_kg_s"],
        secondary_air_excess_factor=DESIGN_DUTY["secondary_air_excess_factor"],
        emissivity=DESIGN_DUTY["emissivity"],
        void_fraction=DESIGN_DUTY["void_fraction"],
        under_grate_air_temp_c=DESIGN_DUTY["recuperator_preheat_c"] + DESIGN_DUTY["ambient_t_c"],
        ambient_t_c=DESIGN_DUTY["ambient_t_c"],
        ambient_rh=DESIGN_DUTY["ambient_rh"],
    )
    state = solve_steady_state(p)
    out_kpi = compute_outputs(state, p)

    print(f"wrote {out}  ({n} rows, 1-min sampling, 4-h shift)")
    print()
    print(f"design-duty v0.5.0 model output at t=0 (the synthetic target):")
    print(f"  secondary_air_outlet_c  = {out_kpi['secondary_air_outlet_c']:.1f} C  (band 600-1000)")
    print(f"  clinker_outlet_c        = {out_kpi['clinker_outlet_c']:.1f} C  (band 120-200)")
    print(f"  exhaust_air_outlet_c    = {out_kpi['exhaust_air_outlet_c']:.1f} C  (band 150-300)")
    print(f"  cooler_efficiency       = {out_kpi['cooler_efficiency']:.3f}    (band 0.65-0.85)")
    print(f"  first_law_imbalance     = {out_kpi['first_law_imbalance']:.2e}  (band <=0.02)")
    print()
    print("HONEST: this v0.5.0 model output is what the synthetic data targets.")
    print("        Day 5 calibration should converge to loss ~0 on this target.")


if __name__ == "__main__":
    main()
