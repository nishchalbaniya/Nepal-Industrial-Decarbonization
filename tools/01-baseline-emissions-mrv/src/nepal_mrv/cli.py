"""
Command-line interface for nepal_mrv.
"""
from __future__ import annotations

import click
import json
from pathlib import Path
from tabulate import tabulate

from nepal_mrv import (
    CementPlant, FuelUse,
    BrickKiln,
    calculate_cement_emissions,
    calculate_brick_emissions,
    calculate_project_emission_reduction,
    ProjectActivity,
)
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.reporting import (
    generate_cement_report, generate_brick_report, generate_project_report,
)


# ----------------------------------------------------------------------------
# Cement CLI
# ----------------------------------------------------------------------------

@click.group()
def cli() -> None:
    """Nepal MRV — Cement & Brick baseline emissions + MRV tool."""
    pass


@cli.command()
@click.option("--name", default="Nepali Cement Plant")
@click.option("--location", default="Hetauda")
@click.option("--year", default=2024, type=int)
@click.option("--clinker-t", required=True, type=float, help="Clinker production t/yr")
@click.option("--cement-t", required=True, type=float, help="Cement production t/yr")
@click.option("--coal-t", default=0.0, type=float)
@click.option("--petcoke-t", default=0.0, type=float)
@click.option("--biomass-t", default=0.0, type=float)
@click.option("--natgas-m3", default=0.0, type=float)
@click.option("--diesel-t", default=0.0, type=float)
@click.option("--elec-kwh", default=0.0, type=float, help="Grid electricity kWh/yr")
@click.option("--json-out", default=None, type=Path)
def cement(
    name, location, year, clinker_t, cement_t,
    coal_t, petcoke_t, biomass_t, natgas_m3, diesel_t,
    elec_kwh, json_out,
):
    """Calculate baseline emissions for a cement plant."""
    ef = EmissionFactors.from_yaml()
    fuel_use = []
    if coal_t > 0: fuel_use.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=coal_t))
    if petcoke_t > 0: fuel_use.append(FuelUse(fuel_name="petcoke", consumption_t=petcoke_t))
    if biomass_t > 0: fuel_use.append(FuelUse(fuel_name="biomass_rice_husk", consumption_t=biomass_t))
    if natgas_m3 > 0: fuel_use.append(FuelUse(fuel_name="natural_gas", consumption_t=natgas_m3))
    if diesel_t > 0: fuel_use.append(FuelUse(fuel_name="diesel", consumption_t=diesel_t))

    plant = CementPlant(
        name=name, location=location, year=year,
        clinker_production_t=clinker_t, cement_production_t=cement_t,
        fuel_use=fuel_use, electricity_consumption_kwh=elec_kwh,
    )
    result = calculate_cement_emissions(plant, ef)

    if json_out:
        json_out.write_text(json.dumps(result.model_dump(), indent=2))
        click.echo(f"Saved: {json_out}")

    click.echo("\n" + "=" * 60)
    click.echo(f"  {plant.name} - {plant.location} ({plant.year})")
    click.echo("=" * 60)
    rows = [
        ("Process (calcination)", f"{result.e_process_tco2:,.1f} tCO2"),
        ("Fuel combustion (total)", f"{result.e_fuel_total_tco2:,.1f} tCO2"),
        ("Grid electricity (Scope 2)", f"{result.e_electricity_tco2:,.1f} tCO2"),
        ("Total Scope 1", f"{result.e_scope1_tco2:,.1f} tCO2"),
        ("Total Scope 2", f"{result.e_scope2_tco2:,.1f} tCO2"),
        ("TOTAL", f"{result.e_total_tco2:,.1f} tCO2"),
        ("", ""),
        ("Intensity (kg CO2/t cement)", f"{result.intensity_kgco2_per_t_cement:,.0f}"),
        ("Intensity (kg CO2/t clinker)", f"{result.intensity_kgco2_per_t_clinker:,.0f}"),
        ("vs BAT (~700 kg/t)", f"{result.delta_vs_bat_kgco2_per_t:+.0f} kg/t"),
        ("vs Nepal avg (~950 kg/t)", f"{result.delta_vs_nepal_avg_kgco2_per_t:+.0f} kg/t"),
        ("SEC (MJ/t clinker)", f"{result.sec_mj_per_t_clinker:,.0f}"),
        ("SEC (MJ/t cement)", f"{result.sec_mj_per_t_cement:,.0f}"),
    ]
    click.echo(tabulate(rows, headers=["Indicator", "Value"], tablefmt="github"))


# ----------------------------------------------------------------------------
# Brick CLI
# ----------------------------------------------------------------------------

@cli.command()
@click.option("--name", default="Nepali Brick Kiln")
@click.option("--location", default="Bhairahawa")
@click.option("--year", default=2024, type=int)
@click.option("--kiln", "kiln_type", default="clamp_traditional",
              type=click.Choice(list(__import__("nepal_mrv.brick", fromlist=["list_kiln_types"]).list_kiln_types())))
