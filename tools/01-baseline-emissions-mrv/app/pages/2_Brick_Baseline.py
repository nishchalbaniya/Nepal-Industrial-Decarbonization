"""
Brick Baseline — page 2
"""
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import plotly.graph_objects as go
import pandas as pd

from nepal_mrv import BrickKiln, calculate_brick_emissions, list_kiln_types
from nepal_mrv.emission_factors import EmissionFactors
from nepal_mrv.reporting import generate_brick_report

st.set_page_config(page_title="Brick Baseline", page_icon="🧱", layout="wide")

st.title("🧱 Brick Kiln Baseline Emissions Calculator")

st.markdown("""
Calculate baseline CO₂ emissions for any of 5 kiln types used in Nepal.
Implements kiln-type-specific coal consumption rates per WBCSD/GCCA brick
protocol and IPCC 2006 stationary combustion methodology.
""")

# ---- Sidebar input ----
with st.sidebar:
    st.header("Kiln inputs")
    kiln_types = list_kiln_types()
    name = st.text_input("Kiln name", "Bhairahawa Clamp Kiln #4")
    location = st.text_input("Location", "Bhairahawa, Lumbini Province")
    year = st.number_input("Year", value=2024, step=1)
    kiln_type = st.selectbox(
        "Kiln type", kiln_types,
        index=kiln_types.index("clamp_traditional"),
        format_func=lambda x: x.replace("_", " ").title(),
    )
    bricks = st.number_input("Annual brick production", value=4_500_000, step=100_000, min_value=1)
    is_project = st.checkbox("Also evaluate a project activity (technology switch)")
    if is_project:
        project_kiln = st.selectbox(
            "Project kiln type", kiln_types,
            index=kiln_types.index("zigzag"),
            format_func=lambda x: x.replace("_", " ").title(),
        )
        biomass_frac = st.slider("Biomass substitution fraction", 0.0, 0.5, 0.20, 0.05)
    else:
        project_kiln = None
        biomass_frac = 0.0

# ---- Calculate ----
ef = EmissionFactors.from_yaml()
kiln = BrickKiln(
    name=name, location=location, year=year,
    kiln_type=kiln_type, annual_brick_production=bricks,
    project_case=is_project, project_kiln_type=project_kiln,
    biomass_substitution_fraction=biomass_frac,
)
result = calculate_brick_emissions(kiln, ef)

# ---- KPIs ----
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total baseline emissions", f"{result.e_total_baseline_tco2:,.0f}", "tCO₂/yr")
c2.metric("Intensity", f"{result.intensity_kgco2_per_1000_bricks:,.0f}", "kg CO₂/1000 bricks")
c3.metric("Thermal efficiency", f"{result.thermal_efficiency*100:.0f}", "%")
if is_project:
    c4.metric("Reduction", f"{result.e_reduction_tco2:,.0f}", f"{result.e_reduction_pct:.1f}%")
else:
    c4.metric("vs Nepal avg (270)", f"{result.delta_vs_nepal_avg_kgco2_per_1000:+,.0f}", "kg/1000")

# ---- Comparison chart ----
st.markdown("### Kiln-type comparison at this production volume")
n_k = bricks / 1000.0
comparison_rows = []
for k in kiln_types:
    test_kiln = BrickKiln(
        name=name, location=location, year=year,
        kiln_type=k, annual_brick_production=bricks,
    )
    test_result = calculate_brick_emissions(test_kiln, ef)
    comparison_rows.append({
        "Kiln type": k.replace("_", " ").title(),
        "tCO₂/yr": test_result.e_total_baseline_tco2,
        "kg CO₂/1000": test_result.intensity_kgco2_per_1000_bricks,
    })
cdf = pd.DataFrame(comparison_rows)
fig = go.Figure(data=[go.Bar(
    x=cdf["Kiln type"], y=cdf["tCO₂/yr"],
    text=[f"{v:,.0f}" for v in cdf["tCO₂/yr"]], textposition="outside",
    marker_color=["#d62728" if k == kiln_type else "#1f77b4" for k in cdf["Kiln type"]],
)])
fig.update_layout(height=380, yaxis_title="tCO₂/yr", showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.caption(f"Highlighted bar = selected baseline kiln type ({kiln_type.replace('_',' ').title()})")

# ---- Detailed table ----
st.markdown("### Detailed results")
df = pd.DataFrame({
    "Indicator": [
        "Kiln type", "Annual brick production",
        "Coal combustion", "Biomass (biogenic)", "Other fuels",
        "Total baseline emissions", "Total project emissions",
        "Emission reduction", "Reduction percentage",
        "Intensity per 1000 bricks", "Intensity per brick",
        "SEC per 1000 bricks", "SEC per brick", "Thermal efficiency",
    ],
    "Value": [
        kiln_type.replace("_", " ").title(),
        f"{bricks:,}",
        f"{result.e_coal_combustion_tco2:,.2f}",
        f"{result.e_biomass_combustion_tco2:,.2f}",
        f"{result.e_other_fuel_tco2:,.2f}",
        f"{result.e_total_baseline_tco2:,.2f}",
        f"{result.e_total_project_tco2:,.2f}" if is_project else "—",
        f"{result.e_reduction_tco2:,.2f}" if is_project else "—",
        f"{result.e_reduction_pct:,.1f}" if is_project else "—",
        f"{result.intensity_kgco2_per_1000_bricks:,.1f}",
        f"{result.intensity_kgco2_per_brick*1000:,.2f}",
        f"{result.sec_mj_per_1000_bricks:,.0f}",
        f"{result.sec_mj_per_brick*1000:,.2f}",
        f"{result.thermal_efficiency*100:,.0f}",
    ],
    "Unit": [
        "-", "bricks/yr", "tCO₂/yr", "tCO₂/yr", "tCO₂/yr",
        "tCO₂/yr", "tCO₂/yr", "tCO₂/yr", "%",
        "kg CO₂/1000", "g CO₂/brick", "MJ/1000", "kJ/brick", "%",
    ],
})
st.dataframe(df, use_container_width=True, hide_index=True)

# ---- Export ----
st.markdown("### Export")
if st.button("📄 Generate PDF report"):
    out = Path("reports") / f"{name.replace(' ', '_')}_{kiln_type}_{year}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    generate_brick_report(kiln, result, out)
    st.success(f"Report saved: {out}")
    with open(out, "rb") as f:
        st.download_button("⬇️ Download PDF", f, file_name=out.name)
