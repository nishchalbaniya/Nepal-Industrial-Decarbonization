"""Core emissions engine: Tier 2 (mass-balance) + Tier 3 (kinetics) for cement and brick."""
from nepal_decarb_pro.core.factors import (
    EmissionFactors,
    Fuel,
    BrickKilnSpec,
    ClinkerChemistry,
    GridSpec,
    default_factors,
)
from nepal_decarb_pro.core.cement import (
    CementPlant,
    CementEmissionsResult,
    calculate_cement_tier2,
    calculate_cement_tier3,
)
from nepal_decarb_pro.core.brick import (
    BrickKiln,
    BrickEmissionsResult,
    calculate_brick_emissions,
)
from nepal_decarb_pro.core.uncertainty import (
    UncertaintySpec,
    MonteCarloResult,
    monte_carlo_cement,
    monte_carlo_brick,
    sobol_indices,
)
from nepal_decarb_pro.core.fuel_blend import (
    FuelBlendResult,
    optimize_fuel_blend,
)
from nepal_decarb_pro.core.multi_objective import (
    ParetoResult,
    multi_objective_optimize,
)

__all__ = [
    "EmissionFactors",
    "Fuel",
    "BrickKilnSpec",
    "ClinkerChemistry",
    "GridSpec",
    "default_factors",
    "CementPlant",
    "CementEmissionsResult",
    "calculate_cement_tier2",
    "calculate_cement_tier3",
    "BrickKiln",
    "BrickEmissionsResult",
    "calculate_brick_emissions",
    "UncertaintySpec",
    "MonteCarloResult",
    "monte_carlo_cement",
    "monte_carlo_brick",
    "sobol_indices",
    "FuelBlendResult",
    "optimize_fuel_blend",
    "ParetoResult",
    "multi_objective_optimize",
]
