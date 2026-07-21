"""
GCCA (Global Cement & Concrete Association) Sustainability Framework KPIs.

The GCCA framework defines 7 KPIs:
  1. CO2 per tonne cementitious
  2. Specific heat consumption
  3. Specific power consumption
  4. Alternative fuel substitution rate
  5. Clinker-to-cement ratio
  6. Cementitious content per m3 of concrete
  7. Concrete strength efficiency

We compute KPIs 1-5 from the plant data.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field

from nepal_decarb_pro.core.cement import CementPlant, CementEmissionsResult
from nepal_decarb_pro.core.factors import EmissionFactors


class GCCAKPI(BaseModel):
    """GCCA sustainability KPIs for a plant."""
    plant_name: str
    reporting_year: int
    # KPI 1
    co2_per_t_cement: float                # kg CO2/t cementitious
    co2_per_t_clinker: float               # kg CO2/t clinker
    # KPI 2
    specific_heat_consumption_mj_per_t_clinker: float
    # KPI 3
    specific_power_consumption_kwh_per_t_cement: float
    # KPI 4
    alternative_fuel_substitution_rate_pct: float
    # KPI 5
    clinker_to_cement_ratio: float
    # Decomposition
    co2_from_fossil_fuel_pct: float
    co2_from_process_pct: float
    co2_from_electricity_pct: float
    # vs GCCA benchmark
    gcca_benchmark_co2: float              # ~700 kg/t
    gcca_benchmark_heat: float             # ~3300 MJ/t clinker
    vs_gcca_benchmark_co2_pct: float
    vs_gcca_benchmark_heat_pct: float


def calculate_gcca_kpis(
    plant: CementPlant,
    result: CementEmissionsResult,
    ef: EmissionFactors,
) -> GCCAKPI:
    """
    Calculate GCCA sustainability KPIs.
    """
    # KPI 1: CO2 per tonne cementitious
    co2_per_t = result.intensity_kgco2_per_t_cement
    co2_per_t_clinker = result.intensity_kgco2_per_t_clinker

    # KPI 2: Specific heat consumption
    shc = result.sec_mj_per_t_clinker

    # KPI 3: Specific power consumption
    spc_kwh_per_t = (
        (plant.electricity_consumption_kwh - plant.whr_generation_kwh)
        / plant.cement_production_t
    )

    # KPI 4: AF substitution rate (energy basis)
    total_energy = sum(
        fu.consumption_t * ef.fuel(fu.fuel_name).ncvc_gj_per_t
        for fu in plant.fuel_use
    )
    alt_energy = sum(
        fu.consumption_t * ef.fuel(fu.fuel_name).ncvc_gj_per_t
        for fu in plant.fuel_use
        if ef.fuel(fu.fuel_name).category in ("biomass", "waste")
    )
    af_rate = (alt_energy / total_energy * 100) if total_energy > 0 else 0

    # KPI 5: Clinker-to-cement ratio
    ctc = plant.clinker_to_cement_ratio

    # Decomposition
    total = result.e_total_tco2
    pct_fossil = result.e_fuel_total_tco2 / total * 100 if total > 0 else 0
    pct_process = result.e_process_tco2 / total * 100 if total > 0 else 0
    pct_elec = (result.e_electricity_tco2 + result.e_whr_offset_tco2) / total * 100 if total > 0 else 0

    gcca_co2 = 700.0
    gcca_heat = 3300.0
    vs_co2 = (co2_per_t - gcca_co2) / gcca_co2 * 100
    vs_heat = (shc - gcca_heat) / gcca_heat * 100

    return GCCAKPI(
        plant_name=plant.name,
        reporting_year=plant.year,
        co2_per_t_cement=round(co2_per_t, 1),
        co2_per_t_clinker=round(co2_per_t_clinker, 1),
        specific_heat_consumption_mj_per_t_clinker=round(shc, 1),
        specific_power_consumption_kwh_per_t_cement=round(spc_kwh_per_t, 1),
        alternative_fuel_substitution_rate_pct=round(af_rate, 1),
        clinker_to_cement_ratio=round(ctc, 3),
        co2_from_fossil_fuel_pct=round(pct_fossil, 1),
        co2_from_process_pct=round(pct_process, 1),
        co2_from_electricity_pct=round(pct_elec, 1),
        gcca_benchmark_co2=gcca_co2,
        gcca_benchmark_heat=gcca_heat,
        vs_gcca_benchmark_co2_pct=round(vs_co2, 1),
        vs_gcca_benchmark_heat_pct=round(vs_heat, 1),
    )
