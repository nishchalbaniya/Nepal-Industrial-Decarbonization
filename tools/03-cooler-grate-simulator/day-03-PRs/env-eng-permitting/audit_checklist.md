# Audit Checklist — Cooler MRV Module (Day 3 v0.3.1)

> **Authored by Dr. Kabita Thapa, env-eng-permitting, 2026-07-22.**
> **Scope:** `tools/03-cooler-grate-simulator` — `cooler_ode.py`, `compute_outputs`, IO round-trip.
> **Audience:** the ISO 14064-3:2019 / Verra / Gold Standard / EU CBAM verifier. Not the marketing department.

This checklist is what a third-party verifier will look at on Day 1 of an audit. Each item names the **clause** the verifier will cite, the **evidence** the verifier will ask for, and the **current state** of the Day 3 build (PASS / PARTIAL / MISSING). Items marked MISSING are blocked items for ship.

---

## A. ISO 14064-1:2018 — Organizational GHG quantification

### A.1 Data quality assessment of input data
- **Clause:** ISO 14064-1:2018 **§6.5** (Data quality), GHG Protocol Corporate Standard §5.2.
- **Verifier question:** "Show me the data-quality tier for every `compute_outputs` field. I need relevance, completeness, consistency, accuracy, and transparency, and a 1-sigma uncertainty on each."
- **Evidence expected:** A `data_quality_tiers.py` mapping with `field → (Tier, source, year, σ)`.
- **Current state:** **MISSING.** `compute_outputs` returns a flat dict with no `tier` or `σ` field. This is the single largest Day 3 MRV gap.
- **Remediation:** Day 3 PR — `data_quality_tiers.py` (per-field Tier + 1σ mapping, in this PR folder).

### A.2 Organizational / operational boundary
- **Clause:** ISO 14064-1:2018 **§5.1** (Organizational boundary), **§5.2** (Operational boundary).
- **Verifier question:** "Is the cooler inside the organizational boundary of the plant? Is the kiln-cooler interface inside or outside the reporting boundary?"
- **Evidence expected:** A `boundary` field in `CoolerParameters` or in the MRV output.
- **Current state:** **MISSING.** Boundary is implicit (clinker enters the cooler from the kiln, secondary air leaves to the kiln burner, exhaust to the dust collector). For an audit, the boundary must be **declared**.
- **Remediation:** Add `boundary: Literal["clinker_in", "secondary_air_out", "tertiary_air_out", "exhaust_air_out"]` to a `Boundary` block. Day 3 PR proposes a sidecar dict; full integration in Day 12 PDD.

### A.3 Base year and methodology version
- **Clause:** ISO 14064-1:2018 **§6.3** (Methodology).
- **Verifier question:** "Which methodology version are you running? IPCC 2006 or 2019 Refinement? Tier 1, 2, or 3? Cite the section."
- **Evidence expected:** `methodology: {ipcc_version, tier, clause, year}` in the output.
- **Current state:** **PARTIAL.** The model physics are documented; the IPCC-version binding is not.
- **Remediation:** Add a `methodology` block in `compute_outputs` returning `{"ipcc": "2006 Vol.3 Ch.2", "tier": "Tier 1 / Tier 2 / measured", "year": 2006}`.

### A.4 Recalculation policy
- **Clause:** ISO 14064-1:2018 **§6.5.3** (Recalculation).
- **Verifier question:** "When IPCC publishes a Refinement, do you re-run the inventory? When a plant datum is found to be wrong, do you restate the base year?"
- **Evidence expected:** A `recalc_policy` doc and a version log in the audit trail.
- **Current state:** **MISSING.** Out of scope for Day 3; carried to Day 19 (audit-ready docs).

---

## B. Verra VCS / VM0009 v3.0 — Project crediting

### B.1 Monitoring parameters (cooler)
- **Clause:** Verra **VM0009 v3.0 §5.3.2** (Monitoring parameters — cooler efficiency, secondary-air T, tertiary-air T, exhaust-air T, fan power, bed pressure drop).
- **Verifier question:** "Show me the monitoring plan. For each parameter: tier (default vs measured), instrument, accuracy, calibration frequency, and uncertainty propagation."
- **Evidence expected:** A monitoring plan table per parameter, with each row mapping to a field in `compute_outputs`.
- **Current state:** **PARTIAL.** The fields exist in the model; the **monitoring plan** (instrument, accuracy, calibration, frequency) does not.
- **Remediation:** Day 3 PR `data_quality_spec.md` (per-field tier + σ + instrument + source) is the monitoring-plan input. Full monitoring plan template is Day 12 (James, with Kabita co-sign).

