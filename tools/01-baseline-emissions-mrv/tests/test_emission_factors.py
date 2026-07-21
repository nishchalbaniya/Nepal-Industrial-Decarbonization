"""Tests for emission_factors module."""
import pytest
from pathlib import Path
from nepal_mrv.emission_factors import EmissionFactors


def test_load_yaml():
    ef = EmissionFactors.from_yaml()
    assert ef.co2_per_t_clinker_process > 0.5
    assert ef.co2_per_t_clinker_process < 0.6
    assert len(ef.fuels) >= 8
    assert len(ef.brick_kilns) >= 4


def test_fuel_lookup():
    ef = EmissionFactors.from_yaml()
    coal = ef.fuel("coal_bituminous_NP")
    assert coal.ncvc_gj_per_t > 20
    assert coal.ef_kgco2_per_gj > 80
    assert coal.ef_kgco2_per_gj < 110


def test_fuel_not_found():
    ef = EmissionFactors.from_yaml()
    with pytest.raises(KeyError):
        ef.fuel("unobtainium")


def test_biomass_biogenic():
    ef = EmissionFactors.from_yaml()
    for name in ["biomass_wood", "biomass_rice_husk", "biomass_sawdust", "biomass_bagasse"]:
        f = ef.fuel(name)
        assert f.ef_kgco2_per_gj == 0.0, f"{name} should be biogenic"


def test_kiln_types():
    ef = EmissionFactors.from_yaml()
    for k in ["clamp_traditional", "hoffman", "tunnel_kiln", "zigzag", "vertical_shaft"]:
        kiln = ef.kiln(k)
        assert kiln.coal_t_per_1000_bricks > 0
        assert 0 < kiln.thermal_efficiency < 1
    # Clamp must be the worst
    clamp = ef.kiln("clamp_traditional")
    tunnel = ef.kiln("tunnel_kiln")
    assert clamp.coal_t_per_1000_bricks > tunnel.coal_t_per_1000_bricks
    assert clamp.thermal_efficiency < tunnel.thermal_efficiency


def test_grid_ef():
    ef = EmissionFactors.from_yaml()
    # Nepal grid is hydro-dominated, should be < 0.05 kg CO2/kWh
    assert ef.grid_cm < 0.05
    assert ef.grid_cm > 0
    assert 0.15 < ef.grid_td_loss < 0.30
