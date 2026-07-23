"""Tests for project activity MRV module."""
import pytest
from nepal_mrv.mrv import ProjectActivity, calculate_project_emission_reduction
from nepal_mrv.cement import CementPlant, FuelUse
from nepal_mrv.brick import BrickKiln


def test_cement_project_reduces_emissions():
    baseline = CementPlant(
        name="PlantA", location="PlantA", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke", consumption_t=18_000),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    project = CementPlant(
        name="PlantA", location="PlantA", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=96_000),
            FuelUse(fuel_name="petcoke", consumption_t=14_400),
            FuelUse(fuel_name="biomass_rice_husk", consumption_t=42_000),
        ],
        electricity_consumption_kwh=63_000_000,
    )
    activity = ProjectActivity(
        project_name="Test", project_type="cement",
        baseline_year=2024, crediting_period_years=10,
        vintage_year=2026, baseline_plant=baseline,
        project_plant=project, leakage_fraction=0.05,
        carbon_price_usd_per_t=15.0, discount_rate=0.10,
    )
    er = calculate_project_emission_reduction(activity)
    assert er.net_annual_reduction_tco2 > 0
    assert er.cumulative_reduction_tco2 > er.net_annual_reduction_tco2
    assert er.annual_revenue_usd > 0
    assert er.npv_revenue_usd > 0
    assert er.npv_at_30_usd > er.npv_revenue_usd
    assert er.npv_at_50_usd > er.npv_at_30_usd
    assert 0 < er.buffer_pool_pct < 1
    assert er.net_issuable_annual_tco2 < er.net_annual_reduction_tco2


def test_brick_project_passes_additionality():
    baseline = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="clamp_traditional", annual_brick_production=5_000_000,
    )
    project = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="zigzag", annual_brick_production=5_000_000,
        biomass_substitution_fraction=0.20,
        project_case=True, project_kiln_type="zigzag",
    )
    activity = ProjectActivity(
        project_name="Clamp to Zigzag", project_type="brick",
        baseline_year=2024, crediting_period_years=7,
        vintage_year=2026, baseline_kiln=baseline,
        project_kiln=project, leakage_fraction=0.05,
        carbon_price_usd_per_t=15.0, discount_rate=0.10,
    )
    er = calculate_project_emission_reduction(activity)
    assert er.net_annual_reduction_tco2 > 0
    assert "PASS" in er.additionality_screening


def test_crediting_period_multiplies_cumulative():
    baseline = CementPlant(
        name="H", location="X", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
    )
    project = CementPlant(
        name="H", location="X", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        fuel_use=[FuelUse(fuel_name="biomass_rice_husk", consumption_t=10_000)],
    )
    a = ProjectActivity(
        project_name="T", project_type="cement",
        baseline_year=2024, crediting_period_years=10,
        vintage_year=2026, baseline_plant=baseline, project_plant=project,
    )
    er = calculate_project_emission_reduction(a)
    assert abs(er.cumulative_reduction_tco2 - er.net_annual_reduction_tco2 * 10) < 1
