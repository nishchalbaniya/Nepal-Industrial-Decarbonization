# Nepal Industrial Decarbonization Platform

> **Open-source industrial decarbonization toolkit for the Nepali cement and brick industry.**
> **Honest engineering. No self-awarded scores. See `docs/METHODOLOGY.md` and `docs/STANDARDS_COVERAGE.md` for the truth.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)]()
[![Methodology](https://img.shields.io/badge/methodology-verified-blue)](docs/METHODOLOGY.md)
[![Standards coverage](https://img.shields.io/badge/standards-see%20truth%20table-orange)](docs/STANDARDS_COVERAGE.md)
[![Status](https://img.shields.io/badge/status-v1.0%20sizing%20model-blueviolet)]()

---

## What is this?

An open-source industrial decarbonization toolkit for **Nepal's cement
and brick industry**, built to be honestly useful for a Nepali plant
engineer, a VVB, a carbon-market analyst, and a DFI credit officer.
The toolkit is split into two layers:

1. **Engineering simulators** (`tools/03-cooler-grate-simulator/`,
   `tools/02-kiln-dynamics/`, `pro/nepal_decarb_pro/sim/`,
   `pro/nepal_decarb_pro/core/`) -- a 5-zone rotary kiln ODE, a
   multi-compartment grate cooler with first-law/second-law
   diagnostics, a brick-kiln dynamics model, LCA, Monte Carlo UQ,
   MILP fuel-blend optimisation, NSGA-II Pareto front, digital twin.
   The numbers from these are reproducible physics / chemistry / heat
   balance and do not depend on any self-asserted boolean.

2. **Standards and markets wrappers** (`pro/nepal_decarb_pro/standards/`,
   `pro/nepal_decarb_pro/markets/`) -- thin checkers for ISO 14064-1/2/3,
   ISO 50001, ISO 14001, GHG Protocol, GCCA, PCAF, TCFD, SBTi, plus
   a Verra/CDM/GS PDD generator. **These are stubs and self-assertion
   wrappers, not compliance engines.** See
   `docs/STANDARDS_COVERAGE.md` for the per-standard honest tag
   (Implemented / Partial / Stub).

This repository is in v1.0.0 "sizing model" status. The engineering
output is real and useful; the standards/markets layer is honest
about what it does and does not yet do.

---

## What this is NOT

- **Not certified by any VVB.** No VVB has reviewed this code, and no
  ISO 14064-3:2019 verification opinion has been issued.
- **Not compliant with any standard by self-assertion.** The standards
  modules are check-wrappers; passing them with the default `True`
  values does not constitute compliance. A VVB will not accept it.
- **Not submittable to Verra or Gold Standard.** The PDD generator
  in `pro/nepal_decarb_pro/markets/verra.py` is missing additionality
  assessment, baseline alternative analysis, stakeholder
  consultation, per-field monitoring tier, leakage per activity, and
  the VVB-prepared Validation Report. The full gap list is in
  `docs/METHODOLOGY.md` section 5.
- **Not "9.78/10" or any other self-awarded rating.** See
  `docs/STANDARDS_COVERAGE.md` for the truth (2 implemented, 2
  partial, 7 stub out of 11 claimed).

---

## Quick start

### Install (Python 3.10+)
```bash
# Clone the repo (the actual GitHub URL -- not the old placeholder)
git clone https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization.git
cd Nepal-Industrial-Decarbonization

# Install the pro package in editable mode
cd pro
pip install -e .
```

### Run the test suite (the tests that pass)
```bash
cd pro
py -m pytest tests/test_markets.py -v
# Expected: 8 passed (the markets module; pre-WP1 this asserted
# a fictional VM0009 v2.0 citation)
```

The full test suite (`py -m pytest tests/`) has some pre-existing
failures documented in `reviews/GROUND_TRUTH.md` (missing optional
deps `reportlab` / `matplotlib`, working-directory assumptions for
`helm/`, `docker-compose.yml`). Fixing these is in the WP6 work
package; the full before/after is in `reviews/REMEDIATION_REPORT.md`.

### Run the end-to-end demo (4 plants, 6 minutes)
See `tools/03-cooler-grate-simulator/demo_site/` for the public demo
and `docs/DEPLOYMENT.md` for the 5 deploy paths (VPS, Docker, free one-click, AWS, IoT edge).

### Live demos
| URL | What | Status |
|---|---|---|
| https://jfp4xr4woteju.space.minimax.io | End-to-end 4-plant demo with P&ID, STEP files, 4-plant CBAM sweep | Live |
| https://nishchalbaniya.github.io/Nepal-Industrial-Decarbonization/ | GitHub Pages static site | Live |

The previous demo URLs (`fnj58e5yu30lp.space.minimax.io`,
`harvey-aside-striking-spas.trycloudflare.com`) are dead and have
been removed from this README (WP6). Do not link to them.

---

## What is in the box

### Engineering simulators (Implemented)

- **Grate cooler** (`tools/03-cooler-grate-simulator/`) -- multi-compartment
  grate cooler, L-BFGS-B calibration, Sobol sensitivity, STEP and
  P&ID export. Default plant configs: PlantA, PlantB, PlantC, PlantD.
  The "PlantA" name is a placeholder; see `docs/PLANT_RENAMING.md`
  for the original 4 specific Nepali plants. (See `docs/PLANT_RENAMING.md`.)
- **Rotary kiln** (`tools/02-kiln-dynamics/`) -- 5-zone ODE with
  Arrhenius kinetics, calcination, NOx. STEP export.
- **Brick kiln** (`pro/nepal_decarb_pro/sim/brick_dynamics.py`) --
  clamp, zigzag, tunnel, Hoffman.
- **LCA** (`pro/nepal_decarb_pro/lca/`) -- 6 categories: GWP100, AP,
  EP, POCP, ADP, HTP.
- **Uncertainty** (`pro/nepal_decarb_pro/core/uncertainty.py`) --
  Monte Carlo, Sobol.
- **Optimisation** (`pro/nepal_decarb_pro/core/multi_objective.py`) --
  NSGA-II Pareto front.
- **Fuel blend** (`pro/nepal_decarb_pro/core/fuel_blend.py`) -- MILP.
- **CAD / I/O** (`pro/nepal_decarb_pro/sim/cad_export.py`,
  `pro/nepal_decarb_pro/io/`) -- DXF, FreeCAD macro, SVG, MQTT,
  OPC-UA, Modbus.

### Standards checkers (Stub / Partial -- see truth table)

- **ISO 14064-1:2018** -- Implemented (`pro/nepal_decarb_pro/standards/iso_14064.py`)
- **ISO 14064-2:2019** -- Partial
- **ISO 14064-3:2019** -- Stub (the V.2, V.5, V.6 hard-coded `True`
  defect was fixed in WP2; the rest of the gap list remains)
- **ISO 50001:2018** -- Stub
- **ISO 14001:2015** -- Stub
- **GHG Protocol Corporate Standard** -- Partial (Scope 3 missing)
- **GCCA Sustainability Framework** -- Implemented
- **PCAF Global Scorebook** -- Stub
- **TCFD / ISSB IFRS S2** -- Stub
- **SBTi** -- Stub (hard-coded pathway multipliers; not traceable to
  the published SBTi sector pathway file)

See `docs/STANDARDS_COVERAGE.md` for the per-standard gap list and
the 7-step fix sequence.

### Carbon markets (Sizing tool, not submittable)

- **Verra VCS PDD generator** (`pro/nepal_decarb_pro/markets/verra.py`)
  -- outputs a Pydantic model with the 18 standard fields. Real
  methodologies cited: CDM ACM0003 v9.0 (cement fuel-switch; status
  in Verra: not active per 2024-2025 listing, re-confirm with VVB),
  CDM ACM0005 v7.1.0 (blended cement). The historical fictional
  citation ("VM0009 v2.0 Cement Plant Decarbonization") was removed
  in WP1.
- **Gold Standard PDD** (`pro/nepal_decarb_pro/markets/gold_standard.py`)
  -- applicable to the BRICK sub-product only (RECH v5.0, formerly
  TPDDTEC, 150 kW/unit ceiling). NOT applicable to industrial cement.
- **Pricing** (`pro/nepal_decarb_pro/markets/pricing.py`) -- 6
  scenarios. The economic story for a Nepali cement exporter is
  India CCTS / Article 6.2 ITMO at USD 5-15/t, NOT EU ETS at
  USD 65/t. The EU ETS figure is kept as a sensitivity upper bound,
  not the central case. See `docs/METHODOLOGY.md` section 3.
- **Tokenisation** (`pro/nepal_decarb_pro/markets/tokenization.py`)
  -- Solidity ERC-3643 (T-REX) carbon credit token contract source.

### Forecasting + Pinch + Digital twin (Implemented)

- ETS forecasting (error/trend/seasonal, MAPE claimed 6.24%)
- Pinch analysis (composite curves, MER)
- Digital twin (Kalman filter + anomaly detection)

### LLM advisor (Bilingual EN / Nepali)

- RAG over plant data + emission factors + standards corpus
- Backends: stub, vLLM (GPU), transformers, OpenAI-compatible

### UI + API (Implemented)

- FastAPI multi-tenant, auth, WebSocket
- Streamlit dashboard
- Admin panel, plant onboarding, bulk CSV

---

## Repository layout

```
Nepal-Industrial-Decarbonization/
  pro/                          # the unified Python package
    nepal_decarb_pro/           # the main module
      core/                     # cement, brick, factors, UQ, MILP, NSGA-II
      sim/                      # kiln, cooler, brick dynamics
      lca/                      # LCA engine
      standards/                # ISO, GHG Protocol, GCCA, PCAF, TCFD, SBTi checkers
      markets/                  # Verra, Gold Standard, pricing, tokenization
      reporting/                # PDF report generator
      io/                       # MQTT, OPC-UA, Modbus, CSV, Excel, historian
      llm/                      # RAG advisor, multi-backend
      pinch/                    # pinch analysis
      dt/                       # digital twin
      forecasting/              # ETS forecasting
      registry/                 # plant registry / presets
      audit/                    # audit trail
      auth/                     # RBAC
      i18n/                     # bilingual EN/Nepali
      cad/                      # DXF writer
    tests/                      # pytest
    deploy/                     # helm, terraform, fly, railway, render configs
    docs/                       # package-level documentation
    launchers/                  # Windows .bat, .vbs, .lnk
  tools/                        # standalone engineering tools
    01-baseline-emissions-mrv/  # cement Tier 1/2/3
    02-kiln-dynamics/           # 5-zone kiln ODE
    03-cooler-grate-simulator/  # grate cooler + demo site
    ...
  docs/                         # repo-level documentation (this README, METHODOLOGY, etc.)
  reviews/                      # WP0 ground truth, REMEDIATION_REPORT
  release/                      # the v1.0 release bundle
  .commit-msg-*.txt             # commit message drafts (gitignored from history)
```

---

## Documentation

- [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md) -- truth table for the
  4 carbon-market methodologies, with citations to primary sources
  on verra.org, cdm.unfccc.int, goldstandard.org, eur-lex.europa.eu.
- [`docs/STANDARDS_COVERAGE.md`](docs/STANDARDS_COVERAGE.md) -- truth
  table for the 11 claimed standards, with Implemented / Partial /
  Stub tag and the 7-step fix sequence.
- [`docs/ROADMAP.md`](docs/ROADMAP.md) -- what we plan to ship next.
- [`reviews/GROUND_TRUTH.md`](reviews/GROUND_TRUTH.md) -- the WP0
  ground-truth audit (17 defects, the basis for the WP1-WP6 work
  packages).
- [`reviews/REMEDIATION_REPORT.md`](reviews/REMEDIATION_REPORT.md) --
  -- before/after, defect list, remaining-risk list.
- [`pro/README.md`](pro/README.md) -- package-level overview.
- [`pro/docs/OPERATOR_MANUAL.md`](pro/docs/OPERATOR_MANUAL.md) --
  for plant operators.
- [`pro/docs/COMMISSIONING.md`](pro/docs/COMMISSIONING.md) -- for
  system integrators.

---

## Known limitations (the honest ones)

The full limitations list is in [`docs/LIMITATIONS.md`](LIMITATIONS.md). The short version:

1. **No plant data yet.** The default plant configs are placeholders
   labelled PlantA, PlantB, PlantC, PlantD. The model has not been
   calibrated to a real Nepali cement plant's DCS export. Three of
   the six ship-gate bands fail on the v0.5.0 calibrated model
   (tertiary 190C vs band 400-700C; exhaust 149C vs 150-300C; clinker
   351C vs 120-200C). For the open-source release these three bands
   are labelled "Worked example" not "Verified."

2. **Standards modules are stubs.** See `docs/STANDARDS_COVERAGE.md`.

3. **PDD generator is a sizing tool.** See `docs/METHODOLOGY.md` section 5.

4. **Pre-existing test failures** for `tests/test_sim.py`,
   `tests/test_standards.py`, and 9 other tests documented in
   `reviews/GROUND_TRUTH.md` (WP6). These are not new in WP1-WP5;
   they are pre-existing and will be fixed in WP6.

5. **The factory default does not match a real kiln in operation.**
   See the "Worked example" framing in (1) above. The v0.5.0 model
   physics at 130 t/h cannot deliver the temperature bands that
   `standards/STANDARDS_AUDIT.md` cites as "expected." This is a
   model-validity issue, not a code bug; it will close when (a) real
   plant data lands or (b) v0.6.0 introduces compartment subdivision
   and lower throughput. The honest current answer is to label the
   failing bands as illustrative.

---

## License

- **Code**: [MIT](LICENSE)
- **Data + documentation**: [CC-BY-4.0](LICENSE-DATA)

---

## Citation

```bibtex
@software{nepal_decarb_pro,
  author = {Baniya, Nishchal},
  title = {Nepal Industrial Decarbonization Platform: open-source toolkit for the Nepali cement and brick industry},
  version = {1.0.0},
  year = {2026},
  url = {https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization}
}
```

See [CITATION.cff](CITATION.cff) for the full citation metadata.

---

## Author

**Nishchal Baniya**
Himalayan Space Solutions
nishchal.baniya@himalayancarbonnepal.com
