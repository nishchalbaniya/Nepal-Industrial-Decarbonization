"""Tests for cement emissions module."""
import pytest
from nepal_mrv.cement import CementPlant, FuelUse, calculate_cement_emissions
from nepal_mrv.emission_factors import EmissionFactors


@pytest.fixture
def ef():
    return EmissionFactors.from_yaml()


def test_basic_cement_plant(ef):
    """Hetauda-style: 950k t clinker, 1.1M t cement, coal+petcoke+diesel."""
    plant = CementPlant(
        name="Test Plant", location="Hetauda", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke", consumption_t=18_000),
            FuelUse(fuel_name="diesel", consumption_t=400),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    r = calculate_cement_emissions(plant, ef)

    # Sanity checks
    assert r.e_process_tco2 > 450_000
    assert r.e_process_tco2 < 600_000
    assert r.e_fuel_total_tco2 > 200_000
    assert r.e_fuel_total_tco2 < 400_000
    assert r.e_total_tco2 > 700_000
    assert r.intensity_kgco2_per_t_cement > 700
    assert r.intensity_kgco2_per_t_cement < 1100


def test_biomass_reduces_scope1(ef):
    """Adding biomass should not increase fossil CO2 (biogenic)."""
    plant_no_bio = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        fuel_use=[FuelUse(fuel_name="coal_bituminous_NP", consumption_t=70_000)],
    )
    plant_with_bio = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=70_000),
            FuelUse(fuel_name="biomass_rice_husk", consumption_t=10_000),
        ],
    )
    r1 = calculate_cement_emissions(plant_no_bio, ef)
    r2 = calculate_cement_emissions(plant_with_bio, ef)
    # Process & coal emissions should be identical (biomass adds 0)
    assert r1.e_process_tco2 == r2.e_process_tco2
    assert r1.e_fuel_tco2["coal_bituminous_NP"] == r2.e_fuel_tco2["coal_bituminous_NP"]


def test_process_emissions_scaling(ef):
    """Process emissions should scale linearly with clinker."""
    p1 = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
    )
    p2 = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=1_000_000, cement_production_t=1_200_000,
    )
    r1 = calculate_cement_emissions(p1, ef)
    r2 = calculate_cement_emissions(p2, ef)
    assert abs(r2.e_process_tco2 - 2 * r1.e_process_tco2) < 0.01


def test_electricity_uses_grid_ef(ef):
    """Verify Scope 2 uses Nepal grid EF."""
    plant = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        electricity_consumption_kwh=1_000_000,  # 1 GWh
    )
    r = calculate_cement_emissions(plant, ef)
    # Expected: 1e6 * 0.0256 * (1/0.775) = ~33,032 kg = 33 tCO2
    assert 30 < r.e_electricity_tco2 < 36


def test_negative_consumption_rejected():
    with pytest.raises(Exception):
        FuelUse(fuel_name="coal", consumption_t=-1)


def test_clinker_ratio(ef):
    p = CementPlant(
        name="X", location="Y", year=2024,
        clinker_production_t=600_000, cement_production_t=1_000_000,
    )
    assert abs(p.clinker_to_cement_ratio - 0.6) < 0.001