### B.2 Data quality assessment under VM0009
- **Clause:** Verra **VM0009 v3.0 §5.3.3** (Data quality assessment), cross-referenced to **VCS Program Guide v4.5 §3.4** (Data quality).
- **Verifier question:** "If a monitoring parameter is `Tier 3` (engineering estimate), what is the discount applied to the credit issuance? Cite the table."
- **Evidence expected:** A scoring table; `Tier 1 = 1.0`, `Tier 2 = 0.95`, `Tier 3 = 0.85`, `measured = 1.0`. (Verify against current VCS Program Guide; version 4.5 as of 2024-01.)
- **Current state:** **MISSING.** Day 3 PR provides the per-field tier; the discount table is referenced but not embedded in code (that's an accounting concern, Day 12/20).

### B.3 Cross-reference to kiln baseline
- **Clause:** Verra **VM0009 v3.0 §5.4** (Project emissions — kiln).
- **Verifier question:** "Your kiln baseline uses coal NCV × secondary air mass flow. Show me the secondary air mass flow source."
- **Evidence expected:** `secondary_air_mass_flow_kg_s` from Ramesh's Fix C, with provenance (kiln-cooler air balance).
- **Current state:** **MISSING today; PENDING Ramesh's Patch C.** The PR flags this.

### B.4 Leakage
- **Clause:** Verra **VM0009 v3.0 §6** (Leakage).
- **Verifier question:** "If the cooler recovers more heat, does the kiln burn less coal, and does that drop the project emissions — or does it drop the baseline by the same amount? Show me the attribution."
- **Evidence expected:** A leakage-attribution block: `project_delta_clinker_t` → `project_delta_coal_kg` → `baseline_coal_kg` → `credit_issuance_kg_co2e`.
- **Current state:** **PARTIAL.** Out of scope for Day 3 (Day 12 PDD, James). Day 3 ships the model; Day 12 ships the leakage attribution that uses the model.

### B.5 Permanence
- **Clause:** Verra **VM0009 v3.0 §7** (Permanence), **VCS Program Guide v4.5 §3.6**.
- **Verifier question:** "Clinker cooling is not a permanence risk per se, but if your baseline is open-loop (no obligation to maintain the cooler retrofit), is this a non-permanence project?"
- **Evidence expected:** A buffer-pool contribution calculation, or a non-permanence risk assessment.
- **Current state:** **OUT OF SCOPE Day 3.** Carried to Day 12.

---

## C. Gold Standard TPDDTEC v3.1 — Technology-specific

### C.1 Project parameter (cooler secondary air T)
- **Clause:** Gold Standard **TPDDTEC v3.1 §4.2** (Project parameters).
- **Verifier question:** "You use the cooler secondary air T as a project parameter. What is the operating range, and what is the data source?"
- **Evidence expected:** `secondary_air_T` with `Tier: measured`, `instrument: Type-K TC`, `range: 600-1000 °C`, `σ: 20 K (1σ)`.
- **Current state:** **PARTIAL.** Field exists; provenance is undeclared.
- **Remediation:** `data_quality_spec.md` documents this per-field.

### C.2 WHR (waste-heat recovery) eligibility
- **Clause:** Gold Standard **TPDDTEC v3.1 §4.3** (WHR eligibility).
- **Verifier question:** "If the cooler is retrofit to feed a WHR boiler on the exhaust air, is the additional WHR eligible? Cite the methodology."
- **Evidence expected:** Eligibility check in the PDD.
- **Current state:** **OUT OF SCOPE Day 3.** This is the post-retrofit story (Day 11).

---

## D. EU CBAM 2023/956 + Implementing Reg 2023/1773

### D.1 Embedded emissions in imported clinker
- **Clause:** **Regulation (EU) 2023/956 Article 3** (Scope), **Implementing Reg 2023/1773 Annex IV** (default values for cement clinker CN 2523 10 00).
- **Verifier question (EU CBAM officer):** "You are exporting cement clinker to the EU. What is the embedded direct emissions per tonne clinker? If you have actual data, use it; if you fall back to the default, declare it."
- **Evidence expected:** `cbam: {cn_code: "2523 10 00", embedded_direct_t_co2_per_t: <measured or default>, source: <DCS log or 2023/1773 Annex IV row>, year: 2023}`.
- **Current state:** **MISSING.** Day 3 PR `permit_relevance.md` flags this; the `cbam` block in `compute_outputs` is proposed for Day 12.
- **Caveat (open question to @James):** I cited 0.642 t CO₂/t clinker as the CBAM direct default for CN 2523 10 00 in my §-block; I have the 0.793 figure in mind for a different product. I will not commit a number I cannot re-verify against the Implementing Reg Annex IV row. **Action: @James re-confirms before the PDD JSON is signed.**

### D.2 Actual vs default values
- **Clause:** **Implementing Reg 2023/1773 Article 7** (Actual values where available).
- **Verifier question:** "You have plant data. Why did you use the default?"
- **Evidence expected:** If plant data is in `compute_outputs`, the CBAM declaration should cite `source: plant_DCS`, not `default`.
- **Current state:** **PARTIAL.** The fields exist; the `source: plant_DCS` annotation is missing.
- **Remediation:** Each field's `_data_quality` entry to declare its source as `plant_DCS` or `default_2023_1773`.

### D.3 Electricity (indirect) embedded emissions
- **Clause:** **Implementing Reg 2023/1773 Annex IV** (electricity default for Nepal grid).
- **Verifier question:** "What is the electricity-mix factor for Nepal? Cite the source."
- **Evidence expected:** `electricity_source: <Nepal grid mix or self-generation>`, `factor_t_co2_per_mwh: <value, source>`.
- **Current state:** **OUT OF SCOPE Day 3.** (Day 1 MRV tool already has the electricity line; Day 3 cooler does not.) Carried to Day 12.

---

## E. Nepal regulatory (domestic)

### E.1 Annual CO₂ reporting to MoFE
- **Clause:** **Nepal Environment Protection Act 2019 §16** (industrial emissions reporting), **Nepal Industrial Emissions Rules 2020** (cement plants > 200 t/d clinker report annual CO₂ to MoPE — now MoFE).
- **Verifier question (Nepal domestic):** "Submit your 2024 annual CO₂ report to MoFE."
- **Evidence expected:** Annual return in the format prescribed by the Rules.
- **Current state:** **OUT OF SCOPE Day 3.** The cooler module provides daily/operator-trended data; the annual return is Day 19 (audit-ready docs).
- **Note:** For plants **< 200 t/d clinker** there is **no current domestic MRV mandate** in Nepal. The plants in scope (Hetauda, Udayapur) are at or above the threshold; the smaller plants (Hongshi-Shivam precalciner at 5000 t/d is well above) are unambiguously in scope.

### E.2 Environmental Impact Assessment (EIA) / Initial Environmental Examination (IEE)
- **Clause:** **Nepal EIA Guidelines 2020** (revised), **Environment Protection Rules 2020**.
- **Verifier question (Nepal domestic):** "Was an EIA / IEE done for this cooler retrofit? Submit the certificate."
- **Evidence expected:** EIA / IEE certificate number, approving authority.
- **Current state:** **OUT OF SCOPE Day 3** (and arguably not Kabita's lane — it's Priya's pilot scoping). Carried to Day 19.

---

## F. ISO 14064-3:2019 — Verification process

### F.1 Risk-based verification
- **Clause:** ISO 14064-3:2019 **§6.4** (Risk-based verification approach).
- **Verifier question:** "What is the materiality threshold? What sampling approach did you use?"
- **Evidence expected:** Materiality threshold (typically 5 % of total reported CO₂e), sampling plan, and a list of higher-risk parameters (e.g. anything that is `Tier 3` rather than `measured`).
- **Current state:** **PARTIAL.** `compute_outputs` returns `first_law_imbalance`; that is a *physics* check, not a *materiality* check.
- **Remediation:** Day 3 PR `data_quality_tiers.py` includes a `materiality` flag per field; full sampling plan is Day 12.

### F.2 Data aggregation / gap-fill
- **Clause:** ISO 14064-3:2019 **§6.5.2** (Estimation and gap-filling).
- **Verifier question:** "When the DCS drops a reading, what is your gap-fill method? Tier 1 default? Average of neighbours? Cite the procedure."
- **Evidence expected:** A gap-fill policy doc, with the substitution rule.
- **Current state:** **MISSING.** The current build does not declare a gap-fill policy.
- **Remediation:** Add a `gap_fill_policy` block to `compute_outputs` (Day 3 PR proposes; Hiro owns the UQ; full integration in Day 12).

### F.3 Uncertainty assessment
- **Clause:** ISO 14064-3:2019 **§6.4.3** (Uncertainty assessment).
- **Verifier question:** "What is the combined uncertainty of your clinker T prediction? Propagate the 1-σ values through the model and show the result."
- **Evidence expected:** Per-field 1-σ, propagation methodology, and combined uncertainty on the headline KPIs (`cooler_efficiency`, `secondary_air_outlet_c`).
- **Current state:** **PARTIAL.** Hiro owns the UQ; the *inputs* (per-field 1-σ) are not declared in `compute_outputs` today.
- **Remediation:** Day 3 PR `data_quality_spec.md` provides the per-field 1-σ; Hiro wires it into his UQ layer (separate PR, separate session).

---

## G. Audit trail (system-level)

### G.1 Change control
- **Clause:** ISO 14064-1:2018 **§6.6** (Information management), **ISO 14064-3:2019 §5.3** (Verification of information systems).
- **Verifier question:** "Who changed `emissivity` from 0.85 to 0.90, and when? Show me the version log."
- **Evidence expected:** A version log keyed by `(timestamp, user, field, old, new, reason)`. Round-trip through CSV/JSON/pickle must preserve the log.
- **Current state:** **PARTIAL.** Maya's `io.py` round-trip preserves the result dict; the *change log* is not part of the data.
- **Remediation:** Day 3 PR proposes a `provenance` block in `compute_outputs`; full change-control log in Day 19 (audit-ready docs).

### G.2 Reproducibility
- **Clause:** ISO 14064-3:2019 **§6.4.2** (Verification of data and information).
- **Verifier question:** "Give me the same inputs; I want the same outputs. Show me the determinism check."
- **Evidence expected:** A hash of `(parameters → outputs)` that is stable across runs and platforms.
- **Current state:** **PARTIAL.** The model is deterministic in the absence of random seeds; Hiro's UQ runs are seed-controlled. The hash is not part of the output today.
- **Remediation:** Day 3 PR `data_quality_tiers.py` includes a `result_hash` field in the `Provenance` block; Maya's `io.py` round-trip is the binding test.

---

## H. Sign-off matrix (Day 3 ship gate)

| Check | Clause | Current | Owner | Blocker? |
|---|---|---|---|---|
| Per-field Tier + 1-σ | ISO 14064-1:2018 §6.5 | **MISSING** | Kabita (this PR) | **YES** |
| Methodology-version block | ISO 14064-1:2018 §6.3 | **PARTIAL** | Kabita (this PR) | yes |
| Monitoring parameters (cooler) | VM0009 v3.0 §5.3.2 | **PARTIAL** | James (Day 12) | no (Day 12) |
| CBAM embedded-emissions block | EU 2023/956 + 2023/1773 Annex IV | **MISSING** | James + Kabita (Day 12) | no (Day 12) |
| Gap-fill policy | ISO 14064-3:2019 §6.5.2 | **MISSING** | Hiro (UQ) | no (separate PR) |
| Reproducibility hash | ISO 14064-3:2019 §6.4.2 | **PARTIAL** | Maya (io.py) | no (separate PR) |
| Nepal annual report | EPA 2019 §16 | **OUT OF SCOPE** | Day 19 | no |

**Day 3 ship-blocking items:** the per-field Tier mapping and the methodology-version block. Both are in this PR.

---

## I. References (clauses cited in this checklist)

- ISO 14064-1:2018 §5.1, §5.2, §6.3, §6.5, §6.6.
- ISO 14064-3:2019 §5.3, §6.4, §6.4.2, §6.4.3, §6.5.2.
- IPCC 2006 Vol.3 Ch.2 §2.3.2 (cement clinker calcination EF 0.527 t CO₂/t cli, Tier 1).
- IPCC 2019 Refinement §2.3.1 (correction for non-100% calcination).
- Verra VM0009 v3.0 §5.3.2 (monitoring), §5.3.3 (data quality), §5.4 (kiln baseline), §6 (leakage), §7 (permanence).
- Verra VCS Program Guide v4.5 §3.4 (data quality), §3.5 (sources), §3.6 (non-permanence).
- Gold Standard TPDDTEC v3.1 §4.2 (project parameters), §4.3 (WHR eligibility).
- EU CBAM Regulation 2023/956 Article 3, Article 7.
- EU CBAM Implementing Reg 2023/1773 Annex IV (default values), Article 7 (actual values where available).
- Nepal Environment Protection Act 2019 §16.
- Nepal Industrial Emissions Rules 2020.
- Nepal EIA Guidelines 2020.
- GHG Protocol Corporate Standard (Revised Edition) §5.2.
- ICCC 2006 §2.2 (kiln discharge pyrometer), §2.3 (clinker emissivity), §2.4 (sieve analysis), §3.4 (IR spot pyrometer, f-CaO < 1.5 %).
- Boateng, A.A. (2008) Ch.7 (cp_clinker = 1.05 kJ/(kg·K) default).
- Peray, K.E. & Waddell, J.J. (1986) §6.4 (secondary air T, fan ΔP, GJ/t benchmark).

— Kabita, 2026-07-22, Day 3 v0.3.1.
