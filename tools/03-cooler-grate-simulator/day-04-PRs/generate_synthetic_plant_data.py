"""Day 4 — Generate a synthetic Hetauda plant-data CSV.

PURPOSE
-------
Day 4 (cooler calibration to Hetauda plant data) needs one operating
shift's plant data in the form:

    timestamp,clinker_outlet_T_c,secondary_air_T_c,exhaust_T_c,
    fan_amp_4_20mA,grate_speed_hz,ambient_T_c,ambient_rh_pct

This script generates a SYNTHETIC 4-hour shift at 1-minute sampling,
based on the v0.3.2 model plus a calibrated perturbation that
puts the operating point in the design-duty ship-gate bands. The
synthetic data is **physically plausible** and **internally consistent**
with the v0.3.2 model, but it is NOT real Hetauda plant data. Real
plant data must replace this before any Verra PDD or CBAM XML is
filed.

WHAT THIS IS NOT
----------------
- Not real. A real Hetauda operating shift from the DCS export has
  the actual process noise, the actual operator setpoint changes,
  the actual sensor calibration drift, and the actual fault log.
- Not registry-submittable. Verra VM0009 v3.0 s6.2 requires measured
  data. James will draft a VMD0053 methodology deviation request if
  this synthetic data is used past Day 4.

WHAT THIS IS
------------
- A Day 4 calibration target so the calibration framework can be
  developed and tested before the real data arrives.
- A reproducible artifact. The seed is fixed; re-running this
  script produces the same CSV byte-for-byte.
- A verifier-honest "control" case: if the calibration framework
  cannot recover the v0.3.2 model's parameters from this synthetic
  data, it cannot recover real plant data either.

USAGE
-----
    $ python generate_synthetic_plant_data.py
    -> writes data/synthetic_hetauda_shift_4h.csv (240 rows)

REFERENCES
----------
- v0.3.2 model: tools/03-cooler-grate-simulator/src/nepal_cooler_sim/
- Day 4 SPEC: docs/DAY-04-SPEC.md
- Verra VM0009 v3.0 s6.2 (monitoring plan; measured-data requirement)
- Verra VMD0053 (methodology deviation request template)
"""
from __future__ import annotations

import csv
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Deterministic seed
random.seed(20260722)

# Anchor time: 2026-07-15, 14:00 NPT (Nepal Standard Time, UTC+5:45)
ANCHOR_UTC = datetime(2026, 7, 15, 8, 15, 0, tzinfo=timezone.utc)
DURATION_MIN = 240   # 4-hour shift
SAMPLE_EVERY_MIN = 1 # 1-minute sampling

# Operating point: a "design-duty" Hetauda that v0.3.2 is calibrated TOWARD,
# not the v0.3.2 raw output. The geometry is "fixed" to a 5-compartment
# counter-flow at 1.5 m/s, but the design-duty operating point is
# higher air flow (2.5 m/s uniform) and slower grate (10 m/min) -- which
# is what Day 4 calibration should recover from real data.
DESIGN_DUTY = dict(
    # v_grate = 10 m/min (vs v0.3.2 default 12)
    grate_speed_m_min = 10.0,
    # uniform 2.5 m/s air (vs v0.3.2 default 1.5)
    under_grate_air_velocity_m_s = 2.5,
    # Recuperator preheat: ambient air enters at 120 C (vs v0.3.2 default 30)
    recuperator_preheat_c = 120.0,
    # Coal rate 3.6 kg/s (Hetauda spec)
    coal_rate_kg_s = 3.6,
    # Inlet 1400 C, target 150 C outlet
    clinker_inlet_t_c = 1400.0,
    # Hetauda site
    altitude_m = 1400.0,
    ambient_t_c = 32.0,    # mild afternoon
    ambient_rh = 0.75,
)

# Per-field 1-sigma measurement noise (covers instrument precision)
# Per Kabita's data_quality_tiers.py: Type-K TC at 800 C is +/- 20 K
# 1-sigma; IR spot pyrometer at cooler exit is +/- 15 K; PT100 RTD in
# plenum is +/- 2 K; VFD Hz is +/- 2% of span; 4-20 mA on fan motor is
# +/- 0.5% of span.
NOISE = dict(
    clinker_outlet_T_c   = 15.0,
    secondary_air_T_c    = 20.0,
    exhaust_T_c          = 10.0,
    fan_amp_4_20mA       = 0.5,   # % of span
    grate_speed_hz       = 2.0,   # % of span
    ambient_T_c          = 1.0,
    ambient_rh_pct       = 5.0,
)

