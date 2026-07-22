"""
One-at-a-time sensitivity sweep for cooler parameters.
"""
from __future__ import annotations

from typing import List, Dict

from .cooler_ode import (
    CoolerParameters, run_to_steady_state, compute_outputs,
)


def sensitivity_sweep(
    base: CoolerParameters,
    factor: str,
    values: List[float],
    output_key: str = "cooler_efficiency",
) -> List[Dict]:
    """One-at-a-time sensitivity sweep on a single parameter."""
    results = []
    for v in values:
        params = base.model_copy(update={factor: v})
        state = run_to_steady_state(params, max_t_s=900.0)
        outs = compute_outputs(state, params)
        row = {"factor": factor, "value": float(v), "output": float(outs.get(output_key, 0.0))}
        row.update({k: float(val) for k, val in outs.items()})
        results.append(row)
    return results
