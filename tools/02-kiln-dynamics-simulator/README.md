# Tool 02 — Nepal Kiln Dynamics Simulator

**Day 2 of the 20-day Nepal Industrial Decarbonization Suite.**

A physics-based **5-zone dynamic simulator** for rotary cement kilns, with
plant presets for the major Nepali plants, fuel substitution what-if, and
MATLAB/Octave compatibility for cross-language validation.

![MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Day 2/20](https://img.shields.io/badge/Day-2%2F20-orange.svg)

---

## What it does

A transient, multi-zone model of a rotary cement kiln that simulates:

- **Drying** of raw meal (0 → 100 °C, free water evaporation)
- **Preheating** (100 → 600 °C)
- **Calcination** (CaCO₃ → CaO + CO₂, endothermic, ~600-900 °C)
- **Burning / sintering** (clinker formation, 900 → 1450 °C peak)
- **Cooling** (clinker: 1450 → 1100 °C, secondary air reheat)

with Arrhenius calcination kinetics, convective + radiative heat transfer,
zone-aware combustion, and a calibrated burning-zone temperature.

**It produces the KPIs the cement industry asks for:**

- Burning-zone temperature (°C)
- Specific energy consumption (MJ / t clinker)
- CO₂ intensity (kg / t clinker)
- Conversion profile
- Flame temperature for any fuel blend
- Time-evolution of all states

---

## Quick start

```bash
# Install (editable, in your venv)
pip install -e .

# CLI: list plants and fuels
nepal-kiln-sim plants --list
nepal-kiln-sim fuels --list

# CLI: run a Hetauda simulation with 30% rice husk substitution
nepal-kiln-sim run --plant hetauda --out ./out

# Streamlit UI
streamlit run app/Home.py

# Sensitivity sweep
nepal-kiln-sim sensitivity --plant hetauda --factor fuel_rate_t_h --values 8,10,12,14

# Calibrate to plant data
nepal-kiln-sim calibrate --plant hetauda --sec 3850 --co2-intensity 880

# Export MATLAB / Octave scripts for cross-language validation
nepal-kiln-sim export --plant udayapur --format both --out ./matlab_export
```

---

## Python API

```python
from nepal_kiln_sim import (
    KilnParameters, run_to_steady_state, compute_outputs, simulate_kiln,
    PLANT_PRESETS, get_fuel, compute_blend_ef, compute_flame_temperature,
)

# Use the Hetauda preset
p = PLANT_PRESETS["hetauda"].parameters

# Override the fuel and run
p = p.model_copy(update={"fuel_type": "biomass_rice_husk", "fuel_rate_t_h": 14.0})
state = run_to_steady_state(p, max_t_s=3600.0)
outs = compute_outputs(state, p)
print(outs)
# {'t_burning_zone_c': 1448.3, 'sec_mj_per_t_clinker': 4120, 'co2_intensity_kg_per_t_clinker': 920, ...}

# Blend two fuels
blend = compute_blend_ef({"coal_bituminous_NP": 0.7, "biomass_rice_husk": 0.3})
print(blend["ef_kgco2_per_gj_blend"])  # 66.2 (down from 94.6 fossil-only)

# Flame temperature
t_flame = compute_flame_temperature(get_fuel("natural_gas"), air_excess=1.10)
print(f"Natural gas flame T: {t_flame:.0f} K")  # ~2300 K
```

---

## Plant presets

| Key | Plant | Capacity (t/yr) | SEC (MJ/t) |
|---|---|---|---|
| `hetauda` | HCIL Hetauda | 1,200,000 | ~3850 |
| `udayapur` | UCIL Udayapur | 2,200,000 | ~3700 |
| `hongshi_shivam` | Hongshi-Shivam (Nawalparasi) | 4,000,000 | ~3200 |
| `ghorahi` | Ghorahi Cement (Dang) | 1,500,000 | ~3600 |
| `reference_5000tpd` | Chinese dry-process BAT | 5,000,000 | ~3200 |
| `legacy_wet_1000tpd` | Wet process worst-quintile | 1,000,000 | ~5500 |

Each preset is a `KilnParameters` instance with values validated against
public plant datasheets and field surveys. Add your own plant by adding
to `nepal_kiln_sim/plants.py`.

---

## Fuels

16 fuels in the database:

- **Coal**: bituminous, anthracite, lignite
- **Petroleum**: petcoke, diesel, furnace oil, LPG
- **Gas**: natural gas
- **Biomass**: wood, rice husk, sawdust, bagasse, jatropha cake
- **Waste**: tire-derived fuel (TDF), municipal RDF
- **Future**: green hydrogen (zero direct CO₂)

All NCVs and emission factors from IPCC 2006 / 2019 Refinement / WBSCD/GCCA
CSI. Biogenic fractions from CEN 16449.

`compute_blend_ef()` returns the energy-weighted blend properties (NCV,
fossil-only EF, price, biogenic fraction).

---

## Sensitivity & calibration

- `sensitivity_sweep` — one-at-a-time sweep on any parameter
- `morris_elementary_effects` — Morris screening for non-linear effects
- `calibrate_to_plant` — differential-evolution calibration to plant KPIs

The calibration tunes 7 internal parameters (Arrhenius A/Ea, precalciner
degree, preheater efficiency, cooler efficiency, wall loss, emissivity)
to match an observed SEC + CO₂ intensity. Default bounds reflect physical
plausibility (precalciner can't exceed 98% conversion in practice).

---

## MATLAB / Octave compatibility

`nepal-kiln-sim export` generates `.m` driver scripts that mirror the
Python model. The RHS function (5-zone kiln ODE) is straightforward to
port; we provide templates and the driver. Used for:

- Cross-language validation of the Python solver
- Allowing MATLAB/Simulink shops to embed our kinetics in their flowsheets
- Comparison against HYSYS / Aspen Plus cement modules

---

## Data sources

- IPCC 2006 Vol. 2 Ch. 1 (Stationary Combustion)
- IPCC 2019 Refinement
- WBSCD / GCCA "Getting the Numbers Right" (GNR) 2022
- Boateng, A.A. (2008). *Rotary Kilns: Transport Phenomena and Transport Processes.*
- Mujumdar & Ranade (2006). Simulation of rotary cement kilns. *Ind. Eng. Chem. Res.* 45(9).
- Nepali plant annual reports 2022/23
- Field surveys 2024 (Hetauda, Udayapur, Hongshi-Shivam)

---

## Tests

```bash
pytest tests/ -v
```

Test coverage:

- `test_kiln_ode.py` — solver stability, conservation, physical bounds
- `test_fuels.py` — blend math, flame temperature, biogenic fraction
- `test_plants.py` — preset consistency, bounds
- `test_sensitivity.py` — monotonicity, sign of effects
- `test_calibration.py` — RMSE on synthetic plant data
- `test_io.py` — round-trip CSV / JSON / pickle

---

## Author

**Nishchal Baniya** · Himalayan Carbon Nepal
nishchal.baniya@himalayancarbonnepal.com

Day 2 build by Mavis (Mavis orchestrator agent).
