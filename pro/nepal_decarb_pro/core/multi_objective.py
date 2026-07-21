"""
Multi-objective optimization using NSGA-II.

Optimizes fuel blend for two objectives simultaneously:
  f1 = -cost          (minimize)
  f2 = emissions      (minimize)

Returns a Pareto front of non-dominated solutions.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
import numpy as np

from nepal_decarb_pro.core.factors import EmissionFactors
from nepal_decarb_pro.core.fuel_blend import optimize_fuel_blend


class ParetoSolution(BaseModel):
    """One point on the Pareto front."""
    cost_usd: float
    emissions_tco2: float
    fuel_masses_t: Dict[str, float]


class ParetoResult(BaseModel):
    """Result of a multi-objective optimization."""
    solutions: List[ParetoSolution]
    n_solutions: int
    pareto_front_x: List[float]      # cost
    pareto_front_y: List[float]      # emissions
    dominated: List[int]             # indices of dominated solutions
    method: str
    hypervolume: Optional[float] = None
    n_iterations: int


def _nsga2_select(
    pop: List[Dict],
    obj1: List[float],
    obj2: List[float],
    n_select: int,
) -> List[int]:
    """NSGA-II non-dominated sorting + crowding distance selection."""
    n = len(pop)
    # Non-dominated sorting
    domination_count = [0] * n
    dominated_set = [[] for _ in range(n)]
    fronts = [[]]

    for i in range(n):
        for j in range(i + 1, n):
            # i dominates j
            if obj1[i] <= obj1[j] and obj2[i] <= obj2[j] and (
                obj1[i] < obj1[j] or obj2[i] < obj2[j]
            ):
                dominated_set[i].append(j)
                domination_count[j] += 1
            elif obj1[j] <= obj1[i] and obj2[j] <= obj2[i] and (
                obj1[j] < obj1[i] or obj2[j] < obj2[i]
            ):
                dominated_set[j].append(i)
                domination_count[i] += 1
        if domination_count[i] == 0:
            fronts[0].append(i)

    current = 0
    while fronts[current]:
        next_front = []
        for i in fronts[current]:
            for j in dominated_set[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)
        current += 1
        fronts.append(next_front)

    # Select from fronts
    selected = []
    for front in fronts:
        if len(selected) + len(front) <= n_select:
            selected.extend(front)
        else:
            # Need crowding distance
            remaining = n_select - len(selected)
            if remaining > 0:
                # Crowding distance
                m = len(front)
                if m <= remaining:
                    selected.extend(front)
                else:
                    distances = np.zeros(m)
                    for k in range(2):
                        vals = np.array([obj1[i] if k == 0 else obj2[i] for i in front])
                        order = np.argsort(vals)
                        distances[order[0]] = distances[order[-1]] = np.inf
                        for j in range(1, m - 1):
                            distances[order[j]] += (
                                vals[order[j + 1]] - vals[order[j - 1]]
                            ) / (vals[order[-1]] - vals[order[0]] + 1e-12)
                    ranked = sorted(range(m), key=lambda x: -distances[x])
                    for j in ranked[:remaining]:
                        selected.append(front[j])
            break
    return selected


def multi_objective_optimize(
    ef: EmissionFactors,
    total_energy_gj: float,
    max_biomass_fraction: float = 0.40,
    n_population: int = 30,
    n_generations: int = 50,
    seed: int = 42,
) -> ParetoResult:
    """
    Multi-objective optimization (NSGA-II style) for fuel blend.

    Returns the Pareto front of (cost, emissions) solutions.
    """
    rng = np.random.default_rng(seed)

    # Initialize population: random fuel mixes
    available = list(ef.fuels.keys())
    n = len(available)
    pop_shares = []
    for _ in range(n_population):
        s = rng.dirichlet(np.ones(n))
        pop_shares.append(s)

    # Evaluate initial population
    def evaluate(shares: np.ndarray) -> Tuple[float, float]:
        # Build fuel mix
        fuel_masses: Dict[str, float] = {}
        for i, fname in enumerate(available):
            if shares[i] > 1e-6:
                f = ef.fuels[fname]
                energy = shares[i] * total_energy_gj
                mass = energy / f.ncvc_gj_per_t
                fuel_masses[fname] = mass

        # Cost
        cost = sum(mass * ef.fuels[fname].price_usd_per_t
                   for fname, mass in fuel_masses.items())

        # Emissions
        emissions_kg = 0.0
        for i, fname in enumerate(available):
            if shares[i] > 1e-6:
                f = ef.fuels[fname]
                emissions_kg += shares[i] * total_energy_gj * f.fossil_ef

        emissions_t = emissions_kg / 1000.0
        return cost, emissions_t

    pop_obj = [evaluate(s) for s in pop_shares]

    # Evolution loop
    for gen in range(n_generations):
        # Generate offspring via crossover + mutation
        offspring_shares = []
        for _ in range(n_population):
            # Tournament selection
            i, j = rng.choice(n_population, 2, replace=False)
            parent1 = pop_shares[i]
            parent2 = pop_shares[j]
            # Crossover (SBX-like)
            child = 0.5 * (parent1 + parent2)
            # Mutation
            child = child + rng.normal(0, 0.05, n)
            child = np.clip(child, 0, 1)
            child = child / child.sum()  # normalize
            # Apply biomass constraint by clipping biomass
            biomass_idx = [i for i, fname in enumerate(available) if ef.fuels[fname].category == "biomass"]
            biomass_sum = sum(child[i] for i in biomass_idx)
            if biomass_sum > max_biomass_fraction:
                scale = max_biomass_fraction / biomass_sum
                for i in biomass_idx:
                    child[i] *= scale
                child = child / child.sum()
            offspring_shares.append(child)

        # Evaluate offspring
        offspring_obj = [evaluate(s) for s in offspring_shares]

        # Combine & select
        combined_shares = pop_shares + offspring_shares
        combined_obj = pop_obj + offspring_obj
        obj1 = [o[0] for o in combined_obj]
        obj2 = [o[1] for o in combined_obj]
        sel = _nsga2_select(combined_shares, obj1, obj2, n_population)
        pop_shares = [combined_shares[i] for i in sel]
        pop_obj = [combined_obj[i] for i in sel]

    # Build Pareto solutions (non-dominated)
    solutions: List[ParetoSolution] = []
    pareto_x = []
    pareto_y = []
    for i, (cost, em) in enumerate(pop_obj):
        # Check non-dominated
        is_dominated = False
        for j, (c2, e2) in enumerate(pop_obj):
            if i != j and c2 <= cost and e2 <= em and (c2 < cost or e2 < em):
                is_dominated = True
                break
        if not is_dominated:
            shares = pop_shares[i]
            fuel_masses = {}
            for k, fname in enumerate(available):
                if shares[k] > 1e-6:
                    f = ef.fuels[fname]
                    energy = shares[k] * total_energy_gj
                    mass = energy / f.ncvc_gj_per_t
                    fuel_masses[fname] = round(float(mass), 2)
            solutions.append(ParetoSolution(
                cost_usd=round(cost, 0),
                emissions_tco2=round(em, 2),
                fuel_masses_t=fuel_masses,
            ))
            pareto_x.append(cost)
            pareto_y.append(em)

    # Sort by cost
    sorted_pairs = sorted(zip(pareto_x, pareto_y, solutions), key=lambda x: x[0])
    pareto_x = [p[0] for p in sorted_pairs]
    pareto_y = [p[1] for p in sorted_pairs]
    solutions = [p[2] for p in sorted_pairs]

    return ParetoResult(
        solutions=solutions,
        n_solutions=len(solutions),
        pareto_front_x=pareto_x,
        pareto_front_y=pareto_y,
        dominated=[],
        method="NSGA-II (custom implementation)",
        n_iterations=n_generations,
    )
