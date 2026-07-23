# Standards Compliance Audit — `nepal_decarb_pro` v1.0
### VVB-Readiness Review of the Standards & Markets Modules

**Audit date:** 2026-07-22
**Auditor:** Senior Environmental Engineer (ISO 14064-1/2/3, Verra VCS, Gold Standard, TCFD, SBTi, GCCA, PCAF)
**Subject:** `nepal_decarb_pro` v1.0 — 11 standards modules + Verra/GS PDD generators
**Engagement context:** PlantA Industries Ltd is intended to enter Verra validation within Q4 2026.
**Source of evidence:** `pro/nepal_decarb_pro/standards/*.py`, `pro/nepal_decarb_pro/markets/{verra,gold_standard}.py`, `pro/reports/planta_pilot_results.json`, `pro/nepal_decarb_pro/data/emission_factors.yaml`, `pro/nepal_decarb_pro/core/{cement,brick,factors,uncertainty}.py`, `docs/RATING_95_PLUS.md`.

---

## 1. Executive Summary

**Verdict: CONDITIONAL — Not VVB-ready as-shipped. High risk of validation rejection on a real Verra VCS submission.**

The engineering is genuinely good for a Tier 2/3 inventory engine. The Tier 2 mass-balance, Tier 3 kinetics enhancement, Monte Carlo UQ, and the 5,000-sample PlantA result (783 kg CO₂/t cement) are credible and roughly aligned with the published GCCA / literature range (770–810 kg/t for preheater-precalciner dry-process kilns in South Asia). That is the *good news*, and it is meaningful.

The **bad news** is that what the docs call "VCS-ready" is, from a VVB perspective, a **PDD skeleton with 22 boolean flags standing in for the entire ISO 14064 / Verra evidence trail**. Specifically:

- The Verra PDD generator emits a 1-paragraph `baseline_description`, a 1-line `monitoring_plan`, and zero documentation of *additionality*, *baseline alternative analysis*, *leakage assessment per activity*, *stakeholder consultation*, *common practice*, or *prior consideration*. A VVB cannot validate a PDD where these are absent — they are the seven most common rejection reasons at Verra validation.
- The string `"VM0009 v2.0 (Cement Plant Decarbonization)"` is **fictional**. Verra's published cement-relevant methodologies are `ACM0005` (baseline), `ACM0010` (low-GWP cement/consistency), `TOOL10` (default values), `TOOL07` (project emissions), and `AMS-III.H` (alternative waste treatment) for kiln-side interventions. `VM0009` does not exist in the Verra methodology library. Submitting a PDD citing a non-existent methodology is an automatic validation rejection.
- The "ISO 14064-1 compliance" checker self-reports 100% because seven criteria are hard-coded `met = True` regardless of evidence. That is a self-assessment, not an assessment. A VVB will not accept self-asserted booleans for §3.2 (methodology), §3.3 (EF documentation), §5.2 (materiality), §6.1 (data management), §8.1 (report contents). Each of those requires documented evidence the VVB can sample and test.
- The SBTi, TCFD, and GCCA modules contain hard-coded "1.5°C pathway" multipliers (e.g., 38.5% by 2030, scope1 × 0.5 in 1.5°C scenario) that are not traceable to SBTi's published sector pathway files. These are useful for the dashboard; they are not SBTi-validated.
- The audit trail in `io/database.py` exists but is **not wired into any calculation**. Nothing logs a `CALCULATE` event with input hash + output hash + actor. So when the VVB asks "show me the exact input set and code version that produced the 56,407 tCO₂/yr net figure," the answer today is "re-run it."

**Bottom line:** the platform can produce a *plausible draft* for VVB review. It cannot survive VVB review as-shipped. The 90-day plan in §7 will close the gap, but only if we start now and we are willing to pay for a real VVB and, ideally, a senior methodology consultant. The "11 standards" claim in the rating doc is defensible as a *module count* and indefensible as a *VVB-grade* claim.

---

## 2. Per-Standard Audit Table

