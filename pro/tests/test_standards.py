"""Tests for standards compliance modules."""
import pytest
from nepal_decarb_pro.standards.iso_14064 import check_iso_14064_part1, check_iso_14064_part2, check_iso_14064_part3
from nepal_decarb_pro.standards.tcfd import generate_tcfd_report
from nepal_decarb_pro.standards.sbti import SBTiTarget, check_sbti_target
from nepal_decarb_pro.standards.gcca import calculate_gcca_kpis
from nepal_decarb_pro.standards.pcaf import calculate_financed_emissions
from nepal_decarb_pro.standards.ghg_protocol import check_scope_completeness, check_significance
from nepal_decarb_pro.core.cement import CementPlant, FuelUse, calculate_cement_tier2
from nepal_decarb_pro.core.factors import default_factors


@pytest.fixture
def ef():
    return default_factors()


@pytest.fixture
def planta():
    ef = default_factors()
    plant = CementPlant(
        name="PlantA", location="PlantA", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke", consumption_t=18_000),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    return plant, calculate_cement_tier2(plant, ef)


def test_iso_14064_1(planta):
    plant, result = planta
    r = check_iso_14064_part1(plant=plant, cement_result=result)
    assert r.score > 70
    assert r.standard == "ISO 14064-1:2018"


def test_iso_14064_2():
    r = check_iso_14064_part2(
        baseline_quantified=True,
        project_quantified=True,
        additionality_demonstrated=True,
        monitoring_plan=True,
        leakage_assessed=True,
    )
    assert r.score > 60


def test_iso_14064_3():
    r = check_iso_14064_part3(
        vvb_accredited=True,
        site_visit_conducted=True,
        materiality_applied=True,
        risk_based_approach=True,
        opinion_issued=True,
    )
    assert r.score > 80


def test_tcfd_report(planta):
    plant, result = planta
    tcfd = generate_tcfd_report(plant=plant, cement_result=result)
    assert tcfd.scope1_tco2 > 0
    assert len(tcfd.scenarios) >= 3


def test_sbti_target():
    target = SBTiTarget(
        target_year=2030,
        intensity_target_kgco2_per_t=400,
        base_year=2020,
        base_year_tco2=1_000_000,
        base_year_intensity_kgco2_per_t=900,
    )
    r = check_sbti_target(target)
    assert r.required_reduction_pct > 0
    assert r.target_reduction_pct > 0


def test_gcca_kpis(planta, ef):
    plant, result = planta
    kpi = calculate_gcca_kpis(plant, result, ef)
    assert kpi.co2_per_t_cement > 500
    assert 0.6 < kpi.clinker_to_cement_ratio < 1.0


def test_pcaf_financed():
    loans = [{
        "company": "PlantA",
        "sector": "cement",
        "loan_amount_usd": 5_000_000,
        "company_revenue_usd": 100_000_000,
        "company_emissions_tco2": 1_000_000,
        "data_quality_score": 3,
    }]
    r = calculate_financed_emissions(loans)
    assert len(r) == 1
    # 5M / 100M = 0.05 attribution
    assert abs(r[0].attribution_factor - 0.05) < 0.001
    # 0.05 * 1Mt = 50,000 tCO2
    assert abs(r[0].financed_emissions_tco2 - 50_000) < 1


def test_ghg_protocol_scope_check(planta):
    plant, result = planta
    r = check_scope_completeness(cement_result=result)
    assert r.score > 80
    assert all(c["pass"] for c in r.checks[:3])


def test_significance_check(planta):
    plant, result = planta
    sig = check_significance(
        result.e_scope1_tco2, result.e_scope2_tco2, result.e_scope3_tco2,
    )
    assert "scopes" in sig
    assert "material_sources" in sig
