"""
Sensitivity analysis and uncertainty quantification for the kiln.

Two methods supported:

  * sensitivity_sweep      - one-at-a-time (OAT) sweep over a list of factors
  * morris_elementary_effects - Morris screening for non-linear effects

For full Sobol variance decomposition, use SALib directly (not bundled here
to keep dependencies lean).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from .kiln_ode import KilnParameters, run_to_steady_state, compute_outputs


def sensitivity_sweep(
    base: KilnParameters,
    factor: str,
    values: List[float],
    output_key: str = "sec_mj_per_t_clinker",
) -> List[Dict[str, float]]:
    """One-at-a-time sensitivity sweep.

    Parameters
    ----------
    base : KilnParameters
        Base case.
    factor : str
        Field name on KilnParameters to vary (e.g. "fuel_rate_t_h").
    values : list
        Values to test (in absolute units, not relative).
    output_key : str
        Which key of compute_outputs() to track.

    Returns
    -------
    list of dicts: [{factor, value, output, sec_mj_per_t_clinker, ...}, ...]
    """
    results = []
    for v in values:
        params = base.model_copy(update={factor: v})
        state = run_to_steady_state(params, max_t_s=3600.0)
        outs = compute_outputs(state, params)
        row = {"factor": factor, "value": float(v), "output": float(outs.get(output_key, 0.0))}
        row.update({k: float(val) for k, val in outs.items()})
        results.append(row)
    return results


def morris_elementary_effects(
    base: KilnParameters,
    factors: List[str],
    delta: float = 0.10,
    n_trajectories: int = 10,
    output_fn: Optional[Callable[[KilnParameters], float]] = None,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """Morris elementary effects (screening).

    For each factor, returns:
      - mu_star: mean of absolute elementary effects
      - sigma: standard deviation of elementary effects
      - mu_star_conf: mu_star / sigma (signal-to-noise; >1 = important)

    Parameters
    ----------
    base : KilnParameters
    factors : list of str
        Field names to perturb.
    delta : float
        Fractional perturbation (0.10 = ±10%).
    n_trajectories : int
        Number of random trajectories.
    output_fn : callable
        Maps KilnParameters -> scalar output.
        Default: SEC (lower is better).
    seed : int
        Random seed.
    """
    if output_fn is None:
        def output_fn(p: KilnParameters) -> float:
            state = run_to_steady_state(p, max_t_s=3600.0)
            return compute_outputs(state, p)["sec_mj_per_t_clinker"]

    rng = np.random.default_rng(seed)
    results: Dict[str, List[float]] = {f: [] for f in factors}
    base_value = float(getattr(base, factors[0]))  # not used directly

    for _ in range(n_trajectories):
        # Random base point: each factor at base*(1 ± u) with u ~ U(0, delta)
        x0 = {}
        for f in factors:
            base_v = float(getattr(base, f))
            u = rng.uniform(-delta, delta)
            x0[f] = base_v * (1.0 + u)
        # Evaluate at x0
        y0 = output_fn(_patch(base, x0))
        # For each factor, perturb and re-evaluate
        for f in factors:
            x1 = dict(x0)
            x1[f] = x0[f] * (1.0 + delta)
            y1 = output_fn(_patch(base, x1))
            results[f].append((y1 - y0) / (delta * x0[f]))

    summary = {}
    for f, effects in results.items():
        if not effects:
            continue
        arr = np.array(effects)
        mu_star = float(np.mean(np.abs(arr)))
        sigma = float(np.std(arr))
        summary[f] = {
            "mu_star": mu_star,
            "sigma": sigma,
            "mu_star_conf": mu_star / max(sigma, 1e-9),
        }
    return summary


def _patch(base: KilnParameters, overrides: Dict[str, float]) -> KilnParameters:
    return base.model_copy(update=overrides)