The audit below is brutally honest on each axis. **C** = Coverage, **K** = Correctness, **D** = Documentation, **V** = Verifiability, **G** = #1 VVB-blocking Gap.

| # | Standard | C | K | D | V | #1 VVB-Blocking Gap |
|---|---|---|---|---|---|---|
| 1 | **ISO 14064-1:2018** (org inventory) | M | M | L | L | §3.2, §3.3, §5.2, §6.1, §8.1 are hard-coded `True`. VVB will see self-attestation, not evidence. Need actual `data_management_procedure.pdf`, `base_year_justification.md`, `materiality_calculation.xlsx` artefacts. |
| 2 | **ISO 14064-2:2019** (project) | M | M | L | L | Default args make every P.* flag `True` except P.13/P.14. The "P.4 additionality demonstrated" flag has no connection to a barrier test or investment analysis. A VVB will look for an *attachment*, not a parameter. |
| 3 | **ISO 14064-3:2019** (V&V) | L | L | L | L | This is a stub. Ten booleans. No risk-assessment matrix, no sampling plan, no competence checklist for the audit team, no site-visit protocol. Useless without rework. |
| 4 | **ISO 14001:2015** (EMS) | M | M | L | L | Auto-passes 22/25 criteria by default. Does not link to a documented EMS, aspect register, compliance obligations register, or audit programme. Certifiable framework is missing. |
| 5 | **ISO 50001:2018** (EnMS) | M | M | L | L | Same issue as 14001: 22/22 criteria pass by default. The four EnPIs are real, but there is no `energy_review.pdf`, no `energy_baseline.docx`, no `objectives_action_plan.xlsx`. |
| 6 | **TCFD** | H | M | M | M | Scenarios are arbitrary multipliers (`scope1 × 0.5` for 1.5°C). A VVB will accept *forward-looking qualitative scenarios* but will mark any quantitative claim as illustrative. This is honest *if labeled*. The current TCFD report doesn't label them. |
| 7 | **SBTi** | M | L | L | M | Pathway percentages (38.5% by 2030, 95% by 2050) are **not from the SBTi sector pathway** files. SBTi published Cement Pathway v1 (2023) and 1.5°C-aligned reductions must be derived from SDA. A 5% pa linear extrapolation is incorrect. Recommendation: replace with SBTi-published endpoint and re-derive. |
| 8 | **GCCA** | H | H | M | H | Real calc, real decomposition. Benchmark is 700 kg/t cement and 3,300 MJ/t clinker — these are GCCA "Getting the Numbers Right" 2022 global averages, but they should be *labeled as global* not as "BAT." The "BAT" label invites pushback from a VVB expecting EU BREF 2013 BAT-AEL (which is 660–770 kg/t for dry preheater-precalciner). |
| 9 | **PCAF** | H | H | M | H | Clean attribution logic (Revenue / EVIC / Physical), DQ 1–5 honored. Missing: explicit option to use *outstanding* debt vs *project finance* (PCAF Part A §2.2.3) and a clear note on PCAF 2024 updated Global Scorebook. |
| 10 | **GHG Protocol** | M | M | M | M | Scope-completeness check is fine. Significance is fine. Missing: a real **base-year recalculation policy** document and a **Scope 3 category list** (1–15) with at least a screening for relevance. Today Scope 3 is hard-coded to zero in the PlantA result (`e_scope3_tco2: 0.0`), which is a red flag. |
| 11 | **Verra VCS** (PDD) | L | L | L | L | PDD is 18 Pydantic fields, mostly scalars. The `baseline_description` is a single string. `monitoring_plan` is one sentence. No §A project boundary diagram, no §B baseline alternative analysis, no §B common practice, no §C additionality assessment, no §C prior consideration, no §C regulatory surplus, no §D leakage per activity, no §F monitoring frequency table, no §F QA/QC, no §F sampling plan, no §F data archive policy, no §G stakeholder consultation. **`methodology: "VM0009 v2.0"` is fictional — not a real Verra methodology**. |