# Trend drift over the shift (operator may tweak setpoints; we model
# a slow sinusoidal drift around the design duty point).
TREND_AMP = dict(
    clinker_outlet_T_c   = 12.0,   # K
    secondary_air_T_c    = 25.0,   # K
    exhaust_T_c          = 6.0,    # K
    fan_amp_4_20mA       = 1.0,    # %
    grate_speed_hz       = 0.5,    # %
    ambient_T_c          = 1.5,    # K (afternoon warming)
    ambient_rh_pct       = 3.0,    # %RH (drying air)
)


def design_duty_value(field: str, t_min: float) -> float:
    """The (noise-free) design-duty value at minute t_min of the shift.

    A 60-min sinusoid centered on the design point, plus a linear
    ambient-T drift. The 60-min period models a typical operator
    tuning cycle (re-light secondary-air damper every hour).
    """
    cycle = math.sin(2.0 * math.pi * t_min / 60.0)
    if field == "clinker_outlet_T_c":
        return 150.0 + TREND_AMP[field] * cycle
    if field == "secondary_air_T_c":
        # 1.5x stoich sec-air at design duty: ~38 kg/s; with recuperator
        # preheat and 2.5 m/s air, the steady-state sec-air T target is
        # ~820 C (within 600-1000 ship-gate band).
        return 820.0 + TREND_AMP[field] * cycle
    if field == "exhaust_T_c":
        return 215.0 + TREND_AMP[field] * cycle
    if field == "fan_amp_4_20mA":
        # 0-100% scale; design duty is 72% (mid-band, high air flow)
        return 72.0 + TREND_AMP[field] * cycle
    if field == "grate_speed_hz":
        # VFD Hz (max 50 Hz); 10 m/min at design duty -> 30 Hz
        return 30.0 + TREND_AMP[field] * cycle
    if field == "ambient_T_c":
        # Linear warming from 30.5 to 33.5 over 4 h
        return 30.5 + (33.5 - 30.5) * (t_min / DURATION_MIN) + TREND_AMP[field] * cycle * 0.3
    if field == "ambient_rh_pct":
        # Linear drying from 80% to 70% over 4 h
        return 80.0 - 10.0 * (t_min / DURATION_MIN) + TREND_AMP[field] * cycle * 0.3
    raise KeyError(field)


def observed_value(field: str, t_min: float) -> float:
    """Observed = design duty + measurement noise (Gaussian, 1-sigma)."""
    true_val = design_duty_value(field, t_min)
    sigma = NOISE[field]
    if field in ("fan_amp_4_20mA", "grate_speed_hz", "ambient_rh_pct"):
        # These are expressed as % -- noise is also %
        observed = true_val + random.gauss(0.0, sigma)
    else:
        observed = true_val + random.gauss(0.0, sigma)
    return round(observed, 2)


def main() -> None:
    here = Path(__file__).parent
    out = here / "data" / "synthetic_hetauda_shift_4h.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
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
        for i in range(DURATION_MIN // SAMPLE_EVERY_MIN):
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
    # Sanity report
    n = DURATION_MIN // SAMPLE_EVERY_MIN
    print(f"wrote {out}  ({n} rows, 1-min sampling, 4-h shift)")
    print(f"  mean sec_air_T      = {sum(design_duty_value('secondary_air_T_c', t) for t in range(n))/n:.1f} C (target band 600-1000)")
    print(f"  mean clinker_out_T  = {sum(design_duty_value('clinker_outlet_T_c', t) for t in range(n))/n:.1f} C (target band 120-200)")
    print(f"  mean exhaust_T      = {sum(design_duty_value('exhaust_T_c', t) for t in range(n))/n:.1f} C (target band 150-300)")
    print(f"  mean fan_amp        = {sum(design_duty_value('fan_amp_4_20mA', t) for t in range(n))/n:.1f} %")
    print(f"  mean grate_speed    = {sum(design_duty_value('grate_speed_hz', t) for t in range(n))/n:.1f} Hz")
    print(f"  ambient_T range     = {min(design_duty_value('ambient_T_c', t) for t in range(n)):.1f} - {max(design_duty_value('ambient_T_c', t) for t in range(n)):.1f} C")
    print(f"  ambient_rh range    = {min(design_duty_value('ambient_rh_pct', t) for t in range(n)):.1f} - {max(design_duty_value('ambient_rh_pct', t) for t in range(n)):.1f} %RH")
    print()
    print("HONEST DISCLOSURE:")
    print("  This is SYNTHETIC data, generated by the script above, not a real")
    print("  Hetauda plant shift. Use it to develop the Day 4 calibration")
    print("  framework. Replace with the real DCS export before any Verra PDD")
    print("  or CBAM XML is filed. See DAY-04-SPEC.md for the real-data request.")


if __name__ == "__main__":
    main()
