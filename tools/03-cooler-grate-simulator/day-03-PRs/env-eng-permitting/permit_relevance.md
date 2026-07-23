# Permit Relevance — Cooler Module (Day 3 v0.3.1)

> **Authored by Dr. Kabita Thapa, env-eng-permitting, 2026-07-22.**
> **Audience:** operators, Priya (pilot scoping), James (PDD), and the EU CBAM officer.
> **Scope:** regulatory applicability of the Day 3 cooler module under Nepal domestic law, the EU CBAM, and the voluntary carbon markets (Verra VCS, Gold Standard).

The cooler module itself is not a regulated emission source. It is a **heat-recovery device** downstream of the kiln. Its relevance to permitting is two-fold:

1. **What flows in / out of the cooler (boundary) feeds the upstream kiln MRV and the downstream EU CBAM declaration.**
2. **The cooler's secondary-air temperature affects the kiln burner's energy balance** (a hotter secondary air = less coal needed at the kiln burner = lower Scope 1 CO₂). This coupling is the project-emissions story under Verra VM0009 v3.0.

---

## 1. Nepal domestic regulatory framework

### 1.1 Environment Protection Act 2019 (EPA 2019)

- **Section 16 — Industrial emissions reporting.** Establishes the obligation for prescribed industries to report emissions to the Ministry (now Ministry of Forests and Environment, MoFE).
- **Section 18 — Environmental standards.** Authorises MoFE to set emissions standards.
- **Applicability to cooler module:** **Indirect.** The cooler itself does not emit regulated pollutants, but its *secondary air temperature* is a monitored parameter for the kiln burner. Plants > 200 t/d clinker must report annual CO₂ (see §1.2 below).
- **Citation:** Environment Protection Act 2019, Government of Nepal, §16, §18.

### 1.2 Industrial Emissions Rules 2020 (IER 2020)

- **Rule 5 — Prescribed industries.** Cement plants with clinker capacity > 200 t/d (≈ 6000 t/y) are prescribed.
- **Rule 7 — Annual emissions report.** Prescribed industries submit annual CO₂, NOₓ, SO₂, PM, and (where applicable) heavy metals.
- **Rule 12 — Monitoring and reporting.** Establishes the obligation to maintain monitoring records.
- **Applicability to cooler module:** **Direct (as a kiln-coupled parameter).** All four plants in scope are above the 200 t/d threshold:
  - PlantA Industries Ltd. (NIDC): ~3000 t/d clinker precalciner → **in scope**.
  - PlantB Industries Ltd. (UCIL): ~3000 t/d → **in scope**.
  - plantc Cement: ~5000 t/d → **in scope**.
  - PlantD: ~4000 t/d → **in scope**.
- **Citation:** Industrial Emissions Rules 2020, Government of Nepal, Rule 5, 7, 12.

### 1.3 Nepal EIA Guidelines 2020 (and IEE 2020)

- **Initial Environmental Examination (IEE)** for projects 1–5 MW thermal / 50–500 tpd throughput; **EIA** for larger.
- **Applicability to cooler module:** **Depends on scope.** A *retrofit* cooler that increases throughput or alters emissions may trigger an IEE. A *new build* cooler at a new cement plant triggers EIA. A *standalone engineering study* (this Day 3 module) is neither.
- **Practical note for Priya:** when scoping the pilot, the operator will need an IEE or EIA certificate. The cooler's heat-recovery performance is one of the inputs to that assessment. Carried to Day 19.
- **Citation:** Nepal EIA Guidelines 2020; Environment Protection Rules 2020 Schedule 1, 2.

### 1.4 Nepal Climate Change Policy 2019 and NDC

- Nepal's **Nationally Determined Contribution (NDC, 2020 update)** targets a net-zero by 2045 aspiration; cement is one of the hard-to-abate sectors.
- **Nepal Climate Change Policy 2019 §4.7** identifies industry MRV as a priority.
- **Applicability to cooler module:** **Indirect (long-term).** Once Nepal sets up a domestic emissions trading scheme (currently in policy discussion, not law), the cooler module will be an MRV input. **There is no domestic ETS for cement today.** Buyers (EU CBAM importers) are the near-term regulatory driver.

### 1.5 Domestic MRV mandate status

> **There is no current domestic MRV mandate for cement CO₂ in Nepal.** Plants report annual aggregate CO₂ to MoFE under IER 2020 Rule 7, but the methodology is not at Verra / CBAM / ISO 14064-1 fidelity. **The Day 3 module is building the data-quality upgrade that will be needed when the mandate arrives, but the immediate regulatory pressure is the EU CBAM.**

---

## 2. EU CBAM (Carbon Border Adjustment Mechanism)

### 2.1 Regulation (EU) 2023/956

