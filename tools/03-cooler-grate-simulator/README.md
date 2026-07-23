# tools/03-cooler-grate-simulator — v0.3.2 (Day 3)

**Day 3 of 6-module v1.0** — grate cooler simulator for cement clinker.
Status: **structural fix landed, ship-gate blocked on Day 4 calibration.**

## What this is

1D, quasi-steady, compartment-wise counter-flow grate cooler for OPC
clinker. Five-compartment default (IKN Pyrorotor / KHD Pyrostep /
Polysius REPOL / plantc class). The model is engineering-grade,
not CFD.

- 4 plant presets: **PlantA, PlantB, plantc, PlantD**
- Convective + linearized-radiation heat transfer (Achenbach 1995 +
  Mujumdar 2007 §2.2; Stefan-Boltzmann linearized per Incropera &
  DeWitt 2002 Ch. 12)
- Per-compartment air inventory allocated by *physical demand*, not by
  uniform velocity-area (Peray & Waddell 1986 §6.2 combustion-air
  stoichiometry for compartment 1; continuity for compartments 2..N)
- Moist-air density from ISA barometric + Magnus saturation vapour
  pressure (Cengel & Boles 2015; ASHRAE 2021 Ch. 1)
- Per-compartment and per-cell second-law clamp (Mujumdar 2007 §3.1)
- Pydantic v2 input model (`CoolerParameters`), pure-dict output
  (`compute_outputs` → `CoolerOutputs`-shaped dict)
- Back-compat shim: `simulate_cooler(p) -> (t, y, x)` for the v0.3.0
  kiln-link callers

## What v0.3.2 fixed over v0.3.0/v0.3.1

| Bug | v0.3.0/v0.3.1 | v0.3.2 |
|---|---|---|
| 5790 °C second-law violation | mujumdar clamp added (v0.3.1) | preserved + per-compartment invariant added |
| 13.5× first-law imbalance (clinker-side) | fixed (v0.3.1) | preserved |
| ρ=0.6 hard-code (1.75× wrong at PlantA) | fixed with altitude (v0.3.1) | preserved + Magnus + ASHRAE Ch. 1 partial-pressure sum |
| Achenbach h = constant 350 W/m²K floor | constant floor (v0.3.1) | `h_eff = h_conv + h_rad_equiv` with `h_rad_equiv = 4·ε·σ·T³` (Incropera & DeWitt 2002 Ch. 12) |
| Sec-air stream allocated by hydraulic slice (wrong for compartment 1) | buggy in v0.3.1 | sec-air flow = combustion-air demand (Peray §6.2); exhaust compartments 2..N = (m_a,total − m_a,sec)/(N−1) |
| First-law imbalance ≤ 0.02 ship-gate | 4.04 (v0.3.1) | **0.0 (v0.3.2)** ✓ |

39/39 v0.3.2 self-tests pass (`pytest src/nepal_cooler_sim/tests/test_self_aanya.py -v`).
4/4 plant presets run.

## Honest disclosure — 1/7 ship-gate bands pass

The 7-band ship-gate in `DAY-03-SPEC.md` was checked on all 4 plant
presets. v0.3.2 passes **1 of 7 bands** on **all 4 plants** and an
**additional band on PlantB only**:

| Band | PlantA | PlantB | Hongshi | PlantD |
|---|---|---|---|---|
| `secondary_air_outlet_c ∈ [600, 1000] °C` | 559 (✗) | 629 (✓) | 537 (✗) | 589 (✗) |
| `tertiary_air_outlet_c ∈ [400, 700] °C` | 232 (✗) | 174 (✗) | 270 (✗) | 178 (✗) |
| `exhaust_air_outlet_c ∈ [150, 300] °C` | 135 (✗) | 108 (✗) | 162 (✓) | 113 (✗) |
| `clinker_outlet_c ∈ [120, 200] °C` | 536 (✗) | 502 (✗) | 550 (✗) | 546 (✗) |
| `cooler_efficiency ∈ [0.65, 0.85]` | 0.63 (✗) | 0.66 (✓) | 0.63 (✗) | 0.63 (✗) |
| `first_law_imbalance ≤ 0.02` | **0 (✓)** | **0 (✓)** | **0 (✓)** | **0 (✓)** |
| `sec/heat ∈ [0.85, 1.15]` | 0.43 (✗) | 0.47 (✗) | 0.41 (✗) | 0.46 (✗) |