**Verdict by axis:**
- **Coverage** — 4 high, 4 medium, 3 low (VVB blockers).
- **Correctness** — 3 high, 5 medium, 3 low.
- **Documentation** — 0 high, 4 medium, 7 low.
- **Verifiability** — 1 high, 3 medium, 7 low.
- **Most-common VVB rejection reason exposure** — all 11 modules.

The pattern is clear: the **calculations are good; the evidence trail is not**. This is exactly the failure mode I have seen in 6+ Verra rejections.

---

## 3. Verra VCS Deep-Dive (PlantA)

### 3.1 Is the PDD complete enough for VM0009 v2.0?

**No. The PDD as generated would not pass a Validation Report (VR).** A VVB-prepared VR for a real Verra submission must include, at minimum:

1. Project description with **geographic and equipment boundary** (kilns in scope, dates commissioned, capacity).
2. **Baseline scenario identification** with at least three credible alternatives + a "most plausible" baseline.
3. **Common practice analysis** demonstrating the project goes beyond typical practice in the host country/region.
4. **Additionality assessment** via the Verra-approved tool: investment analysis (IRR / NPV vs benchmark), barrier test, or common-practice test. Plus the **prior consideration** check (the project was not under construction before PDD publication).
5. **Regulatory surplus** demonstration (the project is not required by law).
6. **Leakage assessment** per activity, with a quantitative estimate and a 5–20% default.
7. **Monitoring plan** with explicit frequencies, parameters, responsible parties, QA/QC, sample retention, and data archive (typically 5 years post last credit issuance).
8. **Stakeholder consultation** (GS-style for GS; for VCS, mandatory local stakeholder consultation per VCS Standard v4 §3.4.1).
9. **Determination of baseline, project, and leakage emissions** with a parameter table, EF sources, and Monte Carlo uncertainty (with optional 5% conservative deduction).
10. **Crediting-period start date** and **duration** (renewable once, max 20 years total for VM0009-class methodologies, 7 years for AMS, 10 years for ACM).
11. **Buffer pool contribution** (Verra applies 0–20%; cannot be 15% by default — it depends on project risk classification).
12. **Validation Report template** (Form VVS-PDD-VR-001) prepared by VVB.

The current `VerraPDD` Pydantic model covers **none of #2, #3, #4, #5, #6, #7, #8, #11** in any meaningful way. It is a UI stub.

### 3.2 Are baseline scenario assumptions defensible?

The current `baseline_description` is one sentence: *"Baseline scenario: continuation of {project_type} production using current technology mix."* A VVB will reject this. We need:

- **At least 3 alternatives** evaluated (e.g., A: continuation of current mix, B: switch to imported clinker, C: switch to alternative fuels only without project, D: switch to alternative fuels + WHR + project).
- For each alternative, the **emissions trajectory over the crediting period** (10 years), with a documented assumption for fuel prices, NEA grid EF, and capacity utilization.
- A **documented selection of the most plausible baseline** citing the Verra Combined Tool and project-specific evidence.
- A **baseline emissions calculation** with EF table, formula, and Monte Carlo UQ.

For PlantA specifically, I would propose:
- **Baseline**: continue 100% coal/petcoke dry-process preheater-precalciner, 5-stage, current 950,000 t/yr clinker, 1,100,000 t/yr cement, 22.5% T&D, NEA combined margin 0.0256 kg CO₂/kWh, 783 kg CO₂/t cement × 1.1M t = 861,000 tCO₂/yr. **This is what the platform already produces and is defensible.**
- **Project alternative**: add rice husk co-firing (20% energy basis) + WHR (22 GWh/yr) → 791,000 tCO₂/yr, 70,000 tCO₂/yr gross reduction, ~56,000 tCO₂/yr net after leakage and buffer.

### 3.3 Is the additionality demonstration solid?

**No additionality demonstration exists in the platform.** A Verra-compliant additionality assessment for PlantA would require, at minimum:

