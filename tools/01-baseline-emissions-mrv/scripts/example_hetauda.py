"""
Example: PlantA Industries Ltd — Full baseline + project assessment
============================================================================

This script demonstrates a complete end-to-end workflow using the nepal_mrv
package: define a plant, calculate baseline, simulate a project (biomass
substitution + waste-heat recovery), and export a monitoring report.

Run:
    python scripts/example_planta.py
"""
from __future__ import annotations

import json
from pathlib import Path

from nepal_mrv import (
    CementPlant, FuelUse,
    calculate_cement_emissions,
    ProjectActivity, calculate_project_emission_reduction,
)
from nepal_mrv.reporting import generate_cement_report, generate_project_report
from nepal_mrv.emission_factors import EmissionFactors


def run() -> None:
    ef = EmissionFactors.from_yaml()

    # ------------------------------------------------------------------
    # 1. Define PlantA baseline (FY 2023/24)
    # ------------------------------------------------------------------
    planta_baseline = CementPlant(
        name="PlantA Industries Ltd",
        location="PlantA, Makwanpur, Bagmati Province",
        year=2024,
        clinker_production_t=950_000,
        cement_production_t=1_100_000,
        cao_fraction_clinker=0.66,
        mgo_fraction_clinker=0.018,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=120_000),
            FuelUse(fuel_name="petcoke",            consumption_t=18_000),
            FuelUse(fuel_name="diesel",             consumption_t=400),
        ],
        electricity_consumption_kwh=85_000_000,   # 85 GWh/yr
    )
    baseline = calculate_cement_emissions(planta_baseline, ef)
    print("=" * 70)
    print(f"  {planta_baseline.name} - Baseline {planta_baseline.year}")
    print("=" * 70)
    print(f"  Process CO2 (calcination)  : {baseline.e_process_tco2:>10,.1f} tCO2")
    print(f"  Fuel combustion (total)    : {baseline.e_fuel_total_tco2:>10,.1f} tCO2")
    print(f"  Grid electricity (Scope 2) : {baseline.e_electricity_tco2:>10,.1f} tCO2")
    print(f"  TOTAL                       : {baseline.e_total_tco2:>10,.1f} tCO2")
    print(f"  Intensity (kg CO2/t cement) : {baseline.intensity_kgco2_per_t_cement:>10,.0f}")
    print(f"  SEC (MJ/t clinker)         : {baseline.sec_mj_per_t_clinker:>10,.0f}")
    print(f"  vs BAT (~700 kg/t)         : {baseline.delta_vs_bat_kgco2_per_t:>+10,.0f} kg/t")
    print()

    # ------------------------------------------------------------------
    # 2. Project scenario: 20% biomass co-firing + WHR (3 MW)
    # ------------------------------------------------------------------
    # Net effect: lower coal use, biomass (biogenic) replaces some coal,
    # and WHR generates ~22 GWh/yr of in-house electricity
    planta_project = CementPlant(
        name="PlantA Industries Ltd",
        location="PlantA, Makwanpur, Bagmati Province",
        year=2024,
        clinker_production_t=950_000,
        cement_production_t=1_100_000,
        cao_fraction_clinker=0.66,
        mgo_fraction_clinker=0.018,
        fuel_use=[
            # Coal + petcoke reduced 20% via biomass substitution
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=96_000),   # 20% less
            FuelUse(fuel_name="petcoke",            consumption_t=14_400),   # 20% less
            FuelUse(fuel_name="diesel",             consumption_t=400),
            # Biomass: 20% of original coal energy from biomass
            FuelUse(fuel_name="biomass_rice_husk",  consumption_t=42_000),   # biogenic
        ],
        # Grid import reduced 22 GWh due to WHR
        electricity_consumption_kwh=63_000_000,  # 85 - 22 = 63 GWh/yr
    )
    project_em = calculate_cement_emissions(planta_project, ef)

    activity = ProjectActivity(
        project_name="PlantA Decarbonization - Biomass Co-firing + WHR",
        project_type="cement",
        baseline_year=2024,
        crediting_period_years=10,
        vintage_year=2026,
        baseline_plant=planta_baseline,
        project_plant=planta_project,
        leakage_fraction=0.05,
        carbon_price_usd_per_t=15.0,
        discount_rate=0.10,
        methodology="Verra VCS AMS-III.H (alternative fuels + waste-heat recovery)",
    )
    er = calculate_project_emission_reduction(activity)
    print("=" * 70)
    print(f"  PROJECT: {activity.project_name}")
    print("=" * 70)
    print(f"  Baseline annual             : {er.baseline_annual_tco2:>10,.0f} tCO2")
    print(f"  Project annual              : {er.project_annual_tco2:>10,.0f} tCO2")
    print(f"  Gross reduction             : {(er.baseline_annual_tco2 - er.project_annual_tco2):>10,.0f} tCO2")
    print(f"  Leakage (5%)                : {er.leakage_annual_tco2:>10,.0f} tCO2")
    print(f"  Net annual reduction        : {er.net_annual_reduction_tco2:>10,.0f} tCO2")
    print(f"  Buffer pool (15%)           : {er.buffer_deduction_annual_tco2:>10,.0f} tCO2")
    print(f"  Net issuable / yr           : {er.net_issuable_annual_tco2:>10,.0f} tCO2e")
    print(f"  Cumulative over 10 yrs      : {er.cumulative_reduction_tco2:>10,.0f} tCO2e")
    print(f"  Annual revenue @ $15/t      : {er.annual_revenue_usd:>10,.0f} USD")
    print(f"  NPV revenue @ $15/t         : {er.npv_revenue_usd:>10,.0f} USD")
    print(f"  NPV @ $30/t                 : {er.npv_at_30_usd:>10,.0f} USD")
    print(f"  NPV @ $50/t                 : {er.npv_at_50_usd:>10,.0f} USD")
    print(f"  Additionality               : {er.additionality_screening}")
    print()

    # ------------------------------------------------------------------
    # 3. Export reports (PDF + JSON)
    # ------------------------------------------------------------------
    out_dir = Path(__file__).parent.parent / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf_cement = generate_cement_report(
        planta_baseline, baseline,
        out_dir / "planta_cement_baseline_2024.pdf",
    )
    print(f"  Cement report  : {pdf_cement}")

    pdf_proj = generate_project_report(
        activity, er,
        out_dir / "planta_cement_project_assessment.pdf",
    )
    print(f"  Project report : {pdf_proj}")

    json_out = out_dir / "planta_cement_project_results.json"
    json_out.write_text(json.dumps(er.model_dump(), indent=2))
    print(f"  JSON results   : {json_out}")
    print()
    print("Done. nepal_mrv v0.1.0 — open source MRV for Nepalese industry.")


if __name__ == "__main__":
    run()
