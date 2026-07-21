"""Tests for brick emissions module."""
import pytest
from nepal_mrv.brick import BrickKiln, calculate_brick_emissions, list_kiln_types
from nepal_mrv.emission_factors import EmissionFactors


@pytest.fixture
def ef():
    return EmissionFactors.from_yaml()


def test_kiln_listing():
    k = list_kiln_types()
    assert "clamp_traditional" in k
    assert "tunnel_kiln" in k
    assert len(k) >= 4


def test_clamp_worst(ef):
    """Clamp must emit more than tunnel/zigzag for same production."""
    clamp = BrickKiln(name="A", location="X", year=2024,
                      kiln_type="clamp_traditional", annual_brick_production=5_000_000)
    tunnel = BrickKiln(name="A", location="X", year=2024,
                       kiln_type="tunnel_kiln", annual_brick_production=5_000_000)
    rc = calculate_brick_emissions(clamp, ef)
    rt = calculate_brick_emissions(tunnel, ef)
    assert rc.e_total_baseline_tco2 > rt.e_total_baseline_tco2
    assert rc.intensity_kgco2_per_1000_bricks > rt.intensity_kgco2_per_1000_bricks
    assert rc.thermal_efficiency < rt.thermal_efficiency


def test_project_reduces_emissions(ef):
    """Project case (clamp->zigzag + biomass) should reduce emissions."""
    clamp = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="clamp_traditional", annual_brick_production=5_000_000,
        project_case=True, project_kiln_type="zigzag",
        biomass_substitution_fraction=0.20,
    )
    r = calculate_brick_emissions(clamp, ef)
    assert r.e_reduction_tco2 > 0
    assert r.e_reduction_pct > 20
    assert r.e_total_project_tco2 < r.e_total_baseline_tco2


def test_biomass_is_biogenic(ef):
    """Biomass should add zero to fossil CO2."""
    k = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="clamp_traditional", annual_brick_production=5_000_000,
        biomass_t=10_000,  # large biomass use
    )
    r = calculate_brick_emissions(k, ef)
    assert r.e_biomass_combustion_tco2 == 0.0


def test_unknown_kiln_raises():
    """Unknown kiln type raises at compute time."""
    ef = EmissionFactors.from_yaml()
    bad = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="not_a_kiln", annual_brick_production=1_000_000,
    )
    with pytest.raises(ValueError):
        calculate_brick_emissions(bad, ef)


def test_intensity_below_bat_for_tunnel(ef):
    tunnel = BrickKiln(
        name="A", location="X", year=2024,
        kiln_type="tunnel_kiln", annual_brick_production=5_000_000,
    )
    r = calculate_brick_emissions(tunnel, ef)
    # Tunnel at BAT should be < 300 kg/1000 (better than clamp 540)
    assert r.intensity_kgco2_per_1000_bricks < 300
