"""
MRV report generator.
=====================

Generates a Verra VCS / Gold Standard–style monitoring report PDF.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from fpdf import FPDF

from nepal_mrv.cement import CementEmissionsBreakdown, CementPlant
from nepal_mrv.brick import BrickEmissionsBreakdown, BrickKiln
from nepal_mrv.mrv import ProjectEmissionReduction, ProjectActivity


class MRVReport(FPDF):
    """PDF report generator for MRV submissions."""

    def header(self) -> None:
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, "Nepal Industrial Decarbonization Suite - MRV Report", 0, 1, "R")
        self.set_draw_color(220, 50, 50)
        self.set_line_width(0.4)
        self.line(10, 18, 200, 18)
        self.set_text_color(0, 0, 0)
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(
            0, 10,
            f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} - "
            f"Author: Nishchal Baniya (Himalayan Carbon Nepal) - Page {self.page_no()}",
            0, 0, "C",
        )

    def title_block(self, title: str, subtitle: str) -> None:
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(20, 50, 90)
        self.cell(0, 12, title, 0, 1)
        self.set_font("Helvetica", "", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, subtitle, 0, 1)
        self.ln(3)
        self.set_text_color(0, 0, 0)

    def section(self, label: str) -> None:
        self.set_font("Helvetica", "B", 12)
        self.set_fill_color(230, 240, 250)
        self.set_text_color(20, 50, 90)
        self.cell(0, 8, label, 0, 1, "L", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def kv(self, key: str, value, unit: str = "") -> None:
        self.set_font("Helvetica", "B", 10)
        self.cell(80, 6, key, 0, 0)
        self.set_font("Helvetica", "", 10)
        if isinstance(value, float):
            value_s = f"{value:,.2f}"
        else:
            value_s = str(value)
        text = f"{value_s} {unit}".strip()
        self.cell(0, 6, text, 0, 1)

    def table(self, headers, rows, col_widths=None) -> None:
        if col_widths is None:
            col_widths = [190 / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(220, 230, 245)
        for h, w in zip(headers, col_widths):
            self.cell(w, 7, str(h), 1, 0, "L", fill=True)
        self.ln()
        self.set_font("Helvetica", "", 9)
        for row in rows:
            for cell, w in zip(row, col_widths):
                text = f"{cell:,.2f}" if isinstance(cell, float) else str(cell)
                self.cell(w, 6, text, 1, 0, "L")
            self.ln()
        self.ln(2)


def generate_cement_report(
    plant: CementPlant, br: CementEmissionsBreakdown, out_path: Path
) -> Path:
    pdf = MRVReport()
    pdf.add_page()
    pdf.title_block(
        "Cement Plant Baseline Emissions Report",
        f"{plant.name} - {plant.location} - Reporting year {plant.year}",
    )

    pdf.section("1. Plant Identification")
    pdf.kv("Plant name", plant.name)
    pdf.kv("Location", plant.location)
    pdf.kv("Reporting year", plant.year)
    pdf.kv("Clinker production", plant.clinker_production_t, "t/yr")
    pdf.kv("Cement production", plant.cement_production_t, "t/yr")
    pdf.kv("Clinker-to-cement ratio", round(plant.clinker_to_cement_ratio, 3))

    pdf.section("2. Emissions Summary (tCO2/yr)")
    pdf.kv("Process emissions (calcination)", br.e_process_tco2)
    pdf.kv("Fuel combustion - total", br.e_fuel_total_tco2)
    pdf.kv("Grid electricity (Scope 2)", br.e_electricity_tco2)
    pdf.kv("Total Scope 1 (process + fuel)", br.e_scope1_tco2)
    pdf.kv("Total Scope 2 (electricity)", br.e_scope2_tco2)
    pdf.kv("Total emissions", br.e_total_tco2)

    pdf.section("3. Fuel Combustion Breakdown")
    rows = [
        (name, t, t / br.e_fuel_total_tco2 * 100 if br.e_fuel_total_tco2 else 0)
        for name, t in br.e_fuel_tco2.items()
    ]
    pdf.table(
        ["Fuel", "tCO2/yr", "% of fuel CO2"],
        rows,
        col_widths=[80, 55, 55],
    )

    pdf.section("4. Emission Intensity")
    pdf.kv("Per tonne cement", br.intensity_kgco2_per_t_cement, "kg CO2/t")
    pdf.kv("Per tonne clinker", br.intensity_kgco2_per_t_clinker, "kg CO2/t")
    pdf.kv("vs global BAT (~700 kg/t)", br.delta_vs_bat_kgco2_per_t, "kg CO2/t")
    pdf.kv("vs Nepal avg (~950 kg/t)", br.delta_vs_nepal_avg_kgco2_per_t, "kg CO2/t")

    pdf.section("5. Specific Energy Consumption")
    pdf.kv("MJ per tonne clinker", br.sec_mj_per_t_clinker, "MJ/t")
    pdf.kv("MJ per tonne cement", br.sec_mj_per_t_cement, "MJ/t")

    pdf.section("6. Methodology")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        "Emissions calculated using IPCC 2006 Guidelines Vol.3 Ch.2 Tier 2 mass-balance "
        "approach for clinker process CO2 and stationary combustion for kiln fuels. "
        "Grid electricity uses NEA 2023/24 combined margin emission factor "
        "(0.0256 kg CO2/kWh) with 22.5% T&D loss adjustment. "
        "Aligned with GHG Protocol Cement Scope 1+2 guidance and Verra VCS methodologies.",
    )

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 4,
        "This report is generated by nepal_mrv v0.1.0 (open source). "
        "All calculations are reproducible from the input data. "
        "Author: Nishchal Baniya, Himalayan Carbon Nepal. "
        "License: MIT (code) / CC-BY-4.0 (data).",
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path


def generate_brick_report(
    kiln: BrickKiln, br: BrickEmissionsBreakdown, out_path: Path
) -> Path:
    pdf = MRVReport()
    pdf.add_page()
    pdf.title_block(
        "Brick Kiln Baseline Emissions Report",
        f"{kiln.name} - {kiln.location} - {kiln.year}",
    )

    pdf.section("1. Kiln Identification")
    pdf.kv("Kiln name", kiln.name)
    pdf.kv("Location", kiln.location)
    pdf.kv("Reporting year", kiln.year)
    pdf.kv("Kiln type", kiln.kiln_type)
    pdf.kv("Annual brick production", kiln.annual_brick_production, "bricks/yr")

    pdf.section("2. Emissions Summary (tCO2/yr)")
    pdf.kv("Coal combustion", br.e_coal_combustion_tco2)
    pdf.kv("Biomass combustion (biogenic)", br.e_biomass_combustion_tco2)
    pdf.kv("Other fuels", br.e_other_fuel_tco2)
    pdf.kv("Total baseline emissions", br.e_total_baseline_tco2)
    if kiln.project_case:
        pdf.kv("Project emissions", br.e_total_project_tco2)
        pdf.kv("Emission reduction", br.e_reduction_tco2)
        pdf.kv("Reduction percentage", br.e_reduction_pct, "%")

    pdf.section("3. Emission Intensity")
    pdf.kv("Per 1000 bricks", br.intensity_kgco2_per_1000_bricks, "kg CO2/1000 bricks")
    pdf.kv("Per single brick", br.intensity_kgco2_per_brick, "kg CO2/brick")
    pdf.kv("vs Nepal avg (270 kg/1000)", br.delta_vs_nepal_avg_kgco2_per_1000, "kg/1000")

    pdf.section("4. Specific Energy Consumption")
    pdf.kv("MJ per brick", br.sec_mj_per_brick, "MJ/brick")
    pdf.kv("MJ per 1000 bricks", br.sec_mj_per_1000_bricks, "MJ/1000")
    pdf.kv("Thermal efficiency", br.thermal_efficiency * 100, "%")

    pdf.section("5. Methodology")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        "Emissions calculated using kiln-type-specific coal consumption rate "
        "(IPCC 2006 Vol.3 Ch.2 stationary combustion) and Nepali coal NCV/EF. "
        "Biomass substitution treated as biogenic (carbon-neutral). "
        "Aligned with Gold Standard TPDDTEC methodology and Verra VCS brick project methodologies.",
    )

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 4,
        "Generated by nepal_mrv v0.1.0 (open source). "
        "Author: Nishchal Baniya, Himalayan Carbon Nepal. "
        "License: MIT (code) / CC-BY-4.0 (data).",
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path


def generate_project_report(
    activity: ProjectActivity, result: ProjectEmissionReduction, out_path: Path
) -> Path:
    pdf = MRVReport()
    pdf.add_page()
    pdf.title_block(
        "Project Activity - Emission Reduction Report",
        f"{activity.project_name} - {activity.project_type.title()} project",
    )

    pdf.section("1. Project Identification")
    pdf.kv("Project name", activity.project_name)
    pdf.kv("Project type", activity.project_type)
    pdf.kv("Vintage year", activity.vintage_year)
    pdf.kv("Crediting period", activity.crediting_period_years, "years")
    pdf.kv("Methodology", activity.methodology)

    pdf.section("2. Annual Emissions (tCO2e/yr)")
    pdf.kv("Baseline emissions", result.baseline_annual_tco2)
    pdf.kv("Project emissions", result.project_annual_tco2)
    pdf.kv("Leakage", result.leakage_annual_tco2)
    pdf.kv("Net annual reduction", result.net_annual_reduction_tco2)
    pdf.kv("Buffer pool deduction (15%)", result.buffer_deduction_annual_tco2)
    pdf.kv("Net issuable credits", result.net_issuable_annual_tco2)

    pdf.section("3. Cumulative Impact")
    pdf.kv("Cumulative reduction", result.cumulative_reduction_tco2, "tCO2e")
    pdf.kv("Period revenue at $15/t", result.npv_revenue_usd, "USD")
    pdf.kv("NPV at $30/t", result.npv_at_30_usd, "USD")
    pdf.kv("NPV at $50/t", result.npv_at_50_usd, "USD")
    pdf.kv("Annual revenue @ base", result.annual_revenue_usd, "USD")

    pdf.section("4. Additionality Assessment")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, result.additionality_screening, 0, 1)

    pdf.section("5. Methodology Notes")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(
        0, 5,
        f"Baseline = sum of clinker process + fuel combustion + grid electricity. "
        f"Project = same components with substituted fuels/technologies. "
        f"Leakage = {activity.leakage_fraction*100:.1f}% (default per Verra buffer guidance). "
        f"Buffer pool = {result.buffer_pool_pct*100:.0f}% (Verra non-permanence risk). "
        f"Revenue NPV discounted at {activity.discount_rate*100:.0f}% over "
        f"{activity.crediting_period_years} years.",
    )

    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(
        0, 4,
        "Generated by nepal_mrv v0.1.0 (open source). "
        "Author: Nishchal Baniya, Himalayan Carbon Nepal. "
        "License: MIT (code) / CC-BY-4.0 (data).",
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))
    return out_path
