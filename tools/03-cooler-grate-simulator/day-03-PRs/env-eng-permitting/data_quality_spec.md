# Data Quality Specification — Cooler MRV (Day 3 v0.3.1)

> **Authored by Dr. Kabita Thapa, env-eng-permitting, 2026-07-22.**
> **Audience:** the ISO 14064-3:2019 / Verra / Gold Standard / EU CBAM verifier, and Hiro for UQ propagation.
> **Style:** "Tier X, year Y, source Z, uncertainty W." Never "I assumed." If a number is uncertain, the uncertainty is the answer.

This document specifies the **per-field data quality** for every `compute_outputs` field of the cooler module, mapped to (Tier, year, source, 1-σ). The Tier vocabulary follows the **IPCC 2006 Vol.1 Ch.3** tier convention, extended with `measured` for plant-DCS-sourced values (the convention used in ISO 14064-1:2018 §6.5 and GHG Protocol Corporate Standard §5.2).

---

## 1. Tier vocabulary

| Tier | Meaning | EF source | Typical σ (1σ) | Verifier treatment |
|---|---|---|---|---|
| **Tier 1** | Default / global | IPCC 2006 / 2019 Refinement default, no plant modification | ±10–50 % | Lowest credit weighting under Verra VM0009 v3.0 §5.3.3 |
| **Tier 2** | Country / industry / plant-class | Country-specific inventory, ICCC industry default, plant-class sieve | ±10–20 % | Mid credit weighting |
| **Tier 3** | Plant-specific engineering estimate | Plant engineering study, vendor data, un-instrumented estimate | ±20–50 % | Lowest credit weighting; may trigger VCS Program Guide §3.4 downgrade |
| **measured** | Plant DCS / instrument direct read | Plant data historian, instrumented sensor, calibrated laboratory | ±1–5 % (instrument-dependent) | Highest credit weighting; preferred under ISO 14064-1:2018 §6.5 |

**Note for the verifier:** I am using the term `measured` (rather than `Tier 0` or `Tier 4`) to align with GHG Protocol Corporate Standard §5.2 ("measured data" as a distinct category from default EFs). The IPCC tiering (1/2/3) is reserved for *emission factors*; *activity data* uses a different vocabulary. The cooler module mixes both: EFs go to `Tier X`, instrument reads go to `measured`.

---

## 2. Per-field specification (cool module inputs)

| Field | Tier | Source (cite) | Year | 1-σ | Verifier rationale |
|---|---|---|---|---|---|
| `clinker_inlet_t_c` | **measured** | ICCC 2006 §2.2 (kiln-discharge pyrometer); plant DCS | plant-year | **±25 K** (1σ) | Pyrometer uncertainty ±20 K at 1400 °C; plus ±5 K for placement; ISO 14064-1:2018 §6.5 |
| `clinker_outlet_t_c` (validation target) | **measured** | ICCC 2006 §3.4 (IR spot pyrometer, free-lime zone); plant DCS | plant-year | **±15 K** (1σ) | IR spot pyrometer ±10 K; placement ±5 K; ISO 14064-1:2018 §6.5 |
| `secondary_air_outlet_c` | **measured** | Peray & Waddell 1986 §6.4; Type-K TC at kiln-burner air duct | plant-year | **±20 K at 800 °C** (1σ) | Type-K intrinsic ±10 K; placement / radiation shielding ±10 K |
| `tertiary_air_outlet_c` | **measured** | Peray & Waddell 1986 §6.4; Type-K TC in calciner air line | plant-year | **±20 K at 600 °C** (1σ) | As above |
| `exhaust_air_outlet_c` | **measured** | Peray & Waddell 1986 §6.4; TC in cooler exhaust plenum | plant-year | **±10 K at 200 °C** (1σ) | Type-K at lower T; smaller intrinsic error |
| `under_grate_air_temp_c` | **measured** | Plant met station / RTD in plenum | plant-year | **±2 K** (1σ) | PT100 RTD typical ±0.5 K + 1.5 K placement |
| `under_grate_air_velocity_m_s` | **measured** (preferred) | Plant DCS (annubar / flow nozzle), **or** Tier 2 derived from fan curve + ΔP (Peray & Waddell 1986 §6.4) | plant-year | **±10 %** (1σ) measured, **±20 %** (1σ) Tier 2 | If plant has flow instrumentation, use it; otherwise fall back to fan-curve-derived |
| `clinker_throughput_t_h` | **measured** | Plant DCS, weighfeeder | plant-year | **±2 %** (1σ) per ISA 1975 weighfeeder | Belt weighfeeder typical ±0.5 % of span; placement/calibration ±1.5 % |
| `clinker_diameter_m` | **Tier 2** | ICCC 2006 §2.4 (sieve analysis); plant-specific sieve if available | plant-year | **±20 %** (1σ) | 1-σ on a log-normal pellet-size distribution |
| `cp_clinker_kj_kg_k` | **Tier 1** | Boateng 2008 Ch.7 (default 1.05 kJ/(kg·K)); IPCC 2006 Vol.3 Ch.2 Annex 2.2.1 | 2008 (Boateng) | **±5 %** (1σ) | Literature default unless plant calorimetry; ±5 % covers composition spread |
| `rho_clinker_kg_m3` | **Tier 2** | Peray & Waddell 1986 §6.1 (loose-packed 1500 kg/m³); plant-specific tap-density if available | 1986 / plant-year | **±10 %** (1σ) | Bulk density varies with pellet size distribution and packing |
| `emissivity` | **Tier 1** | ICCC 2006 §2.3 (clinker emissivity 0.8–0.9; default 0.85) | 2006 | **±10 %** (1σ) | Hot-clinker pellets are near-black; ±10 % covers surface-roughness / oxidation spread |
| `secondary_air_mass_flow_kg_s` | **measured** (preferred) | Kiln-cooler air balance, **or** Tier 2 from coal rate × 6.67 stoich factor (Peray & Waddell 1986 §6.2) | plant-year | **±5 %** (1σ) measured | Stoichiometric derivation: 1.4 kg O₂ / kg coal / 0.21 = 6.67 |
| `altitude_m` | **measured** | Plant met station / GPS | plant-year | **±10 m** (1σ) | Affects air density ±1.2 % at 1400 m |
| `ambient_t_c` | **measured** | Plant met station | plant-year | **±1 K** (1σ) | RTD or calibrated met sensor |
| `ambient_rh` | **measured** | Plant met station | plant-year | **±5 % RH** (1σ) | Capacitive RH sensor typical ±3 %; placement ±2 % |
| `grate_speed_m_min` | **measured** | Plant DCS (VFD Hz → m/min) | plant-year | **±2 %** (1σ) | VFD-controlled, encoder-feedback |
| `n_compartments` | **Tier 2** | Plant engineering (compartment count is design-fixed, not measured) | plant-year | **n/a** (integer) | Categorical; no uncertainty |

