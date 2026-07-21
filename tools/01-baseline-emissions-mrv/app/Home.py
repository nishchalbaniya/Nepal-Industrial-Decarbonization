"""
Nepal MRV — Streamlit multi-page app entry.
"""
import streamlit as st

st.set_page_config(
    page_title="Nepal MRV — Cement & Brick Decarbonization",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🏭 Nepal Industrial Decarbonization Suite")
st.subheader("Baseline Emissions & MRV Tool — Cement & Brick Industry")

st.markdown("""
**Author:** Nishchal Baniya · *Himalayan Carbon Nepal*
**Email:** nishchal.baniya@himalayancarbonnepal.com
**Open source:** MIT License · nepal_mrv v0.1.0

This tool implements IPCC 2006 Tier 2 mass-balance and Verra VCS / Gold
Standard–compatible methodologies for **baseline emissions assessment** and
**Monitoring, Reporting, Verification (MRV)** of Nepali cement and brick
industry projects.

### What you can do here
1. **Calculate baseline** for a cement plant (clinker + fuel + grid)
2. **Calculate baseline** for a brick kiln (any of 5 kiln types)
3. **Simulate a project activity** (biomass co-firing, technology switch, WHR)
4. **Estimate carbon credit revenue** at $15, $30, $50/tCO₂e
5. **Export a Verra-style monitoring report** (PDF)

### Why this matters
Nepal's cement sector emits ~5 MtCO₂/yr and brick sector ~1.4 MtCO₂/yr.
Most of these emissions are **abatable** through technology shifts that
have no net cost when carbon revenue is included.

### Navigation
Use the sidebar to access:
- 🏭 Cement Baseline
- 🧱 Brick Baseline
- 💼 Project Activity
- 📊 Sector Benchmarking
- 📘 Methodology
- 📞 About
""")

# Quick stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Cement CO₂/yr (Nepal)", "~5.2 MtCO₂", "7 plants")
with col2:
    st.metric("Brick CO₂/yr (Nepal)", "~1.4 MtCO₂", "1,200 kilns")
with col3:
    st.metric("Mitigation potential", "~40%", "by 2035")
with col4:
    st.metric("Tools in this suite", "20", "20-day sprint")

st.info("👈 Pick a tool from the sidebar to begin.")

st.markdown("---")
st.caption("""
**Data sources:** IPCC 2006/2019, GCCA, NEA 2023/24, ecoinvent v3.10, WRI GHG
Protocol, field surveys of Nepali plants. See *Methodology* page for full
references.
""")
