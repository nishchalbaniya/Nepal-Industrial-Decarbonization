"""
Cement Baseline — page 1
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import pandas as pd

from nepal_mrv import CementPlant, FuelUse, calculate_cement_emissions
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.reporting import generate_cement_report

st.set_page_config(page_title="Cement Baseline", page_icon="🏭", layout="wide")

st.title("🏭 Cement Plant Baseline Emissions Calculator")

st.markdown("""
Calculate baseline Scope 1 + 2 CO₂ emissions for a Nepali cement plant.
Implements **IPCC 2006 Vol.3 Ch.2 Tier 2 mass-balance** for clinker
calcination and **stationary combustion** for kiln fuels.
""")

# ---- Sidebar input ----
with st.sidebar:
    st.header("Plant inputs")
    preset = st.selectbox(
        "Load preset",
        ["Custom", "Hetauda Cement", "Udayapur Cement", "Hongshi (Nawalparasi)", "Ghorahi Cement"],
    )
    presets = {
        "Hetauda Cement": dict(
            name="Hetauda Cement Industries Ltd",
            location="Hetauda, Makwanpur",
            year=2024,
            clinker_t=950_000, cement_t=1_100_000,
            cao=0.66, mgo=0.018,
            coal_t=120_000, petcoke_t=18_000, diesel_t=400,
            elec_kwh=85_000_000,
        ),
        "Udayapur Cement": dict(
            name="Udayapur Cement Industries Ltd",
            location="Udayapur",
            year=2024,
            clinker_t=1_800_000, cement_t=2_100_000,
            cao=0.65, mgo=0.020,
            coal_t=235_000, petcoke_t=32_000, diesel_t=600,
            elec_kwh=160_000_000,
        ),
        "Hongshi (Nawalparasi)": dict(
            name="Hongshi Shivam Cement",
            location="Nawalparasi",
            year=2024,
            clinker_t=3_200_000, cement_t=3_800_000,
            cao=0.66, mgo=0.015,
            coal_t=420_000, petcoke_t=55_000, diesel_t=900,
            elec_kwh=290_000_000,
        ),
        "Ghorahi Cement": dict(
            name="Ghorahi Cement",
            location="Ghorahi, Dang",
            year=2024,
            clinker_t=1_200_000, cement_t=1_400_000,
            cao=0.65, mgo=0.020,
            coal_t=158_000, petcoke_t=22_000, diesel_t=500,
            elec_kwh=108_000_000,
        ),
    }
    if preset != "Custom":
        d = presets[preset]
        name = st.text_input("Plant name", d["name"])
        location = st.text_input("Location", d["location"])
        year = st.number_input("Reporting year", value=d["year"], step=1)
        clinker_t = st.number_input("Clinker production (t/yr)", value=d["clinker_t"], step=10_000)
        cement_t = st.number_input("Cement production (t/yr)", value=d["cement_t"], step=10_000)
        cao = st.number_input("CaO fraction in clinker", value=d["cao"], min_value=0.5, max_value=0.75, step=0.01)
        mgo = st.number_input("MgO fraction in clinker", value=d["mgo"], min_value=0.0, max_value=0.10, step=0.005)
        coal_t = st.number_input("Coal consumption (t/yr)", value=d["coal_t"], step=1_000)
        petcoke_t = st.number_input("Petcoke (t/yr)", value=d["petcoke_t"], step=1_000)
        diesel_t = st.number_input("Diesel (t/yr)", value=d["diesel_t"], step=100)
        elec_kwh = st.number_input("Grid electricity (kWh/yr)", value=d["elec_kwh"], step=1_000_000)
        biomass_t = st.number_input("Biomass (t/yr, biogenic)", value=0, step=1_000)
        natgas_m3 = st.number_input("Natural gas (m³/yr)", value=0, step=10_000)
    else:
        name = st.text_input("Plant name", "My Cement Plant")
        location = st.text_input("Location", "Kathmandu")
        year = st.number_input("Reporting year", value=2024, step=1)
        clinker_t = st.number_input("Clinker production (t/yr)", value=500_000, step=10_000)
        cement_t = st.number_input("Cement production (t/yr)", value=600_000, step=10_000)
        cao = st.number_input("CaO fraction in clinker", value=0.65, min_value=0.5, max_value=0.75, step=0.01)
        mgo = st.number_input("MgO fraction in clinker", value=0.015, min_value=0.0, max_value=0.10, step=0.005)
        coal_t = st.number_input("Coal (t/yr)", value=70_000, step=1_000)
        petcoke_t = st.number_input("Petcoke (t/yr)", value=10_000, step=1_000)
        diesel_t = st.number_input("Diesel (t/yr)", value=200, step=100)
        elec_kwh = st.number_input("Grid electricity (kWh/yr)", value=45_000_000, step=1_000_000)
        biomass_t = st.number_input("Biomass (t/yr)", value=0, step=1_000)
        natgas_m3 = st.number_input("Natural gas (m³/yr)", value=0, step=10_000)

# ---- Build plant object ----
ef = EmissionFactors.from_yaml()
fuel_use = []
if coal_t > 0: fuel_use.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=coal_t))
if petcoke_t > 0: fuel_use.append(FuelUse(fuel_name="petcoke", consumption_t=petcoke_t))
if diesel_t > 0: fuel_use.append(FuelUse(fuel_name="diesel", consumption_t=diesel_t))
if biomass_t > 0: fuel_use.append(FuelUse(fuel_name="biomass_rice_husk", consumption_t=biomass_t))
if natgas_m3 > 0: fuel_use.append(FuelUse(fuel_name="natural_gas", consumption_t=natgas_m3))

plant = CementPlant(
    name=name, location=location, year=year,
    clinker_production_t=clinker_t, cement_production_t=cement_t,
    cao_fraction_clinker=cao, mgo_fraction_clinker=mgo,
    fuel_use=fuel_use, electricity_consumption_kwh=elec_kwh,
)
result = calculate_cement_emissions(plant, ef)

# ---- KPIs ----
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total emissions", f"{result.e_total_tco2:,.0f}", "tCO₂/yr")
col2.metric("Intensity", f"{result.intensity_kgco2_per_t_cement:,.0f}", "kg CO₂/t cement")
col3.metric("vs BAT (~700)", f"{result.delta_vs_bat_kgco2_per_t:+,.0f}", "kg CO₂/t")
col4.metric("SEC (clinker)", f"{result.sec_mj_per_t_clinker:,.0f}", "MJ/t")

# ---- Charts ----
st.markdown("### Emission breakdown")
breakdown = pd.DataFrame({
    "Source": ["Process (calcination)", "Fuel combustion", "Grid electricity"],
    "tCO₂/yr": [result.e_process_tco2, result.e_fuel_total_tco2, result.e_electricity_tco2],
})
fig = go.Figure(data=[go.Pie(
    labels=breakdown["Source"], values=breakdown["tCO₂/yr"], hole=0.5,
    marker=dict(colors=["#DC143C", "#1f77b4", "#2ca02c"]),
)])
fig.update_layout(height=380, margin=dict(t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

if result.e_fuel_tco2:
    st.markdown("### Fuel-by-fuel breakdown")
    fdf = pd.DataFrame({
        "Fuel": list(result.e_fuel_tco2.keys()),
        "tCO₂/yr": list(result.e_fuel_tco2.values()),
    })
    fig2 = go.Figure(data=[go.Bar(x=fdf["Fuel"], y=fdf["tCO₂/yr"], marker_color="#1f77b4")])
    fig2.update_layout(height=320, yaxis_title="tCO₂/yr", xaxis_title="Fuel")
    st.plotly_chart(fig2, use_container_width=True)

# ---- Benchmarking ----
st.markdown("### Benchmarking")
bench_df = pd.DataFrame({
    "Benchmark": ["Global BAT", "Nepal average", "This plant"],
    "kg CO₂/t cement": [700, 950, result.intensity_kgco2_per_t_cement],
    "color": ["green", "orange", "red"],
})
fig3 = go.Figure(data=[go.Bar(
    x=bench_df["Benchmark"], y=bench_df["kg CO₂/t cement"],
    marker_color=["#2ca02c", "#ff7f0e", "#d62728"],
    text=[f"{v:.0f}" for v in bench_df["kg CO₂/t cement"]], textposition="outside",
)])
fig3.update_layout(height=320, yaxis_title="kg CO₂ per tonne cement", showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

# ---- Detailed table ----
st.markdown("### Detailed results")
df = pd.DataFrame({
    "Indicator": [
        "Process emissions (calcination)", "Coal combustion", "Petcoke combustion",
        "Diesel combustion", "Biomass (biogenic)", "Natural gas", "Total fuel",
        "Scope 1 (process + fuel)", "Scope 2 (electricity)", "TOTAL",
        "Intensity per t cement", "Intensity per t clinker", "SEC MJ/t clinker", "SEC MJ/t cement",
        "Clinker-to-cement ratio",
    ],
    "Value": [
        f"{result.e_process_tco2:,.2f}",
        f"{result.e_fuel_tco2.get('coal_bituminous_NP', 0):,.2f}",
        f"{result.e_fuel_tco2.get('petcoke', 0):,.2f}",
        f"{result.e_fuel_tco2.get('diesel', 0):,.2f}",
        f"{result.e_fuel_tco2.get('biomass_rice_husk', 0):,.2f}",
        f"{result.e_fuel_tco2.get('natural_gas', 0):,.2f}",
        f"{result.e_fuel_total_tco2:,.2f}",
        f"{result.e_scope1_tco2:,.2f}",
        f"{result.e_electricity_tco2:,.2f}",
        f"{result.e_total_tco2:,.2f}",
        f"{result.intensity_kgco2_per_t_cement:,.0f}",
        f"{result.intensity_kgco2_per_t_clinker:,.0f}",
        f"{result.sec_mj_per_t_clinker:,.0f}",
        f"{result.sec_mj_per_t_cement:,.0f}",
        f"{plant.clinker_to_cement_ratio:.3f}",
    ],
    "Unit": [
        "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "tCO₂/yr",
        "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "kg CO₂/t", "kg CO₂/t", "MJ/t", "MJ/t", "-",
    ],
})
st.dataframe(df, use_container_width=True, hide_index=True)

# ---- Export ----
st.markdown("### Export")
if st.button("📄 Generate Verra-style PDF report"):
    out = Path("reports") / f"{name.replace(' ', '_')}_baseline_{year}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_cement_report(plant, result, out)
    st.success(f"Report saved: {out}")
    with open(out, "rb") as f:
        st.download_button("⬇️ Download PDF", f, file_name=out.name)
