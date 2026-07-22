"""
Tests for fuels.py — fuel database, blend math, flame temperature.
"""
from __future__ import annotations

import pytest

from nepal_kiln_sim.fuels import (
    FUEL_DATABASE, get_fuel, list_fuels, compute_blend_ef, compute_flame_temperature,
)


def test_database_has_known_fuels():
    assert "coal_bituminous_NP" in FUEL_DATABASE
    assert "biomass_rice_husk" in FUEL_DATABASE
    assert "tdf_tire" in FUEL_DATABASE


def test_get_fuel_returns_none_for_unknown():
    assert get_fuel("unicornium") is None


def test_list_fuels_sorted():
    fuels = list_fuels()
    cats = [f.category for f in fuels]
    assert cats == sorted(cats)


def test_biomass_has_zero_fossil_ef():
    for f in list_fuels():
        if f.category == "biomass":
            assert f.ef_kgco2_per_gj == 0.0
            assert f.biogenic_fraction == 1.0


def test_tdf_biogenic_27pct():
    f = get_fuel("tdf_tire")
    assert f.biogenic_fraction == pytest.approx(0.27, abs=0.01)


def test_blend_sums_to_one():
    with pytest.raises(ValueError):
        compute_blend_ef({"coal_bituminous_NP": 0.5})


def test_blend_unknown_fuel():
    with pytest.raises(KeyError):
        compute_blend_ef({"coal_bituminous_NP": 0.5, "unicornium": 0.5})


def test_blend_lowers_fossil_ef():
    pure_coal = compute_blend_ef({"coal_bituminous_NP": 1.0})
    half_bio = compute_blend_ef({"coal_bituminous_NP": 0.5, "biomass_rice_husk": 0.5})
    assert half_bio["ef_kgco2_per_gj_blend"] < pure_coal["ef_kgco2_per_gj_blend"]


def test_blend_biogenic_fraction_weighted_average():
    result = compute_blend_ef({"coal_bituminous_NP": 0.7, "biomass_rice_husk": 0.3})
    assert result["biogenic_fraction_blend"] == pytest.approx(0.3, abs=0.01)


def test_flame_temperature_in_expected_range():
    coal = get_fuel("coal_bituminous_NP")
    t = compute_flame_temperature(coal, air_excess=1.10, air_temp_k=800.0)
    # Adiabatic flame T (no heat loss, no dissociation); 1800-2700 K range
    # covers coal/petcoke/biomass in cement kiln conditions
    assert 1800.0 < t < 2800.0


def test_flame_higher_with_preheated_air():
    coal = get_fuel("natural_gas")
    t_cold = compute_flame_temperature(coal, air_temp_k=300.0)
    t_hot  = compute_flame_temperature(coal, air_temp_k=1000.0)
    assert t_hot > t_cold


def test_flame_lower_with_more_excess_air():
    coal = get_fuel("coal_bituminous_NP")
    t_stoich = compute_flame_temperature(coal, air_excess=1.0)
    t_excess = compute_flame_temperature(coal, air_excess=1.5)
    assert t_excess < t_stoich
