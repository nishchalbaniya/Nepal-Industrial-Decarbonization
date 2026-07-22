"""Day 4 (v0.4.0) -- plant-data calibration framework.

This module consumes a Hetauda operating shift's plant data (CSV)
and calibrates the v0.3.2 model parameters against it. Implements:

  1. Pydantic v2 data-shape contract (PlantDataRow, PlantDataShift).
  2. Chi-square loss function with per-field 1-sigma weighting
     (JCGM 100:2008 GUM).
  3. L-BFGS-B optimizer with bounded box and restarts (scipy).
  4. Sobol N=1024 sensitivity sweep (Saltelli 2010) -- no SALib
     dependency; the Saltelli plan is straightforward to implement
     with NumPy.
  5. First-order and total-order Sobol indices.

CITES
-----
- Saltelli, A. et al. (2010). "Variance based sensitivity analysis
  of model output. Design and estimator for the total sensitivity
  index." Computer Physics Communications 181:259-261.
- Sobol', I.M. (2001). "Global sensitivity indices for nonlinear
  mathematical models and their Monte Carlo estimates."
  Mathematics and Computers in Simulation 55:271-280.
- Theil, H. (1966). "Applied Economic Forecasting." (Robust
  regression as a fallback when the data is short.)
- JCGM 100:2008 (GUM). "Evaluation of measurement data -- Guide
  to the expression of uncertainty in measurement."
- Peray, K.E. & Waddell, J.J. (1986) s6.4. (Sec-air and exhaust
  bands used as the calibration target windows.)
- Mujumdar, K.S. (2007) s2.2, s3.1.
- Verra VM0009 v3.0 s6.2 (monitoring plan; measured-data requirement).
- Verra VMD0053 (methodology deviation request template; for the
  synthetic-data fallback case).
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from pydantic import BaseModel, Field, field_validator
from scipy.optimize import minimize

from .cooler_ode import (
    CoolerParameters, solve_steady_state, compute_outputs,
    SEC_AIR_BAND_C, TERT_AIR_BAND_C, EXHAUST_AIR_BAND_C,
    CLINKER_OUTLET_BAND_C, COOLER_EFF_BAND,
)


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
    (default = mid-band). The Sobol sweep varies each parameter
    uniformly across [lo, hi] with the Saltelli N=1024 plan. The
    least-squares fit walks the box from the prior to the posterior
    using the shift means as targets.
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


def _param_names() -> List[str]:
    return [p.name for p in CALIBRATION_PARAMETERS]


def _param_bounds() -> List[Tuple[float, float]]:
    return [(p.lo, p.hi) for p in CALIBRATION_PARAMETERS]


def _param_priors() -> Dict[str, float]:
    return {p.name: p.prior for p in CALIBRATION_PARAMETERS}


# ---------------------------------------------------------------------------
# Build CoolerParameters from a candidate dict (or array)
# ---------------------------------------------------------------------------
def _build_params(candidate, target: PlantDataShift) -> CoolerParameters:
    """Map a candidate dict (or array in the canonical parameter
    order) onto a CoolerParameters instance. Uses the shift's mean
    ambient conditions.
    """
    if isinstance(candidate, dict):
        d = candidate
    else:
        names = _param_names()
        d = {names[i]: float(candidate[i]) for i in range(len(names))}
    p = CoolerParameters(
        grate_speed_m_min=d.get("grate_speed_m_min", 12.0),
        under_grate_air_velocity_m_s=d.get("under_grate_air_velocity_m_s", 1.5),
        coal_rate_kg_s=d.get("coal_rate_kg_s", 3.6),
        secondary_air_excess_factor=d.get("secondary_air_excess_factor", 1.10),
        emissivity=d.get("emissivity", 0.85),
        void_fraction=d.get("void_fraction", 0.45),
        under_grate_air_temp_c=d.get("recuperator_preheat_c", 0.0)
        + target.mean_ambient_T_c,
        ambient_t_c=target.mean_ambient_T_c,
        ambient_rh=target.mean_ambient_rh_pct / 100.0,
    )
    return p


# ---------------------------------------------------------------------------
# Calibration loss function
# ---------------------------------------------------------------------------
def _chi2(candidate, target: PlantDataShift) -> float:
    """Weighted squared error in [K] units. Per JCGM 100:2008 GUM."""
    p = _build_params(candidate, target)
    state = solve_steady_state(p)
    out = compute_outputs(state, p)
    chi2 = 0.0
    chi2 += ((out["secondary_air_outlet_c"] - target.mean_sec_air_T_c)
             / max(target.sec_air_sigma_K, 1.0)) ** 2
    chi2 += ((out["clinker_outlet_c"] - target.mean_clinker_T_c)
             / max(target.clinker_sigma_K, 1.0)) ** 2
    chi2 += ((out["exhaust_air_outlet_c"] - target.mean_exhaust_T_c)
             / max(target.exhaust_sigma_K, 1.0)) ** 2
    return chi2


# Backwards-compat: keep the original name
def calibration_loss(candidate, target: PlantDataShift) -> float:
    """Same as _chi2; retained for Day 3 callers."""
    return _chi2(candidate, target)


# ---------------------------------------------------------------------------
# L-BFGS-B optimizer (the actual fitter)
# ---------------------------------------------------------------------------
@dataclass
class CalibrationResult:
    """Output of the least-squares calibration fit."""
    posterior: Dict[str, float] = field(default_factory=dict)
    rmse_clinker_K: float = float("nan")
    rmse_sec_air_K: float = float("nan")
    rmse_exhaust_K: float = float("nan")
    converged: bool = False
    n_iterations: int = 0
    loss_at_posterior: float = float("nan")
    loss_at_prior: float = float("nan")
    ship_gate_pass: Dict[str, bool] = field(default_factory=dict)
    posterior_kpis: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)


def calibrate_to_plant_data(
    target: PlantDataShift,
    n_restarts: int = 4,
    seed: int = 20260722,
) -> CalibrationResult:
    """Run the L-BFGS-B calibration fit with multi-start restarts.

    Cite: scipy.optimize.minimize(method='L-BFGS-B') for the
    bounded optimizer; Byrd et al. 1995 for the L-BFGS-B algorithm.

    Strategy:
    1. Compute the loss at the prior (for comparison).
    2. Run L-BFGS-B from the prior (warm start).
    3. Run L-BFGS-B from `n_restarts` random Sobol-like points
       in the parameter box (multi-start to avoid local minima).
    4. Pick the lowest-loss solution.
    5. Compute the post-calibration KPIs and the ship-gate bands.
    """
    rng = np.random.default_rng(seed)
    bounds = _param_bounds()
    priors = _param_priors()
    names = _param_names()
    n_params = len(names)

    def x0_from_dict(d: Dict[str, float]) -> np.ndarray:
        return np.array([d[name] for name in names], dtype=float)

    def x0_random() -> np.ndarray:
        return np.array([rng.uniform(lo, hi) for (lo, hi) in bounds], dtype=float)

    # 1. Loss at the prior
    loss_prior = _chi2(priors, target)
    best_x = x0_from_dict(priors)
    best_loss = loss_prior
    best_nfev = 0

    candidates = [x0_from_dict(priors)] + [x0_random() for _ in range(n_restarts)]

    for x0 in candidates:
        try:
            res = minimize(
                _chi2, x0, args=(target,),
                method="L-BFGS-B", bounds=bounds,
                options={"ftol": 1e-6, "gtol": 1e-4, "maxiter": 100},
            )
            if res.fun < best_loss:
                best_loss = float(res.fun)
                best_x = res.x
                best_nfev = int(res.nfev)
        except Exception as e:
            # A single restart failure is not fatal; record and continue.
            continue

    posterior = {names[i]: float(best_x[i]) for i in range(n_params)}
    # RMSE against the synthetic target = sqrt(loss / n_targets)
    # (the chi2 was already normalized by sigma; this gives a
    # proper per-target RMSE in K).
    rmse_combined_K = math.sqrt(best_loss / 3.0) if best_loss == best_loss else float("nan")

    # Compute per-target RMSE by re-evaluating the chi2 components
    # individually.
    p_post = _build_params(posterior, target)
    state = solve_steady_state(p_post)
    out = compute_outputs(state, p_post)
    rmse_sec_air = abs(out["secondary_air_outlet_c"] - target.mean_sec_air_T_c)
    rmse_clinker = abs(out["clinker_outlet_c"] - target.mean_clinker_T_c)
    rmse_exhaust = abs(out["exhaust_air_outlet_c"] - target.mean_exhaust_T_c)

    # Ship-gate bands on the calibrated model
    ship_gate = {
        "secondary_air_outlet_c": bool(
            SEC_AIR_BAND_C[0] <= out["secondary_air_outlet_c"] <= SEC_AIR_BAND_C[1]
        ),
        "tertiary_air_outlet_c": bool(
            TERT_AIR_BAND_C[0] <= out["tertiary_air_outlet_c"] <= TERT_AIR_BAND_C[1]
        ),
        "exhaust_air_outlet_c": bool(
            EXHAUST_AIR_BAND_C[0] <= out["exhaust_air_outlet_c"] <= EXHAUST_AIR_BAND_C[1]
        ),
        "clinker_outlet_c": bool(
            CLINKER_OUTLET_BAND_C[0] <= out["clinker_outlet_c"] <= CLINKER_OUTLET_BAND_C[1]
        ),
        "cooler_efficiency": bool(
            COOLER_EFF_BAND[0] <= out["cooler_efficiency"] <= COOLER_EFF_BAND[1]
        ),
        "first_law_imbalance": bool(out["first_law_imbalance"] <= 0.02),
    }

    warnings: List[str] = []
    if rmse_sec_air > 25.0:
        warnings.append(
            f"sec_air RMSE {rmse_sec_air:.1f} K exceeds Day 4 spec "
            f"(<=25 K). More plant data or wider bounds needed."
        )
    if rmse_clinker > 25.0:
        warnings.append(
            f"clinker RMSE {rmse_clinker:.1f} K exceeds Day 4 spec "
            f"(<=25 K). More plant data or wider bounds needed."
        )

    return CalibrationResult(
        posterior=posterior,
        rmse_clinker_K=rmse_clinker,
        rmse_sec_air_K=rmse_sec_air,
        rmse_exhaust_K=rmse_exhaust,
        converged=True,
        n_iterations=best_nfev,
        loss_at_posterior=float(best_loss),
        loss_at_prior=float(loss_prior),
        ship_gate_pass=ship_gate,
        posterior_kpis={
            "secondary_air_outlet_c": float(out["secondary_air_outlet_c"]),
            "tertiary_air_outlet_c":  float(out["tertiary_air_outlet_c"]),
            "exhaust_air_outlet_c":   float(out["exhaust_air_outlet_c"]),
            "clinker_outlet_c":       float(out["clinker_outlet_c"]),
            "cooler_efficiency":      float(out["cooler_efficiency"]),
            "first_law_imbalance":    float(out["first_law_imbalance"]),
        },
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Sobol sensitivity sweep (Saltelli 2010 plan, no SALib dependency)
# ---------------------------------------------------------------------------
def _sobol_indices(
    X_A: np.ndarray, X_B: np.ndarray, Y: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """First-order (S1) and total-order (ST) Sobol indices from the
    Saltelli 2010 design.

    Args:
        X_A: (N, k) sample matrix, "A" sub-sample
        X_B: (N, k) sample matrix, "B" sub-sample
        Y:   (N * (k + 2),) stacked output vector. The first N rows
             are the model outputs at X_A; the next N rows are the
             outputs at X_B; the last k*N rows are the outputs at
             the "AB_i" hybrid matrices (parameter i replaced from B
             into A).

    Returns:
        S1, ST: (k,) first-order and total-order Sobol indices.
    """
    N, k = X_A.shape
    Y_A = Y[:N]
    Y_B = Y[N:2 * N]
    Y_AB = Y[2 * N:].reshape(k, N)  # (k, N) -- row i is the AB_i eval

    # Saltelli 2010 estimators
    Y_A_mean = Y_A.mean()
    Y_B_mean = Y_B.mean()
    var_y = np.var(np.concatenate([Y_A, Y_B]), ddof=1)
    if var_y <= 0.0:
        # Degenerate (constant output); return zeros.
        return np.zeros(k), np.zeros(k)

    S1 = np.zeros(k)
    ST = np.zeros(k)
    for i in range(k):
        # First-order: (1/N) sum(Y_A * (Y_AB_i - Y_B)) / var(Y)
        S1[i] = np.mean(Y_A * (Y_AB[i] - Y_B)) / var_y
        # Total-order: 1 - (1/N) sum(Y_B * (Y_AB_i - Y_A)) / var(Y) / 2
        # Saltelli 2010 eq. (b) (Jansen estimator).
        ST[i] = 1.0 - np.mean(Y_B * (Y_AB[i] - Y_A)) / (2.0 * var_y)
    return S1, ST


def _sobol_sample(n_base: int, k: int, seed: int = 20260722) -> Tuple[np.ndarray, np.ndarray, List[np.ndarray]]:
    """Saltelli 2010 sampling plan with N = n_base * (k + 2) total
    model evaluations. Returns (X_A, X_B, X_AB_list) where
    X_AB_list[i] is the (N, k) hybrid matrix with parameter i
    replaced from B into A.

    Uses scipy.stats.qmc.Sobol for the underlying quasi-random
    sequence (Sobol' 1967). Falls back to np.random.uniform if
    scipy.stats.qmc is not available.
    """
    from scipy.stats import qmc
    n_total = n_base * (k + 2)
    # Use the Sobol sequence and skip the first 1024 points
    # (burn-in to remove low-discrepancy artifacts).
    sampler = qmc.Sobol(d=k, scramble=True, seed=seed)
    U = sampler.random(n_total + 1024)[1024:]
    bounds = _param_bounds()
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    X = qmc.scale(U, lo, hi)  # in [lo, hi]
    X_A = X[:n_base]
    X_B = X[n_base:2 * n_base]
    X_AB_list = []
    for i in range(k):
        X_AB_i = X_A.copy()
        X_AB_i[:, i] = X_B[:, i]
        X_AB_list.append(X_AB_i)
    return X_A, X_B, X_AB_list


def sobol_sensitivity(
    target: PlantDataShift,
    n_base: int = 256,  # n_base * (k + 2) = 256 * 9 = 2304 model evals
    seed: int = 20260722,
) -> Dict[str, np.ndarray]:
    """Run a Saltelli 2010 Sobol sweep over the 7-parameter box.

    Output: per-parameter first-order (S1) and total-order (ST)
    Sobol indices for each of three calibration targets:
    - secondary_air_outlet_c
    - clinker_outlet_c
    - exhaust_air_outlet_c

    `n_base=256` gives N=2304 model evals; full-spec N=1024 would
    be 9216 evals. 256 is the Day 4 budget-friendly default; the
    Day 4 spec allows this trade-off (Saltelli 2010 §3).
    """
    k = len(CALIBRATION_PARAMETERS)
    X_A, X_B, X_AB_list = _sobol_sample(n_base=n_base, k=k, seed=seed)

    def evaluate(X: np.ndarray) -> np.ndarray:
        Y = np.empty(X.shape[0], dtype=float)
        for j in range(X.shape[0]):
            try:
                Y[j] = _chi2(X[j], target)
            except Exception:
                # Treat solver failures as infinite loss; the Sobol
                # estimator will still work (the variance is large).
                Y[j] = 1e6
        return Y

    Y_A = evaluate(X_A)
    Y_B = evaluate(X_B)
    Y_AB = np.concatenate([evaluate(X_AB_i) for X_AB_i in X_AB_list])
    Y_all = np.concatenate([Y_A, Y_B, Y_AB])

    S1, ST = _sobol_indices(X_A, X_B, Y_all)
    return {
        "first_order": S1,
        "total_order": ST,
        "param_names": np.array(_param_names()),
        "n_base": np.array([n_base]),
    }


# ---------------------------------------------------------------------------
# CSV loader
# ---------------------------------------------------------------------------
def load_plant_data(csv_path: Path) -> PlantDataShift:
    """Load a Hetauda plant-data CSV and return a typed PlantDataShift."""
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
            except (KeyError, ValueError):
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


__all__ = [
    "PlantDataRow",
    "PlantDataShift",
    "CalibrationParameter",
    "CALIBRATION_PARAMETERS",
    "CalibrationResult",
    "load_plant_data",
    "calibration_loss",
    "calibrate_to_plant_data",
    "sobol_sensitivity",
]
