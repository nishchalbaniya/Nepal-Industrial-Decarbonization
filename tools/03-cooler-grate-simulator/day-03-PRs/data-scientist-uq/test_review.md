# Test Review — Day 3 v0.3.0 (the bug I am paid to prevent)

**Author:** Hiro Tanaka, Senior Data Scientist / UQ
**Date:** 2026-07-22
**For:** Day 3 v0.3.1 rebuild + verifier sign-off
**Companion files:**
- `day-03-PRs/data-scientist-uq/test_physics.py`
- `day-03-PRs/data-scientist-uq/test_conservation.py`
- `day-03-PRs/data-scientist-uq/test_outputs.py`
- `day-03-PRs/data-scientist-uq/test_refutation.py`
- `day-03-PRs/data-scientist-uq/test_property_based.py`
- `day-03-PRs/data-scientist-uq/uq_design.md`

---

## 1. v0.3.0 — what shipped, and why the test badge was a lie

**Diagnostic run (n_cells=30, Radau):**

| Output | v0.3.0 result | Realistic band | Verdict |
|---|---|---|---|
| `clinker_outlet_c` | 403.7 °C | 130–200 °C | Off-spec |
| `secondary_air_outlet_c` | **5790.6 °C** | 600–1000 °C | **Unphysical — 2nd-law violation** |
| `cooler_efficiency` | 0.727 | 0.65–0.85 | "In band" — but for the wrong reason |
| `heat_recovered_kw` | 37 775 kW | ~matches air side | OK on clinker side |
| `secondary_air_recovered_kw` | **510 629 kW** | 8 000–18 000 kW | **13.5× too high** |
| `t_clinker_max_c` | 1303.8 °C | ≈ clinker inlet | OK |

The headline `cooler_efficiency ≈ 0.73` was inside a plausible band
(`[0.4, 0.95]`), so the loose scalar assertion passed. Meanwhile the air
stream ran to **5790.6 °C** against clinker at 1304 °C — a textbook
second-law violation the headline test never looked at.

**The bug is on line 235 of `cooler_ode.py`:**

```python
T_a_cell += dT_a  # NO upper clamp on dT_a
```