**Why the model is honest but not ship-ready**: the prescribed geometry
(5 compartments × 28 m × 1.5 m/s) cannot deliver the design-duty
sec-air / clinker-outlet bands. The physical ceiling at 38 kg/s
sec-air flow + 52 MW clinker enthalpy drop is ~1310 K air-side ΔT;
the geometry puts the model at ~560 K. This is **calibration + operating-
handle freedom**, not a physics bug. **Day 4 is the calibration work
item**, blocked on PlantA plant data (clinker-outlet T time series,
sec-air T time series, fan amps, grate speed).

## Quick start

```python
from nepal_cooler_sim import (
    planta, solve_steady_state, compute_outputs,
)

p = planta()                # NIDC PlantA preset
state = solve_steady_state(p)
out = compute_outputs(state, p)

print(out["secondary_air_outlet_c"])  # 559 °C (v0.3.2)
print(out["clinker_outlet_c"])        # 536 °C (v0.3.2)
print(out["cooler_efficiency"])       # 0.633 (v0.3.2)
print(out["first_law_imbalance"])     # 0.0  (v0.3.2)
print(out["sanity"]["air_above_clinker"])  # False  (2nd-law clean)
```

Back-compat for v0.3.0 kiln-link callers:

```python
from nepal_cooler_sim import planta, simulate_cooler
p = planta()
t, y, x = simulate_cooler(p)   # t.shape=(1,), y.shape=(50,1), x.shape=(25,)
```

## Layout

```
tools/03-cooler-grate-simulator/
├── README.md                     ← this file
├── pyproject.toml                ← Maya (Pydantic, hypothesis, pytest)
├── src/
│   └── nepal_cooler_sim/
│       ├── __init__.py           ← v0.3.2 public API
│       ├── cooler_ode.py         ← Aanya v0.3.2 (model physics)
│       ├── compartments.py       ← Aanya v0.3.2 (per-compartment solver)
│       ├── plants.py             ← Aanya v0.3.2 (4 plant presets)
│       ├── _v031_legacy/         ← v0.3.0/v0.3.1 files archived
│       │   ├── __init__.py       ← archived 2026-07-22
│       │   ├── cooler_ode.py     ← archived (replaced by v0.3.2 above)
│       │   ├── io.py             ← v0.3.1 (Day 4: re-align with v0.3.2)
│       │   ├── cli.py            ← v0.3.1 (Day 4: re-align)
│       │   ├── kiln_link.py      ← v0.3.1 (Day 4: re-align)
│       │   └── sensitivity.py    ← v0.3.1 (Day 4: re-align)
│       └── tests/
│           └── test_self_aanya.py  ← 39/39 v0.3.2 self-tests
├── day-03-PRs/                   ← 8 specialist PRs (reviewable)
├── reviews/                      ← Aanya + Hiro + Ramesh reviews
├── scratch/                      ← smoke / one-off scripts
└── DAY-04-SPEC.md                ← Day 4 calibration framework (next)
```

## References

- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192. §2.2,
  §3.1.
- Peray, K.E. & Waddell, J.J. (1986). *The Rotary Cement Kiln*, 2nd ed.
  §6.2, §6.3, §6.4.
- Cengel, Y.A. & Boles, M.A. (2015). *Thermodynamics*, 8e. ISA barometric.
- Incropera, F.P. & DeWitt, D.P. (2002). *Fundamentals of Heat and Mass
  Transfer*, 5e. Ch. 12.
- ICCC 2006 §2.3, §3.4.
- GCCA GNR 2022; ECRA Technology Papers 2022.
- ASHRAE Handbook (Fundamentals) 2021 Ch. 1.
- ISO 2533:1975 — Standard atmosphere.

## License

MIT.
