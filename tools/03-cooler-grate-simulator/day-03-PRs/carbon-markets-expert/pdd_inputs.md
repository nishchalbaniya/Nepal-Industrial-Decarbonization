# PDD Inputs from the Cooler Module — Verra VM0009 v3.0

> **Author:** James Okafor, Carbon Markets Specialist
> **Date:** 2026-07-22
> **Purpose:** Define exactly what the cooler module must emit so a Verra VM0009 v3.0 validator accepts the kiln PDD. Cite the methodology, cite the monitoring-plan requirements, and document the JSON schema.

---

## 1. What the Verra validator needs (and what they will reject)

A Verra validator under VM0009 v3.0 reads the **kiln PDD**, not the cooler module directly. The cooler module is invoked by `kiln_link.py` to feed the kiln baseline equation. The validator's job, for the cooler slice, is to confirm:

1. The cooler monitoring fields are **measured**, not modeled (VM0009 v3.0 §6.2).
2. The cooler fields are **within physical envelopes** (second-law invariant, mass-flow continuity, energy balance closure).
3. The cooler data has **QA/QC** (calibration records, instrument uncertainty, custodian).
4. The **additionality story** (in the kiln PDD) is consistent with the cooler's BAT position.

> **The Day 3 cooler module's job is to provide fields (a) with verifiability metadata (b) (c) (d) and a JSON schema that the validator's auto-checker can read.**

---

## 2. Field-level requirements

Every field the cooler emits to the PDD is grouped below by PDD section. The full JSON schema is in `pdd_json_schema.json`.

### 2.1 Project description (PDD §A.1–A.4)

| Field | Type | Unit | Frequency | Source | Citation |
|---|---|---|---|---|---|
| `plant_name` | string | — | once | operator input | Verra VCS Program Guide v4.5 §3.1 |
| `plant_location.latitude` | float | degrees | once | operator input | Verra VCS Program Guide v4.5 §3.1 |
| `plant_location.longitude` | float | degrees | once | operator input | Verra VCS Program Guide v4.5 §3.1 |
| `plant_location.altitude_m` | float | m | once | operator input (Hetauda: 1400 m) | Cengel & Boles 2015 (ISA barometric) |
| `clinker_capacity_tpd` | float | t/day | once | operator input (Hetauda: ~3 100 tpd for the 130 t/h line) | Verra VCS Program Guide v4.5 §3.1 |
| `cooler_technology` | enum | — | once | "grate" / "rotary" / "planetary" | Verra VM0009 v3.0 §A.4 |
| `cooler_n_compartments` | int | — | once | operator input (default 5) | Peray & Waddell 1986 §6.4 |
| `cooler_manufacturer` | string | — | once | IKN / KHD / Polysius / other | Verra VM0009 v3.0 §A.4 |

### 2.2 Baseline determination (PDD §B.1–B.5)

| Field | Type | Unit | Frequency | Source | Citation |
|---|---|---|---|---|---|
| `baseline_cooler_efficiency` | float | fraction | once at PDD submission | GCCA GNR 2022 regional average or plant-specific historical (Nepali plants: 0.65–0.72 typical, 0.75–0.80 BAT) | VM0009 v3.0 §5.2 |
| `baseline_secondary_air_outlet_c` | float | °C | historical (3-yr average from plant logs) | operator DCS export | VM0009 v3.0 §5.3 |
| `baseline_secondary_air_mass_flow_kg_s` | float | kg/s | historical (3-yr average) | operator DCS export | VM0009 v3.0 §5.3 |
| `baseline_clinker_outlet_c` | float | °C | historical | operator DCS export | VM0009 v3.0 §5.3 |
| `baseline_coal_flow_kg_s` | float | kg/s | historical | operator DCS export | VM0009 v3.0 §5.3 |

> **Important:** the baseline fields are HISTORICAL (before the project), not modeled. The cooler module's job for the baseline is to provide a parser that reads the operator's historical DCS export and emits the same JSON shape as the project fields, so the validator's diff tool can compare apples-to-apples.

### 2.3 Project scenario (PDD §C.1–C.5)

