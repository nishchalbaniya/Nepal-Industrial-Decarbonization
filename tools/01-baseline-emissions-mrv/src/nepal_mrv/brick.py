"""
Brick sector baseline emissions calculator.
==========================================

Calculates emissions for all major kiln types used in Nepal:
- Clamp (traditional, ~70% of Nepali kilns)
- Hoffman (continuous, ~18%)
- Zigzag (~8%, BAT for medium-scale)
- Tunnel (~4%, BAT for large-scale)
- Vertical shaft (emerging BAT)

Implements:
- IPCC 2006 Vol.3 Ch.2 stationary combustion
- Verra/Gold Standard methodology for brick project activities
- WBCSD / GCCA brick protocol

Per-1000-bricks fuel approach (default coal):
  E_brick = N_bricks/1000 * coal_t_per_1000 * ncvc * ef

Biomass substitution (project case):
  E_with_biomass = E_base * (1 - biomass_frac)        (biomass is biogenic)
"""
from __future__ import annotations

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional

from nepal_mrv.emission_factors import EmissionFactors, BrickKilnEF


def list_kiln_types() -> List[str]:
    """Return all available kiln types."""
    ef = EmissionFactors.from_yaml()
    return list(ef.brick_kilns.keys())


class BrickKiln(BaseModel):
    """A brick kiln's annual operating data."""
    name: str
    location: str
    year: int
    kiln_type: str           # clamp / hoffman / tunnel / zigzag / vertical_shaft
    annual_brick_production: float = Field(..., gt=0, description="Number of bricks per year")
    # Optional: measured fuel mix (otherwise use kiln default)
    coal_t: Optional[float] = None
    biomass_t: Optional[float] = None
    natural_gas_m3: Optional[float] = None
    diesel_l: Optional[float] = None
    # Project case
    biomass_substitution_fraction: float = Field(0, ge=0, le=1)
    project_case: bool = False
    project_kiln_type: Optional[str] = None  # e.g. switching clamp->zigzag


class BrickEmissionsBreakdown(BaseModel):
    """Result of a brick kiln emissions calculation."""
    kiln_type: str
    annual_brick_production: float
    # Baseline
    e_coal_combustion_tco2: float
    e_biomass_combustion_tco2: float
    e_other_fuel_tco2: float
    e_total_baseline_tco2: float
    # Project case
    e_total_project_tco2: float
    e_reduction_tco2: float
    e_reduction_pct: float
    # Intensities
    intensity_kgco2_per_1000_bricks: float
    intensity_kgco2_per_brick: float
    # Specific energy
    sec_mj_per_brick: float
    sec_mj_per_1000_bricks: float
    # Benchmark
    thermal_efficiency: float
    delta_vs_nepal_avg_kgco2_per_1000: float


