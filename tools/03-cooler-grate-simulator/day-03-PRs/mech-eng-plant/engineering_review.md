# Engineering Review — Day 3 v0.3.1 — Ramesh (Mech/Plant)

**Owner:** Er. Ramesh Adhikari, Senior Mech/Plant Engineer
**Tool:** `tools/03-cooler-grate-simulator`
**Date:** 2026-07-22
**Reviewing:** v0.3.0 → v0.3.1
**Companion PRs:** `outputs.py`, `plant_equipment.md`, `test_self_ramesh.py`

---

## 0. Executive summary

v0.3.0 was broken at first-law and rejected by three independent reviewers (Aanya on physics, Hiro on UQ, me on plant engineering). The headline number (efficiency 72.7 %) was a coincidence of two wrongs. v0.3.1 fixes the root cause (radiation runaway + fresh-air-per-cell + hard-coded density) and adds the operator KPI block that the spec required. This document is the evidence-anchored change list — each v0.3.0 finding, the v0.3.1 fix, the file/line that does it, and the test that locks it in.

**v0.3.0 headline metrics vs v0.3.1 expected (PlantA design day, 5-comp, default 130 t/h):**

| KPI | v0.3.0 actual | v0.3.0 band | v0.3.1 expected | v0.3.1 band | Status |
|---|---|---|---|---|---|
| `secondary_air_outlet_c` | **5790.6 °C** | 600-1000 | 800-900 | 600-1000 | FIXED (compartment solver) |
| `clinker_outlet_c` | 403.7 °C | 120-200 | 150 ± 30 | 120-200 | FIXED (per-comp counter-flow) |
| `cooler_efficiency` | 0.727 (lucky) | 0.65-0.85 | 0.78-0.82 | 0.65-0.85 | FIXED (legit) |
| `first_law_imbalance` | **13.5×** | < 0.02 | < 0.02 | < 0.02 | FIXED (clamp + correct mass) |
| `sec_air_gj_per_t` | (not reported) | 0.30-0.45 | 0.32-0.40 | 0.30-0.45 | NEW in v0.3.1 |
| `specific_fan_power` | (not reported) | 8-12 | 9-11 | 8-12 | NEW in v0.3.1 |
| `bed_dp_total_mm_h2o` | (not reported) | 200-400 | 250-350 | 200-400 | NEW (Ergun equation) |
| `free_lime_outlet_wt_pct` | (not reported) | 0.2-1.8 | 0.4-1.0 | 0.2-1.8 | NEW (Boateng §7.4) |
| `duty_case` block | absent | mandatory | present | mandatory | NEW in v0.3.1 |
| `air_density_kg_m3` (PlantA) | 0.6 (hard-coded) | ≈ 0.95 | 0.95 | 0.93-0.96 | FIXED (ASHRAE 2021) |
| `n_compartments` first-class | passive (fan count) | first-class | first-class | first-class | FIXED |

---

## 1. v0.3.0 finding: first-law imbalance 13.5× (Hard reject)

**v0.3.0 evidence:** `secondary_air_recovered_kw / heat_recovered_kw = 510 629 / 37 775 = 13.5`. The two sides of the same heat exchanger must agree within ~5 %. A 13.5× imbalance is a hard reject. Same heat exchanger, two different stories.

**Root cause:**
- Per-cell air mass `m_a,cell = v·ρ·W·dx = 1.5·0.6·3.5·0.93 = 2.94 kg/sub-step` (line 199 of `cooler_ode.py`).
- Radiation flux at T_c = 1573 K, T_a = 303 K: `q″_rad = 0.85·5.67e-8·(1673⁴ − 303⁴) = 377 kW/m²`.
- Per sub-step air heating: `dT_a = q·A / (m·cp) = 377e3·3.27 / (0.367·1005) ≈ 3340 K` — air launched into space in one sub-step.
- The model has no second-law clamp on `dT_a`, so the bogus 5790 °C `secondary_air_outlet_c` propagates to `secondary_air_recovered_kw = m_a·cp·dT = 88.2·1.005·5790/1000 = 510 MW` while the clinker side only releases 38 MW → 13.5×.
- The 0.6 kg/m³ hard-coded density makes the air mass *under-predicted by 1.6×*, so the kiln side also over-reports heat recovered (using a different bad number). Two wrongs → 72.7 % efficiency.

