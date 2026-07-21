"""
Verra VCS (Verified Carbon Standard) project activity generator.

Generates a Verra Project Design Document (PDD) skeleton for a cement or
brick decarbonization project. Compatible with methodologies:
  - AMS-III.H (Alternative waste treatment processes)
  - VM0009 (Cement plant decarbonization)
  - ACM0012 (Waste energy recovery)
  - AMS-I.C (Thermal energy production with renewable energy)
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from nepal_decarb_pro.core.cement import CementPlant, CementEmissionsResult
from nepal_decarb_pro.core.brick import BrickKiln, BrickEmissionsResult


class VerraPDD(BaseModel):
    """Verra VCS Project Design Document (PDD) skeleton."""
    project_name: str
    project_id: Optional[str]
    methodology: str
    project_type: str
    project_location: Dict[str, str]
    project_proponent: str
    crediting_period_start: str
    crediting_period_end: str
    crediting_period_years: int
    # Section A: Project description
    project_purpose: str
    project_activities: List[str]
    technology: str
    # Section B: Baseline
    baseline_description: str
    baseline_emissions_annual_tco2: float
    # Section C: Project
    project_emissions_annual_tco2: float
    # Section D: Leakage
    leakage_pct: float
    # Section E: Emission reductions
    gross_emission_reductions_annual_tco2: float
    buffer_pool_pct: float
    buffer_deduction_annual_tco2: float
    net_emission_reductions_annual_tco2: float
    # Section F: Monitoring plan
    monitoring_plan: str
    # Section G: Verification
    vvb_required: str
    # Revenue
    annual_revenue_at_15: float
    annual_revenue_at_30: float
    annual_revenue_at_50: float
    # Metadata
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


def calculate_buffer_deduction(
    net_reduction_tco2: float,
    buffer_pct: float = 0.15,
) -> float:
    """Apply Verra non-permanence buffer."""
    return net_reduction_tco2 * buffer_pct


def generate_verra_pdd(
    project_name: str,
    project_type: str,
    baseline_annual_tco2: float,
    project_annual_tco2: float,
    crediting_period_years: int = 10,
    location: str = "Nepal",
    proponent: str = "Himalayan Carbon Nepal",
    leakage_pct: float = 0.05,
    buffer_pct: float = 0.15,
    technology: str = "Biomass co-firing + WHR",
    vintage_year: Optional[int] = None,
) -> VerraPDD:
    """
    Generate a Verra VCS PDD skeleton.
    """
    if vintage_year is None:
        vintage_year = datetime.now().year

    gross_reduction = max(baseline_annual_tco2 - project_annual_tco2, 0)
    leakage = gross_reduction * leakage_pct
    net = gross_reduction - leakage
    buffer = net * buffer_pct
    net_issuable = net - buffer

    methodology_map = {
        "cement": "VM0009 v2.0 (Cement Plant Decarbonization)",
        "brick": "AMS-III.H v1.0 (Alternative waste treatment)",
    }
    methodology = methodology_map.get(project_type, "ACM0012 v3.0")

    return VerraPDD(
        project_name=project_name,
        project_id=None,
        methodology=methodology,
        project_type=project_type,
        project_location={"country": "Nepal", "region": location, "iso": "NP"},
        project_proponent=proponent,
        crediting_period_start=f"{vintage_year}-01-01",
        crediting_period_end=f"{vintage_year + crediting_period_years - 1}-12-31",
        crediting_period_years=crediting_period_years,
        project_purpose=(
            f"Reduce GHG emissions from {project_type} production in Nepal through "
            f"decarbonization technology adoption"
        ),
        project_activities=[
            f"Installation of {technology}",
            "MRV system deployment",
            "Biomass supply chain development",
            "Worker training and capacity building",
        ],
        technology=technology,
        baseline_description=(
            f"Baseline scenario: continuation of {project_type} production using "
            f"current technology mix (predominantly coal/petcoke for cement, "
            f"traditional clamp kilns for bricks)"
        ),
        baseline_emissions_annual_tco2=baseline_annual_tco2,
        project_emissions_annual_tco2=project_annual_tco2,
        leakage_pct=leakage_pct * 100,
        gross_emission_reductions_annual_tco2=gross_reduction,
        buffer_pool_pct=buffer_pct * 100,
        buffer_deduction_annual_tco2=buffer,
        net_emission_reductions_annual_tco2=net_issuable,
        monitoring_plan=(
            "Continuous monitoring of fuel use, electricity, production. "
            "Quarterly third-party verification. Annual recalibration. "
            "All data archived in immutable ledger."
        ),
        vvb_required="Accredited VVB (TÜV, DNV, RINA, ERM CVS, etc.)",
        annual_revenue_at_15=net_issuable * 15,
        annual_revenue_at_30=net_issuable * 30,
        annual_revenue_at_50=net_issuable * 50,
    )
