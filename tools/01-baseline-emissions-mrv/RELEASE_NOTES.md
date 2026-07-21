# Day 1 Release Notes — Tool 01

**Release tag:** `v0.1.0`
**Date:** 2026-07-21
**Tool:** Baseline Emissions & MRV Calculator for Nepal Cement & Brick Industry
**Author:** Nishchal Baniya · Himalayan Carbon Nepal
**Contact:** nishchal.baniya@himalayancarbonnepal.com

## Headline numbers (Hetauda Cement Industries, baseline 2024)

| Indicator | Value |
|---|---|
| Process CO₂ (calcination) | 511,307 tCO₂/yr |
| Fuel combustion | 346,910 tCO₂/yr |
| Grid electricity (Scope 2) | 2,808 tCO₂/yr |
| **Total emissions** | **861,025 tCO₂/yr (0.86 Mt)** |
| Intensity | 783 kg CO₂/t cement |
| vs Global BAT (~700) | +83 kg CO₂/t |
| vs Nepal avg (~950) | -177 kg CO₂/t (better than average) |
| SEC | 4,168 MJ/t clinker |

## Hetauda project scenario (biomass 20% + WHR 22 GWh/yr)

| Indicator | Value |
|---|---|
| Baseline annual | 861,025 tCO₂ |
| Project annual | 791,171 tCO₂ |
| Gross reduction | 69,854 tCO₂/yr |
| Net (after 5% leakage) | 66,361 tCO₂/yr |
| Net issuable (after 15% buffer) | 56,407 credits/yr |
| Cumulative (10 years) | 663,612 tCO₂e |
| **NPV @ $15/t** | **$6.1M** |
| **NPV @ $30/t** | **$12.2M** |
| **NPV @ $50/t** | **$20.4M** |
| Additionality | ✅ PASS |

## Bhairahawa brick kiln (clamp → zigzag + 20% biomass)

| Indicator | Value |
|---|---|
| Baseline (clamp) | 3,256 tCO₂/yr |
| Project (zigzag + biomass) | 955 tCO₂/yr |
| **Reduction** | **2,301 tCO₂/yr (70.7%)** |
| NPV @ $15/t (7 years) | $143,087 |
| NPV @ $30/t | $286,175 |
| NPV @ $50/t | $476,958 |
| Additionality | ✅ PASS |

## What was delivered

### Code (21 Python files, ~2,800 LOC)
- `src/nepal_mrv/emission_factors.py` — database of emission factors (NEA grid, IPCC fuels, kiln-specific brick factors)
- `src/nepal_mrv/cement.py` — IPCC 2006 Tier 2 mass-balance + fuel combustion + grid
- `src/nepal_mrv/brick.py` — kiln-type-specific brick emissions (5 kiln types)
- `src/nepal_mrv/mrv.py` — Verra VCS / Gold Standard project activity calculator
- `src/nepal_mrv/reporting.py` — Verra-style monitoring report PDF generator
- `src/nepal_mrv/cli.py` — `nepal-mrv` command-line interface

### Web app (6 Streamlit pages)
- Cement Baseline (with 4 plant presets)
- Brick Baseline (5 kiln types)
- Project Activity (Verra / Gold Standard methodology)
- Sector Benchmarking (6 cement plants + 5 kiln types)
- Methodology
- About

### Tests
- 21 unit tests, all passing
- 4 test files: test_cement, test_brick, test_mrv, test_emission_factors

### Documentation
- README.md (tool overview)
- docs/methodology.md (5-page scientific methodology)
- CHANGELOG.md
- RELEASE_NOTES.md (this file)
- Inline docstrings for all public functions

### Deployment
- Dockerfile (Python 3.11-slim, Streamlit)
- requirements.txt
- .dockerignore
- GitHub Actions CI workflow
- pyproject.toml with `nepal-mrv` console script

## Compliance with international standards

- ✅ IPCC 2006 Vol. 3 Ch. 2 Tier 2 (cement)
- ✅ IPCC 2006 Vol. 2 Ch. 1 (stationary combustion)
- ✅ IPCC 2019 Refinement updates
- ✅ GHG Protocol Cement Scope 1+2 Guidance
- ✅ GCCA Sustainability Framework
- ✅ Verra VCS AMS-III.H (alternative fuels / WHR)
- ✅ Verra VCS VM0009 (cement decarbonization)
- ✅ Gold Standard TPDDTEC (brick technology switch)
- ✅ CDM ACM0012 (grid emission factor methodology)

## License
- Code: MIT
- Data: CC-BY-4.0
- Documentation: CC-BY-4.0

## Next: Day 2 — Tool 02: Kiln Dynamics Simulator (MATLAB/Octave)
