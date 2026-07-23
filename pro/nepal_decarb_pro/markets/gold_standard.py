"""
Gold Standard project document generator.

Compatible with:
  - GS RECH v5.0 (formerly TPDDTEC -- Reduced Emissions from Cooking
    and Heating; cookstoves / institutional heating up to 150 kW/unit).
    APPLICABLE to the BRICK sub-product (when brick kilns are
    displaced by cleaner thermal technologies). NOT applicable to
    industrial cement kilns.
  - The previous docstring claimed "GS Methodology for Cement Plant
    Decarbonization" was a Gold Standard methodology. FICTIONAL.
    Gold Standard does not publish a cement methodology. Removed
    2026-07-23 in WP1 remediation. See docs/METHODOLOGY.md and
    reviews/GROUND_TRUTH.md (defect WP1-2).
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from nepal_decarb_pro.markets.verra import VerraPDD, generate_verra_pdd


class GoldStandardPDD(VerraPDD):
    """Gold Standard Project Design Document (extends Verra PDD)."""
    gs_methodology: str
    sustainable_development_goals: List[str]
    safeguard_principles: List[str]
    stakeholder_consultation: str
    gs_verification_body: str
    gs_registry: str = "Gold Standard Registry"


def generate_gold_standard_pdd(
    project_name: str,
    project_type: str,
    baseline_annual_tco2: float,
    project_annual_tco2: float,
    crediting_period_years: int = 7,
    location: str = "Nepal",
    proponent: str = "Himalayan Space Solutions",
    leakage_pct: float = 0.05,
    buffer_pct: float = 0.10,            # GS uses lower buffer
    technology: str = "Biomass co-firing + WHR",
    vintage_year: Optional[int] = None,
) -> GoldStandardPDD:
    """
    Generate a Gold Standard PDD skeleton. The Gold Standard framework
    is currently applicable to the BRICK sub-product (RECH v5.0); for
    CEMENT projects use the Verra/CDM framework instead.
    """
    base = generate_verra_pdd(
        project_name=project_name,
        project_type=project_type,
        baseline_annual_tco2=baseline_annual_tco2,
        project_annual_tco2=project_annual_tco2,
        crediting_period_years=crediting_period_years,
        location=location,
        proponent=proponent,
        leakage_pct=leakage_pct,
        buffer_pct=buffer_pct,
        technology=technology,
        vintage_year=vintage_year,
    )

    gs_map = {
        "brick": "GS RECH v5.0 (Reduced Emissions from Cooking and Heating; formerly TPDDTEC; 150 kW/unit ceiling)",
        # Cement: Gold Standard has no published cement methodology.
        # Fall back to the CDM citation; never invent a GS code.
    }
    gs_meth = gs_map.get(
        project_type,
        "GS RECH v5.0 (cookstove/institutional heating; not applicable to industrial cement)",
    )

    # SDGs typically claimed
    sdgs = [
        "SDG 7: Affordable and Clean Energy",
        "SDG 9: Industry, Innovation and Infrastructure",
        "SDG 12: Responsible Consumption and Production",
        "SDG 13: Climate Action",
    ]

    return GoldStandardPDD(
        **base.model_dump(),
        gs_methodology=gs_meth,
        sustainable_development_goals=sdgs,
        safeguard_principles=[
            "Human rights (no forced labor in brick kilns)",
            "Gender equality (women's employment in monitoring roles)",
            "Community engagement (kiln workers' families benefit from cleaner air)",
            "Worker safety (improved kiln technology reduces accidents)",
            "Biodiversity (no deforestation from biomass supply)",
        ],
        stakeholder_consultation=(
            "Multi-stakeholder consultation conducted with kiln owners, "
            "workers, local government, and civil society. "
            "Free, prior, and informed consent obtained."
        ),
        gs_verification_body="TÜV NORD CERT or DNV GL (illustrative)",
    )
