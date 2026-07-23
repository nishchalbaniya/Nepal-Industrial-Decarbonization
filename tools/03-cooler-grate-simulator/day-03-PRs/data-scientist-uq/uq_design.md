# UQ Design — Day 3 v0.3.1 Cooler

**Author:** Hiro Tanaka, Senior Data Scientist / UQ
**Date:** 2026-07-22
**Tool:** `tools/03-cooler-grate-simulator`
**For:** Day 3 v0.3.1 (post-mortem rebuild after v0.3.0 5790 °C second-law violation)

---

## 1. Scope

This document specifies the uncertainty quantification (UQ) work for the
cooler model in Day 3 v0.3.1. It is the UQ companion to my v0.3.0 review
(`reviews/hiro-day-03-review.md`) and is structured around three questions:

1. **Which inputs matter most?** → Sobol sensitivity ranking (Section 3).
2. **How much uncertainty do those inputs induce in the KPIs?** → Monte
   Carlo propagation (Section 4).
3. **How well does the model match plant data?** → Calibration +
   validation protocol (Section 5).

The headline deliverable for Day 3 v0.3.1 is a **Sobol sensitivity
analysis on the top-3 inputs**, with the 5 new tests from
`reviews/hiro-day-03-review.md` §2 written *and confirmed to FAIL against
v0.3.0*. The MC propagation and the Hetauda calibration are Day 4 / Day 15
deliverables (digital twin) — the design here is what we will run, not
what we will run today.

---

## 2. Inputs and outputs

### 2.1 Inputs (with sources of uncertainty)

The cooler model has 7 floating-point inputs in `CoolerParameters`. They
are not equally important. The 5 that matter for UQ are:

| Input | Nominal | Range (ge..le) | Source of uncertainty | UQ tier |
|---|---|---|---|---|
| `clinker_inlet_t_c` | 1400 °C | [900, 1600] | Kiln burner T logs, pyrometer noise ±15 K | Tier 1 (Hetauda logs) |
| `under_grate_air_velocity_m_s` | 1.5 m/s | [0.3, 5.0] | Filter loading, VFD setpoint, ±10% | Tier 1 (Hetauda VFD Hz) |
| `grate_speed_m_min` | 12 m/min | [1.0, 30.0] | Operator VFD, ±10% | Tier 1 (Hetauda VFD Hz) |
| `cp_clinker_kj_kg_k` | 1.05 kJ/kg·K | [0.8, 1.5] | Literature ±5% | Tier 2 (literature) |
| `clinker_diameter_m` | 0.025 m | [0.005, 0.10] | Sieve data, ±20% | Tier 3 (no data) |

The other 2 (`length_m`, `width_m`) are geometry constants; uncertainty
in them is captured in `clinker_throughput_t_h` (a higher-level driver).

### 2.2 Outputs (KPIs)

Five KPIs from `compute_outputs()`:

1. `secondary_air_outlet_c` (°C) — kiln-coupled, MUST be in [600, 1000].
2. `clinker_outlet_c` (°C) — target 150 ± 30.
3. `cooler_efficiency` (—) — target [0.65, 0.85].
4. `heat_recovered_kw` (kW) — KPI for the heat balance.
5. `secondary_air_recovered_kw` (kW) — kiln-side recovery, MUST match
   `heat_recovered_kw` to within 5% (Ramesh §3.2, Hiro §2.2).

---

## 3. Sobol sensitivity analysis

### 3.1 Method

