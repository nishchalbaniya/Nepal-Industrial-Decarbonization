"""Tests for carbon markets module."""
import pytest
from nepal_decarb_pro.markets.verra import generate_verra_pdd, calculate_buffer_deduction
from nepal_decarb_pro.markets.gold_standard import generate_gold_standard_pdd
from nepal_decarb_pro.markets.pricing import get_carbon_price, get_revenue_scenarios, CARBON_PRICES
from nepal_decarb_pro.markets.tokenization import build_token_metadata, generate_solidity_contract


def test_verra_pdd():
    pdd = generate_verra_pdd(
        project_name="PlantA Decarb",
        project_type="cement",
        baseline_annual_tco2=861_000,
        project_annual_tco2=791_000,
    )
    assert pdd.methodology.startswith("VM0009")
    assert pdd.gross_emission_reductions_annual_tco2 == 70_000
    assert pdd.crediting_period_years == 10
    assert pdd.net_emission_reductions_annual_tco2 < 70_000   # buffer deduction


def test_buffer_deduction():
    assert calculate_buffer_deduction(100, 0.15) == 15
    assert calculate_buffer_deduction(100, 0.10) == 10


def test_gold_standard_pdd():
    pdd = generate_gold_standard_pdd(
        project_name="Bhairahawa Clamp to Zigzag",
        project_type="brick",
        baseline_annual_tco2=3257,
        project_annual_tco2=955,
        crediting_period_years=7,
    )
    assert pdd.gs_methodology.startswith("GS TPDDTEC")
    assert len(pdd.sustainable_development_goals) >= 3
    assert len(pdd.safeguard_principles) >= 3


def test_carbon_price_lookup():
    eu_2024 = get_carbon_price("EU_ETS", 2024)
    assert eu_2024.price_usd_per_tco2 > 50
    assert eu_2024.market == "compliance"


def test_revenue_scenarios():
    scenarios = get_revenue_scenarios(10_000, crediting_period_years=10)
    assert "EU ETS compliance ($65)" in scenarios
    assert scenarios["EU ETS compliance ($65)"]["annual_revenue_usd"] == 650_000


def test_token_metadata():
    md = build_token_metadata(
        project_name="PlantA Decarb",
        vintage_year=2024,
        methodology="VM0009",
        registry="Verra",
        total_tonnes_co2=56_000,
    )
    assert md.serial_number != ""
    assert md.issuance_hash != ""
    assert len(md.issuance_hash) == 64


def test_solidity_contract():
    src = generate_solidity_contract(token_name="Nepal Carbon Credit", token_symbol="nCO2")
    assert "pragma solidity" in src
    assert "issueBatch" in src
    assert "retireBatch" in src
    assert "ERC-3643" in src or "whitelisted" in src.lower()
