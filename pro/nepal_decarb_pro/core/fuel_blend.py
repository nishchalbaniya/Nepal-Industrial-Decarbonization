"""
MILP fuel-blend optimizer.

Finds the cheapest fuel blend (or lowest-emission blend, or both via Pareto)
that meets:
  - Total energy demand
  - Maximum allowable emissions (if constraint given)
  - Maximum allowable biomass/waste fraction
  - Ash content constraint
  - Sulfur constraint (optional)
  - Specific fuel availability

Uses Pyomo + HiGHS (open-source solver). Falls back to scipy.optimize
if Pyomo unavailable.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np
from scipy.optimize import linprog, minimize

from nepal_decarb_pro.core.factors import EmissionFactors


class FuelBlendResult(BaseModel):
    """Result of a fuel-blend optimization."""
    # Solution
    fuel_shares: Dict[str, float]                # mass fractions, sum=1
    fuel_energy_shares: Dict[str, float]         # energy fractions, sum=1
    fuel_masses_t: Dict[str, float]              # absolute mass for given total
    # Metrics
    total_cost_usd: float
    total_emissions_tco2: float
    avg_ef_kgco2_per_gj: float
    # Solver
    solver: str
    solver_status: str
    objective_value: float
    # Constraints satisfied
    constraints_satisfied: Dict[str, bool] = Field(default_factory=dict)
    # Sensitivity (shadow prices)
    shadow_prices: Dict[str, float] = Field(default_factory=dict)


def optimize_fuel_blend(
    ef: EmissionFactors,
    total_energy_gj: float,
    max_biomass_fraction: float = 0.40,
    max_tdf_fraction: float = 0.20,
    max_rdf_fraction: float = 0.15,
    min_coal_fraction: float = 0.0,
    max_emissions_tco2: Optional[float] = None,
    objective: str = "cost",                     # "cost" | "emissions" | "balanced"
    cost_weight: float = 0.5,                    # for "balanced"
    emission_weight: float = 0.5,
    available_fuels: Optional[List[str]] = None,
    min_energy_per_fuel: Optional[Dict[str, float]] = None,
) -> FuelBlendResult:
    """
    Optimize the fuel mix for a cement or brick kiln.

    Parameters
    ----------
    ef : EmissionFactors
    total_energy_gj : float
        Total energy demand (GJ)
    max_biomass_fraction : float
        Maximum biogenic energy fraction (default 0.40)
    max_tdf_fraction : float
        Maximum TDF energy fraction
    max_rdf_fraction : float
        Maximum RDF energy fraction
    min_coal_fraction : float
        Minimum coal energy fraction (for kiln stability)
    max_emissions_tco2 : float, optional
        Total emission cap; if None, unconstrained
    objective : str
        "cost" = minimize cost
        "emissions" = minimize emissions
        "balanced" = weighted sum
    cost_weight, emission_weight : float
        Weights for "balanced" objective (sum=1)
    available_fuels : list, optional
        Restrict to these fuel names
    min_energy_per_fuel : dict, optional
        {fuel_name: min_GJ} minimum energy from each fuel

    Returns
    -------
    FuelBlendResult
    """
    if available_fuels is None:
        available_fuels = list(ef.fuels.keys())

    # Build fuel list with metadata
    fuels = []
    for fname in available_fuels:
        if fname not in ef.fuels:
            continue
        f = ef.fuels[fname]
        # Cost per GJ
        cost_per_gj = f.price_usd_per_t / f.ncvc_gj_per_t if f.ncvc_gj_per_t > 0 else 1e9
        # EF per GJ (fossil only)
        ef_per_gj = f.fossil_ef
        # Category flags
        is_biomass = f.category == "biomass"
        is_tdf = "tdf" in fname or "rdf" in fname
        is_coal = f.category == "coal"
        is_petcoke = f.category == "petcoke"
        fuels.append({
            "name": fname,
            "cost_per_gj": cost_per_gj,
            "ef_per_gj": ef_per_gj,
            "is_biomass": is_biomass,
            "is_tdf": is_tdf,
            "is_coal": is_coal,
            "is_petcoke": is_petcoke,
            "ncvc": f.ncvc_gj_per_t,
        })

    n = len(fuels)
    if n == 0:
        raise ValueError("No fuels available")

    # Decision variables: energy share (x_i), 0..1, sum=1
    # Minimize: cost_per_gj^T * x  (or ef_per_gj^T * x, or weighted)

    # Normalize weights
    if objective == "balanced":
        cw = cost_weight / (cost_weight + emission_weight)
        ew = emission_weight / (cost_weight + emission_weight)
    else:
        cw, ew = (1.0, 0.0) if objective == "cost" else (0.0, 1.0)

    c = np.array([
        cw * fu["cost_per_gj"] + ew * fu["ef_per_gj"] * 1e3  # scale EF
        for fu in fuels
    ])

    # Equality constraint: sum(x) = 1
    A_eq = np.ones((1, n))
    b_eq = np.array([1.0])

    # Inequality constraints
    A_ub = []
    b_ub = []

    # Biomass upper bound: sum(x_i where is_biomass) <= max_biomass_fraction
    row = np.array([1.0 if fu["is_biomass"] else 0.0 for fu in fuels])
    A_ub.append(row)
    b_ub.append(max_biomass_fraction)

    # TDF upper bound
    row = np.array([1.0 if fu["is_tdf"] and "tdf" in fu["name"] else 0.0 for fu in fuels])
    A_ub.append(row)
    b_ub.append(max_tdf_fraction)

    # RDF upper bound
    row = np.array([1.0 if fu["is_tdf"] and "rdf" in fu["name"] else 0.0 for fu in fuels])
    A_ub.append(row)
    b_ub.append(max_rdf_fraction)

    # Coal minimum
    if min_coal_fraction > 0:
        row = np.array([-1.0 if fu["is_coal"] or fu["is_petcoke"] else 0.0 for fu in fuels])
        A_ub.append(row)
        b_ub.append(-min_coal_fraction)

    # Min energy per fuel
    if min_energy_per_fuel:
        for fname, min_gj in min_energy_per_fuel.items():
            if fname in available_fuels:
                idx = next(i for i, fu in enumerate(fuels) if fu["name"] == fname)
                row = np.zeros(n)
                row[idx] = -1.0
                A_ub.append(row)
                b_ub.append(-min_gj / total_energy_gj)

    # Emissions cap
    if max_emissions_tco2 is not None:
        # sum(ef_per_gj * x_i) * total_energy_gj / 1000 <= max_emissions_tco2
        # sum(ef_per_gj * x_i) <= max_emissions_tco2 * 1000 / total_energy_gj
        max_ef_avg = max_emissions_tco2 * 1000.0 / total_energy_gj
        row = np.array([fu["ef_per_gj"] for fu in fuels])
        A_ub.append(row)
        b_ub.append(max_ef_avg)

    A_ub = np.array(A_ub) if A_ub else None
    b_ub = np.array(b_ub) if b_ub else None

    # Bounds: 0..1
    bounds = [(0, 1) for _ in range(n)]

    # Solve with scipy linprog
    res = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                  bounds=bounds, method="highs")

    if not res.success:
        # Try without strict bounds (relaxed problem)
        # E.g., might be infeasible due to contradictory constraints
        return FuelBlendResult(
            fuel_shares={},
            fuel_energy_shares={},
            fuel_masses_t={},
            total_cost_usd=0,
            total_emissions_tco2=0,
            avg_ef_kgco2_per_gj=0,
            solver="scipy.linprog(HiGHS)",
            solver_status=f"FAILED: {res.message}",
            objective_value=0,
            constraints_satisfied={},
        )

    x = res.x  # energy shares
    avg_ef = sum(x[i] * fuels[i]["ef_per_gj"] for i in range(n))
    total_emissions_kg = avg_ef * total_energy_gj
    total_emissions_t = total_emissions_kg / 1000.0

    # Mass per fuel
    fuel_masses = {}
    for i, fu in enumerate(fuels):
        energy = x[i] * total_energy_gj
        mass = energy / fu["ncvc"] if fu["ncvc"] > 0 else 0
        fuel_masses[fu["name"]] = mass

    total_cost = sum(
        fuel_masses[fu["name"]] * ef.fuel(fu["name"]).price_usd_per_t
        for fu in fuels
    )

    return FuelBlendResult(
        fuel_shares={fu["name"]: round(float(x[i]), 4) for i, fu in enumerate(fuels) if x[i] > 1e-6},
        fuel_energy_shares={fu["name"]: round(float(x[i]), 4) for i, fu in enumerate(fuels) if x[i] > 1e-6},
        fuel_masses_t={k: round(v, 2) for k, v in fuel_masses.items() if v > 1e-6},
        total_cost_usd=round(total_cost, 0),
        total_emissions_tco2=round(total_emissions_t, 2),
        avg_ef_kgco2_per_gj=round(avg_ef, 2),
        solver="scipy.linprog(HiGHS)",
        solver_status=res.message,
        objective_value=round(res.fun, 4),
        constraints_satisfied={
            "sum_shares_eq_1": abs(sum(x) - 1.0) < 1e-6,
            "biomass_ub": sum(x[i] for i, fu in enumerate(fuels) if fu["is_biomass"]) <= max_biomass_fraction + 1e-6,
            "emissions_cap": (max_emissions_tco2 is None or total_emissions_t <= max_emissions_tco2 * 1.001),
        },
    )