| Field | Type | Unit | Frequency | Source | Citation |
|---|---|---|---|---|---|
| `project_cooler_efficiency` | float | fraction | daily computed, monthly reported | cooler module `compute_outputs` | ECRA 2022; GCCA GNR 2022 |
| `project_secondary_air_outlet_c` | float | °C | continuous (1-min average, 1-h logged) | cooler module `state.secondary_air_outlet_c` | Peray & Waddell 1986 §6.4 |
| `project_secondary_air_outlet_k` | float | K | continuous | `state.secondary_air_outlet_c + 273.15` (kiln model takes Kelvin) | Verra VM0009 v3.0 §5.3 |
| `project_secondary_air_mass_flow_kg_s` | float | kg/s | continuous | cooler module `parameters.secondary_air_mass_flow_kg_s` | Peray & Waddell 1986 §6.2 |
| `project_tertiary_air_outlet_c` | float | °C | continuous (compartments 2..N-1 weighted-mean) | cooler module `state.tertiary_air_outlet_c` | Peray & Waddell 1986 §6.4 |
| `project_exhaust_air_outlet_c` | float | °C | continuous (compartment N) | cooler module `state.exhaust_air_outlet_c` | Peray & Waddell 1986 §6.4 |
| `project_clinker_outlet_c` | float | °C | continuous | cooler module `state.clinker_outlet_c` | ECRA 2022 (target 150 ± 30 °C) |
| `project_bed_pressure_drop_mm_h2o` | float | mm H₂O | continuous (per compartment) | cooler module `state.bed_pressure_drop_mm_h2o` | Peray & Waddell 1986 §6.4 |
| `project_fan_power_kw` | float | kW | continuous (sum across compartments) | cooler module `state.fan_power_kw` | KHD Pyrostep brochure (8–12 kW/(t/h)) |
| `project_secondary_air_recovered_kw` | float | kW | daily computed | cooler module `outputs.secondary_air_recovered_kw` | VM0009 v3.0 §5.3 |
| `project_secondary_air_recovered_gj_per_t_clinker` | float | GJ/t-cli | monthly reported | `Q_sec_kw × 3.6 / clinker_throughput_t_h` | Peray & Waddell 1986 §6.4 (0.30–0.45 GJ/t) |
| `project_first_law_imbalance` | float | fraction | daily | `|Q_in - Q_recovered - Q_out| / Q_in` (must be ≤ 0.02) | VM0009 v3.0 §6.2 QA/QC |
| `project_cooler_loss_mj_per_t_cli` | float | MJ/t-cli | monthly | cooler module | ECRA 2022 (BAT ceiling 0.42 MJ/kg-cli) |

### 2.4 Monitoring plan (PDD §D.1–D.6) — the verifier's hardest section

| Field | Type | Unit | Frequency | Source | Citation |
|---|---|---|---|---|---|
| `monitoring.instrument_cooler_outlet_T` | string | — | once at PDD | "Type-K thermocouple, class 1, 0–1100 °C, shielded" | VM0009 v3.0 §6.2 |
| `monitoring.uncertainty_cooler_outlet_T` | float | K | once at PDD | ±10 K at 800 °C | VM0009 v3.0 §6.2 |
| `monitoring.calibration_frequency_cooler_outlet_T` | string | — | once at PDD | "quarterly single-point + annual re-cal" | ISO 17025 |
| `monitoring.instrument_secondary_air_flow` | string | — | once at PDD | "orifice plate / thermal mass flowmeter" | ISO 5167 |
| `monitoring.uncertainty_secondary_air_flow` | float | fraction | once at PDD | ±0.02 (2 % of reading) | VM0009 v3.0 §6.2 |
| `monitoring.data_custodian` | string | — | once at PDD | "Plant DCS / control room" | VM0009 v3.0 §6.2 |
| `monitoring.qa_qc_procedure` | string | — | once at PDD | "see data_quality_spec.md, Kabita" | ISO 14064-2 §5.7 |
| `monitoring.frequency_data_logging` | string | — | once at PDD | "1-min average, 1-h logged, daily reported, monthly aggregated" | VM0009 v3.0 §6.2 |

### 2.5 Sanity / diagnostic block (NEW for v0.3.1)

These are not in the PDD directly; they are in the `monitoring_report.json` that the validator inspects. A sanity check failure is a **red flag** that triggers a verification site visit.

| Field | Type | Unit | Pass criterion | Citation |
|---|---|---|---|---|
| `sanity.air_above_clinker` | bool | — | `False` (second-law invariant) | Mujumdar 2007 §3.1 |
| `sanity.first_law_imbalance` | float | fraction | ≤ 0.02 | VM0009 v3.0 §6.2 |
| `sanity.sec_air_in_realistic_band` | bool | — | `True` (600–1000 °C for default Hetauda) | Peray & Waddell 1986 §6.4 |
| `sanity.clinker_outlet_in_realistic_band` | bool | — | `True` (120–200 °C) | ECRA 2022 |
| `sanity.efficiency_in_realistic_band` | bool | — | `True` (0.65–0.85) | GCCA GNR 2022 |