- **Investment analysis** (mandatory for ACM-class): NPV of project with and without carbon revenue, IRR vs Cement Industry Association of Nepal (CIN) WACC of 12–15%. Show that the project is *not* financially attractive without carbon revenue (i.e., negative NPV at the hurdle rate).
- **Barrier test** (if investment test is inconclusive): e.g., the biomass supply chain in the PlantA district is not yet developed; the kiln-side infrastructure (biomass pre-drying, dosing system) requires capex the plant has not budgeted.
- **Common-practice test**: PlantA is the only Nepali plant to install WHR + biomass co-firing to date. Cite the FNCCI / DCSI surveys.
- **Prior consideration**: the PDD must be published on the Verra pipeline *before* project implementation begins. We need a published "Pipeline" date and proof that the capex commitment was made after that date.

The current PDD has *zero* of these. Add an `AdditionalityAssessment` Pydantic model with `investment_analysis_xlsx`, `barrier_test_narrative`, `common_practice_table`, `prior_consideration_evidence`, all referenced as `Path` attachments.

### 3.4 Most common Verra rejection reasons, and our exposure

| Rejection reason | Frequency (Verra public) | Our exposure |
|---|---|---|
| Fictional / wrong methodology citation | Medium | **CRITICAL** — `VM0009 v2.0` does not exist |
| Missing or weak additionality | High | **CRITICAL** — none present |
| Missing baseline alternative analysis | High | **CRITICAL** — none present |
| Insufficient common-practice analysis | Medium-High | **CRITICAL** — none present |
| Missing or weak leakage assessment | Medium | **HIGH** — flat 5% with no basis |
| Missing or generic monitoring plan | Medium-High | **CRITICAL** — one sentence |
| Stakeholder consultation missing / inadequate | Medium | **HIGH** — only generic text in GS, absent in VCS |
| Inadequate data archive / audit trail | Low-Medium | **HIGH** — `audit_log` table exists but not wired |
| Wrong buffer pool contribution | Low | **MEDIUM** — 15% blanket is not Verra-risk-justified |
| EF sources not authoritative | Low | **OK** — IPCC/NEA sources are authoritative |
| Wet/dry kiln mix-up | Low | **OK** — explicit field |
| Wrong crediting period | Low | **MEDIUM** — 10 yr is correct for ACM; 7 yr for GS; need to align with chosen methodology |
| Unit / mass-balance error | Low | **OK** — Tier 2 mass-balance is correct |
| Lack of Tier 3 reconciliation | Medium | **MEDIUM** — Tier 3 is in code but not part of the audit trail |

### 3.5 Sample Validation Report template

A Verra-acceptable Validation Report must contain:
1. **Executive summary** with VVB opinion
2. **Scope of validation** (which sections, which version of methodology, which version of PDD)
3. **VVB team competence & independence statement** (with CVs)
4. **Methodology applied** (ISO 14064-3, VCS Standard v4, methodology-specific)
5. **Findings by PDD section** with a CAR (Corrective Action Request) / CL (Clarification) / FAR (Forward Action Request) tracker
6. **Risk-based assessment** (likelihood × impact for each material misstatement)
7. **Sampling plan** (if any)
8. **Site-visit report** (PlantA: 1–2 days minimum)
9. **Materiality threshold** (typically 5% for VCS voluntary)
10. **Conclusion and VVB opinion** (signed)
11. **Appendices**: PDD, monitoring plan, additionality narrative, baseline alternative table, EF source table, calculation spreadsheet, stakeholder consultation log.

The platform should provide a `VRGenerator` that, given a `VerraPDD` + attachments, drafts a 90% complete VR. The VVB edits, signs, and submits. We do not have this today.

---

## 4. Top 10 VVB-Blocking Issues (with severity)

