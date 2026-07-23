"""
Tests for plants.py — preset consistency and validation.
"""
from __future__ import annotations

import pytest

from nepal_kiln_sim.plants import PLANT_PRESETS, get_plant_preset, list_plants
from nepal_kiln_sim.kiln_ode import KilnParameters


def test_all_presets_load():
    for key in PLANT_PRESETS:
        p = get_plant_preset(key)
        assert p is not None
        assert p.parameters is not None


def test_preset_keys():
    expected = {"planta", "plantb", "plantc", "plantd",
                "reference_5000tpd", "legacy_wet_1000tpd"}
    assert set(PLANT_PRESETS.keys()) >= expected


def test_planta_in_range():
    p = PLANT_PRESETS["planta"].parameters
    assert 50.0 <= p.length_m <= 80.0
    assert 3.0 <= p.diameter_m <= 5.0
    assert 5.0 <= p.fuel_rate_t_h <= 15.0


def test_hongshi_more_capacity_than_planta():
    a = PLANT_PRESETS["plantc"].parameters
    b = PLANT_PRESETS["planta"].parameters
    assert a.raw_meal_throughput_t_h > b.raw_meal_throughput_t_h


def test_legacy_wet_process_has_moisture():
    p = PLANT_PRESETS["legacy_wet_1000tpd"].parameters
    assert p.raw_meal_moisture_wt > 0.20


def test_unknown_preset_returns_none():
    assert get_plant_preset("narnia") is None


def test_all_presets_have_valid_fuel():
    for key, preset in PLANT_PRESETS.items():
        assert preset.parameters.fuel_type != ""
        # Should not raise
        KilnParameters.model_validate(preset.parameters.model_dump())
