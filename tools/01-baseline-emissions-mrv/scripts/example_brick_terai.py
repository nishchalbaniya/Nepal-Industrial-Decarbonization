"""
Example: Nepal Terai Brick Kiln Sector — Baseline + Clamp->Zigzag Conversion
=============================================================================

Demonstrates a project activity converting a traditional clamp kiln to a
modern zigzag kiln, with biomass co-firing. This is one of the most
common project types in the Nepali brick sector (UNEP/GEF has promoted
this transformation since 2014).

Run:
    python scripts/example_brick_terai.py
"""
from __future__ import annotations

import json
from pathlib import Path

from nepal_mrv import (
    BrickKiln,
    calculate_brick_emissions,
    ProjectActivity, calculate_project_emission_reduction,
)
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.reporting import generate_brick_report, generate_project_report


def run() -> None:
    ef = EmissionFactors.from_yaml()

    # ------------------------------------------------------------------
    # 1. Baseline: traditional clamp kiln in Bhairahawa
    # ------------------------------------------------------------------
    bhairahawa_clamp = BrickKiln(
        name="Bhairahawa Clamp Kiln #4",
        location="Bhairahawa, Lumbini Province",
        year=2024,
        kiln_type="clamp_traditional",
        annual_brick_production=4_500_000,
        # Defaults used: coal = 300 kg / 1000 bricks
        project_case=True,
        project_kiln_type="zigzag",
        biomass_substitution_fraction=0.20,
    )

    result = calculate_brick_emissions(bhairahawa_clamp, ef)
    print("=" * 70)
    print(f"  {bhairahawa_clamp.name} - Baseline & Project")
    print("=" * 70)
    print(f"  Kiln type              : {bhairahawa_clamp.kiln_type} (baseline)")
    print(f"  Annual bricks          : {bhairahawa_clamp.annual_brick_production:,}")
    print(f"  Baseline emissions     : {result.e_total_baseline_tco2:>10,.1f} tCO2/yr")
    print(f"  Project emissions      : {result.e_total_project_tco2:>10,.1f} tCO2/yr")
    print(f"  Emission REDUCTION     : {result.e_reduction_tco2:>10,.1f} tCO2/yr")
    print(f"  Reduction %            : {result.e_reduction_pct:>10,.1f} %")
    print(f"  Baseline intensity     : {result.intensity_kgco2_per_1000_bricks:>10,.1f} kg/1000")
    print()

    # ------------------------------------------------------------------
    # 2. Project Activity (Verra/Gold Standard)
    # ------------------------------------------------------------------
    # The "baseline" and "project" plants are the same kiln object —
    # but the project_plant is the new zigzag configuration.
    bhairahawa_zigzag = BrickKiln(
        name="Bhairahawa Zigzag Kiln (post-conversion)",
        location="Bhairahawa, Lumbini Province",
        year=2024,
        kiln_type="zigzag",
        annual_brick_production=4_500_000,
        project_case=False,
    )

    activity = ProjectActivity(
        project_name="Bhairahawa Clamp-to-Zigzag Conversion + Biomass Co-firing",
        project_type="brick",
        baseline_year=2024,
        crediting_period_years=7,  # Gold Standard brick crediting period
        vintage_year=2026,
        baseline_kiln=bhairahawa_clamp,
        project_kiln=bhairahawa_zigzag,
        leakage_fraction=0.05,
        carbon_price_usd_per_t=15.0,
        discount_rate=0.10,
        methodology="Gold Standard TPDDTEC (clamp->zigzag)",
    )
    er = calculate_project_emission_reduction(activity)
    print(f"  Crediting period        : {activity.crediting_period_years} years")
    print(f"  Net annual reduction    : {er.net_annual_reduction_tco2:>10,.0f} tCO2")
    print(f"  Cumulative (7 yrs)      : {er.cumulative_reduction_tco2:>10,.0f} tCO2")
    print(f"  Annual revenue @ $15/t  : {er.annual_revenue_usd:>10,.0f} USD")
    print(f"  NPV @ $15/t             : {er.npv_revenue_usd:>10,.0f} USD")
    print(f"  NPV @ $30/t             : {er.npv_at_30_usd:>10,.0f} USD")
    print(f"  NPV @ $50/t             : {er.npv_at_50_usd:>10,.0f} USD")
    print(f"  Additionality           : {er.additionality_screening}")
    print()

    # ------------------------------------------------------------------
    # 3. Export
    # ------------------------------------------------------------------
    out_dir = Path(__file__).parent.parent / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = generate_brick_report(
        bhairahawa_clamp, result,
        out_dir / "bhairahawa_brick_baseline_2024.pdf",
    )
    print(f"  Brick PDF report : {pdf}")
    json_out = out_dir / "bhairahawa_brick_results.json"
    json_out.write_text(json.dumps(result.model_dump(), indent=2))
    print(f"  JSON results     : {json_out}")
    print()
    print("Done. nepal_mrv v0.1.0 — open source MRV for Nepalese brick sector.")


if __name__ == "__main__":
    run()