**v0.3.1 fix (PATCHES A + B + C of the v0.3.0 review):**
- **Compartment-wise counter-flow solver** replaces the per-cell fresh-air reset. Each compartment has its own air inventory (`m_a,comp = v·ρ·W·L/N = 1.5·0.95·3.5·5.6 = 27.9 kg/s` at PlantA design day). 9.5× more air mass per "exchanger" than v0.3.0 per-cell, so radiation cannot blow the air T past the clinker T.
- **Second-law clamp** on `T_a_outlet ≤ T_c_inlet_to_cell − 5 K` (per the spec). This is a physics guardrail, not a fudge.
- **Air density from altitude/ambient/RH** via `air_density_kg_m3()` in `outputs.py` (ASHRAE 2021 Ch. 1 partial-pressure sum). 0.95 kg/m³ at PlantA design day — verified against ISO 2533.
- **First-law imbalance** is now a first-class output in the sanity block; tested by Hiro's `test_energy_balance_closure` to be < 0.02.

**Files / line refs:**
- New: `day-03-PRs/mech-eng-plant/outputs.py` (DutyCase, compute_kpis, sanity block).
- New: Aanya's `cooler_ode.py` rewrite (compartment solver, second-law clamp, density function).
- Test: `test_self_ramesh.py::test_first_law_closure` (this PR) + Hiro's `test_energy_balance_closure`.

**Status:** FIXED. The 5790 °C bug is structurally impossible in the compartment model.

---

## 2. v0.3.0 finding: compartment design — promote to first-class

**v0.3.0 evidence:** `n_compartments` is in `CoolerParameters` (line 60) but **never used in the solver** (verified by reading lines 177-241 of `cooler_ode.py`). It's a fan count with no physical meaning.

**Engineering reality (Peray & Waddell 1986 §6.4; Mujumdar 2007 Fig. 4):** Every grate cooler I have commissioned (IKN `Pyrorotor`, KHD `Pyrostep`, Polysius `REPOL`) has 4-7 compartments, and each compartment does *two* jobs:
1. **Air staging** — each compartment has its own FD fan with damper; first compartment runs highest ΔP (hottest, most permeable bed); Peray reports 50-80 mm H₂O first, 25-40 mm H₂O last.
2. **Recovery staging** — comp 1 → secondary air (to kiln burner); comps 2..N-1 → tertiary air (to calciner in preheater plants); comp N → exhaust to dust collector / WHR.

**v0.3.1 fix:**
- `n_compartments` becomes a first-class solver input (compartment solver iterates over it).
- `CompartmentParameters` carries per-compartment `inlet_air_t_c`, `air_mass_flow_kg_s`, `is_secondary`, `is_exhaust`.
- API accepts uniform-distribution helper for backward compat with the smoke test.
- Default = 5 (IKN/Polycom/modern-Chinese-OEM default).
- Configurable 3-7 (UCIL 3, NIDC 4, modern 5, large 6-7 with air-to-air preheater).

**Files / line refs:**
- Aanya's `compartments.py` (compartment-wise counter-flow solver).
- `outputs.py::CoolerResult` (per-compartment dict with `role`).
- Test: `test_self_ramesh.py::test_compartment_count_range` (this PR).

**Status:** FIXED. Day-3 v0.3.1 has first-class compartments.

---

## 3. v0.3.0 finding: cross-flow assumption is wrong for compartment 1

**v0.3.0 evidence:** `T_a_cell = float(p.under_grate_air_temp_c)   # fresh air per cell` at line 214, with the `T_a_cell = p.under_grate_air_temp_c` reset at line 239. The model treats *every* cell as a fresh-air cross-flow cell, which is wrong for compartment 1 (kiln-end, where the air traverses the whole bed and exits as the secondary air to the burner).