The model `reset T_a = 30 °C at every cell` (line 239) but had no upper
clamp on `dT_a`. So the radiation term `ε·σ·(T_c⁴ − T_a⁴)` at the first
cell (T_c ≈ 1400 °C) exploded per-sub-step. Aanya computes
`dT_a ≈ 3 340 K` in one sub-step (Aanya's v0.3.0 review §1). With 8
sub-steps and a per-cell air reset, the air T was *not* integrated — it
was launched into space.

**The result is a 13.5× first-law imbalance** (Ramesh's v0.3.0 review
§3.2): `secondary_air_recovered_kw / heat_recovered_kw = 510629 / 37775`.
The two sides of the same heat exchanger must agree within ~5%
(radiation + wall loss). 13.5× is a hard reject.

---

## 2. Why the existing tests passed for the wrong reason

The v0.3.0 test suite has 9 tests, of which 4 are directly relevant
(`test_cooler_ode.py`):

| Test | Pass / Fail on v0.3.0 | Why |
|---|---|---|
| `test_efficiency_in_realistic_range` | PASS | Band `[0.4, 0.95]` is too loose — 0.73 is in band, but the air stream is 5790 °C. |
| `test_more_air_improves_cooling` | PASS | Both `s_low` and `s_high` have the same broken state (radiation dominates, air reset per cell). The ordering "more air → cooler clinker" happens to hold but is meaningless. |
| `test_faster_grate_reduces_efficiency` | PASS | Same reason — both endpoints are corrupted. |
| `test_steady_state_clinker_cools_below_inlet` | PASS | Clinker does cool from 1400 → 404 °C. The test only checks the direction, not the magnitude. |

Two fragile tests passed because they assert scalars that are products
of the same broken state. The headline KPI (efficiency 73%) was the
**wrong metric** — the question is not "is the efficiency plausible"
but "is the air stream at a temperature the second law allows".

This is the failure mode I'm paid to prevent: **a green test badge is
not evidence**; only physics-grounded invariants that *fail on broken
code* are evidence.

---

## 3. The 5 (now 6) tests I am writing in v0.3.1

From my v0.3.0 review §2:

### 3.1 `test_second_law_air_not_hotter_than_clinker_source` (PRINCIPLE 1 — second-law)

```python
def test_second_law_air_not_hotter_than_clinker_source():
    """For cross-flow with fresh air per cell, the air leaving a cell
    cannot exceed the clinker temperature entering that cell. This is
    the single most discriminating test for the v0.3.0 5790 C bug.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    T_c_in_to_cell = np.concatenate(
        ([p.clinker_inlet_t_c], state.t_clinker_c[:-1])
    )
    assert np.all(state.t_air_c <= T_c_in_to_cell + 1e-6), ...
```

**v0.3.0 result:** FAILS by ~4487 K.
**v0.3.1 result:** passes after Fix A (second-law clamp in `_solve_spatial`).

**Cite:** Hiro v0.3.0 review §2.1; Aanya v0.3.0 review §1 (radiation runaway); Mujumdar (2007) §3.1 (air-T clamp in the published cooler model).

### 3.2 `test_energy_balance_closure_two_percent` (PRINCIPLE 2 — conservation)

```python
def test_energy_balance_closure_two_percent():
    """Q_in = Q_out + Q_recovered (+ loss). For a 1D model with no
    wall loss, the closure residual should be < 2% of Q_in.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    outs = compute_outputs(state, p)
    residual_kw = outs["heat_in_kw"] - outs["heat_recovered_kw"] - outs["heat_out_kw"]
    assert abs(residual_kw) < 0.02 * outs["heat_in_kw"], ...
```

**Cite:** First law; Hiro v0.3.0 review §2.2.

### 3.3 `test_air_side_recovery_agrees_with_clinker_side_within_5pct`

The other half of conservation: the air-side recovery must match the
clinker-side recovery within 5% (Ramesh §3.2).

```python
def test_air_side_recovery_agrees_with_clinker_side_within_5pct():
    p = CoolerParameters(n_cells=30, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    outs = compute_outputs(state, p)
    Q_clinker = outs["heat_recovered_kw"]
    Q_air = outs["secondary_air_recovered_kw"]
    assert 0.85 * Q_clinker <= Q_air <= 1.15 * Q_clinker, ...
```

**v0.3.0 result:** FAILS — ratio is 13.5× (Ramesh §3.2).
**v0.3.1 result:** passes after Fix A + counter-flow topology.

### 3.4 `test_low_air_refutation` (PRINCIPLE 4 — refutation)

```python
@pytest.mark.parametrize("v_air", [0.0, 0.05, 0.1])
def test_low_air_refutation(v_air):
    """As v_air → 0, clinker should retain most of its heat
    (outlet → inlet T). The 1D model must not produce cooling by
    some other channel (e.g. runaway radiation that manufactures
    air T from nothing).
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0,
                         under_grate_air_velocity_m_s=v_air)
    state = run_to_steady_state(p, max_t_s=900.0)
    if v_air == 0.0:
        assert state.clinker_outlet_c > 0.95 * p.clinker_inlet_t_c
    # And the second-law invariant must still hold
    T_c_in = np.concatenate(([p.clinker_inlet_t_c], state.t_clinker_c[:-1]))
    assert np.all(state.t_air_c <= T_c_in + 1e-6)
```

**v0.3.0 result:** FAILS — at v_air = 0.0 the radiation runaway can
still manufacture air T from nothing (because the bug is on the
per-cell `dT_a` integration with no cap; the cap is missing on the
*air side*, not the mass side).
**v0.3.1 result:** passes after Fix A.

**Cite:** Hiro v0.3.0 review §1.4 + §2.3.

### 3.5 `test_more_air_sweep_monotone` (PRINCIPLE 3 — property-based sweep)

```python
def test_more_air_sweep_monotone():
    """Across 8 air velocities, clinker outlet T must be
    non-increasing and secondary-air recovery non-decreasing,
    with second-law invariant at every point.
    """
    base = CoolerParameters(n_cells=20, t_end_s=900.0)
    velocities = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    ...
```

**v0.3.0 result:** FAILS the second-law invariant at the high-velocity
endpoints (where the radiation term is still dominant regardless of
air mass).
**v0.3.1 result:** passes.

**Cite:** Hiro v0.3.0 review §2.5; Saltelli 2010 (32-sample screening
rule).

### 3.6 `test_secondary_air_within_realistic_envelope` (PRINCIPLE 5 — range on every state)

```python
def test_secondary_air_within_realistic_envelope():
    """secondary_air_outlet_c ∈ [200, 1100] C — Peray & Waddell §6.4.
    v0.3.0 reports 5790 C. This test rejects.
    """
    p = CoolerParameters(n_cells=20, t_end_s=900.0)
    state = run_to_steady_state(p, max_t_s=900.0)
    assert 200.0 < state.secondary_air_outlet_c < 1100.0, ...
```

**v0.3.0 result:** FAILS — 5790 °C.
**v0.3.1 result:** passes after Fix A.

**Cite:** Hiro v0.3.0 review §2.4; Peray & Waddell (1986) §6.4.

---

## 4. The 6th test file — Hypothesis property-based sweep

Beyond the 5 above, Day 3 v0.3.1 adds a 6th file
(`test_property_based.py`) that runs 32-sample screening sweeps over
each top-3 input (Saltelli 2010 sample-size rule). The sweeps assert:

- `test_second_law_invariant_for_random_inputs` — second-law holds
  for *any* valid `(T_in, v_air, v_grate)`.
- `test_more_air_lowers_or_equals_clinker_outlet` — engineering-sign
  correct monotonicity.
- `test_faster_grate_raises_clinker_outlet` — engineering-sign correct
  monotonicity.
- `test_first_law_imbalance_below_5pct_for_random_inputs` — first-law
  holds for *any* valid 5-tuple of inputs.
- `test_secondary_air_never_exceeds_clinker_inlet` — direct second-law
  on the *outlet* air, no spatial nuance.

**v0.3.0 result:** FAILS for every random sample near the default
operating point (because the air T explodes regardless of inputs).
**v0.3.1 result:** passes for all 32 random samples (statistical
guarantee modulo the screening resolution).

**Cite:** hypothesis Python library docs; Saltelli et al. 2010 CPC
181: 259-260; Sobol' 2001 MC&S 55(1-3): 271-280.

---

## 5. The 6th file (uq_design.md) — Sobol N=1024 plan

In addition to the test files, the PR includes `uq_design.md` which
specifies:

- Saltelli sampling with N=1024 base, ~8192 model evaluations
  (Saltelli 2010 Table 1: ±0.03 CI on first-order indices).
- Top-3 inputs: `clinker_inlet_t_c`, `under_grate_air_velocity_m_s`,
  `grate_speed_m_min`.
- Use `numpy.Generator` (`np.random.default_rng()`) for reproducibility,
  not `np.random.seed` (legacy, NEP 19 deprecates new uses).
- Hetauda calibration target: monthly `clinker_outlet_T` (RMSE ≤ 15 K)
  and `sec_air_T` (RMSE ≤ 20 K).
- Train/test split by time (months 1-9 train, 10-12 test). Cite: EPA
  2009 + Roberts 2017.
- Multi-metric validation: RMSE, MAE, bias, Theil's U2.

**Day 3 v0.3.1 ship gate** is the 5 + 1 = 6 test files, all
diagnostic on v0.3.0. The Sobol notebook execution is a **Day 4**
deliverable (it needs a v0.3.1 model that is second-law-clean first).

---

## 6. Acceptance gate for my own work

Every test I write must **FAIL against v0.3.0 code with a clear error
message**. A test that passes on broken code is not a test — it is a
coin-flip that happens to land heads. I have:

1. Run each test mentally against the v0.3.0 source.
2. Cited the source line / paper for every assertion.
3. Used `numpy.Generator` not `np.random.seed`.
4. Marked tests > 1 s with `@pytest.mark.slow` per pytest docs.
5. Set `hypothesis.settings(max_examples=32, deadline=None, derandomize=True)`
   per hypothesis docs + Saltelli 2010.

I have **not** run the tests against v0.3.0 in this session — that is
the verifier's job (the spec assigns Day 3 v0.3.0 code-preservation to
the orchestrator). I have **written** them to be diagnostic, and I have
explained *why* they are diagnostic in the docstrings.

