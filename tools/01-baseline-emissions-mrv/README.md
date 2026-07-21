# Tool 01 — Nepal Cement & Brick Baseline Emissions + MRV Tool

**Day 1 of the 20-day Nepal Industrial Decarbonization Suite.**

## What it does

A Verra VCS / Gold Standard–compatible **baseline emissions calculator** and **MRV (Monitoring, Reporting, Verification) tool** specifically designed for:

- **Cement sector** (integrated plants, grinding units, clinker import)
- **Brick sector** (clamp, Hoffman, tunnel, zigzag kilns)
- **Cogeneration & waste-heat recovery** (when paired with a project activity)

The tool implements:
- **IPCC 2006 Guidelines** Tier 2 approach for cement (Vol. 3 Ch. 2)
- **IPCC 2019 Refinement** updates
- **GHG Protocol Cement Scope 1 & 2** guidance
- **Nepal Electricity Authority** (NEA) grid emission factor (dynamic, hydro-dominated)
- **Verra VCS Methodology VM0009 / VCS AMS-III.H** for project activities
- **Gold Standard TPDDTEC** for brick kiln technologies

## Features

✅ Tier 2 mass-balance approach for clinker calcination CO₂
✅ Tier 1 + Tier 2 fuel combustion for kiln fuels (coal, biomass, TDF, petcoke, natural gas, diesel)
✅ Scope 1 / 2 / 3 decomposition
✅ Plant-level & kiln-level benchmarking against global BAT (Best Available Techniques)
✅ Cement and brick inventory with full data validation
✅ Per-tonne product emission intensity (kgCO₂/t cement, kgCO₂/1000 bricks)
✅ **Project-level additionality** screening (investment analysis vs. biomass availability)
✅ **Baseline → Project → Leakage → Net** emission reduction calculation
✅ **Sample Verra Monitoring Report PDF** generator
✅ Interactive Streamlit UI
✅ Command-line interface (`nepal-mrv`)
✅ Python API

## Quick start

```bash
# Install
pip install -e .

# CLI
nepal-mrv cement --plant hetauda --year 2024
nepal-mrv brick --kiln clamp --production 5000000
nepal-mrv project --baseline cement-opc --project lcm-geopolymer --volume 50000
nepal-mrv report --plant hetauda --year 2024 --out reports/hetauda_2024.pdf

# Streamlit UI
streamlit run app/Home.py
```

## Data sources

All emission factors are sourced from:
- IPCC 2006 Guidelines for National Greenhouse Gas Inventories (Vol. 3, Ch. 2)
- IPCC 2019 Refinement
- GHG Protocol Cement Scope 1+2 Guidance (2017)
- ecoinvent v3.10 (LCA database)
- Nepal Electricity Authority Annual Report 2023/24
- WBSCD Cement Sustainability Initiative (CSI) / GCCA database
- Field surveys of Nepali cement plants and brick kilns (Hetauda, Bhairahawa, Kathmandu Valley)

See `data/emission_factors.yaml` and `data/nepali_plants.yaml` for full sources.

## Authors
Nishchal Baniya · Himalayan Carbon Nepal
nishchal.baniya@himalayancarbonnepal.com
