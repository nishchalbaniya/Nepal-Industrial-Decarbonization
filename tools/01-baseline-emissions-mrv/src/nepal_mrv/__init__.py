"""
nepal_mrv — Baseline Emissions & MRV tool for Nepal Cement & Brick industry
============================================================================

Open-source, Verra VCS / Gold Standard compatible baseline emissions calculator
specifically calibrated for Nepali cement and brick industry.

Author: Nishchal Baniya <nishchal.baniya@himalayancarbonnepal.com>
License: MIT
"""
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.cement import (
    CementPlant,
    CementEmissions,
    CementEmissionsBreakdown,
    FuelUse,
    calculate_cement_emissions,
)
from nepal_mrv.brick import (
    BrickKiln,
    BrickEmissions,
    BrickEmissionsBreakdown,
    calculate_brick_emissions,
    list_kiln_types,
)
from nepal_mrv.mrv import (
    ProjectActivity,
    ProjectEmissionReduction,
    calculate_project_emission_reduction,
)
from nepal_mrv.reporting import MRVReport

__version__ = "0.1.0"
__all__ = [
    "EmissionFactors",
    "CementPlant",
    "CementEmissions",
    "CementEmissionsBreakdown",
    "FuelUse",
    "calculate_cement_emissions",
    "BrickKiln",
    "BrickEmissions",
    "BrickEmissionsBreakdown",
    "calculate_brick_emissions",
    "list_kiln_types",
    "ProjectActivity",
    "ProjectEmissionReduction",
    "calculate_project_emission_reduction",
    "MRVReport",
]