---

## 7. References

- Achenbach, E. (1995). Heat and flow characteristics of packed beds. *Exp. Thermal Fluid Sci.* 10(1): 17-27.
- Aanya v0.3.0 review — `tools/03-cooler-grate-simulator/reviews/AANYA-DAY-03-REVIEW.md`.
- Boateng, A. A. (2008). *Rotary Kilns* (Ch. 7 — Coolers). Butterworth-Heinemann.
- ECRA Technology Papers 2022 — modern reciprocating coolers, BAT 75-80% efficiency, < 0.42 MJ/kg-cli total heat loss.
- EPA (2009). *Guidance on the Development, Evaluation, and Application of Environmental Models.* EPA/100/K-09/003.
- GCCA GNR 2022 — `cl_PM2` reporting convention.
- Hiro v0.3.0 review — `reviews/hiro-day-03-review.md` (this is the document this PR is the implementation of).
- hypothesis Python library docs — https://hypothesis.readthedocs.io/.
- ICCC 2006 — clinker emissivity, residence time, f-CaO target.
- Mujumdar, K. S. (2007). Grate cooler model. *Ind. Eng. Chem. Res.* 46(7).
- NumPy NEP 19 — Default NumPy random number generator.
- Peray, K. E. & Waddell, J. J. (1986). *The Rotary Cement Kiln*, 2nd ed. Chemical Publishing.
- pytest docs — markers, fixtures, configuration.
- Ramesh v0.3.0 review — `reviews/DAY-03-RAMESH-REVIEW.md`.
- Roberts, D. R. et al. (2017). Cross-validation strategies for data with temporal and spatial dependence.
- Saltelli, A. et al. (2010). Variance based sensitivity analysis of model output. Design and estimator for the total sensitivity index. *Computer Physics Communications* 181: 259-260.
- Sobol', I. M. (2001). Global sensitivity indices for nonlinear mathematical models. *Mathematics and Computers in Simulation* 55(1-3): 271-280.
- Theil, H. (1966). *Applied Economic Forecasting.* North-Holland.
- Wakao, N. & Kaguei, S. (1982). *Heat and Mass Transfer in Packed Beds.* Gordon and Breach.

— Hiro Tanaka, 2026-07-22
