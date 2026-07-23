"""
Plant-data calibration.

Adjust selected kiln parameters to match observed plant KPIs (e.g. SEC,
burning-zone temperature, CO2 intensity). Uses differential evolution
on a bounded parameter space, with the residual being the weighted
sum of squared errors between simulated and observed KPIs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import differential_evolution

from .kiln_ode import KilnParameters, run_to_steady_state, compute_outputs


@dataclass
class CalibrationResult:
    """Outcome of a calibration run."""
    success: bool
    best_params: KilnParameters
    observed: Dict[str, float]
    simulated: Dict[str, float]
    rmse: float
    n_iterations: int
    message: str = ""


# Bounds for each tunable parameter (relative or absolute)
DEFAULT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "arrhenius_a":           (1.0e5, 5.0e6),
    "arrhenius_ea_j_per_mol":(80_000.0, 150_000.0),
    "precalciner_degree":    (0.70, 0.98),
    "preheater_efficiency":  (0.80, 0.96),
    "cooler_efficiency":     (0.55, 0.90),
    "wall_loss_coeff_w_m2_k":(1.0, 6.0),
    "emissivity":            (0.70, 0.95),
}


def calibrate_to_plant(
    base: KilnParameters,
    observed: Dict[str, float],
    tunable: Optional[List[str]] = None,
    bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    weights: Optional[Dict[str, float]] = None,
    maxiter: int = 30,
    seed: int = 42,
) -> CalibrationResult:
    """Calibrate `base` to plant-observed KPIs.

    Parameters
    ----------
    base : KilnParameters
        Starting point.
    observed : dict
        Plant KPIs, e.g. {"sec_mj_per_t_clinker": 3850, "co2_intensity_kg_per_t_clinker": 880}.
    tunable : list of str, optional
        Parameter names to tune. Default: all in DEFAULT_BOUNDS.
    bounds : dict, optional
        Override bounds for some parameters.
    weights : dict, optional
        Per-output weights. Default: equal.
    maxiter : int
        Maximum DE iterations.
    seed : int
        Random seed.
    """
    tunable = list(tunable) if tunable else list(DEFAULT_BOUNDS.keys())
    bnd = dict(DEFAULT_BOUNDS)
    if bounds:
        bnd.update(bounds)
    bnd = {k: bnd[k] for k in tunable if k in bnd}
    if not bnd:
        return CalibrationResult(
            success=False, best_params=base, observed=observed,
            simulated={}, rmse=float("inf"), n_iterations=0,
            message="No tunable parameters specified",
        )

    keys_out = list(observed.keys())
    if weights is None:
        weights = {k: 1.0 for k in keys_out}

    def objective(x: np.ndarray) -> float:
        overrides = {k: float(v) for k, v in zip(bnd.keys(), x)}
        try:
            p = base.model_copy(update=overrides)
            state = run_to_steady_state(p, max_t_s=180.0)   # short for calibration
            sim = compute_outputs(state, p)
        except Exception:
            return 1e9
        if not keys_out:
            return 0.0
        sse = 0.0
        for k in keys_out:
            obs = observed[k]
            pred = sim.get(k, 0.0)
            if obs == 0:
                continue
            sse += weights.get(k, 1.0) * ((pred - obs) / obs) ** 2
        return sse

    bounds_list = [bnd[k] for k in bnd.keys()]
    popsize = max(5, min(15, 4 * len(bounds_list)))
    result = differential_evolution(
        objective, bounds=bounds_list, maxiter=maxiter, seed=seed,
        tol=1e-4, polish=False, workers=1, popsize=popsize,
    )

    best_overrides = {k: float(v) for k, v in zip(bnd.keys(), result.x)}
    best_params = base.model_copy(update=best_overrides)
    state = run_to_steady_state(best_params, max_t_s=3600.0)
    sim = compute_outputs(state, best_params)
    rmse = float(np.sqrt(result.fun))

    return CalibrationResult(
        success=bool(result.success),
        best_params=best_params,
        observed=observed,
        simulated=sim,
        rmse=rmse,
        n_iterations=int(result.nit),
        message=str(result.message),
    )
