"""
Project activity & emission reduction calculation.
==================================================

Implements the additionality & crediting framework for cement & brick projects
seeking Verra VCS or Gold Standard carbon credits.

Verra VCS Equation (simplified):
  ER = BE - PE - LE
  Where:
    ER  = Emission Reduction (tCO2e/yr)
    BE  = Baseline Emissions
    PE  = Project Emissions
    LE  = Leakage Emissions

Baseline scenarios supported (cement):
  BE_cement = clinker_t * process_ef + sum(fuel_i * ef_i) + elec_kwh * grid_ef
  PE_cement = clinker_t * process_ef + sum(fuel_i * ef_i_post) + elec_kwh * grid_ef_post

Project activities supported:
  CEMENT:
    - Alternative fuel substitution (biomass, RDF, TDF) — AMS-III.H
    - Clinker substitution (LC3, geopolymer, flyash, slag) — large impact
    - Waste-heat recovery power generation (WHR)
    - Kiln modernisation (improved preheater)
  BRICK:
    - Clamp -> Zigzag conversion
    - Clamp -> Hoffman conversion
    - Clamp -> Tunnel conversion
    - Biomass co-firing
    - Vertical shaft kiln
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import numpy as np

from nepal_mrv.cement import (
    CementPlant, calculate_cement_emissions, CementEmissionsBreakdown
)
from nepal_mrv.brick import (
    BrickKiln, calculate_brick_emissions, BrickEmissionsBreakdown
)
from nepal_mrv.emission_factors import EmissionFactors



# ----------------------------------------------------------------------------
# Data models
# ----------------------------------------------------------------------------

class ProjectActivity(BaseModel):
    """
    Defines a project activity (cement or brick) for emission reduction.
    """
    project_name: str
    project_type: str          # "cement" or "brick"
    baseline_year: int
    crediting_period_years: int = Field(10, ge=1, le=20)
    vintage_year: int
    # Baseline
    baseline_plant: Optional[CementPlant] = None
    baseline_kiln: Optional[BrickKiln] = None
    # Project
    project_plant: Optional[CementPlant] = None
    project_kiln: Optional[BrickKiln] = None
    # Leakage (default 5% if not specified)
    leakage_fraction: float = Field(0.05, ge=0, le=1)
    # Carbon price (USD/tCO2e)
    carbon_price_usd_per_t: float = Field(15.0, ge=0)
    # Discount rate for NPV
    discount_rate: float = Field(0.10, ge=0, le=1)
    # Methodology label
    methodology: str = "Verra VCS AMS-III.H (alternative fuels/waste heat)"
    # Buffer pool (Verra non-permanence risk)
    buffer_pool_pct: float = Field(0.15, ge=0, le=0.5)

    @property
    def baseline(self) -> "CementEmissionsBreakdown | BrickEmissionsBreakdown":
        ef = EmissionFactors.from_yaml()
        if self.project_type == "cement":
            assert self.baseline_plant is not None
            return calculate_cement_emissions(self.baseline_plant, ef)
        assert self.baseline_kiln is not None
        return calculate_brick_emissions(self.baseline_kiln, ef)

    @property
    def project(self) -> "CementEmissionsBreakdown | BrickEmissionsBreakdown":
        ef = EmissionFactors.from_yaml()
        if self.project_type == "cement":
            assert self.project_plant is not None
            return calculate_cement_emissions(self.project_plant, ef)
        assert self.project_kiln is not None
        return calculate_brick_emissions(self.project_kiln, ef)


class ProjectEmissionReduction(BaseModel):
    """Result of a project emission reduction calculation."""
    project_name: str
    project_type: str
    methodology: str
    crediting_period_years: int
    # Annual
    baseline_annual_tco2: float
    project_annual_tco2: float
    leakage_annual_tco2: float
    net_annual_reduction_tco2: float
    # Cumulative
    cumulative_reduction_tco2: float
    # Revenue
    annual_revenue_usd: float
    npv_revenue_usd: float
    npv_at_30_usd: float            # sensitivity at $30/t
    npv_at_50_usd: float            # sensitivity at $50/t
    # Additionality
    additionality_screening: str
    # Verra buffer pool deduction (default 15%)
    buffer_pool_pct: float = 0.15
    buffer_deduction_annual_tco2: float
    net_issuable_annual_tco2: float


# ----------------------------------------------------------------------------
# Calculator
# ----------------------------------------------------------------------------

def calculate_project_emission_reduction(
    activity: ProjectActivity,
) -> ProjectEmissionReduction:
    """
    Calculate annual and cumulative emission reductions for a project activity,
    plus estimated carbon credit revenue.
    """
    ef = EmissionFactors.from_yaml()
    b = activity.baseline
    p = activity.project

    if activity.project_type == "cement":
        baseline_annual = b.e_total_tco2
        project_annual = p.e_total_tco2
    else:
        baseline_annual = b.e_total_baseline_tco2
        # Use the project kiln directly to compute project emissions
        # (the project_kiln is already the new technology; we just need its
        # baseline-mode emissions, then apply biomass substitution)
        pk = activity.project_kiln
        assert pk is not None
        proj_ef = ef.brick_kilns[pk.kiln_type]
        coal_ef = ef.fuel("coal_bituminous_NP")
        n_k = pk.annual_brick_production / 1000.0
        coal_t_proj = n_k * proj_ef.coal_t_per_1000_bricks
        coal_t_after = coal_t_proj * (1 - pk.biomass_substitution_fraction)
        e_kg = coal_t_after * coal_ef.ncvc_gj_per_t * coal_ef.ef_kgco2_per_gj
        project_annual = e_kg / 1000.0

    gross_annual = max(baseline_annual - project_annual, 0.0)
    leakage_annual = gross_annual * activity.leakage_fraction
    net_annual = gross_annual - leakage_annual

    cumulative = net_annual * activity.crediting_period_years

    # Revenue
    annual_rev = net_annual * activity.carbon_price_usd_per_t
    npv_rev = sum(
        annual_rev / ((1 + activity.discount_rate) ** y)
        for y in range(1, activity.crediting_period_years + 1)
    )
    npv_30 = sum(
        net_annual * 30.0 / ((1 + activity.discount_rate) ** y)
        for y in range(1, activity.crediting_period_years + 1)
    )
    npv_50 = sum(
        net_annual * 50.0 / ((1 + activity.discount_rate) ** y)
        for y in range(1, activity.crediting_period_years + 1)
    )

    # Buffer pool deduction (Verra requires non-permanence buffer)
    buffer_pct = activity.buffer_pool_pct
    buffer_annual = net_annual * buffer_pct
    net_issuable = net_annual - buffer_annual

    # Additionality screening
    if activity.project_type == "cement":
        # Conservative check: positive NPV at $15/t and emissions reduction > 5%
        ratio = gross_annual / baseline_annual if baseline_annual > 0 else 0
        add = (
            "PASS" if (npv_rev > 0 and ratio > 0.05)
            else "FAIL — insufficient reduction or negative NPV"
        )
    else:
        ratio = gross_annual / baseline_annual if baseline_annual > 0 else 0
        add = (
            "PASS" if (ratio > 0.20)
            else "FAIL — minimum 20% reduction required (Gold Standard brick)"
        )

    return ProjectEmissionReduction(
        project_name=activity.project_name,
        project_type=activity.project_type,
        methodology=activity.methodology,
        crediting_period_years=activity.crediting_period_years,
        baseline_annual_tco2=round(baseline_annual, 2),
        project_annual_tco2=round(project_annual, 2),
        leakage_annual_tco2=round(leakage_annual, 2),
        net_annual_reduction_tco2=round(net_annual, 2),
        cumulative_reduction_tco2=round(cumulative, 2),
        annual_revenue_usd=round(annual_rev, 0),
        npv_revenue_usd=round(npv_rev, 0),
        npv_at_30_usd=round(npv_30, 0),
        npv_at_50_usd=round(npv_50, 0),
        additionality_screening=add,
        buffer_pool_pct=buffer_pct,
        buffer_deduction_annual_tco2=round(buffer_annual, 2),
        net_issuable_annual_tco2=round(net_issuable, 2),
    )
