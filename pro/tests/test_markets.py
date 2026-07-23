"""Tests for carbon markets module."""
import pytest
from nepal_decarb_pro.markets.verra import generate_verra_pdd, calculate_buffer_deduction
from nepal_decarb_pro.markets.gold_standard import generate_gold_standard_pdd
from nepal_decarb_pro.markets.pricing import get_carbon_price, get_revenue_scenarios, CARBON_PRICES
from nepal_decarb_pro.markets.tokenization import build_token_metadata, generate_solidity_contract


# Real (verified) cement/brick methodology codes. See docs/METHODOLOGY.md.
REAL_CEMENT_METHODOLOGIES = ("ACM0003", "ACM0005")
REAL_BRICK_METHODOLOGIES = ("RECH", "TPDDTEC", "AMS-III.H")


def test_verra_pdd_cement_uses_real_methodology():
    """The PDD generator must use a real, verified cement methodology.

    The historical "VM0009 v2.0 (Cement Plant Decarbonization)" string
    was FICTIONAL and is forbidden. See docs/METHODOLOGY.md section 1
    and reviews/GROUND_TRUTH.md (defect WP1-1).
    """
    pdd = generate_verra_pdd(
        project_name="PlantA Decarb",
        project_type="cement",
        baseline_annual_tco2=861_000,
        project_annual_tco2=791_000,
    )
    assert "VM0009" not in pdd.methodology, (
        "VM0009 is the Avoided Ecosystem Conversion methodology, "
        "not a cement methodology. Banned from the cement PDD."
    )
    assert any(code in pdd.methodology for code in REAL_CEMENT_METHODOLOGIES), (
        f"Cement PDD must reference one of {REAL_CEMENT_METHODOLOGIES}, got: {pdd.methodology}"
    )
    assert pdd.methodology_status == "real (CDM; Verra status to be re-confirmed)"
    assert pdd.gross_emission_reductions_annual_tco2 == 70_000
    assert pdd.crediting_period_years == 10
    assert pdd.net_emission_reductions_annual_tco2 < 70_000   # buffer deduction


def test_verra_pdd_brick_uses_real_methodology():
    pdd = generate_verra_pdd(
        project_name="Brick Decarb",
        project_type="brick",
        baseline_annual_tco2=3257,
        project_annual_tco2=955,
    )
    assert "VM0009" not in pdd.methodology
    assert pdd.methodology_status == "real"


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
    assert "Methodology for Cement Plant Decarbonization" not in pdd.gs_methodology, (
        "Gold Standard does not publish a 'Cement Plant Decarbonization' "
        "methodology. The historical string was fictional."
    )
    assert any(code in pdd.gs_methodology for code in REAL_BRICK_METHODOLOGIES), (
        f"Brick PDD must reference one of {REAL_BRICK_METHODOLOGIES}, got: {pdd.gs_methodology}"
    )
    assert len(pdd.sustainable_development_goals) >= 3
    assert len(pdd.safeguard_principles) >= 3


def test_carbon_price_lookup():
    eu_2024 = get_carbon_price("EU_ETS", 2024)
    assert eu_2024.price_usd_per_tco2 > 50
    assert eu_2024.market == "compliance"


def test_revenue_scenarios_includes_voluntary_floor():
    """Realistic voluntary carbon price for a South Asian cement project is
    USD 5-15/t, NOT the EU ETS price. The pricing module must expose a
    voluntary-floor scenario, not lead with EU ETS.
    See docs/METHODOLOGY.md section 3.
    """
    scenarios = get_revenue_scenarios(10_000, crediting_period_years=10)
    # At least one voluntary scenario at <= USD 15/t must be present
    has_voluntary_floor = any(
        v.get("price_usd_per_tco2", 999) <= 15
        for v in scenarios.values()
    )
    assert has_voluntary_floor, (
        f"No voluntary-floor scenario at <= USD 15/t found in: {list(scenarios.keys())}"
    )


def test_token_metadata_uses_real_methodology():
    md = build_token_metadata(
        project_name="PlantA Decarb",
        vintage_year=2024,
        methodology="ACM0003",  # was "VM0009"
        registry="Verra",
        total_tonnes_co2=56_000,
    )
    assert "VM0009" not in md.methodology
    assert md.serial_number != ""
    assert md.issuance_hash != ""
    assert len(md.issuance_hash) == 64


def test_solidity_contract():
    src = generate_solidity_contract(token_name="Nepal Carbon Credit", token_symbol="nCO2")
    assert "pragma solidity" in src
    assert "issueBatch" in src
    assert "retireBatch" in src
    assert "ERC-3643" in src or "whitelisted" in src.lower()