### 2.6 Nepal duty case (mandatory for HCIL / UCIL)

| Field | Type | Unit | Value (Hetauda) | Citation |
|---|---|---|---|---|
| `duty_case.altitude_m` | float | m | 1400 | Cengel & Boles 2015 |
| `duty_case.ambient_t_c` | float | °C | 35 (May design day) | HCIL plant documents |
| `duty_case.ambient_rh` | float | fraction | 0.90 (monsoon) | HCIL plant documents |
| `duty_case.air_density_kg_m3` | float | kg/m³ | 1.05 (computed, not 0.6) | Cengel & Boles 2015 + Ramesh §5.1 |
| `duty_case.p_atm_mbar` | float | mbar | 858 | ISA barometric formula |

---

## 3. The `to_pdd_json()` method contract

The cooler module exposes a method `to_pdd_json()` that emits a dict matching `pdd_json_schema.json`. The method:

1. **Takes** the cooler state and parameters.
2. **Returns** a `dict` that validates against `pdd_json_schema.json` (Draft 2020-12).
3. **Includes** all 2.1–2.6 sections.
4. **Includes** the `meta` block (PDD schema version, generator version, timestamp, signature hash).

**Implementation recommendation (per Maya's question):**

> **Use Pydantic v2.** Reasons: (a) runtime validation at the boundary, (b) auto-generated JSON Schema, (c) Verra validators often use JSON Schema validators, (d) TypeScript-style ergonomics with `model_dump()`. TypedDict is lighter but doesn't validate at runtime. Plain dict is asking for a validation rejection. Cite: Pydantic v2 docs (2024); Verra VCS Program Guide v4.5 §3.4 (controlled PDD template).

```python
# Sketch (not for v0.3.1 — for Day 13 / Day 20 tokenization)
from pydantic import BaseModel, Field

class PDDMeta(BaseModel):
    pdd_schema_version: str = "1.0.0"
    generator_version: str = "nepal_cooler_sim-0.3.1"
    generated_at_utc: str  # ISO 8601
    sha256_of_inputs: str  # for audit trail

class ToPDDJSON(BaseModel):
    meta: PDDMeta
    project_description: ProjectDescription
    baseline: BaselineFields
    project: ProjectFields
    monitoring: MonitoringFields
    sanity: SanityFields
    duty_case: DutyCase
```

---

## 4. What the verifier will look at first (and the failure modes)

In order of likely failure:

1. **`secondary_air_outlet_c` outside [600, 1000] °C** — fail, the kiln baseline is invalid.
2. **`first_law_imbalance` > 2 %** — fail, monitoring data is not mass-balanced.
3. **No measurement-instrument metadata** — fail, monitoring plan is incomplete.
4. **`baseline_cooler_efficiency` > 0.75 with no project activity** — fail, the project is not additional (the baseline is already BAT).
5. **`cooler_efficiency` > 0.85** — fail, claims exceed BAT ceiling (ECRA 2022).
6. **No calibration records** — fail, QA/QC is unproven.
7. **Vintage mismatch** (e.g. 2025 emission reductions claimed but tokens minted in 2026) — fail, VCS Program Guide v4.5 §4.2.

---

## 5. The verifier is the customer

> *"If the verifier would reject it, don't ship it. The verifier is your customer."* — agent.md, *Style*.

Day 3 v0.3.1 will be inspected by a Verra-accredited VVB (validation/verification body) when the kiln PDD is filed. The cooler module's JSON output is the VVB's first stop. Get the JSON right and the credit pathway stays open. Get it wrong and the entire 20-day project loses the kiln-credit revenue.

---

## 6. References

See `credit_eligibility.md` for the full reference list. The additional references for this PR:

- **Verra VM0009 v3.0** (2023-Q4) §5.3 (Kiln Baseline Methodology), §6.2 (Monitoring Plan).
- **Verra VCS Program Guide v4.5** (2024-Q2) §3.1 (Project Description), §3.4 (PDD Template), §3.5 (Project Ownership and Credit Allocation), §3.6 (PDD Completion), §4 (Monitoring), §4.2 (Vintage Year).
- **ISO 14064-2:2019** §5.7 (Project Monitoring).
- **ISO 5167** (Orifice plates for flow measurement).
- **ISO 17025** (Calibration laboratory competence).
- **Pydantic v2 docs** (2024) — https://docs.pydantic.dev/latest/
- **JSON Schema Draft 2020-12** — https://json-schema.org/draft/2020-12/schema

— James Okafor, Carbon Markets Specialist
*2026-07-22*