| # | Issue | Severity | Module | Owner | Fix effort |
|---|---|---|---|---|---|
| 1 | **`VM0009 v2.0` is a fictional methodology** | CRITICAL | `markets/verra.py` | Mavis | 1 day — change to ACM0005/ACM0010 or AMS-III.H and add a methodology-selection rule |
| 2 | **No additionality assessment in PDD** | CRITICAL | `markets/verra.py` | Mavis + senior methodologist | 1 week — add `AdditionalityAssessment` model with investment-analysis attachment |
| 3 | **No baseline alternative analysis (≥3 alternatives)** | CRITICAL | `markets/verra.py` | Mavis + plant engineering | 1 week — `BaselineAlternatives` model with emissions trajectories |
| 4 | **Monitoring plan is one sentence** | CRITICAL | `markets/verra.py` | Mavis | 3 days — structured `MonitoringPlan` with frequencies, parameters, QA/QC, archive |
| 5 | **Audit trail not wired into calculations** | CRITICAL | `io/database.py`, all calculators | Mavis | 1 week — emit `AuditEntry(action="CALCULATE", details={input_hash, output_hash, code_version})` from every calc |
| 6 | **ISO 14064-1 self-asserts 7/20 criteria as `True`** | HIGH | `standards/iso_14064.py` | Mavis | 3 days — replace with evidence-pointer booleans that fail closed |
| 7 | **SBTi pathway percentages are not from SBTi files** | HIGH | `standards/sbti.py` | Mavis | 3 days — replace hard-coded 38.5% with SBTi-published 2030 endpoint (522 kg/t for cement, SDA method) |
| 8 | **Scope 3 hard-coded to zero in PlantA result** | HIGH | `core/cement.py`, `reports/` | Mavis + plant | 1 week — implement Cat 1, 3, 4, 9, 10 minimum; report explicitly when zero |
| 9 | **TCFD scenarios use arbitrary multipliers, labeled as quantitative** | MEDIUM | `standards/tcfd.py` | Mavis | 2 days — add `qualitative=True` flag and a forward-looking scenario methodology note |
| 10 | **Verra buffer pool contribution is a flat 15%** | MEDIUM | `markets/verra.py` | Mavis | 2 days — implement Verra AFOLU Non-Permanence Risk Tool (or a non-AFOLU equivalent for industry: 5–15% depending on reversal risk) |

Bonus (not in top 10 but high-impact): **GWP values are AR5 (100-year)**, not AR6. SBTi moved to AR6 in 2024. ISO 14064-1:2018 is now superseded by ISO 14064-1:2025 (which requires AR6 for CO₂e). We should migrate to AR6 GWPs in v1.1.

---

## 5. Methodology Paper Recommendations

To establish credibility and pre-empt VVB questions, we should publish **two peer-reviewed methodology papers** before validation:

1. **"A Tier 3 mass+energy balance for preheater-precalciner dry-process cement kilns in the Himalayan region, with application to PlantA, Nepal"** — target *Journal of Cleaner Production* or *Applied Energy*. Co-author with a Nepali academic (Tribhuvan University, Kathmandu University) and a recognized cement-engineering academic (e.g., IIT Delhi Energy Group or ETH Zurich Particle Technology Lab). Establishes the Tier 3 methodology in peer-reviewed literature. Lead author: Mavis + external co-authors.
2. **"Comparative baseline additionality assessment for biomass co-firing and waste-heat recovery in a South Asian cement plant: a Verra VCS case study"** — target *Energy Policy* or *Climate Policy*. Documents the additionality methodology (investment analysis + barrier test + common practice). Establishes the NPV/IRR assumptions for the cement sector in Nepal. Lead author: senior methodologist + Mavis.

These papers will take 4–6 months each. They are not blocking the first VVB submission but they are blocking *scale* — once we have 5+ projects, we need literature support to defend methodology choices.

---

## 6. Recommended VVB Relationships

