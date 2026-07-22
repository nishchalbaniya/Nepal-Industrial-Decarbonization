"""Day 4 (v0.4.0) -- plant-data calibration framework skeleton.

This module consumes a Hetauda operating shift's plant data (CSV)
and calibrates the v0.3.2 model parameters against it.

The skeleton defines the data contract and the loss function. The
actual optimizer (Hiro's `calibrate_to_plant_data()`) is Day 4 work
and is not yet implemented. The skeleton lets the Day 4 PR land
incrementally: the schema first, then the optimizer, then the
Sobol sweep, then the fragility tests.

Why this lives in `src/nepal_cooler_sim/calibration.py` (production
code) rather than `tests/` or `day-04-PRs/`: the calibration is a
v0.4.0 deliverable, not a Day 3 deliverable. The Day 3 ship is the
v0.3.2 model; the calibration is the upgrade that brings the model
into the ship-gate bands.

CITES
-----
- Saltelli, A. et al. (2010). "Variance based sensitivity analysis of
  model output. Design and estimator for the total sensitivity index."
  Computer Physics Communications 181:259-261. (Sobol sampling plan.)
- Sobol', I.M. (2001). "Global sensitivity indices for nonlinear
  mathematical models and their Monte Carlo estimates."
  Mathematics and Computers in Simulation 55:271-280.
- Theil, H. (1966). "Applied Economic Forecasting." (Theil-Sen
  robust regression as a fallback when the data is short.)
- JCGM 100:2008 (GUM). "Evaluation of measurement data -- Guide to
  the expression of uncertainty in measurement." (Per-field 1-sigma
  propagation through the calibration loss function.)
- Peray, K.E. & Waddell, J.J. (1986) s6.4. (Sec-air and exhaust
  bands used as the calibration target windows.)
- Mujumdar, K.S. (2007) s2.2, s3.1. (h_eff curve used as the
  calibration h parameter; 2nd-law clamp as a hard constraint.)
- Verra VM0009 v3.0 s6.2 (monitoring plan; measured-data requirement).
- Verra VMD0053 (methodology deviation request template; for the
  synthetic-data fallback case).
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from .cooler_ode import CoolerParameters, solve_steady_state, compute_outputs


# ---------------------------------------------------------------------------
# Plant-data row schema
# ---------------------------------------------------------------------------
class PlantDataRow(BaseModel):
    """One minute of Hetauda cooler operating data.

    Cite:
    - Peray & Waddell (1986) s6.4 (sec-air and exhaust instrument
      conventions).
    - ISA-5.1 / ISA-5.3 (instrument tag conventions; the field
      names here map to TI-1101 sec-air, TI-1103 exhaust, FT-1101
      fan, SC-1101 grate, etc.).
    - Kabita's data_quality_tiers.py: per-field 1-sigma noise
      floors used in the calibration loss function.
    """

    timestamp_utc: str
    clinker_outlet_T_c: float = Field(..., ge=80.0, le=300.0)
    secondary_air_T_c: float = Field(..., ge=200.0, le=1200.0)
    exhaust_T_c: float = Field(..., ge=50.0, le=400.0)
    fan_amp_4_20mA: float = Field(..., ge=0.0, le=100.0,
                                   description="Fan current as % of span (4-20 mA loop)")
    grate_speed_hz: float = Field(..., ge=0.0, le=60.0,
                                  description="VFD Hz (not m/min); convert via VFD calibration")
    ambient_T_c: float = Field(..., ge=-20.0, le=55.0)
    ambient_rh_pct: float = Field(..., ge=0.0, le=100.0)


class PlantDataShift(BaseModel):
    """A 4-hour Hetauda operating shift.

    `n_rows` is the row count after filtering (rows with NaN, rows
    flagged as fault, rows outside the 4-h steady-state window).
    `mean_sec_air_T_c`, `mean_clinker_T_c` etc. are the shift means
    used as the calibration targets.
    """

    rows: List[PlantDataRow]
    n_rows: int
    mean_sec_air_T_c: float
    mean_clinker_T_c: float
    mean_exhaust_T_c: float
    mean_fan_amp_pct: float
    mean_grate_speed_hz: float
    mean_ambient_T_c: float
    mean_ambient_rh_pct: float
    sec_air_sigma_K: float = Field(
        ..., description="1-sigma noise on sec_air_T (Type-K TC at 800 C, ~20 K)")
    clinker_sigma_K: float = Field(
        ..., description="1-sigma noise on clinker_out_T (IR spot pyrometer, ~15 K)")
    exhaust_sigma_K: float = Field(
        ..., description="1-sigma noise on exhaust_T (TC in plenum, ~10 K)")

    @field_validator("n_rows")
    @classmethod
    def _n_rows_matches(cls, v: int, info) -> int:
        rows = info.data.get("rows")
        if rows is not None and len(rows) != v:
            raise ValueError(f"n_rows={v} != len(rows)={len(rows)}")
        return v


# ---------------------------------------------------------------------------
# Calibration parameters (with bounds)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CalibrationParameter:
    """One parameter in the calibration box.

    The calibration fits a 7-parameter box:
    1. grate_speed_m_min
    2. under_grate_air_velocity_m_s (uniform across compartments)
    3. recuperator_preheat_c (T_a_inlet shift above ambient)
    4. coal_rate_kg_s (sec-air stoichiometry)
    5. secondary_air_excess_factor (1.0-1.2x stoich)
    6. emissivity (clinker surface)
    7. void_fraction (bed)

    Each parameter has a lower bound, an upper bound, and a prior
    (default = mid-band). The Sobol sweep (Day 4 work) varies each
    parameter uniformly across [lo, hi] with the Saltelli N=1024
    plan. The least-squares fit (Day 4 work) walks the box from the
    prior to the posterior using the shift means as targets.
    """
    name: str
    lo: float
    hi: float
    prior: float
    unit: str
    cite: str

    def __post_init__(self) -> None:
        if not self.lo <= self.prior <= self.hi:
            raise ValueError(
                f"CalibrationParameter {self.name}: prior {self.prior} "
                f"not in [{self.lo}, {self.hi}]"
            )


CALIBRATION_PARAMETERS: List[CalibrationParameter] = [
    CalibrationParameter(
        name="grate_speed_m_min",
        lo=8.0, hi=18.0, prior=12.0, unit="m/min",
        cite="Peray & Waddell 1986 s6.4: 10-16 m/min typical; "
             "ECRA 2022: modern BAT 12-14 m/min.",
    ),
    CalibrationParameter(
        name="under_grate_air_velocity_m_s",
        lo=1.0, hi=4.0, prior=1.5, unit="m/s",
        cite="Peray & Waddell 1986 s6.4: 1.0-2.5 m/s typical; "
             "ECRA 2022: BAT up to 3.5 m/s with pressure drop 50-80 mm H2O.",
    ),
    CalibrationParameter(
        name="recuperator_preheat_c",
        lo=0.0, hi=200.0, prior=0.0, unit="K",
        cite="Plant-specific. No recuperator at Hetauda baseline. "
             "Modern Polysius REPOL recovers 100-150 K via secondary "
             "recuperator (ECRA 2022 BAT).",
    ),
    CalibrationParameter(
        name="coal_rate_kg_s",
        lo=2.5, hi=5.0, prior=3.6, unit="kg/s",
        cite="HCIL spec: 100 kg-coal/t-cli at 130 t/h = 3.6 kg/s. "
             "ECRA 2022: modern BAT 80-90 kg-coal/t-cli = 2.9-3.3 kg/s.",
    ),
    CalibrationParameter(
        name="secondary_air_excess_factor",
        lo=1.0, hi=2.0, prior=1.10, unit="dimensionless",
        cite="Peray & Waddell 1986 s6.2: 1.05-1.15x stoich typical; "
             "Hetauda spec 1.58x stoich is the high end.",
    ),
    CalibrationParameter(
        name="emissivity",
        lo=0.7, hi=0.95, prior=0.85, unit="dimensionless",
        cite="ICCC 2006 s2.3: 0.8-0.9 for hot clinker pellets. "
             "Incropera & DeWitt 2002 Ch. 12: radiation linearization.",
    ),
    CalibrationParameter(
        name="void_fraction",
        lo=0.35, hi=0.55, prior=0.45, unit="dimensionless",
        cite="Peray & Waddell 1986 s6.4: 0.40-0.50 typical for "
             "loose-packed clinker on grate. ECRA 2022: 0.42-0.48 BAT.",
    ),
]


# ---------------------------------------------------------------------------
# Calibration loss function (skeleton)
# ---------------------------------------------------------------------------
@dataclass
class CalibrationResult:
    """Output of the least-squares calibration fit (Day 4 work).

    The skeleton defines the shape; the fitter is Day 4 work.
    """
    posterior: dict = field(default_factory=dict)
    rmse_clinker_K: float = float("nan")
    rmse_sec_air_K: float = float("nan")
    rmse_exhaust_K: float = float("nan")
    converged: bool = False
    n_iterations: int = 0
    ship_gate_pass: dict = field(default_factory=dict)


def load_plant_data(csv_path: Path) -> PlantDataShift:
    """Load a Hetauda plant-data CSV and return a typed PlantDataShift.

    The CSV format is the one produced by
    `day-04-PRs/generate_synthetic_plant_data.py` (synthetic) or
    the real DCS export format agreed with the plant engineering
    team.
    """
    rows: List[PlantDataRow] = []
    with csv_path.open(encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for raw in rdr:
            try:
                rows.append(PlantDataRow(
                    timestamp_utc=raw["timestamp_utc"],
                    clinker_outlet_T_c=float(raw["clinker_outlet_T_c"]),
                    secondary_air_T_c=float(raw["secondary_air_T_c"]),
                    exhaust_T_c=float(raw["exhaust_T_c"]),
                    fan_amp_4_20mA=float(raw["fan_amp_4_20mA"]),
                    grate_speed_hz=float(raw["grate_speed_hz"]),
                    ambient_T_c=float(raw["ambient_T_c"]),
                    ambient_rh_pct=float(raw["ambient_rh_pct"]),
                ))
            except (KeyError, ValueError) as e:
                # Skip malformed rows; a real loader should log the
                # skip + row number + error to an audit log.
                continue

    def _mean(field: str) -> float:
        return sum(getattr(r, field) for r in rows) / len(rows) if rows else 0.0

    def _stdev(field: str) -> float:
        if not rows:
            return 0.0
        m = _mean(field)
        return math.sqrt(sum((getattr(r, field) - m) ** 2 for r in rows) / (len(rows) - 1))

    return PlantDataShift(
        rows=rows,
        n_rows=len(rows),
        mean_sec_air_T_c=_mean("secondary_air_T_c"),
        mean_clinker_T_c=_mean("clinker_outlet_T_c"),
        mean_exhaust_T_c=_mean("exhaust_T_c"),
        mean_fan_amp_pct=_mean("fan_amp_4_20mA"),
        mean_grate_speed_hz=_mean("grate_speed_hz"),
        mean_ambient_T_c=_mean("ambient_T_c"),
        mean_ambient_rh_pct=_mean("ambient_rh_pct"),
        sec_air_sigma_K=_stdev("secondary_air_T_c"),
        clinker_sigma_K=_stdev("clinker_outlet_T_c"),
        exhaust_sigma_K=_stdev("exhaust_T_c"),
    )


def calibration_loss(
    candidate: dict,
    target: PlantDataShift,
) -> float:
    """Loss function: weighted squared error in [K] units.

    Day 4 work to fill in: this is the *log-prior + chi-square*
    log-posterior. The skeleton is a pure chi-square against the
    shift means. The full posterior requires the Jacobian of the
    v0.3.2 model outputs with respect to each calibration
    parameter, which Hiro's UQ work is the right home for.

    Cite: JCGM 100:2008 GUM for the 1-sigma weighting; Theil 1966
    for the robust-regression fallback when the data is short.
    """
    # Build a CoolerParameters from the candidate dict + the
    # shift's mean ambient conditions.
    p = CoolerParameters(
        grate_speed_m_min=candidate.get("grate_speed_m_min", 12.0),
        under_grate_air_velocity_m_s=candidate.get(
            "under_grate_air_velocity_m_s", 1.5
        ),
        coal_rate_kg_s=candidate.get("coal_rate_kg_s", 3.6),
        secondary_air_excess_factor=candidate.get(
            "secondary_air_excess_factor", 1.10
        ),
        emissivity=candidate.get("emissivity", 0.85),
        void_fraction=candidate.get("void_fraction", 0.45),
        under_grate_air_temp_c=candidate.get(
            "recuperator_preheat_c", 0.0
        ) + target.mean_ambient_T_c,
        ambient_t_c=target.mean_ambient_T_c,
        ambient_rh=target.mean_ambient_rh_pct / 100.0,
    )
    # Run the model.
    state = solve_steady_state(p)
    out = compute_outputs(state, p)
    # Chi-square.
    chi2 = 0.0
    chi2 += ((out["secondary_air_outlet_c"] - target.mean_sec_air_T_c)
             / max(target.sec_air_sigma_K, 1.0)) ** 2
    chi2 += ((out["clinker_outlet_c"] - target.mean_clinker_T_c)
             / max(target.clinker_sigma_K, 1.0)) ** 2
    chi2 += ((out["exhaust_air_outlet_c"] - target.mean_exhaust_T_c)
             / max(target.exhaust_sigma_K, 1.0)) ** 2
    return chi2


def calibrate_to_plant_data(target: PlantDataShift) -> CalibrationResult:
    """Run the least-squares calibration fit.

    Day 4 work: this is the *placeholder* for the optimizer. It
    returns the prior (no fit performed) so the rest of the
    framework can be wired up incrementally. The optimizer lands
    in a follow-up PR; the schema, the loss function, and the
    target loader are the Day 4 first cut.
    """
    posterior = {p.name: p.prior for p in CALIBRATION_PARAMETERS}
    return CalibrationResult(
        posterior=posterior,
        rmse_clinker_K=float("nan"),
        rmse_sec_air_K=float("nan"),
        rmse_exhaust_K=float("nan"),
        converged=False,
        n_iterations=0,
        ship_gate_pass={},
    )


__all__ = [
    "PlantDataRow",
    "PlantDataShift",
    "CalibrationParameter",
    "CALIBRATION_PARAMETERS",
    "CalibrationResult",
    "load_plant_data",
    "calibration_loss",
    "calibrate_to_plant_data",
]