@click.option("--bricks", required=True, type=int, help="Annual brick production")
@click.option("--coal-t", default=None, type=float)
@click.option("--biomass-t", default=None, type=float)
@click.option("--natgas-m3", default=None, type=float)
@click.option("--diesel-l", default=None, type=float)
@click.option("--project-kiln", default=None, type=click.Choice(list(__import__("nepal_mrv.brick", fromlist=["list_kiln_types"]).list_kiln_types())))
@click.option("--biomass-frac", default=0.0, type=float, help="Biomass substitution 0-1")
@click.option("--json-out", default=None, type=Path)
def brick(
    name, location, year, kiln_type, bricks,
    coal_t, biomass_t, natgas_m3, diesel_l,
    project_kiln, biomass_frac, json_out,
):
    """Calculate baseline emissions for a brick kiln."""
    ef = EmissionFactors.from_yaml()
    is_project = project_kiln is not None
    kiln = BrickKiln(
        name=name, location=location, year=year,
        kiln_type=kiln_type, annual_brick_production=bricks,
        coal_t=coal_t, biomass_t=biomass_t, natural_gas_m3=natgas_m3,
        diesel_l=diesel_l,
        biomass_substitution_fraction=biomass_frac,
        project_case=is_project, project_kiln_type=project_kiln,
    )
    result = calculate_brick_emissions(kiln, ef)

    if json_out:
        json_out.write_text(json.dumps(result.model_dump(), indent=2))
        click.echo(f"Saved: {json_out}")

    click.echo("\n" + "=" * 60)
    click.echo(f"  {kiln.name} - {kiln.location} ({kiln.year}) - {kiln.kiln_type}")
    click.echo("=" * 60)
    rows = [
        ("Annual bricks", f"{kiln.annual_brick_production:,.0f}"),
        ("Coal combustion", f"{result.e_coal_combustion_tco2:,.1f} tCO2"),
        ("Biomass (biogenic)", f"{result.e_biomass_combustion_tco2:,.1f} tCO2"),
        ("Other fuels", f"{result.e_other_fuel_tco2:,.1f} tCO2"),
        ("TOTAL baseline", f"{result.e_total_baseline_tco2:,.1f} tCO2"),
        ("", ""),
        ("Intensity (kg CO2/1000 bricks)", f"{result.intensity_kgco2_per_1000_bricks:,.1f}"),
        ("Intensity (g CO2/brick)", f"{result.intensity_kgco2_per_brick*1000:,.1f}"),
        ("Thermal efficiency", f"{result.thermal_efficiency*100:,.0f} %"),
        ("vs Nepal avg (270 kg/1000)", f"{result.delta_vs_nepal_avg_kgco2_per_1000:+.1f} kg"),
    ]
    if is_project:
        rows.extend([
            ("", ""),
            ("Project emissions", f"{result.e_total_project_tco2:,.1f} tCO2"),
            ("Emission REDUCTION", f"{result.e_reduction_tco2:,.1f} tCO2"),
            ("Reduction %", f"{result.e_reduction_pct:,.1f} %"),
        ])
    click.echo(tabulate(rows, headers=["Indicator", "Value"], tablefmt="github"))


# ----------------------------------------------------------------------------
# Project CLI
# ----------------------------------------------------------------------------

@cli.command()
@click.option("--name", required=True)
@click.option("--type", "project_type", type=click.Choice(["cement", "brick"]), required=True)
@click.option("--vintage", default=2026, type=int)
@click.option("--crediting-years", default=10, type=int)
@click.option("--carbon-price", default=15.0, type=float, help="USD/tCO2e")
@click.option("--json-out", default=None, type=Path)
@click.option("--report-out", default=None, type=Path)
def project(name, project_type, vintage, crediting_years, carbon_price, json_out, report_out):
    """Calculate emission reductions and revenue for a project activity.

    Reads project definition from 'project_<name>.yaml' in current directory.
    """
    # Stub - real impl reads YAML
    click.echo("Note: 'project' command expects a YAML file in cwd.")
    click.echo("Use the Python API for full project workflows:")
    click.echo("  from nepal_mrv import ProjectActivity, calculate_project_emission_reduction")


# ----------------------------------------------------------------------------
# Report CLI
# ----------------------------------------------------------------------------

@cli.command()
@click.option("--plant", required=True, help="Plant name (cement only for now)")
@click.option("--year", required=True, type=int)
@click.option("--out", required=True, type=Path)
def report(plant, year, out):
    """Generate a Verra-style monitoring report PDF."""
    # This is a demo entry point; for full functionality use the Python API
    click.echo(f"Report generation requires plant data. Use Python API:")
    click.echo(f"  from nepal_mrv.reporting import generate_cement_report")
    click.echo(f"  from nepal_mrv.cement import CementPlant, calculate_cement_emissions")
    click.echo(f"  ... etc.")
    click.echo(f"See README.md for examples.")


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------

def main() -> None:
    cli()


if __name__ == "__main__":
    main()