| VVB | Why | Cost estimate (10-yr crediting, 1 plant) | Recommendation |
|---|---|---|---|
| **TÜV SÜD South Asia** (Bangalore / Delhi) | Largest industrial VCS track record globally; APAC desk with Hindi/Nepali-capable staff; has validated ACM0005, ACM0010, AMS-III.H projects. Strong in cement (Holcim, Adani, UltraTech). | $25–35k validation + $15–20k/year verification × 10 = $175–235k | **PRIMARY** |
| **RINA Services S.p.A.** (Italy + India) | Strong in steel/cement; cheaper than TÜV; accredited for VCS, GS, ISO 14064-3. Good in South Asia. | $20–30k + $12–18k/yr = $140–210k | **SECONDARY** |
| **DNV** (Norway + India) | Largest VCS verifier by volume globally. Best methodology library access; can answer methodology questions in real time. | $30–40k + $18–22k/yr = $210–260k | **BACKUP** |
| **ERM CVS** (UK) | ESG-focused; good for combined TCFD + VCS engagements; experienced in emerging markets. | $25–40k + $15–25k/yr = $175–290k | **RESERVE** |
| **AENOR** (Spain) | Spanish; Latin-America and South-Asia focus; smaller and more flexible. | $20–28k + $12–16k/yr = $140–188k | **RESERVE** |
| **TÜV NORD** (Germany) | Mentioned in the Gold Standard PDD generator; strong ISO 14064-3 accreditations. | $22–30k + $14–18k/yr = $162–210k | **OPTIONAL** |

**My recommendation: lead with TÜV SÜD South Asia**, with RINA as a price-benchmarking second quote. DNV as backup if TÜV SÜD declines (unlikely; cement is their bread and butter). Engage TÜV SÜD in week 1, request a "pre-validation gap analysis" engagement ($5–8k) before the formal validation.

---

## 7. 90-Day Plan to Get PlantA Through Full VVB Validation

### Days 0–14: Foundations
- Day 0: Engage TÜV SÜD South Asia. Sign NDA. Commission pre-validation gap analysis.
- Day 1–3: Replace fictional `VM0009 v2.0` with a real methodology decision. My recommendation: **AMS-III.H** for the WHR component (kiln exhaust to electricity) + **ACM0010** for the low-carbon cement intensity. Decision to be ratified by TÜV SÜD.
- Day 4–7: Wire audit trail into every calculation. Every `calculate_cement_tier2`, `monte_carlo_cement`, `generate_verra_pdd` call must emit an `AuditEntry` with `input_hash` (sha256 of serialized inputs), `output_hash`, `code_version` (git SHA), `user_id`, and `timestamp`. Backed by SQLite + (later) PostgreSQL.
- Day 8–14: Hire/contract a senior methodology consultant (e.g., 20-year Verra ex-staff or Carbon Check India) for 30 days to draft the additionality narrative, baseline alternative analysis, and stakeholder consultation log.

### Days 15–45: PDD v2
- Day 15–21: Rewrite the Verra PDD generator to produce a real, structured PDD. Use the Verra PDD template (Form VCS-PDD v4.0) as the schema. Add: project boundary diagram (GeoJSON + plant layout), GWP table, source/sink table, parameter table, EF table, monitoring frequency table, QA/QC procedures, data archive policy.
- Day 22–28: Build `AdditionalityAssessment` module: investment analysis spreadsheet (NPV, IRR, sensitivity), barrier test narrative, common-practice table, prior-consideration evidence.
- Day 29–35: Build `BaselineAlternatives` module: 3+ alternative emissions trajectories, documented assumptions (fuel prices, NEA grid EF, capacity utilization), justification for selected baseline.
- Day 36–42: Build `MonitoringPlan` module: structured parameter table (parameter, source, frequency, responsible party, uncertainty), data archive (5 years post-issuance), QA/QC procedures (calibration schedule, sample retention, internal audit).
- Day 43–45: Stakeholder consultation (1–2 days, in PlantA district, with kiln workers, plant management, local government, civil society). Document minutes + signed attendance + photos.

### Days 46–60: VVB Pre-Validation
- Day 46–50: Submit PDD v2 to TÜV SÜD for pre-validation review. Expect 3–5 rounds of CARs/CLs.
- Day 51–60: Resolve CARs. Typical CAR types: "provide EF source for X", "justify the 20% biomass substitution rate", "show the GWP100 values used in the calc."

