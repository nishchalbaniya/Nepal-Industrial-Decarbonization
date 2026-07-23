# Day 4 Spec — Cooler Calibration to PlantA Plant Data

> **Authored by Mavis, 2026-07-22, after Day 3 v0.3.2 ship (commit 49fe94d).**
> Read this after `DAY-03-SPEC.md` and `DAY-03-VERIFIER-REPORT.md`.
> Day 3 closed the physics (1/7 ship-gate bands pass). Day 4 closes the
> ship-gate via plant-data calibration. **This day is blocked on
> PlantA plant data from the user. No code can substitute for that.**

## Goal

Bring the 6 failing ship-gate bands on the PlantA preset into spec
by **calibrating** the v0.3.2 model to plant data, not by changing the
physics. The physics is right; the geometry/operating-handle is
undersized for the design duty.

## What the spec ships

1. **A plant-data loader** (`pro/nepal_decarb_pro/data/plant_history.py`):
   CSV ingestion of one PlantA operating shift's `timestamp,
   clinker_outlet_T_c, secondary_air_T_c, exhaust_T_c, fan_amp_4_20mA,
   grate_speed_hz, ambient_T_c, ambient_rh_pct`. Pydantic v2
   validation. Schema in `day-04-PRs/data/plant_history_schema.json`.
2. **A calibration framework** (`tools/03-cooler-grate-simulator/src/
   nepal_cooler_sim/calibration.py`): least-squares fit of the
   v0.3.2 model parameters against the plant time series, with
   per-parameter bounds and a 95% confidence interval.
3. **A Sobol sensitivity sweep** (`tools/03-cooler-grate-simulator/src/
   nepal_cooler_sim/sensitivity_sobol.py`): N=1024 Saltelli sampling
   (Saltelli 2010) over the calibration-parameter box. Identifies
   which parameters the ship-gate bands are most sensitive to.
4. **A fragility test** (`tests/test_calibration_sobol.py`): property-
   based sweep with 5 Hypothesis strategies over the parameter box.
   Catches the v0.3.0/v0.3.1 "monotonicity but not physical" failure
   mode.
5. **A post-calibration ship-gate report** (`scratch/day4_ship_gate.md`):
   the 7 ship-gate bands on the calibrated PlantA preset. If 7/7
   pass, the day ships. If not, Day 4 is incomplete and Day 5 picks
   up the remaining bands.
6. **Re-integration of the 8 specialist PRs** that ride along in
   `day-03-PRs/`: Hiro's 5 tests, Maya's `cooler_types.py`, Ramesh's
   `outputs.py`, Kabita's `data_quality_tiers.py`, James's
   `pdd_json_schema.json`, Sofia's `llm_advisor_spec.md`, Priya's
   `sales_one_pager.md`, Aanya's `physics_notes.md`. Each PR is
   re-aligned to the v0.3.2 public API (`solve_steady_state` not
   `run_to_steady_state`, no `arrhenius_rate` in public surface,
   no `radiative_flux_cooler` in public surface).

## Calibration parameters (with bounds and priors)

| Parameter | Symbol | Bounds | Prior | Source |
|---|---|---|---|---|
| Grate length | L | [20, 50] m | 28 m | engineering design |
| Compartment 1 sec-air flow | m_a_sec | [20, 50] kg/s | 26.4 kg/s (1.10x stoich) | Peray & Waddell 1986 §6.2 |
| Secondary-air excess factor | ε_excess | [1.0, 2.0] | 1.10 | Peray & Waddell 1986 §6.2 |
| Recuperator preheat (T_a_inlet shift) | ΔT_recup | [0, 200] K | 0 | plant-specific |
| Compartment-wise air-velocity schedule | v_i | [0.5, 5.0] m/s | 1.5 m/s uniform | plant-specific (when available) |
| Effective emissivity (uncertainty) | ε_eff | [0.7, 0.95] | 0.85 | ICCC 2006 §2.3 |
| Clinker residence time scale | τ_res | [0.5, 2.0] | 1.0 | plant-specific (when available) |

## What Day 4 does NOT change

- The 1D compartment-wise counter-flow model architecture
- The Achenbach (1995) + Mujumdar (2007) heat-transfer correlation
- The ISO 2533 + ASHRAE 2021 Ch. 1 moist-air density
- The Pydantic v2 input model (`CoolerParameters`)
- The ship-gate band definitions (they were chosen by Mavis on Day 3
  and not adjusted for v0.3.2 — that would be cheating)

## Ship gate (Day 4)

- [ ] `secondary_air_outlet_c ∈ [600, 1000] °C` on calibrated PlantA
- [ ] `tertiary_air_outlet_c ∈ [400, 700] °C`
- [ ] `exhaust_air_outlet_c ∈ [150, 300] °C`
- [ ] `clinker_outlet_c ∈ [120, 200] °C`
- [ ] `cooler_efficiency ∈ [0.65, 0.85]`
- [ ] `first_law_imbalance ≤ 0.02` (Day 3 already passes)
- [ ] `sec/heat ∈ [0.85, 1.15]`
- [ ] Calibration RMSE ≤ 25 K on clinker_outlet_T
- [ ] Calibration RMSE ≤ 15 K on secondary_air_T
- [ ] Sobol N=1024 sweep identifies the top-3 parameters
- [ ] All 4 plant presets still run (PlantA is the calibration
      target; the others are sanity checks)
- [ ] 5+ Hiro fragility tests added, all green
- [ ] Re-integration of 8 specialist PRs, smoke-tested

## What I need from the user

**One PlantA operating shift's plant data**, CSV format, 1-minute
sampling, columns:

```
timestamp,clinker_outlet_T_c,secondary_air_T_c,exhaust_T_c,
fan_amp_4_20mA,grate_speed_hz,ambient_T_c,ambient_rh_pct
```

If 1-minute sampling is not available, 5-minute or 15-minute is fine
as long as the timestamp is the row's wall-clock and the data covers
at least 4 hours of steady-state operation (a single steady-state
shift is the goal, not a transients-rich start-up log).

If the user cannot provide this data within 24 hours, Day 4's
calibration step is replaced by a **synthetic-truth Monte Carlo
calibration** (Hiro's `test_property_based.py` style), with the
honest disclosure that the synthetic truth was generated by the
v0.3.2 model itself, NOT by independent plant data. This is a
**known-broken substitute** — Verra VM0009 v3.0 §6.2 explicitly
requires measured plant data for the kiln-baseline monitoring, not
synthetic. The user must approve the synthetic substitution if the
real data is not available, and James must mark the resulting PDD
as a "methodology deviation request per VMD0053" rather than a
standard Verra submission.

## Owner assignments

- **Aanya** (chem-eng): physics, calibration-parameter bounds, post-
  calibration air-density recomputation
- **Hiro** (data-scientist-uq): plant-data loader, calibration
  algorithm, Sobol sweep, fragility tests
- **Maya** (cs-architect): Pydantic schema, FastAPI stub for the
  data-ingest endpoint, JSON serialization
- **Ramesh** (mech-eng): per-compartment engineering review of the
  calibrated model (do the calibrated compartment T profiles make
  physical sense for a real IKN/KHD/Polysius cooler?)
- **Kabita** (env-eng): per-field data-quality tier for the plant
  data, with measured-instrument sigma (e.g. Type-K TC at sec-air
  duct is ±20 K at 800 °C, IR spot pyrometer at cooler exit is
  ±15 K, fan amp 4-20 mA is ±0.5% span)
- **James** (carbon-markets): confirm the calibrated model's PDD
  inputs match VM0009 v3.0 §5.3 monitoring parameters; if Day 4
  ends with synthetic data, draft the VMD0053 deviation request
- **Sofia** (ai-ml-engineer): RAG ingestion of the calibration
  report into pgvector so the LLM advisor (Day 14) can answer
  "what is the calibration RMSE on PlantA?" without re-running
  the calibration
- **Priya** (business-lead): pilot handoff — does the calibrated
  model + plant data change the $337K-$1.35M/yr fuel-savings range
  from Day 3? If yes, update the sales one-pager.
- **Mavis** (orchestrator): ship gate, post-calibration retro, format-
  patch bundle, re-integration of the 8 specialist PRs
- **verifier** (built-in): signs off on the 7-band ship gate + the
  calibration RMSE + the 8-PR re-integration smoke

## Asks (forward to user)

1. **Plant data** (above). Without it, Day 4 is synthetic-only and
   the ship gate is unverifiable per Verra §6.2.
2. **Approve the synthetic-substitution fallback** if the data is
   not available in 24 hours. James's VMD0053 draft will land
   either way; the user just needs to acknowledge the synthetic
   data is research-only, not registry-submittable.
3. **Pick the Day 4 pilot plant** if the user wants Day 4 to also
   validate against PlantB or plantc. Default: PlantA
   (per ADR-001). Optional: PlantB (300 m, dry-process, easier
   geometry match).

## References

- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192.
- Peray, K.E. & Waddell, J.J. (1986). *The Rotary Cement Kiln*, 2nd ed.
- Incropera, F.P. & DeWitt, D.P. (2002). Ch. 12.
- Saltelli, A. et al. (2010). *Computer Physics Communications* 181:259.
- Sobol', I.M. (2001). *Mathematics and Computers in Simulation* 55:271.
- Cengel, Y.A. & Boles, M.A. (2015). *Thermodynamics*, 8e.
- ASHRAE Handbook (Fundamentals) 2021 Ch. 1.
- ISO 2533:1975.
- Verra VCS Program Guide v4.5 (2024-Q2).
- Verra VM0009 v3.0 (2024-ICVCM Tier 3 assessment).
- Verra VMD0053 (Methodology Deviation Request template).
- IPCC 2006 Vol.3 Ch.2.
- GCCA GNR 2022; ECRA 2022.

— Mavis, 2026-07-22.
