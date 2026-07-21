# 20-Day Engineering Roadmap — Cement & Brick Decarbonization, Nepal

## Strategic framing

Every tool maps to a real, deployable workflow that a Nepali cement plant, brick kiln, MRV auditor, or carbon project developer needs. Nothing is academic-only.

## Technology stack distribution (one tool per paradigm, 20 days)

| Day | Paradigm | Why this stack |
|----:|---|---|
| 1 | Python data + web | Baseline & MRV are data-intensive; needs Web UI for plant operators |
| 2 | MATLAB/Octave ODE | Dynamic kiln simulation needs high-fidelity numerical integration |
| 3 | OpenFOAM CFD | Clinker cooler radiation & turbulent flow |
| 4 | FreeCAD parametric | Alternative kiln designs (tunnel, zigzag) → STEP/DXF for fab |
| 5 | DWSIM steady-state | LC3 / geopolymer process flowsheet with mass/energy balance |
| 6 | R + Bayesian | Statistical fuel-switch model for brick sector heterogeneity |
| 7 | Julia + JuMP | High-performance HEN synthesis (LP/NLP) |
| 8 | Next.js full-stack | Interactive MRV dashboard for plant managers |
| 9 | Superset + dbt | Benchmarking 7 cement plants + 100+ brick kilns |
| 10 | QGIS geospatial | CCUS / mineralization siting across Nepal provinces |
| 11 | Pyomo MILP | Fuel blend + cement mix optimization |
| 12 | Brightway2 LCA | Cradle-to-gate LCA with ecoinvent background |
| 13 | Python pinch | Heat integration targeting (Linnhoff MER) |
| 14 | SimPy digital twin | Real-time DEVS plant simulation |
| 15 | PyTorch ML | Time-series emissions forecasting (TFT) |
| 16 | Docker + Helm | Production deployment (cloud + on-prem edge) |
| 17 | Solidity + Foundry | Tokenized carbon credit on-chain |
| 18 | ESP32 + MQTT | IoT sensor stack for direct emissions monitoring |
| 19 | LaTeX | Verra-acceptable methodology white paper |
| 20 | Full integration | Verra-aligned MRV platform, end-to-end |

## How to push to GitHub

Once you've created the empty repo on github.com, run from this directory:

```bash
git remote add origin https://github.com/<your-username>/nepal-decarb.git
git push -u origin main
```

## Daily release cadence

Each day, a single commit with a semantic version tag:
- `v0.1.0` Day 1
- `v0.2.0` Day 2
- ...
- `v1.0.0` Day 20
