"""Tests for optimization modules."""
import pytest
from nepal_decarb_pro.core.fuel_blend import optimize_fuel_blend
from nepal_decarb_pro.core.multi_objective import multi_objective_optimize
from nepal_decarb_pro.core.factors import default_factors


@pytest.fixture
def ef():
    return default_factors()


def test_fuel_blend_cheapest(ef):
    r = optimize_fuel_blend(ef, total_energy_gj=1_000_000, objective="cost")
    assert "Optimization terminated" in r.solver_status or "optimal" in r.solver_status.lower()
    assert abs(sum(r.fuel_energy_shares.values()) - 1.0) < 0.01
    assert r.total_cost_usd > 0
    # Check biomass constraint
    biomass_share = sum(
        share for name, share in r.fuel_energy_shares.items()
        if "biomass" in name
    )
    assert biomass_share <= 0.401   # 0.40 + epsilon


def test_fuel_blend_lowest_emissions(ef):
    r = optimize_fuel_blend(ef, total_energy_gj=1_000_000, objective="emissions")
    assert r.total_emissions_tco2 > 0
    # When optimizing for emissions, biomass share should be high
    biomass_share = sum(
        share for name, share in r.fuel_energy_shares.items()
        if "biomass" in name
    )
    assert biomass_share > 0.30   # should push biomass to its limit


def test_fuel_blend_balanced(ef):
    r = optimize_fuel_blend(ef, total_energy_gj=1_000_000, objective="balanced",
                            cost_weight=0.5, emission_weight=0.5)
    assert "Optimization terminated" in r.solver_status or "optimal" in r.solver_status.lower()
    assert r.total_cost_usd > 0


def test_pareto_optimization(ef):
    r = multi_objective_optimize(ef, total_energy_gj=500_000,
                                 n_population=20, n_generations=20)
    assert r.n_solutions > 0
    # Pareto solutions should be sorted by cost
    if len(r.pareto_front_x) > 1:
        assert all(r.pareto_front_x[i] <= r.pareto_front_x[i+1]
                   for i in range(len(r.pareto_front_x) - 1))
