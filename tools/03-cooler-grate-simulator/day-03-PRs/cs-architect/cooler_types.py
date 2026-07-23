"""
Typed result + TypedDict for the v0.3.1 cooler.

Why this lives in its own module
--------------------------------
The v0.3.0 code returned a 3-tuple ``(t, y, x)`` from ``simulate_cooler``
where ``y.shape = (2*n, 1)`` and ``t = [0.0]`` — a band-aid for the kiln
I/O contract. The 1-D cooler is *quasi-steady spatial*, not *transient*
(see McCabe-Smith-Harriott §15). A typed dataclass + TypedDict makes the
shape contract self-documenting and stops the next refactor from
silently corrupting downstream code (Day 14 LLM advisor, Day 18
desktop shell).

Pydantic v2 is used for the *input* (already on v2 in cooler_ode.py).
The *result* uses a stdlib dataclass because:
  - it has no validation needs (computed, not user-supplied),
  - it round-trips through pickle and JSON without a custom encoder,
  - mypy --strict inference is simpler.

References
----------
  - McCabe, W.L., Smith, J.C. & Harriott, P. (2005), §15 (1-D HX).
  - Pydantic v2 docs — TypedDict is stdlib typing.

Module name note
----------------
This module is named ``cooler_types`` (not ``types``) so it does not
shadow the stdlib ``types`` module when the package is on ``sys.path``
for ad-hoc imports or during pytest collection. See the negotiation
post / PR comment for the rationale.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, TypedDict

import numpy as np

# Try a relative import first (production: the v0.3.1 module lives in
# the same package as `cooler_ode`). Fall back to absolute (smoke test,
# ad-hoc import, pytest collection without a conftest).
try:
    from .cooler_ode import (  # type: ignore[import-not-found]
        CoolerParameters,
        CoolerState,
        compute_outputs as _compute_outputs_compat,
        run_to_steady_state as _run_to_steady_state_compat,
    )
except ImportError:  # pragma: no cover — smoke-test path
    from nepal_cooler_sim.cooler_ode import (  # type: ignore[no-redef]
        CoolerParameters,
        CoolerState,
        compute_outputs as _compute_outputs_compat,
        run_to_steady_state as _run_to_steady_state_compat,
    )

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class ShapeContractError(ValueError):
    """Raised when a value violates the v0.3.1 shape contract.

    The shape contract is documented in :mod:`nepal_cooler_sim.__init__`.
    Anything that touches the result of ``solve_steady_state`` (CLI
    table printer, JSON serializer, pickle round-trip) should catch
    this and re-raise as a CLI-friendly error.
    """


# ---------------------------------------------------------------------------
# Spatial profile
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoolerProfile:
    """Spatial profile along the grate (quasi-steady).

    Attributes
    ----------
    x : np.ndarray, shape (n_cells,)
        Position along the grate, meters. ``x[0]`` is the kiln
        discharge (hot end), ``x[-1]`` is the clinker exit (cold end).
    t_clinker_c : np.ndarray, shape (n_cells,)
        Clinker temperature in °C at each spatial cell.
    t_air_c : np.ndarray, shape (n_cells,)
        Under-grate air temperature in °C at each spatial cell.

    Invariants (enforced by the solver + tests):
        len(x) == len(t_clinker_c) == len(t_air_c) == n_cells
        t_air_c[i] <= t_clinker_c[i] + 1e-6  for all i  (second law)
    """

    x: np.ndarray
    t_clinker_c: np.ndarray
    t_air_c: np.ndarray

    def __post_init__(self) -> None:
        if not (self.x.ndim == self.t_clinker_c.ndim == self.t_air_c.ndim == 1):
            raise ShapeContractError(
                f"CoolerProfile arrays must be 1-D, got shapes "
                f"{self.x.shape}, {self.t_clinker_c.shape}, {self.t_air_c.shape}"
            )
        if not (len(self.x) == len(self.t_clinker_c) == len(self.t_air_c)):
            raise ShapeContractError(
                f"CoolerProfile arrays must have equal length, got "
                f"len(x)={len(self.x)}, len(t_clinker_c)={len(self.t_clinker_c)}, "
                f"len(t_air_c)={len(self.t_air_c)}"
            )
        if np.any(np.isnan(self.t_clinker_c)) or np.any(np.isnan(self.t_air_c)):
            raise ShapeContractError("CoolerProfile contains NaN")

    def to_dict(self) -> dict[str, list[float]]:
        """Return a JSON-serialisable dict of lists."""
        return {
            "x": self.x.tolist(),
            "t_clinker_c": self.t_clinker_c.tolist(),
            "t_air_c": self.t_air_c.tolist(),
        }


# ---------------------------------------------------------------------------
# Typed result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CoolerResult:
    """Canonical v0.3.1 result of a quasi-steady cooler solve.

    This is the typed replacement for the v0.3.0 ``(t, y, x)`` 3-tuple.
    It is ``frozen=True`` so a result cannot be mutated after the solver
    returns it (catches a class of "I tweak the result and the test
    passes" bugs).

    Attributes
    ----------
    profile : CoolerProfile
        Spatial profile along the grate.
    secondary_air_outlet_c : float
        Secondary air temperature in °C (compartment 1 outlet in
        counter-flow / per-Ramesh the kiln-end air parcel).
    clinker_outlet_c : float
        Clinker temperature at the cooler exit in °C.
    cooler_efficiency : float
        Heat-recovery efficiency (clinker-side), dimensionless ∈ [0, 1].
    air_flow_kg_s : float
        Total under-grate air mass flow in kg/s.
    mass_flow_kg_s : float
        Clinker mass flow in kg/s (== throughput / 3.6).
    first_law_imbalance : float
        ``|Q_in - Q_recovered - Q_out| / Q_in`` — must be ≤ 0.02.
    """

    profile: CoolerProfile
    secondary_air_outlet_c: float
    clinker_outlet_c: float
    cooler_efficiency: float
    air_flow_kg_s: float
    mass_flow_kg_s: float
    first_law_imbalance: float
    # Diagnostic-only fields below; not part of the canonical contract
    # but useful for the CLI "diagnose" subcommand and for
    # `save_results_json` consumers.
    fan_power_kw: float = 0.0
    bed_pressure_drop_mm_h2o: float = 0.0
    tertiary_air_outlet_c: float = 0.0
    exhaust_air_outlet_c: float = 0.0
    free_lime_outlet_wt_pct: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """JSON-friendly dict. Arrays become lists; scalars stay scalar."""
        d = asdict(self)
        d["profile"] = self.profile.to_dict()
        return d


# ---------------------------------------------------------------------------
# TypedDict for the KPIs returned by compute_outputs()
# ---------------------------------------------------------------------------


class CoolerOutputs(TypedDict, total=False):
    """TypedDict for ``compute_outputs(state, p)``.

    ``total=False`` so individual fields can be missing (e.g. when the
    underlying state has not been computed yet, or when an optional
    measurement is unavailable). Every field that *is* present is
    strictly typed.

    This is what the CLI table printer iterates; what
    ``save_results_json`` writes under the ``"outputs"`` key; and what
    James's PDD adapter pulls from.

    Categories
    ----------
    Geometry / operating
        Length, width, grate area, throughput, mass flow.
    Thermal KPIs
        Clinker inlet/outlet, secondary air, tertiary air, exhaust.
    Energy balance
        Q_in, Q_out, Q_recovered, first-law imbalance, efficiency.
    Operator / Ramesh §4
        Fan power, bed ΔP, free lime, MJ/t-cli.
    Data quality (Kabita §6)
        Per-field tier mapping (Tier1 | Tier2 | Tier3 | measured).
    """

    # Geometry / operating
    clinker_throughput_t_h: float
    clinker_mass_flow_kg_s: float
    cooler_length_m: float
    cooler_width_m: float
    grate_area_m2: float
    n_compartments: int
    # Thermal KPIs
    clinker_inlet_c: float
    clinker_outlet_c: float
    secondary_air_outlet_c: float
    secondary_air_outlet_k: float
    secondary_air_mass_flow_nm3_h: float
    tertiary_air_outlet_c: float
    exhaust_air_outlet_c: float
    t_clinker_max_c: float
    t_clinker_min_c: float
    t_air_max_c: float
    t_air_min_c: float
    clinker_quench_rate_k_per_min: float
    free_lime_outlet_wt_pct: float
    # Energy balance
    heat_in_kw: float
    heat_out_kw: float
    heat_recovered_kw: float
    secondary_air_recovered_kw: float
    cooler_efficiency: float
    first_law_imbalance: float
    # Ramesh §4 operator KPIs
    fan_power_kw: float
    specific_fan_power_kw_per_tph: float
    bed_pressure_drop_mm_h2o: float
    secondary_air_stoich_ratio: float
    mj_per_t_cli_recovered: float
    secondary_air_recovered_gj_per_t_clinker: float
    cooler_duty_case: dict[str, Any]
    # Sanity block (Ramesh §4)
    sanity: dict[str, bool]
    # Targets
    clinker_outlet_target_c: float
    outlet_within_target: bool
    # Audit / MRV (Kabita §6)
    _data_quality: dict[str, str]


# ---------------------------------------------------------------------------
# solve_steady_state — the v0.3.1 canonical entry point
# ---------------------------------------------------------------------------


def solve_steady_state(p: CoolerParameters) -> CoolerResult:
    """Canonical v0.3.1 entry point. Returns a typed :class:`CoolerResult`.

    This wraps the v0.3.0 ``run_to_steady_state`` (which returns a
    :class:`CoolerState`) and re-projects the result into a
    :class:`CoolerResult` with explicit shape contract.

    Pydantic v2 callers can use ``model_copy(update=...)`` for what-ifs,
    cite: https://docs.pydantic.dev/latest/concepts/serialization/#model_copy
    """
    state: CoolerState = _run_to_steady_state_compat(p, max_t_s=p.t_end_s)

    profile = CoolerProfile(
        x=state.x,
        t_clinker_c=state.t_clinker_c,
        t_air_c=state.t_air_c,
    )

    # First-law imbalance: |Q_in - Q_recovered - Q_out| / Q_in
    # Use the same energy balance that compute_outputs() uses, so the
    # two stay consistent.
    outs: CoolerOutputs = _compute_outputs_compat(state, p)
    q_in = float(outs.get("heat_in_kw", 0.0))
    q_out = float(outs.get("heat_out_kw", 0.0))
    q_rec = float(outs.get("heat_recovered_kw", 0.0))
    if q_in > 0.0:
        imbalance = abs(q_in - q_rec - q_out) / q_in
    else:
        imbalance = 0.0

    return CoolerResult(
        profile=profile,
        secondary_air_outlet_c=float(state.secondary_air_outlet_c),
        clinker_outlet_c=float(state.clinker_outlet_c),
        cooler_efficiency=float(state.cooler_efficiency),
        air_flow_kg_s=float(state.air_flow_kg_s),
        mass_flow_kg_s=float(state.mass_flow_kg_s),
        first_law_imbalance=imbalance,
    )