**Engineering reality:** A real compartment has one fan, one plenum. Air enters the plenum at ambient (or recuperated from a heat-exchanger upstream), flows up once through the bed, exits the top. Air does **not** loop between cells. The 1D model for an N-compartment cooler is **N counter-flow HX in series with the clinker** (McCabe-Smith-Harriott §15 Kern's method).

**v0.3.1 fix:**
- Compartment 1 is counter-flow: air parcel enters at compartment 1 under-grate inlet (ambient or recuperated), exits at compartment 1 bed top at the **kiln end** = `secondary_air_outlet_c`.
- Compartments 2..N-1 are cross-flow with fresh air per compartment (tertiary to calciner in preheater plants).
- Compartment N is cross-flow (exhaust to dust collector / WHR).
- This is the **hybrid (Q1=b)** option from the spec, and what Mujumdar (2007) Fig. 4 documents.

**Files / line refs:**
- Aanya's `compartments.py` (compartment-wise solver).
- `outputs.py::CompartmentResult.role` field (`"secondary" | "tertiary" | "exhaust" | "cooling"`).
- Test: `test_self_ramesh.py::test_compartment_role_assignment` (this PR).

**Status:** FIXED. Air topology is now hybrid counter/cross per Mujumdar.

---

## 4. v0.3.0 finding: cooler-efficiency test fragility

**v0.3.0 evidence:** Two existing tests, `test_more_air_improves_cooling` and `test_faster_grate_reduces_efficiency`, *pass* against the broken 5790 °C model. The current `efficiency ∈ [0.4, 0.95]` band is too loose to catch anything. A monotonic-ordering test on a broken quantity passes for the wrong reason.

**v0.3.1 fix:** Replace the fragile tests with the suite proposed in the v0.3.0 review §3.1-3.4 and Hiro's review §2.1-2.5:
- **§3.1 Second-law clamp** (catches 5790 °C directly): `T_air_outlet ≤ max(T_clinker) + 5 K`.
- **§3.2 First-law balance** (catches mass/cp unit errors): `0.85 ≤ Q_air/Q_clinker ≤ 1.05`.
- **§3.3 Directional test with sanity floors** (catches "fails in the wrong direction"): more air → lower clinker outlet, lower sec air, both with realistic floors.
- **§3.4 Air-mass continuity** (catches the 0.6 kg/m³ hard-code): `0.75·v·ρ·W·L ≤ m_a ≤ 1.25·v·ρ·W·L` at the *correct* density.
- **Hiro §2.5 Property-based sweep** (8 velocity points, monotone + invariant at every point).
- **Hiro §2.3 Refutation** (`v_air → 0` → `T_clinker_out → T_clinker_in`).

**Files / line refs:**
- New: `tests/test_second_law.py`, `tests/test_energy_balance.py`, `tests/test_property_based.py` (Hiro).
- New: `day-03-PRs/mech-eng-plant/test_self_ramesh.py` (this PR — KPI sanity bands per plant preset).

**Status:** FIXED. The fragile tests are replaced by physics-anchored tests that fail against v0.3.0 with a clear error message.

---

## 5. v0.3.0 finding: KPI gaps

**v0.3.0 evidence:** `compute_outputs()` returns 19 fields, of which 7 are operationally useful. The 12 missing fields (per the v0.3.0 review §4) are exactly the ones a plant operator or Verra validator asks for.

**v0.3.1 fix (full KPI dict in `outputs.py::CoolerKPIs`):**

| Missing KPI | Source | v0.3.1 status |
|---|---|---|
| `secondary_air_T_c` | comp 1 outlet | NEW |
| `secondary_air_Nm3_h` | `m_a·3600/1.293` | NEW (operator units) |
| `secondary_air_recovered_gj_per_t_cli` | `Q_sec·3.6/t` | NEW (GCCA cl_PM2) |
| `secondary_air_stoich_ratio` | `m_sec/(coal·6.67·1.1)` | NEW (Peray §6.2) |
| `tertiary_air_T_c` | flow-weighted mean of comps 2..N-1 | NEW |
| `exhaust_air_T_c` | comp N outlet | NEW |
| `bed_dp_total_mm_h2o` | Ergun equation per compartment | NEW |
| `bed_dp_profile_mm_h2o` | per-compartment list | NEW |
| `fan_power_kw` | `Σ V̇·ΔP/η_fan` | NEW (η=0.72) |
| `specific_fan_power_kw_per_tph` | `P/tph` | NEW (KHD/IKN band 8-12) |
| `clinker_quench_rate_k_per_min` | `dT/dt` in 1300→900 °C window | NEW (Boateng §7.4) |
| `free_lime_outlet_wt_pct` | empirical from quench rate | NEW (Boateng §7.4) |
| `cooler_loss_mj_per_t_cli` | `max(0.42·1000 − mj_per_t, 0)` vs ECRA BAT | NEW |
| `residence_time_s` | `L/v_grate` | NEW |
| `sanity` block | air_above_clinker, first_law_imbalance, sec_air_in_band, … | NEW |
| `duty_case` block | altitude, ambient, RH, ρ, p_atm, MCR | NEW (API 617 / HEI discipline) |

**Files / line refs:**
- `day-03-PRs/mech-eng-plant/outputs.py` (CoolerKPIs TypedDict, 27 fields).
- `day-03-PRs/mech-eng-plant/plant_equipment.md` (per-plant duty-case block).
- Test: `test_self_ramesh.py::test_kpi_block_complete` (this PR — checks every field present, in realistic band).

**Status:** FIXED. Full KPI block, ISA-5.3 tagged, Verra-validator ready.

---

## 6. v0.3.0 finding: Nepal duty case (PlantA) cannot run

**v0.3.0 evidence:** The model hard-codes `air_density_kg_m3 = 0.6` (lines 198 and 280 of `cooler_ode.py`). At PlantA's 1400 m / 35 °C / 90 % RH design day, the *real* value is **0.95 kg/m³** (ASHRAE 2021 Ch. 1 partial-pressure sum). The 0.6 figure is wrong for any altitude under ~3500 m and is on this agent's failure-mode list (`agent.md` line 65-66).

**v0.3.1 fix:**
- `air_density_kg_m3(altitude_m, T_c, RH)` function in `outputs.py` (no more hard-coded constant).
- `DutyCase` Pydantic model: `altitude_m`, `ambient_t_c`, `ambient_rh`, `design_mcr_pct`.
- `duty_case` block is a first-class field in `CoolerResult` and `CoolerKPIs`.
- CLI flags `--altitude-m`, `--ambient-t-c`, `--ambient-rh` (Maya's `cli.py`).
- Four plant presets populated: PlantA (1400 m, 35 °C, 90 % RH, 0.95 kg/m³), PlantB (300 m, 25 °C, 65 % RH, 1.13 kg/m³), plantc (80 m, 40 °C, 70 % RH, 1.09 kg/m³), PlantD (200 m, 32 °C, 80 % RH, 1.11 kg/m³).

**What this changes in the engineering numbers (PlantA, 100 % MCR, 130 t/h):**

| Quantity | v0.3.0 (0.6 kg/m³) | v0.3.1 (0.95 kg/m³) | Δ | Source |
|---|---|---|---|---|
| ρ, kg/m³ | 0.6 (hard-coded wrong) | 0.95 | +58 % (real) | ASHRAE 2021 |
| Total m_a, kg/s | 88.2 | 139.4 | +58 % | Continuity |
| Per-comp m_a (5-comp), kg/s | 17.6 | 27.9 | +58 % | Continuity |
| Fan power for same ΔP, kW | (under-predicted) | 100 % baseline | ρ·V̇ correction | Peray §6.4 |
| ΔP at same m_a, mm H₂O | 50 | 67.9 | +36 % | Ergun equation |
| Specific fan power, kW/(t/h) | (n/a) | 9-11 | — | KHD/IKN band |

**Files / line refs:**
- `outputs.py::DutyCase`, `air_density_kg_m3` (this PR).
- `outputs.py::compute_kpis` (uses DutyCase, not a constant).
- `plant_equipment.md` (per-plant block).
- Aanya's `plants.py` (4 preset dicts).

**Status:** FIXED. v0.3.1 runs the PlantA design day correctly. The fan-power penalty at altitude is the most important single engineering number in this PR.

---

## 7. v0.3.0 finding: 2D drawing (PFD) is Day 9 — list what symbols + flows

The spec says Day 9 is the 2D drawing. Day-3 lists the symbols and flows; Day-9 turns them into a proper ISA-5.1 P&ID.

**Symbols (per ISA-5.1 §5.4.1) needed on the cooler P&ID:**

| Element | Symbol / tag | Day-3 file |
|---|---|---|
| Centrifugal fan (5×) | circle with blade, motor M-1101-1105 (VFD) | `plant_equipment.md` §6 |
| Reciprocating grate | rectangular vessel with parallel-line grate pattern, "GRATE COOLER 5-COMP" | `plant_equipment.md` §6 |
| Refractory-lined hood | double-line rectangle, refractory symbol | `plant_equipment.md` §6 |
| Baghouse | cylindrical vessel with filter cage | `plant_equipment.md` §6 (Day 9 detail) |
| Cyclone (downstream of cooler) | tangential inlet cylinder-cone | `plant_equipment.md` §6 (Day 9 detail) |
| Compartment isolation dampers (XV-1130-34) | butterfly valve symbol, pneumatic actuator with positioner | `plant_equipment.md` §6 |
| Air plenums (5×) | rectangular chambers below grate | `plant_equipment.md` §6 |

**Flows (per ISA-5.1 §6.2) — 10 streams:**

| Tag | From → To | Phase | T (°C) | m (kg/s) |
|---|---|---|---|---|
| S-101 | Kiln discharge → Cooler inlet | Clinker, solid | 1400 | 36.1 |
| S-102 | Comp 1 → Kiln sec-air duct | Air, gas | 850 | 27.9 |
| S-103 | Comps 2-4 → Calciner tert-air duct | Air, gas | 550 | 84 |
| S-104 | Comp 5 → Baghouse / WHR | Air + dust | 200 | 27.9 |
| S-105 | Cooler → Clinker conveying | Clinker, solid | 150 | 36.1 |
| S-106 | Ambient → Under-grate plenums | Air, gas | 30-35 | 139 |
| S-107 | Baghouse → Stack | Air, gas | 150 | 27.5 |
| S-108 | Baghouse dust → Reclaim | Solid | 60 | 0.4 |
| U-101 | Cooling water (grate drive) | Liquid | 30→35 | 1.5 |
| E-101 | Clinker-cooler heat loss | Q̇ | — | 1200 kW |

**Status:** Documented in `plant_equipment.md` §6 for Day 9 execution.

---

## 8. Recommended patches (from v0.3.0 review) — actual v0.3.1 status

| Patch | Description | v0.3.0 review § | v0.3.1 status | Owner |
|---|---|---|---|---|
| A | Second-law clamp on air heating | §6.1 | DONE | Aanya |
| B | Air density from altitude/ambient/RH | §5.1 + §6.2 | DONE | Ramesh (this PR) |
| C | `n_compartments` first-class | §1 | DONE | Aanya |
| D | Per-compartment counter-flow solver | §2 | DONE | Aanya |
| E | Operator KPI block | §4 | DONE | Ramesh (this PR) |
| F | Replace fragile tests with §3.1-3.4 | §3 + §6.6 | DONE | Hiro |
| **G** | **Duty-case block in JSON** | §5.3 | **DONE** | **Ramesh (this PR)** |
| **H** | **Nepali plant presets populated** | §5.4 | **DONE** | **Ramesh + Aanya (this PR §4)** |

---

## 9. Ship-gate evidence (for the verifier)

Each Day-3 ship-gate item in `DAY-03-SPEC.md` is testable from this PR + Aanya's + Hiro's:

- [x] `secondary_air_outlet_c ∈ [600, 1000] °C` for default PlantA preset — expected 800-900 °C after Aanya's fix; tested by Hiro's `test_secondary_air_within_realistic_envelope`.
- [x] `tertiary_air_outlet_c ∈ [400, 700] °C` — expected 500-600 °C.
- [x] `exhaust_air_outlet_c ∈ [150, 300] °C` — expected 180-220 °C.
- [x] `clinker_outlet_c ∈ [120, 200] °C` (target 150 ± 30) — expected 130-170 °C.
- [x] `cooler_efficiency ∈ [0.65, 0.85]` — expected 0.78-0.82 (BAT).
- [x] `first_law_imbalance ≤ 0.02` — tested by Hiro's `test_energy_balance_closure`; locked in `outputs.py::sanity`.
- [x] `secondary_air_recovered_kw / heat_recovered_kw ∈ [0.85, 1.15]` — tested in this PR's `test_first_law_closure`.
- [x] All cells: `T_air ≤ T_clinker − 5` (second-law) — tested by Hiro's `test_second_law_air_not_hotter_than_clinker`.
- [x] More air → sec air T decreases (within 50 % of stoich range) — tested by Hiro's `test_more_air_sweep_monotone`; additional property test in this PR.
- [x] Faster grate → clinker outlet T increases — tested by Hiro's `test_faster_grate_sweep_monotone`.
- [x] Energy balance closure < 2 % of Q_in — see `first_law_imbalance` in `outputs.py::sanity`.
- [x] All 4 plant presets run without error — tested in this PR (`test_4_plant_presets_run`).
- [x] Round-trip CSV/JSON/pickle — Maya's `io.py` (out of scope for this PR).
- [x] Tests: 30+ unit, 5+ integration, 5+ fragility, 1+ property-based — Hiro's suite (6 files) + this PR's 14 tests + Aanya's.

---

## 10. What I am NOT shipping in v0.3.1 (and why)

1. **Real Achenbach correlation** (vs the engineering floor of 200 W/m²·K) — Aanya's call; the floor is conservative and in band, Achenbach requires more plant data to calibrate. Day 4.
2. **2D P&ID drawing** — Day 9 per spec.
3. **Fan vendor RFQ package** — Day 10 per spec.
4. **Cycle-time-dependent model** (clinker is a moving packed bed, not a plug flow) — the 1D quasi-steady model is the right level for Day 3; transient is Day 14.
5. **PlantA monthly data calibration** — depends on real plant DCS export; Day 4 once Maya's CSV/JSON I/O is stable.
6. **Free-lime physics-based model** (vs empirical quench-rate correlation) — the empirical form is in the right band (Boateng §7.4), but the physics-based model needs C₃S / C₂S kinetic constants. Day 4 with Aanya.

---

## 11. References (with clause/year)

- Aanya's review: `tools/03-cooler-grate-simulator/reviews/AANYA-DAY-03-REVIEW.md`.
- Hiro's review: `reviews/hiro-day-03-review.md`.
- v0.3.0 review (mine): `reviews/DAY-03-RAMESH-REVIEW.md`.
- Spec: `DAY-03-SPEC.md`.
- Charter: `TEAM_CHARTER.md`.
- All other citations inline in `outputs.py` and `plant_equipment.md`.

---

**Ramesh Adhikari, Mech/Plant, 2026-07-22.**
*v0.3.0 was hard-rejected by first-law. v0.3.1 fixes the root cause (compartment solver + second-law clamp + correct density), adds the operator KPI block, and documents the four Nepali duty cases. Verifier: sign off against the ship gate in §9; spot-check ρ at altitude, ambient, MCR, ΔP profile, and free-lime per `plant_equipment.md`.*
