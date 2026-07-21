# Nepal Industrial Decarbonization Suite
### *Open-source engineering toolkit for cement & brick industry decarbonization in Nepal*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)]()
[![Open Source](https://img.shields.io/badge/Open%20Source-100%25-brightgreen.svg)]()
[![Nepal](https://img.shields.io/badge/Made%20in-Nepal-DC143C.svg)]()
[![Daily Release](https://img.shields.io/badge/Release-20%20Day%20Sprint-orange.svg)]()

> **Mission:** Build and openly publish 20 production-grade, deployable engineering simulation tools that Nepali cement and brick manufacturers, project developers, and policy makers can use *today* to baseline, mitigate, monitor, and trade carbon.

**Author:** Nishchal Baniya · *Himalayan Carbon Nepal* · nishchal.baniya@himalayancarbonnepal.com

---

## Why this exists

Nepal's two largest industrial CO₂ sources — the **cement sector** (~3.2 MtCO₂/yr, 7 integrated plants + 40+ grinding units) and the **brick sector** (~1.4 MtCO₂/yr, 1,200+ kilns, 80% still using clamp/traditional technologies) — together emit more CO₂ than Nepal's entire passenger road transport. Yet no open, Nepali-specific engineering toolkit exists to:

1. Baseline emissions (MRV)
2. Simulate alternative technologies (LC3, geopolymer, tunnel kilns, zigzag)
3. Optimize fuel & raw-material mixes
4. Verify CO₂ reductions for **Verra / Gold Standard** carbon credit issuance
5. Provide geospatial siting for CCUS, mineralization, biomass supply

This repository fills that gap. **20 tools, 20 days, fully open source.**

---

## The 20-day deployment plan

| Day | Tool | Engineering core | Status |
|---|---|---|---|
| 1 | `01-baseline-emissions-mrv` | Python · Streamlit · IPCC Tier 2/3 | 🔨 building today |
| 2 | `02-kiln-dynamics-matlab` | MATLAB / Octave · ODE dynamic model | ⏳ |
| 3 | `03-clinker-cooler-cfd` | OpenFOAM · RANS turbulence · radiation | ⏳ |
| 4 | `04-kiln-cad-designs` | FreeCAD · STEP/DXF parametric | ⏳ |
| 5 | `05-lc3-process-flowsheet` | DWSIM · calcined clay blend optimization | ⏳ |
| 6 | `06-brick-fuel-statistics` | R · Shiny · Bayesian fuel-switch model | ⏳ |
| 7 | `07-hen-synthesis-julia` | Julia · JuMP · pinch synthesis | ⏳ |
| 8 | `08-mrv-dashboard` | Next.js · tRPC · Postgres · Auth.js | ⏳ |
| 9 | `09-plant-benchmarking-bi` | Apache Superset · dbt · star schema | ⏳ |
| 10 | `10-ccus-siting-qgis` | QGIS · Python · AHP-MCDA | ⏳ |
| 11 | `11-fuel-blend-milp` | Pyomo · CPLEX/Gurobi · MILP | ⏳ |
| 12 | `12-lca-brightway2` | Brightway2 · ecoinvent · cradle-to-gate | ⏳ |
| 13 | `13-pinch-analysis` | Python · Linnhoff · MER targeting | ⏳ |
| 14 | `14-cement-digital-twin` | SimPy · DEVS · real-time | ⏳ |
| 15 | `15-emissions-forecasting-ml` | PyTorch · TFT/Transformer | ⏳ |
| 16 | `16-deployment-stack` | Docker · Helm · Terraform · K8s | ⏳ |
| 17 | `17-carbon-credit-token` | Solidity · Foundry · ERC-3643 | ⏳ |
| 18 | `18-iot-sensor-firmware` | ESP32 · MQTT · LoRaWAN · OTA | ⏳ |
| 19 | `19-policy-whitepaper` | LaTeX · open-access submission | ⏳ |
| 20 | `20-integrated-platform` | Full-stack Verra-aligned MRV | ⏳ |

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-username>/nepal-decarb.git
cd nepal-decarb

# 2. Run any tool (each has its own venv-friendly setup)
cd tools/01-baseline-emissions-mrv
python -m venv .venv && source .venv/bin/activate
pip install -e .
streamlit run app/Home.py

# 3. CLI alternative
nepal-mrv --plant hetauda_cement --year 2024
```

## Stack at a glance
- **Languages:** Python · MATLAB/Octave · Julia · R · JS/TS · Solidity · C++ (OpenFOAM) · LaTeX
- **Data:** Nepali plant field data (Hetauda, Udayapur, Maruti, Hongshi, Shree, Ghorahi) + Verra/Gold Standard methodology
- **Open standards:** GHG Protocol · IPCC 2006/2019 Refinement · ISO 14064 · Verra VCS · Gold Standard
- **License:** MIT (code) · CC-BY-4.0 (data & docs)

## Contact
- **Author:** Nishchal Baniya
- **Email:** nishchal.baniya@himalayancarbonnepal.com
- **Org:** Himalayan Carbon Nepal

*This is open-source infrastructure for Nepal's low-carbon industrial transition. Use it, fork it, deploy it, cite it.*