def calculate_brick_emissions(
    kiln: BrickKiln, ef: EmissionFactors
) -> BrickEmissionsBreakdown:
    """
    Calculate baseline (and optional project) emissions for a brick kiln.
    """
    if kiln.kiln_type not in ef.brick_kilns:
        raise ValueError(
            f"Unknown kiln_type '{kiln.kiln_type}'. "
            f"Available: {list(ef.brick_kilns)}"
        )
    kiln_ef: BrickKilnEF = ef.brick_kilns[kiln.kiln_type]

    # Number of thousands of bricks
    n_k = kiln.annual_brick_production / 1000.0

    # Baseline fuel mix
    # Default: only coal at kiln-specific rate
    coal_t = kiln.coal_t if kiln.coal_t is not None else (
        n_k * kiln_ef.coal_t_per_1000_bricks
    )
    biomass_t = kiln.biomass_t or 0.0
    natgas_m3 = kiln.natural_gas_m3 or 0.0
    diesel_l = kiln.diesel_l or 0.0

    coal_ef = ef.fuel("coal_bituminous_NP")
    biomass_ef = ef.fuel("biomass_wood")  # any biomass, biogenic
    natgas_ef = ef.fuel("natural_gas")
    diesel_ef = ef.fuel("diesel")

    e_coal_kg = coal_t * coal_ef.ncvc_gj_per_t * coal_ef.ef_kgco2_per_gj
    e_coal_tco2 = e_coal_kg / 1000.0

    # Biomass is biogenic (carbon-neutral in this accounting)
    e_biomass_kg = biomass_t * biomass_ef.ncvc_gj_per_t * biomass_ef.ef_kgco2_per_gj
    e_biomass_tco2 = e_biomass_kg / 1000.0  # = 0 if biogenic

    # Natural gas: NCV in GJ per cubic meter approx 0.0383 GJ/m3
    e_natgas_kg = natgas_m3 * 0.0383 * natgas_ef.ef_kgco2_per_gj
    e_natgas_tco2 = e_natgas_kg / 1000.0

    # Diesel: 1 L ≈ 0.00085 t, NCV 43 GJ/t → 0.0366 GJ/L
    e_diesel_kg = diesel_l * 0.0366 * diesel_ef.ef_kgco2_per_gj
    e_diesel_tco2 = e_diesel_kg / 1000.0

    e_other_tco2 = e_natgas_tco2 + e_diesel_tco2
    e_baseline_tco2 = e_coal_tco2 + e_biomass_tco2 + e_other_tco2

    # Project case
    e_project_tco2 = e_baseline_tco2
    e_reduction_tco2 = 0.0
    e_reduction_pct = 0.0

    if kiln.project_case and kiln.project_kiln_type:
        if kiln.project_kiln_type not in ef.brick_kilns:
            raise ValueError(
                f"Unknown project_kiln_type '{kiln.project_kiln_type}'"
            )
        proj_ef = ef.brick_kilns[kiln.project_kiln_type]
        # Recalculate coal consumption at project kiln rate
        proj_coal_t = n_k * proj_ef.coal_t_per_1000_bricks
        proj_e_coal_kg = proj_coal_t * coal_ef.ncvc_gj_per_t * coal_ef.ef_kgco2_per_gj
        proj_e_coal_tco2 = proj_e_coal_kg / 1000.0

        # Apply biomass substitution (biomass is biogenic)
        proj_coal_after_sub = proj_coal_t * (1 - kiln.biomass_substitution_fraction)
        proj_e_coal_after_kg = (
            proj_coal_after_sub * coal_ef.ncvc_gj_per_t * coal_ef.ef_kgco2_per_gj
        )
        proj_e_coal_after_tco2 = proj_e_coal_after_kg / 1000.0

        e_project_tco2 = proj_e_coal_after_tco2 + e_biomass_tco2 + e_other_tco2
        e_reduction_tco2 = e_baseline_tco2 - e_project_tco2
        if e_baseline_tco2 > 0:
            e_reduction_pct = (e_reduction_tco2 / e_baseline_tco2) * 100.0

    # Intensities
    intensity_per_1000 = (e_baseline_tco2 * 1000.0) / n_k if n_k > 0 else 0
    intensity_per_brick = (e_baseline_tco2 * 1000.0) / kiln.annual_brick_production

    # Specific energy consumption
    total_energy_gj = (
        coal_t * coal_ef.ncvc_gj_per_t
        + biomass_t * biomass_ef.ncvc_gj_per_t
        + natgas_m3 * 0.0383
        + diesel_l * 0.0366
    )
    sec_per_brick_mj = (total_energy_gj * 1000.0) / kiln.annual_brick_production
    sec_per_1000 = sec_per_brick_mj * 1000.0

    # Benchmark
    nepal_avg_kg_per_1000 = 270.0
    delta_vs_nepal = intensity_per_1000 - nepal_avg_kg_per_1000

    return BrickEmissionsBreakdown(
        kiln_type=kiln.kiln_type,
        annual_brick_production=kiln.annual_brick_production,
        e_coal_combustion_tco2=round(e_coal_tco2, 2),
        e_biomass_combustion_tco2=round(e_biomass_tco2, 2),
        e_other_fuel_tco2=round(e_other_tco2, 2),
        e_total_baseline_tco2=round(e_baseline_tco2, 2),
        e_total_project_tco2=round(e_project_tco2, 2),
        e_reduction_tco2=round(e_reduction_tco2, 2),
        e_reduction_pct=round(e_reduction_pct, 2),
        intensity_kgco2_per_1000_bricks=round(intensity_per_1000, 2),
        intensity_kgco2_per_brick=round(intensity_per_brick, 4),
        sec_mj_per_brick=round(sec_per_brick_mj, 4),
        sec_mj_per_1000_bricks=round(sec_per_1000, 2),
        thermal_efficiency=kiln_ef.thermal_efficiency,
        delta_vs_nepal_avg_kgco2_per_1000=round(delta_vs_nepal, 2),
    )


# Backwards-compatible alias
BrickEmissions = BrickEmissionsBreakdown
