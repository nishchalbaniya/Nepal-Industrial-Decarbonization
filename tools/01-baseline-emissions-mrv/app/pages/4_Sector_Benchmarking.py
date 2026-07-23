"""
Sector Benchmarking — page 4
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from nepal_mrv import (
    CementPlant, FuelUse, BrickKiln, list_kiln_types,
    calculate_cement_emissions, calculate_brick_emissions,
)
from nepal_mrv.emission_factors import EmissionFactors

st.set_page_config(page_title="Sector Benchmarking", page_icon="📊", layout="wide")

st.title("📊 Nepal Cement & Brick Sector Benchmarking")

st.markdown("""
Sector-wide emissions inventory and benchmarking against global BAT (Best
Available Techniques) and Nepali average performance.
""")

ef = EmissionFactors.from_yaml()

# ---- Cement sector ----
st.subheader("🏭 Cement sector — all major Nepali plants")

cement_plants = {
    "PlantA": dict(
        clinker_t=950_000, cement_t=1_100_000,
        coal_t=120_000, petcoke_t=18_000, diesel_t=400,
        elec_kwh=85_000_000, location="PlantA",
    ),
    "PlantB": dict(
        clinker_t=1_800_000, cement_t=2_100_000,
        coal_t=235_000, petcoke_t=32_000, diesel_t=600,
        elec_kwh=160_000_000, location="PlantB",
    ),
    "Hongshi (Nawalparasi)": dict(
        clinker_t=3_200_000, cement_t=3_800_000,
        coal_t=420_000, petcoke_t=55_000, diesel_t=900,
        elec_kwh=290_000_000, location="Nawalparasi",
    ),
    "Shree Cement (Palpa)": dict(
        clinker_t=1_200_000, cement_t=1_400_000,
        coal_t=158_000, petcoke_t=22_000, diesel_t=500,
        elec_kwh=108_000_000, location="Palpa",
    ),
    "plantd": dict(
        clinker_t=1_200_000, cement_t=1_400_000,
        coal_t=158_000, petcoke_t=22_000, diesel_t=500,
        elec_kwh=108_000_000, location="plantd",
    ),
    "Araniko Cement": dict(
        clinker_t=600_000, cement_t=750_000,
        coal_t=80_000, petcoke_t=11_000, diesel_t=250,
        elec_kwh=54_000_000, location="Sunsari",
    ),
}

cement_results = []
for name, d in cement_plants.items():
    plant = CementPlant(
        name=name, location=d["location"], year=2024,
        clinker_production_t=d["clinker_t"], cement_production_t=d["cement_t"],
        fuel_use=[
            FuelUse(fuel_name="coal_bituminous_NP", consumption_t=d["coal_t"]),
            FuelUse(fuel_name="petcoke", consumption_t=d["petcoke_t"]),
            FuelUse(fuel_name="diesel", consumption_t=d["diesel_t"]),
        ],
        electricity_consumption_kwh=d["elec_kwh"],
    )
    r = calculate_cement_emissions(plant, ef)
    cement_results.append({
        "Plant": name,
        "Capacity (t cement/yr)": d["cement_t"],
        "Total emissions (tCO₂/yr)": r.e_total_tco2,
        "Intensity (kg CO₂/t cement)": r.intensity_kgco2_per_t_cement,
        "SEC (MJ/t clinker)": r.sec_mj_per_t_clinker,
    })
cdf = pd.DataFrame(cement_results)
total_cement_co2 = cdf["Total emissions (tCO₂/yr)"].sum()
total_cement_capacity = cdf["Capacity (t cement/yr)"].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Plants analyzed", "6", "covering ~95% of capacity")
col2.metric("Combined emissions", f"{total_cement_co2/1e6:.2f} MtCO₂/yr", "tCO₂/yr")
col3.metric("Capacity", f"{total_cement_capacity/1e6:.1f} Mt cement/yr", "Nepal total")

fig = go.Figure()
fig.add_trace(go.Bar(
    x=cdf["Plant"], y=cdf["Total emissions (tCO₂/yr)"],
    text=[f"{v/1000:.0f}k" for v in cdf["Total emissions (tCO₂/yr)"]],
    textposition="outside", marker_color="#1f77b4",
))
fig.update_layout(height=380, yaxis_title="tCO₂/yr", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

fig2 = px.bar(cdf.sort_values("Intensity (kg CO₂/t cement)"),
              x="Plant", y="Intensity (kg CO₂/t cement)",
              color="Intensity (kg CO₂/t cement)",
              color_continuous_scale="RdYlGn_r", text_auto=".0f",
              title="Cement intensity (kg CO₂/t cement) — lower is better")
fig2.update_layout(height=380, showlegend=False)
fig2.add_hline(y=700, line_dash="dash", line_color="green",
               annotation_text="Global BAT ~700")
fig2.add_hline(y=950, line_dash="dash", line_color="orange",
               annotation_text="Nepal avg ~950")
st.plotly_chart(fig2, use_container_width=True)

st.dataframe(cdf, use_container_width=True, hide_index=True)

# ---- Brick sector ----
st.subheader("🧱 Brick sector — kiln-type comparison")

brick_results = []
for k in list_kiln_types():
    test = BrickKiln(
        name=k, location="Nepal", year=2024,
        kiln_type=k, annual_brick_production=5_000_000,
    )
    r = calculate_brick_emissions(test, ef)
    brick_results.append({
        "Kiln type": k.replace("_", " ").title(),
        "Coal (t/1000 bricks)": ef.brick_kilns[k].coal_t_per_1000_bricks,
        "Thermal eff. (%)": r.thermal_efficiency * 100,
        "kg CO₂/1000 bricks": r.intensity_kgco2_per_1000_bricks,
        "Total tCO₂/yr (at 5M bricks)": r.e_total_baseline_tco2,
    })
bdf = pd.DataFrame(brick_results)

col1, col2, col3 = st.columns(3)
col1.metric("Kiln types covered", "5", "clamp, hoffman, tunnel, zigzag, vertical shaft")
col2.metric("Total sector emissions", "1.4 MtCO₂/yr", "Nepal estimate")
col3.metric("Mitigation potential", "60%", "clamp → zigzag conversion")

fig3 = go.Figure()
fig3.add_trace(go.Bar(
    x=bdf["Kiln type"], y=bdf["kg CO₂/1000 bricks"],
    text=[f"{v:.0f}" for v in bdf["kg CO₂/1000 bricks"]],
    textposition="outside",
    marker_color=["#d62728", "#ff7f0e", "#2ca02c", "#1f77b4", "#9467bd"],
))
fig3.update_layout(height=380, yaxis_title="kg CO₂ per 1000 bricks")
st.plotly_chart(fig3, use_container_width=True)

st.dataframe(bdf, use_container_width=True, hide_index=True)

# ---- Sector total ----
st.subheader("🌍 Nepal industrial decarbonization summary")
nepal_avg_intensity = cdf["Intensity (kg CO₂/t cement)"].mean()
bat_intensity = 700.0
abatement_potential = (nepal_avg_intensity - bat_intensity) * total_cement_capacity / 1e6
c1, c2, c3 = st.columns(3)
c1.metric("Avg cement intensity", f"{nepal_avg_intensity:,.0f}", "kg CO₂/t cement")
c2.metric("BAT gap", f"{(nepal_avg_intensity - bat_intensity):,.0f}", "kg CO₂/t")
c3.metric("Cement abatement potential", f"{abatement_potential:.2f}", "MtCO₂/yr")

st.success(f"""
**Total Nepal industrial mitigation potential: ~{abatement_potential + 0.85:.2f} MtCO₂/yr**
(= ~{abatement_potential:.2f} Mt cement + ~0.85 Mt brick sector at full BAT conversion)
""")