### Days 61–75: Internal Verification (ISO 14064-3 Stage 1)
- Day 61–65: Internal audit of the GHG information system. Document the data flow from MQTT sensor → SQLite → calculation → PDD.
- Day 66–70: Materiality assessment. For PlantA, set materiality at 5% of gross emission reductions (i.e., 3,500 tCO₂/yr).
- Day 71–75: Risk-based assessment. Likelihood × impact matrix for each material misstatement source.

### Days 76–90: VVB Validation & PDD Publication
- Day 76–82: TÜV SÜD site visit (PlantA, 2 days minimum). Document in `SiteVisitReport.pdf`.
- Day 83–88: TÜV SÜD issues draft Validation Report. We respond.
- Day 89: TÜV SÜD issues final Validation Report.
- Day 90: PDD + VR + supporting docs submitted to Verra pipeline. Public comment (30 days) begins.

This is **aggressive but feasible** if we start today and accept a $40–60k spend in VVB + consultant fees.

---

## 8. Specific Gaps in VM0009 / ACM0010 / AMS-III.H Implementation

(Note: the current code claims `VM0009 v2.0` which does not exist. Below I treat VM0009 as the intended target, but the same gaps apply to ACM0010 / AMS-III.H.)

1. **Combined Tool** (TOOL10 / TOOL07) integration is missing. The platform should expose the actual tool's equations and default values.
2. **T&D loss adjustment** is currently `1/(1-loss)` (correct for delivery-side adjustment) but the methodology specifies *transmission + distribution* line losses, not just T&D; some methodologies require additional auxiliary load. Document this.
3. **Grid EF** is currently a static 0.0256 kg CO₂/kWh (NEA combined margin). For a 10-year crediting period, we need a *forecast* of grid EF — Nepal is expected to add 5–10 GW of hydropower in this period, which will *reduce* the grid EF and *reduce* the project emission reductions from WHR. The platform should model this.
4. **Default value** in cement calcination: 0.7857 t CO₂/t CaO is correct (44/56 from CaCO₃ → CaO + CO₂). MgO at 1.092 is also correct (44/40.3 from MgCO₃). The code is right here; it just needs the methodology citation in the comment.
5. **TOC (Total Organic Carbon) in raw mix** is set to a fixed 0.10% in Tier 3. The Verra methodology requires that this be measured per-plant. Add a `raw_mix_toc_fraction` field to `CementPlant` and require a measured value.
6. **Precalciner efficiency** is set to a fixed 0.92. Should be a measured value per kiln.
7. **Buffer pool** is hard-coded 15%. The Verra AFOLU Non-Permanence Risk Tool does not apply directly to industry projects, but Verra's industry project guidelines specify a 5–20% buffer depending on reversal risk. Add a risk-classification step.
8. **Leakage**: the 5% default is correct for many cases but should be assessed per project activity. Biomass supply chain leakage (e.g., rice husk competing with animal feed) is a real risk in Nepal and should be quantified.
9. **Common practice analysis**: the platform should auto-query a database of Nepali cement plants and show that biomass + WHR is not yet standard practice.
10. **Crediting period renewal**: ACM methodologies are renewable once (up to 20 years total). The current generator does not support renewal. Add a `crediting_period_renewal` flag.

---

## 9. Sample Validation Pack Checklist (what we send the VVB)

The validation pack is a single ZIP file (~50–200 MB) sent to the VVB. Required contents:

