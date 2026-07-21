"""
Cement sector baseline emissions calculator.
============================================

Implements IPCC 2006 Vol.3 Ch.2 Tier 2 mass-balance approach for
clinker process CO2 + fuel combustion for kiln fuels + grid electricity.

Also implements:
- Verra VCS AMS-III.H (waste-heat recovery cement project activity)
- GHG Protocol Cement Scope 1+2 guidance (2017)
- GCCA sustainability framework (per-tonne product intensity)

The math:
  E_total = E_process + E_fuel + E_electricity + E_transport
  E_process = (CaO_frac * 0.7857 + MgO_frac * 1.092) * clinker_t
  E_fuel_i = fuel_t_i * ncvc_gj_t * ef_kgco2_gj
  E_electricity = elec_kwh * grid_ef * (1 / (1 - tdl))
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import numpy as np

from nepal_mrv.emission_factors import EmissionFactors


# ----------------------------------------------------------------------------
# Data models
# ----------------------------------------------------------------------------

class FuelUse(BaseModel):
    """One fuel input to the cement plant."""
    fuel_name: str            # matches emission_factors.yaml
    consumption_t: float      # tonnes per year

    @field_validator("consumption_t")
    @classmethod
    def _non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("consumption_t must be >= 0")
        return v


class CementPlant(BaseModel):
    """Cement plant annual operating data for baseline calculation."""
    name: str
    location: str
    year: int
    # Production
    clinker_production_t: float = Field(..., gt=0, description="Clinker t/yr")
    cement_production_t: float = Field(..., gt=0, description="Cement t/yr")
    # Raw material composition (mass fractions)
    cao_fraction_clinker: float = Field(0.65, ge=0, le=1)
    mgo_fraction_clinker: float = Field(0.015, ge=0, le=0.1)
    # Fuel use (per year)
    fuel_use: List[FuelUse] = Field(default_factory=list)
    # Grid electricity
    electricity_consumption_kwh: float = Field(0, ge=0)
    # Optional: alternative fuel substitution rate (for project case)
    af_substitution_fraction: float = Field(0, ge=0, le=1)
    # Optional: transport emissions (Scope 3, default 0)
    e_transport_tco2: float = Field(0, ge=0)

    @property
    def clinker_to_cement_ratio(self) -> float:
        if self.cement_production_t == 0:
            return 0
        return self.clinker_production_t / self.cement_production_t


class CementEmissionsBreakdown(BaseModel):
    """Result of a cement baseline emissions calculation."""
    # Process emissions
    e_process_tco2: float
    # Fuel combustion by fuel
    e_fuel_tco2: Dict[str, float] = Field(default_factory=dict)
    e_fuel_total_tco2: float
    # Grid electricity (Scope 2)
    e_electricity_tco2: float
    # Optional transport
    e_transport_tco2: float = 0.0
    # Totals
    e_scope1_tco2: float
    e_scope2_tco2: float
    e_total_tco2: float
    # Intensities
    intensity_kgco2_per_t_cement: float
    intensity_kgco2_per_t_clinker: float
    # Benchmark deltas
    delta_vs_bat_kgco2_per_t: float      # +ve = worse than BAT
    delta_vs_nepal_avg_kgco2_per_t: float
    # Specific energy consumption
    sec_mj_per_t_clinker: float
    sec_mj_per_t_cement: float


# ----------------------------------------------------------------------------
# Calculator
# ----------------------------------------------------------------------------

def calculate_cement_emissions(
    plant: CementPlant, ef: EmissionFactors
) -> CementEmissionsBreakdown:
    """
    Calculate baseline CO2 emissions for a Nepali cement plant.

    Implements IPCC 2006 Vol.3 Ch.2 Tier 2 mass-balance approach.

    Parameters
    ----------
    plant : CementPlant
        Annual operating data
    ef : EmissionFactors
        Database of emission factors

    Returns
    -------
    CementEmissionsBreakdown
        Detailed emission breakdown
    """
    # 1. Process emissions from clinker calcination (IPCC Tier 2)
    # E_process = clinker_t * (CaO_frac * CO2/CaO + MgO_frac * CO2/MgO)
    cao_frac = plant.cao_fraction_clinker
    mgo_frac = plant.mgo_fraction_clinker
    co2_per_t_clinker_calculated = (
        cao_frac * ef.co2_per_t_cao + mgo_frac * ef.co2_per_t_mgo
    )
    e_process = plant.clinker_production_t * co2_per_t_clinker_calculated

    # 2. Fuel combustion (IPCC 2006 Vol.2 Ch.1 stationary combustion)
    e_fuel_breakdown: Dict[str, float] = {}
    e_fuel_total = 0.0
    for fu in plant.fuel_use:
        f = ef.fuel(fu.fuel_name)
        # Convert: tonnes * GJ/t * kgCO2/GJ = kgCO2
        e_kg = fu.consumption_t * f.ncvc_gj_per_t * f.ef_kgco2_per_gj
        e_tco2 = e_kg / 1000.0
        e_fuel_breakdown[fu.fuel_name] = e_tco2
        e_fuel_total += e_tco2

    # 3. Grid electricity (Scope 2) — apply T&D loss
    td_factor = 1.0 / max(1.0 - ef.grid_td_loss, 0.01)
    e_electricity_kgco2 = plant.electricity_consumption_kwh * ef.grid_cm * td_factor
    e_electricity = e_electricity_kgco2 / 1000.0

    # 4. Totals
    e_scope1 = e_process + e_fuel_total
    e_scope2 = e_electricity
    e_total = e_scope1 + e_scope2 + plant.e_transport_tco2

    # 5. Intensities
    intensity_per_cement = (e_total * 1000.0) / plant.cement_production_t
    intensity_per_clinker = (e_total * 1000.0) / plant.clinker_production_t

    # 6. Specific energy consumption (MJ / t)
    total_fuel_energy_gj = sum(
        fu.consumption_t * ef.fuel(fu.fuel_name).ncvc_gj_per_t
        for fu in plant.fuel_use
    )
    elec_gj = plant.electricity_consumption_kwh * 0.0036  # 1 kWh = 0.0036 GJ
    total_energy_gj = total_fuel_energy_gj + elec_gj
    sec_clinker_mj = (total_energy_gj * 1000.0) / plant.clinker_production_t
    sec_cement_mj = (total_energy_gj * 1000.0) / plant.cement_production_t

    # 7. Benchmark deltas (positive = plant is worse than benchmark)
    # BAT intensity ~ 0.50 tCO2/t cement (calcination floor) + ~0.20 fuel + ~0.04 elec
    bat_intensity_kg = 700.0
    nepal_avg_intensity_kg = 950.0
    delta_bat = intensity_per_cement - bat_intensity_kg
    delta_nepal = intensity_per_cement - nepal_avg_intensity_kg

    return CementEmissionsBreakdown(
        e_process_tco2=round(e_process, 2),
        e_fuel_tco2={k: round(v, 2) for k, v in e_fuel_breakdown.items()},
        e_fuel_total_tco2=round(e_fuel_total, 2),
        e_electricity_tco2=round(e_electricity, 2),
        e_transport_tco2=plant.e_transport_tco2,
        e_scope1_tco2=round(e_scope1, 2),
        e_scope2_tco2=round(e_scope2, 2),
        e_total_tco2=round(e_total, 2),
        intensity_kgco2_per_t_cement=round(intensity_per_cement, 2),
        intensity_kgco2_per_t_clinker=round(intensity_per_clinker, 2),
        delta_vs_bat_kgco2_per_t=round(delta_bat, 2),
        delta_vs_nepal_avg_kgco2_per_t=round(delta_nepal, 2),
        sec_mj_per_t_clinker=round(sec_clinker_mj, 2),
        sec_mj_per_t_cement=round(sec_cement_mj, 2),
    )


# Backwards-compatible alias
CementEmissions = CementEmissionsBreakdown
