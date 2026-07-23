"""
Command-line interface for the Nepal Decarbonization Platform.
"""
from __future__ import annotations

import click
import json
from pathlib import Path
from tabulate import tabulate

from nepal_decarb_pro.core.cement import CementPlant, FuelUse, calculate_cement_tier2, calculate_cement_tier3
from nepal_decarb_pro.core.brick import BrickKiln, calculate_brick_emissions, list_kiln_types
from nepal_decarb_pro.core.factors import default_factors
from nepal_decarb_pro.standards.iso_14064 import check_iso_14064_part1
from nepal_decarb_pro.markets.verra import generate_verra_pdd
from nepal_decarb_pro.markets.pricing import get_revenue_scenarios


@click.group()
def cli() -> None:
    """Nepal Industrial Decarbonization Platform — Pro Edition."""
    pass


@cli.command()
@click.option("--name", default="PlantA Industries Ltd")
@click.option("--location", default="PlantA, Makwanpur")
@click.option("--year", default=2024, type=int)
@click.option("--clinker-t", required=True, type=float)
@click.option("--cement-t", required=True, type=float)
@click.option("--coal-t", default=0, type=float)
@click.option("--petcoke-t", default=0, type=float)
@click.option("--diesel-t", default=0, type=float)
@click.option("--elec-kwh", default=0, type=float)
@click.option("--whr-kwh", default=0, type=float)
@click.option("--tier", default=2, type=int, help="2 or 3")
@click.option("--json-out", type=Path, default=None)
def cement(
    name, location, year, clinker_t, cement_t, coal_t, petcoke_t,
    diesel_t, elec_kwh, whr_kwh, tier, json_out,
) -> None:
    """Calculate cement baseline emissions."""
    ef = default_factors()
    fuels = []
    if coal_t > 0: fuels.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=coal_t))
    if petcoke_t > 0: fuels.append(FuelUse(fuel_name="petcoke", consumption_t=petcoke_t))
    if diesel_t > 0: fuels.append(FuelUse(fuel_name="diesel", consumption_t=diesel_t))

    plant = CementPlant(
        name=name, location=location, year=year,
        clinker_production_t=clinker_t, cement_production_t=cement_t,
        fuel_use=fuels, electricity_consumption_kwh=elec_kwh,
        whr_generation_kwh=whr_kwh,
    )
    result = (calculate_cement_tier3 if tier == 3 else calculate_cement_tier2)(plant, ef)

    if json_out:
        json_out.write_text(json.dumps(result.model_dump(), indent=2))

    click.echo(f"\n{'='*70}\n  {name} - {location} ({year}) [Tier {tier}]\n{'='*70}")
    rows = [
        ("Process (calcination)", f"{result.e_process_tco2:,.0f} tCO2"),
        ("Fuel combustion", f"{result.e_fuel_total_tco2:,.0f} tCO2"),
        ("Grid electricity", f"{result.e_electricity_tco2:,.0f} tCO2"),
        ("WHR offset", f"{result.e_whr_offset_tco2:,.0f} tCO2"),
        ("Scope 1", f"{result.e_scope1_tco2:,.0f} tCO2"),
        ("Scope 2", f"{result.e_scope2_tco2:,.0f} tCO2"),
        ("TOTAL", f"{result.e_total_tco2:,.0f} tCO2"),
        ("", ""),
        ("Intensity", f"{result.intensity_kgco2_per_t_cement:,.0f} kg CO2/t cement"),
        ("vs BAT (700)", f"{result.delta_vs_bat_kgco2_per_t:+,.0f} kg/t"),
        ("vs Nepal avg (950)", f"{result.delta_vs_nepal_avg_kgco2_per_t:+,.0f} kg/t"),
    ]
    click.echo(tabulate(rows, headers=["Indicator", "Value"], tablefmt="github"))


@cli.command()
@click.option("--name", default="Bhairahawa Kiln")
@click.option("--location", default="Bhairahawa")
@click.option("--year", default=2024, type=int)
@click.option("--kiln", "kiln_type", default="clamp_traditional",
              type=click.Choice(list_kiln_types()))