Saltelli's extension of Sobol' (Sobol' 2001; Saltelli 2010). With `D`
inputs and a base sample size `N`, the total number of model evaluations
is `N × (2D + 2)`. The first-order and total-order indices are estimated
from a single Saltelli sample, and their 95% confidence intervals
half-widths decay as `1/√N` (Saltelli 2010, Table 1).

### 3.2 Sample size

**N = 1024 base, ~8192 model evaluations for D = 3 inputs.**

This is the sample size that puts the 95% CI half-width on the first-order
indices at ±~0.03 (Saltelli 2010, Table 1, "design resolution"). It is
adequate to rank-order the three inputs. Smaller `N` is a false economy:
at `N = 256` the CIs are ±0.06 and the (grate, air) interaction is
unreadable.

### 3.3 Top-3 inputs (decided in v0.3.0 review §3)

1. **Clinker inlet T** — biggest absolute lever, kiln-coupled, and the
   one we have least plant data on (Hetauda's kiln-burner T logs are
   noisy). Cited: Aanya v0.3.0 review §3 (clinker inlet T sets the
   enthalpy budget).
2. **Air velocity** — operator-controllable, large uncertainty band
   from filter loading, and the variable that exposes the cross-flow vs
   counter-flow modelling choice the team is debating today.
3. **Grate speed** — operator-controllable, Hetauda logs it directly
   (VFD Hz), and the (grate × air) interaction is the physically
   interesting second-order term.

Skip `cp` for Day 3 (cp is in the noise compared to plant variability)
and `d` (Day 4 once we have sieve data from Hetauda).

### 3.4 Expected total-order index magnitudes (prior)

| Input | First-order S1 on `cooler_efficiency` | Total-order ST on `clinker_outlet_c` |
|---|---|---|
| Clinker inlet T | 0.45 ± 0.03 | 0.50 ± 0.03 |
| Air velocity | 0.20 ± 0.03 | 0.35 ± 0.03 |
| Grate speed | 0.15 ± 0.03 | 0.25 ± 0.03 |
| (interaction) | — | ~0.10 (air × grate) |

This prior will be **reported with the 95% CI**, not as a point estimate.
A model whose first-order indices agree with the prior to within ±0.05
is "as expected"; a divergence >0.10 indicates a structural surprise
that warrants a code review.

### 3.5 Implementation

- Use `SALib` (Saltelli sampling, Sobol' analyzer) — `pip install SALib`.
- `numpy.Generator` (`np.random.default_rng()`) for reproducibility, not
  `np.random.seed` (legacy, NEP 19 deprecates new uses).
- Run the sweep on the v0.3.1 model ONLY. Running it on v0.3.0 will
  produce a sensitivity ranking of "the radiation runaway" — informative
  but not the deliverable.
- Persist the notebook + the `n_eval` count in the commit message.
  "1000 MC samples" is not a sample size, it is a confession of
  insufficient work.

---

## 4. Monte Carlo propagation (post-Sobol, Day 4 / Day 15)

Once the top-3 inputs are identified, propagate their **calibrated**
uncertainty through the model to get a CI on each KPI. Per Hiro v0.3.0
review §5.3 (statistical reference):

> "For the MC error bars: the 95% CI half-width on a mean is
> `1.96·σ/√N`. With `N=1000` and `σ/μ ≈ 5%`, the CI half-width is
> `~0.31%` of the mean — that is *not* the model uncertainty, that is
> the MC sampling noise. The model uncertainty is the spread *across*
> the input distribution, which is what the Sobol gives you. Always
> report both, label them, and never let '1000 MC samples' substitute
> for 'input distribution characterised'."

For Day 3 v0.3.1, the immediate deliverable is the Sobol sweep itself.
The MC propagation comes once we have Tier 1 input distributions from
Kabita's PR (the data-quality tier mapping). It is *not* a Day 3 ship
gate.

---

## 5. Calibration & validation

### 5.1 Calibration target

**Hetauda plant data, monthly `clinker_outlet_T` and `sec_air_T`.**

Why these two variables (cite v0.3.0 review §4):
- They are the only plant-measurable variables that are (a) directly
  comparable to a model state, (b) not on the model's input side, and
  (c) sensitive to *all* the parameters we want to identify (h_conv
  floor, emissivity, air mass flow).
- `secondary_air_outlet_c` is the variable v0.3.0 is currently getting
  wrong, so calibrating against it surfaces the radiation bug.

### 5.2 RMSE threshold

Per output measurement's own reproducibility:

| Variable | Reproducibility | Monthly RMSE target | Weekly RMSE target |
|---|---|---|---|
| `clinker_outlet_T` (IR pyrometer) | ±15 K | ≤ 15 K | ≤ 25 K |
| `sec_air_T` (Type-K TC at 800 °C) | ±10 K | ≤ 20 K | — |
| `fan_amps` (4-20 mA transducer) | ±0.5% of span | consistency check only | — |

Cite: pyrometer vendor data (Raytek/Fluke ±15 K IR spot at 100-400 °C);
thermocouple accuracy tables (Type K ±10 K at 800 °C, ASTM E230).

### 5.3 Validation protocol

Per Hiro v0.3.0 review §5 (the 6-point validation discipline):

1. **Train/test split by time, not random.** Train on months 1-9,
   validate on months 10-12. Cite: EPA 2009 *"Guidance on the
   Development, Evaluation, and Application of Environmental Models"*
   EPA/100/K-09/003; Roberts et al. 2017 *"Cross-validation strategies
   for data with temporal and spatial dependence"*. Time-based split
   catches regime shifts (raw-material changes, monsoon humidity) that
   a random split hides.
2. **Multi-metric, not just RMSE.** Report RMSE, MAE, bias, Theil's U2.
3. **Error bars on every reported KPI.** From Sobol propagation, not
   from one MC run.
4. **Refutation / sensitivity-for-validation.** Re-fit on half the
   data, predict the other half. If predictions move, the validation
   is honest.
5. **State validation, not just scalar validation.** Where plant data
   permit, plot predicted T(x) profile against any profile measurement
   (rare; Hetauda likely has only single-point). If only single-point,
   do a "model-up to plant measurement" comparison on a scatter plot
   with identity line, not a time-series overlay.
6. **Document the sample size.** For the MC error bars: `1.96·σ/√N`.
   Always report both the CI on the *mean* and the spread of the
   *output distribution*.

### 5.4 Theil's U2

`U2 = sqrt(MSE_model / MSE_naive)` where `MSE_naive` is the MSE of a
naive random-walk forecast (cite: Theil 1966 *Applied Economic
Forecasting*, North-Holland).

- `U2 < 0.5` — model is better than chance.
- `U2 < 0.3` — model is useful.
- `U2 > 1.0` — model is worse than the naive baseline (reject).

This is the dimensionless skill metric that makes the RMSE comparable
across outputs of different scales.

---

## 6. Day 3 v0.3.1 deliverable summary

| Deliverable | Status | Where |
|---|---|---|
| 5 new tests, FAIL against v0.3.0 | Written | `day-03-PRs/data-scientist-uq/test_*.py` |
| 6th test (property-based) | Written | `day-03-PRs/data-scientist-uq/test_property_based.py` |
| Sobol N=1024 plan (this doc) | Written | `day-03-PRs/data-scientist-uq/uq_design.md` |
| Sobol notebook execution | **Day 4** (need v0.3.1 model first) | TBD |
| MC propagation | **Day 4 / Day 15** | TBD |
| Hetauda calibration | **Day 4 / Day 15** (need plant data) | TBD |
| Validation protocol on hold-out | **Day 4 / Day 15** | TBD |

---

## 7. References

- Boateng, A. A. (2008). *Rotary Kilns* (Ch. 7 — Coolers). Butterworth-Heinemann.
- EPA (2009). *Guidance on the Development, Evaluation, and Application of Environmental Models.* EPA/100/K-09/003.
- Mujumdar, K. S. (2007). Grate cooler model. *Ind. Eng. Chem. Res.* 46(7).
- Peray, K. E. & Waddell, J. J. (1986). *The Rotary Cement Kiln*, 2nd ed. Chemical Publishing.
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal and spatial dependence. *Ecological Modelling*.
- Saltelli, A. et al. (2010). Variance based sensitivity analysis of model output. Design and estimator for the total sensitivity index. *Computer Physics Communications* 181: 259-260.
- Sobol', I. M. (2001). Global sensitivity indices for nonlinear mathematical models. *Mathematics and Computers in Simulation* 55(1-3): 271-280.
- Theil, H. (1966). *Applied Economic Forecasting.* North-Holland.
- NumPy NEP 19 — Default NumPy random number generator (`numpy.random.default_rng()`).

— Hiro Tanaka, 2026-07-22