---

## 3. Per-field specification (cool module outputs)

| Field | Tier | Source (cite) | Year | 1-σ | Verifier rationale |
|---|---|---|---|---|---|
| `clinker_outlet_c` (model prediction) | **Tier 2** (engineering-grade 1D) | Aanya's `cooler_ode.py` model physics; Mujumdar 2007 | model-year | **±30 K** (1σ) propagated | Physics model; ±30 K covers numerical + parameter uncertainty combined; **note:** Aanya/Ramesh are debating model fidelity — Tier 2 today, Tier 1 if the model passes the Day 3 fragility tests with a calibration against PlantA pyrometer data |
| `secondary_air_outlet_c` (model prediction) | **Tier 2** | Aanya's model | model-year | **±50 K** (1σ) | Larger uncertainty because of compartment-flow modelling choice (counter-flow vs cross-flow); Hiro's UQ run will tighten this post-Day-3 |
| `cooler_efficiency` | **derived (Tier 2)** | Ratio of `heat_recovered_kw` to `heat_in_kw`; numerator and denominator both Tier 2 | model-year | **±3 % absolute** (1σ) propagated | Energy-balance ratio; combined uncertainty via root-sum-square |
| `heat_recovered_kw` | **derived (Tier 2)** | Air-side heat uptake; depends on `secondary_air_mass_flow_kg_s` (measured) and `secondary_air_outlet_c` (Tier 2) | model-year | **±5 %** (1σ) | Propagation: 5 % from mass × 5 % from ΔT (uncorrelated) → ~7 %; reduced to 5 % with cross-correlation |
| `clinker_quench_rate_k_per_min` (Ramesh's Patch E) | **derived (Tier 2)** | dT/dt in the 1300 → 900 °C window; Ramesh's spec | model-year | **±10 %** (1σ) | Grate speed ±2 % × outlet T ±30 K → 4 %+ propagation; ±10 % is conservative |
| `secondary_air_stoich_ratio` (Ramesh's Patch E) | **derived (measured)** | `secondary_air_mass_flow_kg_s` (measured) / (coal_rate × 6.67) | plant-year | **±5 %** (1σ) | Numerator measured ±5 %; denominator coal rate ±2 %; RSS ~5.4 % |
| `mj_per_t_cli_recovered` (Ramesh's Patch E) | **derived (Tier 2)** | `heat_recovered_kw × 3.6 / clinker_throughput_t_h` | model-year | **±6 %** (1σ) | RSS of numerator (5 %) and denominator (2 %) |
| `residence_time_s` (Ramesh's Patch E) | **derived (measured)** | `L / v_grate` | plant-year | **±2 %** (1σ) | Both `L` (engineering) and `v_grate` (measured) tight |
| `first_law_imbalance` | **derived** | Energy balance residual; should be ≤ 2 % | model-year | **n/a** (diagnostic) | This is a sanity check, not a KPI |

---

## 4. Emission factors used in the cooler-MRV chain (for CBAM)

The cooler module is downstream of the kiln calcination step. The cooler *itself* is not a direct source of CO₂; it is a heat-recovery device. However, for the **EU CBAM 2023/1773** default-value chain, the relevant CO₂ is upstream in the kiln.

| Source | Tier | EF | Source (cite) | Year | 1-σ | Verifier note |
|---|---|---|---|---|---|---|
| Clinker calcination (stoichiometric) | **Tier 1** | 0.527 t CO₂/t clinker | **IPCC 2006 Vol.3 Ch.2 §2.3.2** | 2006 | ±5 % | Stoichiometric; uncertainty covers CaO-content variation (0.60–0.67 t CaO/t cli) |
| Calcination correction (CKD / bypass) | **Tier 2** | -1 to -2 % downward | **IPCC 2019 Refinement §2.3.1** | 2019 | ±0.5 % | Plant-specific; Nepali precalciner kilns typically 1 % CKD loss |
| CBAM direct default for CN 2523 10 00 | **Tier 1 (default)** | **0.642 t CO₂/t clinker** (Caveat: this is the figure in my training data for CBAM 2023/1773 Annex IV §4, but I have not re-verified the row) | **EU 2023/1773 Annex IV §4** | 2023 | n/a (default) | **Action: @James to re-confirm the Annex IV row before PDD commit** |
| CBAM cement (not clinker) default | **Tier 1 (default)** | 0.793 t CO₂/tonne (this is the "cement" default, not clinker) | **EU 2023/1773 Annex IV §4** | 2023 | n/a (default) | Differentiate clinker (CN 2523 10 00) from cement (CN 2523 29) |
| Coal combustion (CO₂ from kiln burner) | **Tier 2** | 2.42 t CO₂/t coal (Nepal mixed coal) | **IPCC 2006 Vol.2 Ch.1 §1.2** (default coal EF 2.42 t CO₂/t), 2019 Refinement for mixed coal | 2006 / 2019 | ±5 % | Plant-specific if coal CV is logged; otherwise default |
| Electricity (Nepal grid) | **Tier 2** | ~0.05 t CO₂/MWh (Nepal grid, hydro-dominated) | **CEA / Nepal Electricity Authority 2022** | 2022 | ±20 % | Nepal grid is ~99 % hydro; small embedded thermal backup |

---

## 5. Data-quality gaps (Day 3 PR follow-up)

Items below are **NOT in this Day 3 PR** but are flagged for Day 12 (PDD) and Day 19 (audit-ready docs):

1. **Gap-fill policy** — when the DCS drops a reading, what is the substitution rule? Out of scope Day 3; Hiro owns the UQ layer.
2. **Change-control log** — who changed what when. Out of scope Day 3; Maya's `io.py` is the foundation.
3. **Plant-specific Tier 2 EFs** for the PlantA / PlantB / plantc / PlantD presets. Day 3 ships *literature defaults* (Tier 1); Day 12 ships *plant-specific Tier 2* where the operator has data.
4. **CBAM default-value confirmation** — the 0.642 t CO₂/t clinker figure for CN 2523 10 00 is cited as Annex IV §4 but I have not re-verified the row. **Action: @James re-confirms.**

---

## 6. References (clauses cited)

- ISO 14064-1:2018 §6.5.
- GHG Protocol Corporate Standard (Revised Edition) §5.2.
- IPCC 2006 Vol.1 Ch.3 (tier convention).
- IPCC 2006 Vol.2 Ch.1 §1.2 (coal combustion EF).
- IPCC 2006 Vol.3 Ch.2 §2.3.2 (cement calcination EF 0.527 t CO₂/t cli, Tier 1).
- IPCC 2019 Refinement §2.3.1 (correction for non-100% calcination).
- Verra VM0009 v3.0 §5.3.2, §5.3.3, §5.4.
- Verra VCS Program Guide v4.5 §3.4, §3.5.
- Gold Standard TPDDTEC v3.1 §4.2.
- EU CBAM Regulation 2023/956 Article 3, Article 7.
- EU CBAM Implementing Reg 2023/1773 Annex IV §4 (defaults; row 2523 10 00).
- Nepal Environment Protection Act 2019 §16.
- Nepal Industrial Emissions Rules 2020.
- ICCC 2006 §2.2, §2.3, §2.4, §3.4.
- Boateng 2008 Ch.7.
- Peray & Waddell 1986 §6.1, §6.2, §6.4.
- Mujumdar 2007.
- ISA 1975 (weighfeeder standards, RP 31.1 belt-feeder accuracy).

— Kabita, 2026-07-22, Day 3 v0.3.1.