@click.option("--bricks", required=True, type=int)
@click.option("--coal-t", default=None, type=float)
@click.option("--biomass-t", default=None, type=float)
@click.option("--elec-kwh", default=0, type=float)
def brick(name, location, year, kiln_type, bricks, coal_t, biomass_t, elec_kwh) -> None:
    """Calculate brick kiln baseline emissions."""
    ef = default_factors()
    fuels = []
    if coal_t is not None:
        fuels.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=coal_t))
    if biomass_t is not None:
        fuels.append(FuelUse(fuel_name="biomass_rice_husk", consumption_t=biomass_t))

    kiln = BrickKiln(
        name=name, location=location, year=year,
        kiln_type=kiln_type, annual_brick_production=bricks,
        fuel_use=fuels, electricity_consumption_kwh=elec_kwh,
    )
    result = calculate_brick_emissions(kiln, ef)

    click.echo(f"\n{'='*70}\n  {name} - {location} ({year}) - {kiln_type}\n{'='*70}")
    rows = [
        ("Annual bricks", f"{bricks:,}"),
        ("Coal combustion", f"{result.e_coal_combustion_tco2:,.1f} tCO2"),
        ("Biomass (biogenic)", f"{result.e_biomass_combustion_tco2:,.1f} tCO2"),
        ("Other fuels", f"{result.e_other_fuel_tco2:,.1f} tCO2"),
        ("TOTAL", f"{result.e_total_baseline_tco2:,.1f} tCO2"),
        ("Intensity", f"{result.intensity_kgco2_per_1000_bricks:,.0f} kg/1000"),
        ("Thermal efficiency", f"{result.thermal_efficiency*100:.0f}%"),
    ]
    click.echo(tabulate(rows, headers=["Indicator", "Value"], tablefmt="github"))


@cli.command()
@click.option("--name", required=True)
@click.option("--baseline-tco2", required=True, type=float)
@click.option("--project-tco2", required=True, type=float)
@click.option("--crediting-years", default=10, type=int)
@click.option("--type", "project_type", default="cement",
              type=click.Choice(["cement", "brick"]))
def verra(name, baseline_tco2, project_tco2, crediting_years, project_type) -> None:
    """Generate a Verra VCS PDD skeleton."""
    pdd = generate_verra_pdd(
        project_name=name,
        project_type=project_type,
        baseline_annual_tco2=baseline_tco2,
        project_annual_tco2=project_tco2,
        crediting_period_years=crediting_years,
    )
    click.echo(f"\n{'='*70}\n  Verra VCS PDD: {name}\n{'='*70}")
    rows = [
        ("Methodology", pdd.methodology),
        ("Period", f"{pdd.crediting_period_start} to {pdd.crediting_period_end}"),
        ("Baseline annual", f"{pdd.baseline_emissions_annual_tco2:,.0f} tCO2"),
        ("Project annual", f"{pdd.project_emissions_annual_tco2:,.0f} tCO2"),
        ("Gross reduction", f"{pdd.gross_emission_reductions_annual_tco2:,.0f} tCO2"),
        ("Leakage", f"{pdd.leakage_pct:.0f}%"),
        ("Net reduction", f"{pdd.net_emission_reductions_annual_tco2:,.0f} tCO2"),
        ("Annual revenue @ $15", f"${pdd.annual_revenue_at_15:,.0f}"),
        ("Annual revenue @ $30", f"${pdd.annual_revenue_at_30:,.0f}"),
        ("Annual revenue @ $50", f"${pdd.annual_revenue_at_50:,.0f}"),
    ]
    click.echo(tabulate(rows, headers=["Field", "Value"], tablefmt="github"))


@cli.command()
@click.option("--annual-reduction-tco2", required=True, type=float)
@click.option("--crediting-years", default=10, type=int)
def carbon_price(annual_reduction_tco2, crediting_years) -> None:
    """Show revenue scenarios across carbon prices."""
    scenarios = get_revenue_scenarios(annual_reduction_tco2, crediting_years)
    click.echo(f"\n{'='*70}\n  Revenue scenarios: {annual_reduction_tco2:,.0f} tCO2/yr for {crediting_years} yrs\n{'='*70}")
    rows = [
        (name, f"${info['price_usd_per_tco2']:.0f}/t",
         f"${info['annual_revenue_usd']:,.0f}",
         f"${info['npv_revenue_usd']:,.0f}")
        for name, info in scenarios.items()
    ]
    click.echo(tabulate(rows, headers=["Market", "Price", "Annual", "NPV"], tablefmt="github"))


@cli.command()
def version() -> None:
    """Show version."""
    from nepal_decarb_pro import __version__
    click.echo(f"nepal_decarb_pro v{__version__}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
