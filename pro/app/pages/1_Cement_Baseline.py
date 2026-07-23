"""
Cement Baseline — Tier 2 + Tier 3 with real Nepali plant presets.
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import plotly.graph_objects as go
import pandas as pd

from nepal_decarb_pro.core.cement import CementPlant, FuelUse, calculate_cement_tier2, calculate_cement_tier3
from nepal_decarb_pro.core.factors import default_factors
from nepal_decarb_pro.reporting import generate_verra_monitoring_report, generate_executive_summary

st.set_page_config(page_title="Cement Baseline", page_icon="🏭", layout="wide")
st.title("🏭 Cement Plant Baseline — Tier 2 + Tier 3")

presets = {
    "PlantA": dict(
        name="PlantA Industries Ltd",
        location="PlantA, Makwanpur",
        year=2024, clinker_t=950_000, cement_t=1_100_000,
        cao=0.66, mgo=0.018,
        coal_t=120_000, petcoke_t=18_000, diesel_t=400,
        elec_kwh=85_000_000, whr_kwh=0,
    ),
    "PlantB": dict(
        name="PlantB Industries Ltd",
        location="PlantB",
        year=2024, clinker_t=1_800_000, cement_t=2_100_000,
        cao=0.65, mgo=0.020,
        coal_t=235_000, petcoke_t=32_000, diesel_t=600,
        elec_kwh=160_000_000, whr_kwh=0,
    ),
    "Hongshi (Nawalparasi)": dict(
        name="plantc Cement",
        location="Nawalparasi",
        year=2024, clinker_t=3_200_000, cement_t=3_800_000,
        cao=0.66, mgo=0.015,
        coal_t=420_000, petcoke_t=55_000, diesel_t=900,
        elec_kwh=290_000_000, whr_kwh=0,
    ),
}

with st.sidebar:
    preset = st.selectbox("Plant preset", list(presets.keys()) + ["Custom"])
    tier = st.radio("Methodology tier", [2, 3], index=0)
    d = presets.get(preset, {})
    name = st.text_input("Plant name", d.get("name", "My Plant"))
    location = st.text_input("Location", d.get("location", "Nepal"))
    year = st.number_input("Year", value=d.get("year", 2024), step=1)
    clinker_t = st.number_input("Clinker (t/yr)", value=d.get("clinker_t", 500_000), step=10_000)
    cement_t = st.number_input("Cement (t/yr)", value=d.get("cement_t", 600_000), step=10_000)
    cao = st.number_input("CaO fraction", value=d.get("cao", 0.65), step=0.01)
    mgo = st.number_input("MgO fraction", value=d.get("mgo", 0.015), step=0.005)
    coal_t = st.number_input("Coal (t/yr)", value=d.get("coal_t", 70_000), step=1_000)
    petcoke_t = st.number_input("Petcoke (t/yr)", value=d.get("petcoke_t", 10_000), step=1_000)
    diesel_t = st.number_input("Diesel (t/yr)", value=d.get("diesel_t", 200), step=100)
    elec_kwh = st.number_input("Electricity (kWh/yr)", value=d.get("elec_kwh", 50_000_000), step=1_000_000)
    whr_kwh = st.number_input("WHR generation (kWh/yr)", value=d.get("whr_kwh", 0), step=1_000_000)

ef = default_factors()
fuels = []
if coal_t > 0: fuels.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=coal_t))
if petcoke_t > 0: fuels.append(FuelUse(fuel_name="petcoke", consumption_t=petcoke_t))
if diesel_t > 0: fuels.append(FuelUse(fuel_name="diesel", consumption_t=diesel_t))

plant = CementPlant(
    name=name, location=location, year=year,
    clinker_production_t=clinker_t, cement_production_t=cement_t,
    cao_fraction_clinker=cao, mgo_fraction_clinker=mgo,
    fuel_use=fuels, electricity_consumption_kwh=elec_kwh,
    whr_generation_kwh=whr_kwh,
)
result = (calculate_cement_tier3 if tier == 3 else calculate_cement_tier2)(plant, ef)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total emissions", f"{result.e_total_tco2:,.0f}", "tCO₂/yr")
c2.metric("Intensity", f"{result.intensity_kgco2_per_t_cement:,.0f}", "kg CO₂/t cement")
c3.metric("vs BAT (700)", f"{result.delta_vs_bat_kgco2_per_t:+,.0f}", "kg/t")
c4.metric("SEC", f"{result.sec_mj_per_t_clinker:,.0f}", "MJ/t clinker")

st.markdown(f"**Methodology:** {result.tier}")
st.markdown(f"_{result.method_description}_")

# Charts
st.markdown("### Emission breakdown")
br_df = pd.DataFrame({
    "Source": ["Process (calcination)", "Fuel combustion", "Grid electricity"],
    "tCO₂/yr": [result.e_process_tco2, result.e_fuel_total_tco2, result.e_electricity_tco2 + result.e_whr_offset_tco2],
})
fig = go.Figure(data=[go.Pie(labels=br_df["Source"], values=br_df["tCO₂/yr"], hole=0.5)])
fig.update_layout(height=380)
st.plotly_chart(fig, use_container_width=True)

# Export
if st.button("📄 Generate Executive Summary PDF"):
    out = Path("reports") / f"{name.replace(' ', '_')}_executive.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_executive_summary(plant, result, out)
    with open(out, "rb") as f:
        st.download_button("⬇️ Download", f, file_name=out.name)
