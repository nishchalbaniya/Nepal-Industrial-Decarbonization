"""
About — page 6
"""
import streamlit as st

st.set_page_config(page_title="About", page_icon="📞", layout="wide")

st.title("📞 About this tool")

st.markdown("""
## Nepal Industrial Decarbonization Suite
### Day 1: Baseline Emissions & MRV Tool

**Author:** Nishchal Baniya
**Organization:** Himalayan Carbon Nepal
**Email:** nishchal.baniya@himalayancarbonnepal.com

### Why I built this

I'm Nishchal Baniya, working in climate and industrial decarbonization
in Nepal. When I started looking at decarbonization of Nepal's cement
and brick sectors, I found a glaring gap: there was **no open-source
Nepali-specific tool** for plant-level baseline emissions and MRV.

Most global tools (GHG Protocol calculators, IPCC software) are
generic and don't reflect Nepali conditions:
- Coal is imported, with Nepali-specific NCV/EF
- Grid is hydropower-dominated (very different from India)
- Brick kilns are 70% traditional clamps (huge mitigation potential)
- No domestic CO₂ tax (yet) — so carbon credits are the main lever

This tool fixes that. It's the first of **20 open-source tools** I'm
building over 20 days, each covering a different aspect of industrial
decarbonization.

### What "MRV" means

**Monitoring, Reporting, Verification** is the framework used by all
credible carbon standards (Verra VCS, Gold Standard, ACR, CAR):
- **M** — measure your emissions with calibrated methods
- **R** — report them in a transparent, auditable format
- **V** — get them independently verified for credit issuance

### Roadmap (20 tools, 20 days)

| Day | Tool | Stack |
|----:|---|---|
| 1 | Baseline MRV | Python · Streamlit |
| 2 | Kiln dynamic model | MATLAB/Octave |
| 3 | Clinker cooler CFD | OpenFOAM |
| 4 | Kiln CAD | FreeCAD |
| 5 | LC3 process | DWSIM |
| 6 | Brick fuel stats | R |
| 7 | HEN synthesis | Julia |
| 8 | MRV dashboard | Next.js |
| 9 | BI benchmarking | Superset |
| 10 | CCUS siting | QGIS |
| 11 | Fuel blend MILP | Pyomo |
| 12 | LCA tool | Brightway2 |
| 13 | Pinch analysis | Python |
| 14 | Digital twin | SimPy |
| 15 | Forecasting ML | PyTorch |
| 16 | Deployment | Docker/Helm |
| 17 | Carbon credit token | Solidity |
| 18 | IoT sensors | ESP32 |
| 19 | White paper | LaTeX |
| 20 | Full platform | Integration |

### Get in touch

- **Email:** nishchal.baniya@himalayancarbonnepal.com
- **Org:** Himalayan Carbon Nepal

If you operate a cement plant, brick kiln, or carbon project in Nepal —
let's talk. This tool is open source. Use it, fork it, contribute.

### License

This work is licensed under **MIT** (code) and **CC-BY-4.0** (data & docs).
Use freely. Cite when you do.

© 2026 Nishchal Baniya · Himalayan Carbon Nepal
""")
