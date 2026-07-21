"""Tests for LCA module."""
import pytest
from nepal_decarb_pro.lca import lca_cement, lca_brick, lca_compare, get_cf, list_categories
from nepal_decarb_pro.core.cement import CementPlant, FuelUse
from nepal_decarb_pro.core.brick import BrickKiln
from nepal_decarb_pro.core.factors import default_factors


@pytest.fixture
def ef():
    return default_factors()


def test_cf_loaded():
    cf = get_cf()
    cats = list_categories()
    assert "GWP100" in cats
    assert "AP" in cats
    assert cf.get("CO2", "GWP100") == 1.0


def test_lca_cement_opc(ef):
    plant = CementPlant(
        name="Hetauda", location="Hetauda", year=2024,
        clinker_production_t=950_000, cement_production_t=1_100_000,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke", consumption_t=18_000),
        ],
        electricity_consumption_kwh=85_000_000,
    )
    r = lca_cement(plant, ef)
    # GWP per tonne cement (functional unit = 1 tonne cement)
    # Result is in t CO2-eq/t cement. Hetauda should be ~0.77 t = 770 kg.
    assert r.impacts["GWP100"] > 0.6   # > 600 kg CO2/t
    assert r.impacts["GWP100"] < 1.5   # < 1500 kg CO2/t
    assert "raw_materials" in r.stage_contributions
    assert "fuel_combustion" in r.stage_contributions


def test_lca_brick(ef):
    kiln = BrickKiln(
        name="Test", location="Bhairahawa", year=2024,
        kiln_type="clamp_traditional", annual_brick_production=5_000_000,
    )
    r = lca_brick(kiln, ef)
    assert r.impacts["GWP100"] > 0
    assert r.functional_unit == "1000 bricks"


def test_lca_compare(ef):
    plant = CementPlant(
        name="A", location="X", year=2024,
        clinker_production_t=500_000, cement_production_t=600_000,
        fuel_use=[FuelUse(fuel_name="coal_bituminous_NP", consumption_t=70_000)],
        electricity_consumption_kwh=50_000_000,
    )
    r1 = lca_cement(plant, ef)

    plant2 = plant.model_copy(update={
        "fuel_use": [
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=50_000),
            FuelUse(fuel_name="biomass_rice_husk", consumption_t=20_000),
        ]
    })
    r2 = lca_cement(plant2, ef)

    cmp = lca_compare([r1, r2])
    assert "GWP100" in cmp
    # Biomass substitution should reduce GWP
    assert r2.impacts["GWP100"] < r1.impacts["GWP100"]
