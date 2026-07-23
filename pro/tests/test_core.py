"""Tests for the core engine."""
import pytest
from nepal_decarb_pro.core.cement import CementPlant, FuelUse, calculate_cement_tier2, calculate_cement_tier3
from nepal_decarb_pro.core.brick import BrickKiln, calculate_brick_emissions, list_kiln_types
from nepal_decarb_pro.core.factors import default_factors


@pytest.fixture
def ef():
    return default_factors()


def test_default_factors_load(ef):
    assert len(ef.fuels) > 8
    assert len(ef.brick_kilns) >= 5
    assert ef.grid.combined_margin < 0.05  # Nepal hydro-dominated


def test_cement_tier2_planta(ef):
    plant = CementPlant(
        name="PlantA", location="PlantA", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke", consumption_t=18_000),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    r = calculate_cement_tier2(plant, ef)
    assert r.e_total_tco2 > 800_000
    assert r.e_total_tco2 < 1_000_000
    assert r.intensity_kgco2_per_t_cement > 700
    assert r.intensity_kgco2_per_t_cement < 1000
    assert r.tier == "Tier 2 (IPCC 2006 mass-balance)"


def test_cement_tier3(ef):
    plant = CementPlant(
        name="PlantA", location="PlantA", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    r = calculate_cement_tier3(plant, ef)
    # Tier 3 should be slightly higher than Tier 2 due to TOC and precalc
    r2 = calculate_cement_tier2(plant, ef)
    assert r.tier.startswith("Tier 3")
    assert r.e_process_tco2 > r2.e_process_tco2   # Tier 3 has TOC


def test_brick_all_kiln_types(ef):
    for k in list_kiln_types():
        kiln = BrickKiln(
            name="X", location="X", year=2024,
            kiln_type=k, annual_brick_production=5_000_000,
        )
        r = calculate_brick_emissions(kiln, ef)
        assert r.e_total_baseline_tco2 > 0
        assert r.intensity_kgco2_per_1000_bricks > 0


def test_biomass_is_biogenic(ef):
    kiln = BrickKiln(
        name="X", location="X", year=2024,
        kiln_type="clamp_traditional", annual_brick_production=5_000_000,
        fuel_use=[FuelUse(fuel_name="biomass_rice_husk", consumption_t=10_000)],
    )
    r = calculate_brick_emissions(kiln, ef)
    assert r.e_biomass_combustion_tco2 == 0.0


def test_whr_offset(ef):
    plant_no_whr = CementPlant(
        name="X", location="X", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        electricity_consumption_kwh=50_000_000,
    )
    plant_with_whr = plant_no_whr.model_copy(update={"whr_generation_kwh": 20_000_000})
    r1 = calculate_cement_tier2(plant_no_whr, ef)
    r2 = calculate_cement_tier2(plant_with_whr, ef)
    # WHR offset should reduce Scope 2
    assert r2.e_scope2_tco2 < r1.e_scope2_tco2
    assert r2.e_total_tco2 < r1.e_total_tco2