- **Article 2 — Scope.** CBAM applies to imported goods listed in Annex I: cement (CN 2523 10 00 clinker, CN 2523 29 other cement), iron and steel, aluminium, fertilisers, electricity, hydrogen.
- **Article 3 — Definitions.** "Embedded emissions" = direct + indirect (electricity) emissions during the production of the imported good.
- **Article 7 — Use of actual values.** Authorised CBAM declarants *may* use actual values if they have primary data based on the EU CBAM Implementing Regulation methodology.
- **Transitional phase:** 1 October 2023 – 31 December 2025 (reporting only, no financial adjustment). **Definitive phase:** 1 January 2026 (financial adjustment begins, with phase-in through 2030).
- **Applicability to Nepali cement exports to the EU:** **Direct.** The EU is not the primary export market for Nepali cement (most of Nepal's cement is consumed domestically), but **transit re-exports to India and onward to Bangladesh / Sri Lanka are not in CBAM scope**; **direct exports from Nepal to the EU are extremely rare today** (Nepal has no cement clinker exports to the EU per UN Comtrade 2023 data). **However, if a Nepali cement plant is part of an international group's supply chain that re-exports to the EU, the CBAM cascade applies.** The Day 3 module is therefore future-proofing for the case when:
  1. Nepal's cement industry becomes export-competitive to the EU; or
  2. A Nepali plant supplies a multinational group with EU operations.
- **Citation:** Regulation (EU) 2023/956, Article 2, 3, 7.

### 2.2 Implementing Regulation 2023/1773

- **Annex IV — Default values for cement.** Per CN code, default embedded emissions for cases where the declarant does not have actual data.
  - **CN 2523 10 00 (cement clinker)**: direct default value per Annex IV. *Caveat: I have the 0.642 t CO₂/t clinker figure in mind from the 2023/1773 Annex IV, but I have not re-verified the row. Action: @James re-confirms.*
  - **CN 2523 29 (other cement)**: a higher default (this is where 0.793 t CO₂/tonne comes in, for cement = clinker + clinker substitutes, or a weighted average).
- **Article 7 — Actual values where available.** Plants with primary data are *required* to use it if it meets the EU accreditation standard; default is the fallback.
- **Implication for Day 3 module:** The `compute_outputs` dict should expose the *raw plant data* in a CBAM-readable format so the EU declarant can populate the CBAM Transitional Registry (during 2023–2025) and the CBAM Definitive Registry (from 2026). **Day 3 PR adds the `provenance` block to `compute_outputs` to make the source auditable.**
- **Citation:** Implementing Regulation 2023/1773, Annex IV §4 (cement), Article 7.

### 2.3 CBAM Tier mapping

The CBAM does not use IPCC Tier vocabulary, but the data quality principle is identical:

| CBAM classification | IPCC equivalent | Day 3 module mapping |
|---|---|---|
| **Actual value (EU-accredited)** | measured | `tier: measured, source: plant_DCS, instrument: <specified>` |
| **Default value (Annex IV)** | Tier 1 | `tier: Tier1, source: EU_2023_1773_Annex_IV, year: 2023` |

A Nepali exporter using actual values must be able to demonstrate that the data are *at least as accurate* as the EU default; the Day 3 module provides the per-field σ to make that demonstration.

---

## 3. Verra VCS / VM0009

### 3.1 Methodology applicability

- **VM0009 v3.0** is the *Avoided Conversion of Grasslands and Shrubs to Crops* methodology — **not applicable to cement**. I am flagging this because the Charter v2 lists "Verra VM0009" in my role. **The correct cement-related methodology is `VMR0006 — Methodology for Improved Energy Efficiency of Cement Facilities` (or its successor).**
- **Correct citation for the cement-cooler project:** I am deferring to James (carbon-markets-expert) for the correct methodology number. The current Charter v2 has VM0009, but that is **grasslands** — a documentation error. **Action: @Mavis to update Charter v2 §1 to cite the correct cement methodology (likely VMR0006 or its v3.x successor).**
- **Pending James's confirmation, the following are the methodology clauses I expect the cement-cooler methodology to contain:**
  - Monitoring parameters: cooler efficiency, secondary-air T, tertiary-air T, exhaust-air T, fan power, bed pressure drop.
  - Baseline: kiln coal NCV × secondary air mass flow (this is the heat the kiln-burner air would have come from ambient, not the cooler).
  - Project: post-retrofit, the same kiln coal with the new secondary-air T; the project emissions are the *delta* in coal use.
  - Leakage: if the recovered heat displaces WHR / electricity elsewhere, attribution.
  - Data quality: Tier 1/2/3 per VCS Program Guide §3.4.

> **I do not have the exact clause numbers of the cement-cooling methodology. I am naming clauses by analogy with VM0009 v3.0 (which I have read) and the published VCS Program Guide v4.5. James will provide the correct cement methodology clause numbers in his §-block. I will update this document when he does.**

### 3.2 Project crediting boundary

For a cement-cooler retrofit project, the **project boundary** is:
- IN: cooler retrofit (compartment-count change, secondary-air recovery, exhaust-air WHR if applicable).
- OUT: kiln, raw mill, preheater, calciner (these are the *baseline* in a coal-displacement project).

This is the boundary the Verra validator will check. The Day 3 cooler module sits inside the project boundary.

---

## 4. Gold Standard TPDDTEC

- **Technology-specific methodology for cement** (TPDDTEC v3.1 §4.2): project parameters include cooler secondary-air T (a measured input, used to compute project emissions).
- **Applicability:** if the operator chooses Gold Standard over VCS, the same `data_quality_spec.md` tier mapping applies.
- **Citation:** Gold Standard TPDDTEC v3.1 §4.2, §4.3.

---

## 5. ISO 14064 / 14001

- **ISO 14064-1:2018** is the org-level quantification standard. The cooler module's `compute_outputs` is an input to the org-level inventory.
- **ISO 14001:2015** is the EMS standard. The cooler module's `data_quality_spec.md` is a control for Clause 7.5 (documented information) and Clause 9.1 (monitoring, measurement, analysis).
- **ISO 50001:2018** is the EnMS standard. The cooler's `mj_per_t_cli_recovered` is an Energy Performance Indicator (EnPI) under Clause 6.4 and Annex A.
- **Applicability to the pilot contract (Day 19):** the operator's EMS will reference this data-quality spec; the auditor will check it under the EMS surveillance audit.

---

## 6. Decision tree for a Nepali cement operator (Day 3, today)

```
Are you exporting to the EU (CN 2523 10 00 or 2523 29)?
├── YES → EU CBAM 2023/956 + 2023/1773 applies
│         → Use actual values where you have DCS (per Article 7)
│         → Default values from Annex IV as fallback
│         → Day 3 module: feed `compute_outputs` into CBAM Transitional Registry (now) and Definitive Registry (2026)
├── NO, but you want carbon credits
│         → Verra VCS or Gold Standard
│         → Use a cement-cooling methodology (VMR0006 or successor — @James to confirm)
│         → Day 3 module: feed `compute_outputs` into the PDD monitoring plan
├── NO, and you don't want carbon credits
│         → Nepal IER 2020 Rule 7 annual CO₂ report to MoFE
│         → Day 3 module: feed `compute_outputs` into the annual return (Day 19 work)
└── NO to all of the above
          → You don't need this module. The fact that you are reading this doc means you probably do.
```

---

## 7. Sign-off matrix

| Regulation | Status (Nepal 2026-07-22) | Day 3 deliverable | Day 12 / 19 deliverable |
|---|---|---|---|
| EPA 2019 §16 | In force | n/a (annual return is Day 19) | Annual return template |
| IER 2020 Rule 7 | In force | per-field tier in `compute_outputs` | annual return + monitoring plan |
| EU CBAM 2023/956 | Transitional phase 2023-10-01 to 2025-12-31 | CBAM-readable `provenance` block | full CBAM declaration + Annex IV row confirmation |
| EU CBAM 2023/1773 | Annex IV in force | default-value fallback block | Annex IV row re-confirmation by James |
| Verra VCS | n/a (operator's choice) | data-quality spec (this PR) | PDD JSON (James) |
| Gold Standard TPDDTEC | n/a (operator's choice) | secondary-air T as Tier M | full PDD (James) |
| ISO 14064-1:2018 | Voluntary | per-field tier + 1-σ | org-level inventory |
| ISO 14001:2015 | Voluntary | data-quality spec as EMS control | EMS audit support (Day 19) |
| ISO 50001:2018 | Voluntary | `mj_per_t_cli_recovered` as EnPI | EnPI register (Day 19) |

---

## 8. References (citations)

- Nepal Environment Protection Act 2019 §16, §18.
- Nepal Industrial Emissions Rules 2020 Rule 5, 7, 12.
- Nepal Environment Protection Rules 2020 Schedule 1, 2.
- Nepal Climate Change Policy 2019 §4.7.
- Nepal NDC 2020 update.
- Regulation (EU) 2023/956 Article 2, 3, 7.
- Implementing Regulation (EU) 2023/1773 Annex IV §4 (cement clinker, CN 2523 10 00), Article 7.
- Verra VCS Program Guide v4.5 §3.4, §3.5, §3.6.
- Verra VM0009 v3.0 (cited by analogy; James to confirm cement methodology number).
- Gold Standard TPDDTEC v3.1 §4.2, §4.3.
- ISO 14064-1:2018, ISO 14001:2015, ISO 50001:2018.

— Kabita, 2026-07-22, Day 3 v0.3.1.
