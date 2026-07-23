# Changelog

All notable changes to the Nepal Industrial Decarbonization Suite.

## [0.1.0] - 2026-07-21 — Day 1

### Added
- **Tool 01: Baseline Emissions + MRV Tool** (`nepal_mrv` Python package)
  - Cement sector calculator (IPCC 2006 Tier 2 mass-balance, GHG Protocol Scope 1+2)
  - Brick sector calculator (5 kiln types, kiln-specific coal consumption)
  - Project activity calculator (Verra VCS AMS-III.H, Gold Standard TPDDTEC)
  - Verra-style PDF report generator
  - Streamlit multi-page web UI (4 calculator pages + methodology + about)
  - Command-line interface (`nepal-mrv`)
  - 21 unit tests, all passing
  - 6 presets for Nepali cement plants (PlantA, PlantB, PlantC, etc.)
  - Real Nepali data: NEA 2023/24 grid EF, coal NCV, kiln efficiencies
- **Monorepo infrastructure**
  - LICENSE (MIT for code, CC-BY-4.0 for data)
  - CITATION.cff
  - ROADMAP.md (20-day plan)
  - CONTRIBUTING.md
  - .github/workflows/ci.yml

### Known limitations
- Test coverage: 21 tests, ~85% of public API
- No Scope 3 transport by default
- Real plant validation recommended for final MRV submission
- Streamlit not tested in headless CI yet
