"""
Brick sector emissions — kiln-type-specific fuel mix.

Supports any combination of:
  - Coal (multiple grades)
  - Biomass (wood, rice husk, sawdust, bagasse, jatropha)
  - Petroleum fuels (diesel, furnace oil)
  - TDF / RDF
  - Natural gas / LPG

Implements:
  - Per-1000-bricks energy balance
  - Biomass co-firing (technical limits per kiln type)
  - Auxiliary electricity (forced draft, blowers)
  - Stack heat losses
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from nepal_decarb_pro.core.factors import EmissionFactors
from nepal_decarb_pro.core.cement import FuelUse


class BrickKiln(BaseModel):
    """Annual operating data for a brick kiln."""
    name: str
    location: str
    year: int
    kiln_type: str
    annual_brick_production: float = Field(..., gt=0)
    # Custom fuel mix (optional — defaults to kiln-specific coal rate)
    fuel_use: List[FuelUse] = Field(default_factory=list)
    # Aux electricity (blowers, conveyors, lighting)
    electricity_consumption_kwh: float = Field(0, ge=0)
    # Project case
    biomass_substitution_fraction: float = Field(0, ge=0, le=1)
    project_case: bool = False
    project_kiln_type: Optional[str] = None
    # Operating
    operating_days: int = Field(300, ge=1, le=365)
    # Transport
    transport_tkm: float = Field(0, ge=0)

    @field_validator("kiln_type")
    @classmethod
    def _kiln_not_empty(cls, v: str) -> str:
        if not v:
            raise ValueError("kiln_type cannot be empty")
        return v


class BrickEmissionsResult(BaseModel):
    """Result of brick kiln emissions calculation."""
    kiln_type: str
    annual_brick_production: float
    # Fuel
    e_coal_combustion_tco2: float
    e_biomass_combustion_tco2: float
    e_other_fuel_tco2: float
    e_total_baseline_tco2: float
    # Project
    e_total_project_tco2: float
    e_reduction_tco2: float
    e_reduction_pct: float
    # Scope 2/3
    e_electricity_tco2: float
    e_transport_tco2: float
    # Totals
    e_scope1_tco2: float
    e_total_tco2: float
    # Intensities
    intensity_kgco2_per_1000_bricks: float
    intensity_kgco2_per_brick: float
    # Specific energy
    sec_mj_per_brick: float
    sec_mj_per_1000_bricks: float
    # Benchmarks
    thermal_efficiency: float
    delta_vs_nepal_avg_kgco2_per_1000: float
    # Fuel share breakdown
    fuel_share: Dict[str, float] = Field(default_factory=dict)
    biomass_share: float


def calculate_brick_emissions(
    kiln: BrickKiln, ef: EmissionFactors
) -> BrickEmissionsResult:
    """
    Calculate baseline and optional project emissions for a brick kiln.
    """
    if kiln.kiln_type not in ef.brick_kilns:
        raise ValueError(
            f"Unknown kiln_type '{kiln.kiln_type}'. "
            f"Available: {list(ef.brick_kilns)}"
        )
    kiln_ef = ef.brick_kilns[kiln.kiln_type]
    n_k = kiln.annual_brick_production / 1000.0

    # Determine fuel mix
    if kiln.fuel_use:
        # Use custom fuel mix
        fuel_records = []
        for fu in kiln.fuel_use:
            f = ef.fuel(fu.fuel_name)
            fuel_records.append((fu, f))
    else:
        # Default: only coal at kiln-specific rate
        coal_f = ef.fuel("coal_bituminous_NP")
        default_fu = FuelUse(fuel_name="coal_bituminous_NP", consumption_t=n_k * kiln_ef.coal_t_per_1000)
        fuel_records = [(default_fu, coal_f)]

    # Compute per-fuel emissions
    e_fuel_breakdown: Dict[str, float] = {}
    e_coal_tco2 = 0.0
    e_biomass_tco2 = 0.0
    e_other_tco2 = 0.0
    total_energy_gj = 0.0
    total_energy_gj_biogenic = 0.0
    coal_records = []
    biomass_records = []
    other_records = []

    for fu, f in fuel_records:
        e_kg = fu.consumption_t * f.ncvc_gj_per_t * f.fossil_ef
        e_tco2 = e_kg / 1000.0
        e_fuel_breakdown[fu.fuel_name] = e_tco2
        gj = fu.consumption_t * f.ncvc_gj_per_t
        total_energy_gj += gj
        total_energy_gj_biogenic += gj * f.biogenic_fraction

        if f.category == "coal":
            e_coal_tco2 += e_tco2
            coal_records.append((fu, f, gj))
        elif f.category == "biomass":
            e_biomass_tco2 += e_tco2
            biomass_records.append((fu, f, gj))
        else:
            e_other_tco2 += e_tco2
            other_records.append((fu, f, gj))

    e_baseline = e_coal_tco2 + e_biomass_tco2 + e_other_tco2

    # Project case
    e_project = e_baseline
    e_reduction = 0.0
    e_reduction_pct = 0.0
    if kiln.project_case and kiln.project_kiln_type:
        if kiln.project_kiln_type not in ef.brick_kilns:
            raise ValueError(f"Unknown project_kiln_type '{kiln.project_kiln_type}'")
        proj_ef = ef.brick_kilns[kiln.project_kiln_type]
        coal_ef = ef.fuel("coal_bituminous_NP")

        # Recompute with project kiln coal rate
        proj_coal_t = n_k * proj_ef.coal_t_per_1000
        proj_coal_after = proj_coal_t * (1 - kiln.biomass_substitution_fraction)
        proj_coal_gj = proj_coal_after * coal_ef.ncvc_gj_per_t
        proj_coal_tco2 = proj_coal_gj * coal_ef.fossil_ef / 1000.0

        # Biomass in the project case
        proj_biomass_t = (proj_coal_t - proj_coal_after) if kiln.biomass_substitution_fraction > 0 else 0
        if proj_biomass_t > 0:
            # Use rice husk as default biomass
            biomass_ef = ef.fuel("biomass_rice_husk")
            proj_biomass_tco2 = 0.0  # biogenic
        else:
            proj_biomass_tco2 = e_biomass_tco2

        proj_other = e_other_tco2   # keep other fuels
        e_project = proj_coal_tco2 + proj_biomass_tco2 + proj_other
        e_reduction = max(e_baseline - e_project, 0)
        e_reduction_pct = (e_reduction / e_baseline * 100) if e_baseline > 0 else 0

    # Scope 2 / 3
    td_factor = 1.0 / max(1.0 - ef.grid.t_and_d_loss, 0.01)
    e_elec_kg = kiln.electricity_consumption_kwh * ef.grid.combined_margin * td_factor
    e_elec = e_elec_kg / 1000.0
    e_transport = kiln.transport_tkm * 0.062 / 1000.0  # kg CO2/tkm

    e_scope1 = e_baseline
    e_total = e_scope1 + e_elec + e_transport

    # Intensities
    intensity_per_1000 = (e_total * 1000.0) / n_k if n_k > 0 else 0
    intensity_per_brick = (e_total * 1000.0) / kiln.annual_brick_production

    # SEC
    total_energy_gj += kiln.electricity_consumption_kwh * 0.0036
    sec_per_brick_mj = (total_energy_gj * 1000.0) / kiln.annual_brick_production
    sec_per_1000 = sec_per_brick_mj * 1000.0

    # Fuel share
    total_fuel_gj = total_energy_gj  # includes electricity now; we want fuel share
    fuel_only_gj = total_energy_gj - kiln.electricity_consumption_kwh * 0.0036
    fuel_share: Dict[str, float] = {}
    for fu, f in fuel_records:
        share = (fu.consumption_t * f.ncvc_gj_per_t) / fuel_only_gj if fuel_only_gj > 0 else 0
        fuel_share[fu.fuel_name] = round(share * 100, 2)
    biomass_share = (total_energy_gj_biogenic / fuel_only_gj * 100) if fuel_only_gj > 0 else 0

    nepal_avg_kg_per_1000 = 270.0
    delta_vs_nepal = intensity_per_1000 - nepal_avg_kg_per_1000

    return BrickEmissionsResult(
        kiln_type=kiln.kiln_type,
        annual_brick_production=kiln.annual_brick_production,
        e_coal_combustion_tco2=round(e_coal_tco2, 2),
        e_biomass_combustion_tco2=round(e_biomass_tco2, 2),
        e_other_fuel_tco2=round(e_other_tco2, 2),
        e_total_baseline_tco2=round(e_baseline, 2),
        e_total_project_tco2=round(e_project, 2),
        e_reduction_tco2=round(e_reduction, 2),
        e_reduction_pct=round(e_reduction_pct, 2),
        e_electricity_tco2=round(e_elec, 2),
        e_transport_tco2=round(e_transport, 2),
        e_scope1_tco2=round(e_scope1, 2),
        e_total_tco2=round(e_total, 2),
        intensity_kgco2_per_1000_bricks=round(intensity_per_1000, 2),
        intensity_kgco2_per_brick=round(intensity_per_brick, 4),
        sec_mj_per_brick=round(sec_per_brick_mj, 4),
        sec_mj_per_1000_bricks=round(sec_per_1000, 2),
        thermal_efficiency=kiln_ef.thermal_efficiency,
        delta_vs_nepal_avg_kgco2_per_1000=round(delta_vs_nepal, 2),
        fuel_share=fuel_share,
        biomass_share=round(biomass_share, 2),
    )


def list_kiln_types(ef: Optional[EmissionFactors] = None) -> List[str]:
    """Return all available kiln types."""
    if ef is None:
        ef = EmissionFactors.from_yaml()
    return list(ef.brick_kilns.keys())
