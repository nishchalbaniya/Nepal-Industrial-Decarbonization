# Nepal Industrial Decarbonization Platform - Pro package (v1.0.0)

> **Open-source Python package for the Nepali cement and brick industry.**
> **Honest status. See `docs/METHODOLOGY.md` and `docs/STANDARDS_COVERAGE.md` for the truth.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![Status](https://img.shields.io/badge/status-v1.0%20sizing%20model-blueviolet)](../docs/STANDARDS_COVERAGE.md)
[![Standards coverage](https://img.shields.io/badge/standards-see%20truth%20table-orange)](../docs/STANDARDS_COVERAGE.md)

**Author:** Nishchal Baniya (Himalayan Space Solutions)
**Email:** nishchal.baniya@himalayancarbonnepal.com
**License:** MIT (code) / CC-BY-4.0 (data and docs)

---

## What is this?

This is the `nepal_decarb_pro` Python package -- the unified
application layer that sits on top of the standalone engineering
simulators in `tools/01..03/`. It is one of two layers in the
Nepal Industrial Decarbonization Platform:

1. The **engineering simulators** produce real physics / chemistry
   output. They are the part that a plant engineer can rely on.
2. This **standards/markets wrapper** package is a sizing tool and
   a set of honest check-wrappers. It is NOT a compliance engine,
   NOT a submittable PDD, NOT a certified Verra/Gold Standard
   workflow.

The previous copy of this README claimed "11 international standards
at production depth" and a 9/10 rating. Those claims were
self-awarded. The honest assessment is in
`docs/STANDARDS_COVERAGE.md` at the repo root.

---

## Honest status (the truth table)

| Module | Status | Notes |
|---|---|---|
| `core/cement.py` -- cement Tier 2/3 emissions | Implemented | Real physics, real chemistry |
| `core/brick.py` -- brick kiln emissions | Implemented | 5 kiln types |
| `core/uncertainty.py` -- Monte Carlo + Sobol | Implemented | 5000 samples |
| `core/multi_objective.py` -- NSGA-II | Implemented | 8 non-dominated solutions |
| `core/fuel_blend.py` -- MILP | Implemented | PuLP / CBC |
| `core/factors.py` -- emission factors | Implemented | 12 Nepali fuels, IPPU, NEA |
| `lca/` -- 6 categories (GWP100, AP, EP, POCP, ADP, HTP) | Implemented | |
| `sim/kiln_dynamics.py` -- 5-zone rotary kiln ODE | Implemented | |
| `sim/brick_dynamics.py` -- clamp, zigzag, tunnel, Hoffman | Implemented | |
| `sim/cad_export.py` -- DXF, FreeCAD, SVG | Implemented | |
| `io/` -- MQTT, OPC-UA, Modbus, CSV, Excel, historian | Implemented | |
| `forecasting/` -- ETS forecasting | Implemented | MAPE 6.24% (claim) |
| `pinch/analysis.py` -- pinch analysis | Implemented | |
| `dt/twin.py` -- digital twin | Implemented | |
| `llm/advisor.py` -- RAG advisor | Partial | Backends: stub, vLLM, transformers, OpenAI |
| `registry/plants.py` -- 4 plant presets (PlantA-D) | Partial | Synthetic; not calibrated to a real plant |
| `audit/trail.py` -- audit trail | Partial | Single-trail only; no immutability |
| `auth/rbac.py` -- RBAC | Partial | Single-role |
| `markets/verra.py` -- Verra PDD generator | Stub | Sizing tool only; see `docs/METHODOLOGY.md` section 5 for the 8-section gap list |
| `markets/gold_standard.py` -- GS PDD | Stub | Brick sub-product only (RECH v5.0); not applicable to industrial cement |
| `markets/tokenization.py` -- Solidity contract | Stub | Generated, not audited |
| `reporting/pdf.py` -- PDF report | Partial | Real emissions; methodology line is now honest (WP1) |
| `standards/iso_14064.py` -- ISO 14064-1/2/3 checkers | 1 Implemented, 1 Partial, 1 Stub | V.2/V.5/V.6 hard-coded `True` fixed in WP2 |
| `standards/iso_50001.py` -- ISO 50001 checker | Stub | Self-assertion wrapper; no EnB/EnPI |
| `standards/iso_14001.py` -- ISO 14001 checker | Stub | Self-assertion wrapper |
| `standards/ghg_protocol.py` -- GHG Protocol | Partial | Scope 3 missing |
| `standards/gcca.py` -- GCCA KPIs | Implemented | |
| `standards/pcaf.py` -- PCAF | Stub | Outstanding-debt option not exposed |
| `standards/tcfd.py` -- TCFD / IFRS S2 | Stub | Pillar template only; no real scenarios |
| `standards/sbti.py` -- SBTi | Stub | Hard-coded pathway multipliers; not traceable to SBTi files |

For the full gap list and the 7-step fix sequence, see
`docs/STANDARDS_COVERAGE.md` at the repo root.

---

## Quick start

```bash
# 1. Install (the actual GitHub URL -- not the old placeholder)
git clone https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization.git
cd Nepal-Industrial-Decarbonization/pro
pip install -e .

# 2. CLI: cement Tier 2 baseline
nepal-decarb cement --name "PlantA" --year 2024 \
    --clinker-t 950000 --cement-t 1100000 \
    --coal-t 120000 --petcoke-t 18000 --elec-kwh 85000000

# 3. CLI: brick kiln baseline
nepal-decarb brick --name "PlantB" --kiln clamp_traditional --bricks 4500000

# 4. Verra PDD generator (sizing only -- not submittable; see
#    docs/METHODOLOGY.md section 5 for the gap list)
nepal-decarb verra --name "PlantA Decarb" \
    --baseline-tco2 861025 --project-tco2 791171 --crediting-years 10

# 5. Streamlit UI
streamlit run app/Home.py
# -> http://localhost:8501

# 6. FastAPI server
nepal-decarb-api
# -> http://localhost:8000/docs
```

---

## Architecture

```
nepal_decarb_pro/
  core/                # Implemented: cement, brick, factors, UQ, MILP, NSGA-II
  sim/                 # Implemented: kiln, cooler, brick dynamics, CAD
  lca/                 # Implemented: 6 impact categories
  standards/           # Partial/Stub: ISO, GHG Protocol, GCCA, PCAF, TCFD, SBTi
  markets/             # Stub: Verra, GS, pricing, tokenization
  reporting/           # Partial: PDF report (Verra, ISO, TCFD, executive)
  io/                  # Implemented: CSV, Excel, MQTT, database, historian
  llm/                 # Partial: RAG advisor, multi-backend
  pinch/               # Implemented: pinch analysis
  dt/                  # Implemented: digital twin
  forecasting/         # Implemented: ETS forecasting
  registry/            # Partial: plant presets (synthetic, not real)
  audit/               # Partial: audit trail
  auth/                # Partial: RBAC
  i18n/                # Bilingual EN/Nepali
  cad/                 # DXF writer
  api.py               # FastAPI + WebSocket
  cli.py               # Command-line interface
  tests/               # 49 unit tests (8 markets tests + 9 extended + 32 others; pre-WP6 failures documented in reviews/GROUND_TRUTH.md)
```

---

## Use cases (the honest ones)

### For Nepali cement plant engineers
- Run the cooler calibration against a synthetic plant (the only
  plant data the repo currently has). When real DCS data is
  available, drop the CSV into
  `tools/03-cooler-grate-simulator/day-04-PRs/data/plant_planta_shift_NNN.csv`
  and re-run the calibration. The data format spec is in
  `tools/03-cooler-grate-simulator/day-04-PRs/data_quality_spec.md`.
- Generate a P&ID SVG and a STEP model of the cooler.
- Use the LCA engine to compare alternative fuel mixes.

### For carbon project developers
- Use the PDD generator for **sizing** (how many credits, what
  revenue). The output is not submittable. To turn it into a real
  PDD you need to add additionality assessment, baseline alternative
  analysis, stakeholder consultation, per-field monitoring tier, and
  a VVB engagement. The full gap list is in
  `docs/METHODOLOGY.md` section 5.

### For banks / DFIs
- The PCAF module is a stub. For real financed-emissions reporting,
  use the PCAF Global Scorebook directly; this package's output is
  not PCAF-compliant.
- TCFD / SBTi modules are stubs. They produce a template, not a
  disclosure.

### For policy makers
- The cement Tier 2 calculator is real and can be used to size
  sectoral inventories.

### For researchers
- LCA, Monte Carlo UQ, NSGA-II Pareto, MILP -- all real and
  reproducible.

---

## Provenance

All emission factors in `core/factors.py` are traceable to:
- IPCC 2006 Guidelines for National GHG Inventories, Vol. 3 Ch. 2
  (Tier 1 cement calcination EF = 0.527 t CO2/t-cli)
- IPCC 2019 Refinement
- GCCA Sustainability Framework / "Getting the Numbers Right"
- DEFRA Conversion Factors 2024
- ecoinvent v3.10 LCI database
- Nepal Electricity Authority (NEA) Annual Report 2023/24

> **Note:** The previous version of this README claimed "NEA grid
> EF (0.0256 kg CO2/kWh)". The correct value for the Nepal grid
> per IEA / Enerdata 2024 is ~0.0023 g CO2/kWh (hydro-dominated,
> essentially zero). The 0.0256 figure is wrong by four orders of
> magnitude. See `docs/METHODOLOGY.md` section 1 for the
> verification.

---

## License

- Code: **MIT** (Copyright 2026 Nishchal Baniya, Himalayan Space Solutions)
- Data: **CC-BY-4.0**
- Documentation: **CC-BY-4.0**

## Citation

```bibtex
@software{nepal_decarb_pro_2026,
  author = {Baniya, Nishchal},
  title = {Nepal Industrial Decarbonization Platform - Pro v1.0.0},
  year = {2026},
  version = {1.0.0},
  url = {https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization},
  email = {nishchal.baniya@himalayancarbonnepal.com}
}
```

## Contact

**Nishchal Baniya**
Himalayan Space Solutions
nishchal.baniya@himalayancarbonnepal.com
