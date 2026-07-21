"""
Project Activity — page 3
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import pandas as pd

from nepal_mrv import (
    CementPlant, FuelUse, BrickKiln,
    calculate_cement_emissions, calculate_brick_emissions,
    ProjectActivity, calculate_project_emission_reduction, list_kiln_types,
)
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.reporting import generate_project_report

st.set_page_config(page_title="Project Activity", page_icon="💼", layout="wide")

st.title("💼 Project Activity — Emission Reductions & Carbon Revenue")

st.markdown("""
Define a baseline and project scenario, and we calculate annual emission
reductions, total Verra buffer deductions, and NPV at $15/$30/$50/tCO₂e.
""")

project_type = st.radio("Project type", ["Cement", "Brick"], horizontal=True)

if project_type == "Cement":
    st.subheader("Cement project")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Baseline plant**")
        b_coal = st.number_input("Baseline coal (t/yr)", value=120_000, step=1000, key="bc")
        b_petcoke = st.number_input("Baseline petcoke (t/yr)", value=18_000, step=1000, key="bp")
        b_diesel = st.number_input("Baseline diesel (t/yr)", value=400, step=100, key="bd")
        b_elec = st.number_input("Baseline grid electricity (kWh/yr)", value=85_000_000, step=1_000_000, key="be")
        b_clinker = st.number_input("Baseline clinker (t/yr)", value=950_000, step=10_000, key="bcl")
        b_cement = st.number_input("Baseline cement (t/yr)", value=1_100_000, step=10_000, key="bce")
    with col2:
        st.markdown("**Project plant (post-mitigation)**")
        p_coal = st.number_input("Project coal (t/yr)", value=96_000, step=1000, key="pc")
        p_petcoke = st.number_input("Project petcoke (t/yr)", value=14_400, step=1000, key="pp")
        p_diesel = st.number_input("Project diesel (t/yr)", value=400, step=100, key="pd")
        p_biomass = st.number_input("Project biomass (t/yr, biogenic)", value=42_000, step=1000, key="pbi")
        p_elec = st.number_input("Project grid electricity (kWh/yr, after WHR)", value=63_000_000, step=1_000_000, key="pe")
        p_clinker = st.number_input("Project clinker (t/yr)", value=950_000, step=10_000, key="pcl")
        p_cement = st.number_input("Project cement (t/yr)", value=1_100_000, step=10_000, key="pce")
    p_natgas = 0.0
else:
    st.subheader("Brick project")
    kiln_types = list_kiln_types()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Baseline kiln**")
        b_kiln = st.selectbox("Baseline kiln type", kiln_types,
                              index=kiln_types.index("clamp_traditional"),
                              format_func=lambda x: x.replace("_"," ").title())
        b_bricks = st.number_input("Annual bricks", value=4_500_000, step=100_000, key="bb")
    with col2:
        st.markdown("**Project kiln**")
        p_kiln = st.selectbox("Project kiln type", kiln_types,
                              index=kiln_types.index("zigzag"),
                              format_func=lambda x: x.replace("_"," ").title())
        biomass_frac = st.slider("Biomass substitution fraction", 0.0, 0.5, 0.20, 0.05)
    p_bricks = b_bricks

# ---- Activity parameters ----
st.markdown("**Activity parameters**")
col3, col4, col5 = st.columns(3)
with col3:
    project_name = st.text_input("Project name", "Hetauda Cement Decarbonization")
    vintage = st.number_input("Vintage year", value=2026, step=1)
with col4:
    crediting = st.number_input("Crediting period (years)", value=10, min_value=1, max_value=20)
    carbon_price = st.number_input("Base carbon price (USD/t)", value=15.0, step=1.0)
with col5:
    discount = st.slider("Discount rate", 0.0, 0.30, 0.10, 0.01)
    leakage = st.slider("Leakage fraction", 0.0, 0.20, 0.05, 0.01)

# ---- Build & run ----
ef = EmissionFactors.from_yaml()
if project_type == "Cement":
    base_plant = CementPlant(
        name=project_name, location="Nepal", year=2024,
        clinker_production_t=b_clinker, cement_production_t=b_cement,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=b_coal),
            FuelUse(fuel_name="petcoke", consumption_t=b_petcoke),
            FuelUse(fuel_name="diesel", consumption_t=b_diesel),
        ],
        electricity_consumption_kwh=b_elec,
    )
    proj_plant = CementPlant(
        name=project_name, location="Nepal", year=2024,
        clinker_production_t=p_clinker, cement_production_t=p_cement,
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=p_coal),
            FuelUse(fuel_name="petcoke", consumption_t=p_petcoke),
            FuelUse(fuel_name="diesel", consumption_t=p_diesel),
            FuelUse(fuel_name="biomass_rice_husk", consumption_t=p_biomass),
        ],
        electricity_consumption_kwh=p_elec,
    )
    activity = ProjectActivity(
        project_name=project_name, project_type="cement",
        baseline_year=2024, crediting_period_years=crediting,
        vintage_year=vintage, baseline_plant=base_plant,
        project_plant=proj_plant, leakage_fraction=leakage,
        carbon_price_usd_per_t=carbon_price, discount_rate=discount,
        methodology="Verra VCS AMS-III.H (alternative fuels + WHR)",
    )
else:
    base_kiln = BrickKiln(
        name=project_name, location="Nepal", year=2024,
        kiln_type=b_kiln, annual_brick_production=b_bricks,
    )
    proj_kiln = BrickKiln(
        name=project_name, location="Nepal", year=2024,
        kiln_type=p_kiln, annual_brick_production=p_bricks,
        biomass_substitution_fraction=biomass_frac,
        project_case=True, project_kiln_type=p_kiln,
    )
    activity = ProjectActivity(
        project_name=project_name, project_type="brick",
        baseline_year=2024, crediting_period_years=crediting,
        vintage_year=vintage, baseline_kiln=base_kiln,
        project_kiln=proj_kiln, leakage_fraction=leakage,
        carbon_price_usd_per_t=carbon_price, discount_rate=discount,
        methodology="Gold Standard TPDDTEC" if "clamp" in b_kiln else "Verra VCS brick methodology",
    )

er = calculate_project_emission_reduction(activity)

# ---- KPIs ----
st.markdown("### Annual emission reductions")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Baseline", f"{er.baseline_annual_tco2:,.0f}", "tCO₂/yr")
c2.metric("Project", f"{er.project_annual_tco2:,.0f}", "tCO₂/yr")
c3.metric("Net reduction", f"{er.net_annual_reduction_tco2:,.0f}", "tCO₂/yr")
c4.metric("Net issuable", f"{er.net_issuable_annual_tco2:,.0f}", "tCO₂/yr (after 15% buffer)")

# ---- NPV at different prices ----
st.markdown("### Revenue NPV across carbon prices")
years = list(range(1, crediting + 1))
npv_15 = [er.net_annual_reduction_tco2 * 15.0 / ((1+discount)**y) for y in years]
npv_30 = [er.net_annual_reduction_tco2 * 30.0 / ((1+discount)**y) for y in years]
npv_50 = [er.net_annual_reduction_tco2 * 50.0 / ((1+discount)**y) for y in years]
fig = go.Figure()
fig.add_trace(go.Scatter(x=years, y=npv_15, name="$15/t", fill="tozeroy", line_color="#1f77b4"))
fig.add_trace(go.Scatter(x=years, y=npv_30, name="$30/t", fill="tonexty", line_color="#2ca02c"))
fig.add_trace(go.Scatter(x=years, y=npv_50, name="$50/t", fill="tonexty", line_color="#d62728"))
fig.update_layout(
    height=380, xaxis_title="Project year", yaxis_title="Cumulative NPV (USD)",
    legend=dict(orientation="h", y=-0.15),
)
st.plotly_chart(fig, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cumulative reduction", f"{er.cumulative_reduction_tco2:,.0f}", f"tCO₂ over {crediting} yrs")
c2.metric("NPV @ $15/t", f"${er.npv_revenue_usd:,.0f}")
c3.metric("NPV @ $30/t", f"${er.npv_at_30_usd:,.0f}")
c4.metric("NPV @ $50/t", f"${er.npv_at_50_usd:,.0f}")

st.info(f"**Additionality screening:** {er.additionality_screening}")

# ---- Export ----
if st.button("📄 Generate project PDF report"):
    out = Path("reports") / f"{project_name.replace(' ','_')}_project.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_project_report(activity, er, out)
    st.success(f"Report saved: {out}")
    with open(out, "rb") as f:
        st.download_button("⬇️ Download PDF", f, file_name=out.name)