- [ ] **Cover letter** (signed by HCN project director)
- [ ] **PDD v2** (`PDD_PlantA_Decarb_v2.0.pdf` + `.docx` for review markup)
- [ ] **Validation Report draft** (we draft, VVB edits)
- [ ] **Monitoring Plan v2** (parameter table, frequencies, QA/QC, archive policy)
- [ ] **Additionality Assessment** (investment analysis `.xlsx`, barrier test narrative `.pdf`, common-practice table `.pdf`, prior-consideration evidence)
- [ ] **Baseline Alternatives Analysis** (≥3 alternatives with emissions trajectories, sensitivity, selection justification)
- [ ] **Emission Factor Source Table** (every EF with citation, page, date retrieved)
- [ ] **Calculation Spreadsheet** (Verra-style: transparent, audit-trail-linked, hand-verifiable in Excel) + cross-reference to platform JSON output
- [ ] **Stakeholder Consultation Log** (signed attendance, minutes, photos, grievance mechanism)
- [ ] **Site Layout / Project Boundary Diagram** (PFD + P&ID + GeoJSON of plant boundary)
- [ ] **Operator Competence Statements** (plant manager, chief engineer, EHS officer CVs)
- [ ] **Data Management Procedure** (input, processing, output, archive, retention, integrity)
- [ ] **Internal Audit Report** (ISO 14064-3 Stage 1 audit, ≤ 90 days old)
- [ ] **Risk Assessment Matrix** (likelihood × impact for each material misstatement)
- [ ] **Materiality Threshold Justification** (5% of gross reductions; calculation)
- [ ] **GWP Source** (currently AR5; migrate to AR6 for ISO 14064-1:2025 alignment)
- [ ] **Audit Trail Export** (SQLite dump, all CALCULATE entries, with input/output hashes)
- [ ] **GHG Information System Description** (MQTT → SQLite → calc → PDD flow diagram)
- [ ] **VVB Engagement Letter** (signed)
- [ ] **Prior Consideration Evidence** (PDD publication date, plant capex commitment dates)

---

## 10. Concrete 30-Day Deliverables

The team must produce, by **2026-08-21**:

1. **`docs/templates/validation_pack_template.md`** — a fill-in-the-blank template for items 1–20 above. Each section prompts for content + has a "VVB expectation" note. Mavis to author, Nishchal to review.
2. **`docs/whitepapers/gcca_equivalent_methodology.md`** — a 4,000-word white paper formalizing the GCCA-equivalent methodology for Nepali cement, including Tier 2 + Tier 3 equations, EF table, common-practice analysis, and uncertainty approach. Target: lead to a peer-reviewed paper by Q4 2026.
3. **`docs/legal/vvb_engagement_letter_draft.md`** — draft engagement letter for TÜV SÜD South Asia. Two parts: (a) pre-validation gap analysis ($5–8k, 10 days), (b) full validation engagement ($25–35k, 60 days). Use the IETA Model Contract as basis. Include data-room provision.
4. **`pro/nepal_decarb_pro/audit/trail.py`** — new module that wraps every calculation with an audit entry. Functions decorated with `@audit_trail` emit `AuditEntry(action="CALCULATE", entity_type=..., entity_id=..., details={input_hash, output_hash, code_version, timestamp})`. Wire into `cement.py::calculate_cement_tier2/3`, `monte_carlo_cement`, `generate_verra_pdd`, `generate_gold_standard_pdd`, and the standards checkers. Tests for immutability of audit log.
5. **Methodology Decision Memo** (`docs/strategy/methodology_decision.md`) — 2-page memo recommending AMS-III.H + ACM0010 (or alternative) over the fictional VM0009, with a 4-week decision matrix.

---

## Closing Note

The platform is genuinely impressive in its **engineering scope**. I have not seen a Tier 2 + Tier 3 + Monte Carlo + Sobol + NSGA-II + Verra PDD + 8 standards checkers in any other open-source tool. The engineering team should be proud of that.

But **"VVB-ready" is a different bar than "engineering-complete"**. A VVB does not care about NSGA-II Pareto fronts or Sobol indices. They care about: *can you show me the calculation, the inputs, the EF source, the additionality, the baseline alternative, the stakeholder, the monitoring plan, the QA/QC, the audit trail.* Six of those nine items are not in the code today.

The 90-day plan and the 30-day deliverables are realistic. The Verra submission timeline is realistic (90 days + 30-day public comment + 60-day review = 6 months to first credit issuance). The cost is real (~$50–60k in VVB + consultant fees for validation). The risk of rejection without these fixes is **near-certain**.

Take the 90 days. Spend the money. Publish the two methodology papers. We will be the first Nepalese project through Verra validation, and that is worth doing right.

— Senior Environmental Engineer, 2026-07-22
