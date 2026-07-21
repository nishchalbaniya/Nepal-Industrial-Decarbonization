"""
TCFD (Task Force on Climate-related Financial Disclosures) report generator.

Generates TCFD-aligned disclosure for a cement/brick plant or company.
Covers the 4 pillars: Governance, Strategy, Risk Management, Metrics & Targets.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from nepal_decarb_pro.core.cement import CementPlant, CementEmissionsResult
from nepal_decarb_pro.core.brick import BrickKiln, BrickEmissionsResult


class TCFDResult(BaseModel):
    """TCFD disclosure result."""
    organization: str
    reporting_year: int
    governance: Dict
    strategy: Dict
    risk_management: Dict
    metrics_targets: Dict
    # Quantitative
    scope1_tco2: float
    scope2_tco2: float
    scope3_tco2: float
    intensity_kgco2_per_t_product: float
    target_2030_reduction_pct: float
    target_2050_reduction_pct: float
    # Scenario analysis
    scenarios: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


def generate_tcfd_report(
    plant: Optional[CementPlant] = None,
    kiln: Optional[BrickKiln] = None,
    cement_result: Optional[CementEmissionsResult] = None,
    brick_result: Optional[BrickEmissionsResult] = None,
    target_2030_pct: float = 30.0,
    target_2050_pct: float = 100.0,
) -> TCFDResult:
    """
    Generate a TCFD-aligned disclosure.
    """
    scope1 = cement_result.e_scope1_tco2 if cement_result else (brick_result.e_scope1_tco2 if brick_result else 0)
    scope2 = cement_result.e_scope2_tco2 if cement_result else (brick_result.e_electricity_tco2 if brick_result else 0)
    scope3 = cement_result.e_scope3_tco2 if cement_result else (brick_result.e_transport_tco2 if brick_result else 0)
    intensity = (
        cement_result.intensity_kgco2_per_t_cement if cement_result
        else (brick_result.intensity_kgco2_per_1000_bricks if brick_result else 0)
    )

    # Scenario analysis (3 scenarios)
    # 1.5C, 2C, BAU
    scenarios = {
        "1.5C-aligned (Net Zero by 2050)": {
            "scope1_2030": scope1 * 0.5,
            "scope1_2050": scope1 * 0.05,
            "carbon_price_usd_per_t_2030": 100,
            "carbon_price_usd_per_t_2050": 250,
        },
        "Well-below 2C": {
            "scope1_2030": scope1 * 0.7,
            "scope1_2050": scope1 * 0.2,
            "carbon_price_usd_per_t_2030": 50,
            "carbon_price_usd_per_t_2050": 150,
        },
        "Business as Usual": {
            "scope1_2030": scope1 * 1.05,  # slight growth
            "scope1_2050": scope1 * 0.95,  # small improvement
            "carbon_price_usd_per_t_2030": 20,
            "carbon_price_usd_per_t_2050": 50,
        },
    }

    return TCFDResult(
        organization=(plant.name if plant else kiln.name if kiln else "Unknown"),
        reporting_year=(plant.year if plant else kiln.year if kiln else datetime.now().year),
        governance={
            "board_oversight": "Board-level Sustainability Committee reviews climate risks quarterly",
            "management_role": "Chief Sustainability Officer reports to CEO; reports to Board quarterly",
            "expertise": "At least 2 Board members with climate/sustainability expertise",
        },
        strategy={
            "short_term_risks": [
                "Carbon credit revenue loss if technology shift not adopted (1-3 yr)",
                "Stranded asset risk for inefficient kilns (3-5 yr)",
                "Customer demand for low-carbon cement (1-3 yr)",
            ],
            "long_term_risks": [
                "Carbon Border Adjustment Mechanism (CBAM) impact on exports (5-10 yr)",
                "Nepal CO2 tax introduction (5-10 yr)",
                "Physical climate risks: water scarcity for cooling, extreme heat",
            ],
            "opportunities": [
                "Biomass co-firing: $6-20M NPV per cement plant",
                "Brick kiln technology upgrade: $143k-477k NPV per kiln",
                "Verra VCS / Gold Standard credit revenue: $15-50/tCO2e",
                "LC3 / geopolymer product premium: 10-20%",
            ],
        },
        risk_management={
            "identification": "Annual climate risk assessment aligned with TCFD framework",
            "integration": "Climate risks integrated into enterprise risk management (ERM)",
            "monitoring": "KPIs reviewed monthly; targets reset annually",
        },
        metrics_targets={
            "scope1": f"{scope1:,.0f} tCO2e/yr",
            "scope2": f"{scope2:,.0f} tCO2e/yr",
            "scope3": f"{scope3:,.0f} tCO2e/yr",
            "intensity": f"{intensity:,.0f} kg CO2/t product",
            "target_2030": f"{target_2030_pct:.0f}% absolute reduction by 2030",
            "target_2050": f"Net Zero by 2050",
            "methodology": "GHG Protocol Corporate Standard + ISO 14064-1",
        },
        scope1_tco2=scope1,
        scope2_tco2=scope2,
        scope3_tco2=scope3,
        intensity_kgco2_per_t_product=intensity,
        target_2030_reduction_pct=target_2030_pct,
        target_2050_reduction_pct=target_2050_pct,
        scenarios=scenarios,
    )
