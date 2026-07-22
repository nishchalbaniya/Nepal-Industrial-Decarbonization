# Verra VCS Validation Pack — Fill-in-the-Blank Template
### For: Hetauda Cement Industries Ltd — Decarbonization Project
### Verra Registry: `[to be assigned on pipeline publication]`
### Author: Himalayan Carbon Nepal · Author: Mavis, CTO · Reviewer: Nishchal Baniya, Founder
### Last updated: 2026-07-22

> **How to use this template.** Each section has a `VVB Expectation` note that says what the
> third-party Validation/Verification Body (VVB) is looking for. Fill in *only* the `<<...>>`
> placeholders. The VVB will sample and re-calculate; if a placeholder is empty or the content is
> generic, the VVB issues a Corrective Action Request (CAR) and the validation timeline slips.
> Every numeric value must be traceable to an attached evidence file.

---

## SECTION 0 — Cover Letter
**File:** `00_cover_letter.pdf` · **Owner:** Project Director

```
[Letterhead — Himalayan Carbon Nepal]

To: <<VVB_NAME>> (e.g., TÜV SÜD South Asia)
Re: Engagement to validate the <<PROJECT_NAME>> VCS Project (Methodology: <<METHOD>>)

Dear <<VVB_CONTACT>>,

Himalayan Carbon Nepal is pleased to submit the attached Validation Pack for the
<<PROJECT_NAME>> ("the Project"), a Verra VCS project located at <<PLANT_NAME>> in
<<DISTRICT>>, <<COUNTRY>>. The Project applies the Verra-approved methodology
<<METHOD>> (version <<X.Y>>) and is expected to deliver approximately
<<NN,NNN>> tCO₂e/yr in net emission reductions over a <<N>>-year crediting period.

We propose the following engagement structure:
  - Stage 1: Pre-validation gap analysis (10 working days)
  - Stage 2: Validation including site visit (60 working days)
  - Stage 3: First verification at end of Year 1 (separate engagement)

Enclosed:
  1. This cover letter
  2. Signed Engagement Letter (Schedule A)
  3. Validation Pack (Sections 1–20, this template)
  4. Data room access credentials (<<SECURE_LINK>>)

We confirm:
  - All information provided is true and complete to the best of our knowledge.
  - No project capex commitment was made before the PDD pipeline publication
    date of <<YYYY-MM-DD>>.
  - The Project Proponent retains operational control of the host plant.

Sincerely,
<<NAME>>, Project Director
<<SIGNATURE>>, <<DATE>>
```

**VVB Expectation:** One-page cover, signed, dated, with project IDs, methodology version, and PDD pipeline date. Without these, the VVB cannot start the 5-business-day Stage 1 review.

---

## SECTION 1 — Project Design Document (PDD)
**File:** `01_PDD_<<PROJECT_NAME>>_v<<X.Y>>.pdf` and `.docx`
**Owner:** Mavis (CTO) + senior methodology consultant
**Source:** Use Verra Form VCS-PDD v4.0 (latest published). Do **not** freeform.

### §A — Project description
- **§A.1 Project title:** `<<PROJECT_NAME>>`
- **§A.2 Project ID:** `<<VCS_REGISTRY_ID>>` (assigned at pipeline)
- **§A.3 Project proponent:** `<<HCN_LEGAL_NAME>>`, registration `<<REG>>`, country `NP`
- **§A.4 Host organization:** `<<PLANT_NAME>>`, address `<<ADDRESS>>`, country `NP`
- **§A.5 Project location:** lat/lon `<<LAT>>`, `<<LON>>`; district `<<DISTRICT>>`; province `<<PROVINCE>>`
- **§A.6 Project start date:** `<<YYYY-MM-DD>>` (must be ≥ 1 day after pipeline publication)
- **§A.7 Crediting period start:** `<<YYYY-MM-DD>>` (= start of first monitoring year)
- **§A.8 Crediting period length:** `<<N>>` years (≤ 10 for ACM, ≤ 7 for AMS, ≤ 20 for VM-class)
- **§A.9 Project type:** `<<Sector | Activity>>` (e.g., `Cement | Alternative fuels + WHR`)
- **§A.10 Technology:** `<<Biomass co-firing (rice husk, sawdust) + WHR turbine>>`
- **§A.11 Sectoral scope:** `05 – Mineral industry / 01 – Energy industries (renewable)`
- **§A.12 Project boundary (geographic):** GeoJSON of plant perimeter, attached as `01A_boundary.geojson`
- **§A.13 Project boundary (equipment):** PFD of cement plant with **highlighted** project equipment (rice husk dryer, dosing system, WHR turbine, generator, grid interconnection), attached as `01B_pfd_with_project_highlight.pdf`
- **§A.14 Project boundary (gases):** CO₂, CH₄, N₂O (per IPCC AR6 GWPs)
- **§A.15 Project activities (numbered list):**
  1. Install rice husk pre-drying and dosing system at Kiln 1
  2. Install 22 GWh/yr waste-heat recovery turbine on kiln exhaust
  3. Re-route kiln exhaust to WHR turbine (bypass preheater)
  4. Build rice husk procurement contract with Tarai biomass cooperative
  5. Deploy IoT sensors for fuel flow, kiln temperature, and electricity generation (MQTT)
  6. Implement quarterly monitoring + annual VVB verification
- **§A.16 Estimated annual emission reductions:** `<<NN,NNN>>` tCO₂e/yr (gross); `<<NN,NNN>>` (net after buffer)

**VVB Expectation:** GeoJSON + PFD are **mandatory**. The PDD must show what the project changes vs. the baseline; vague "decarbonization technology adoption" is a CAR.

### §B — Baseline scenario
- **§B.1 Identified alternatives (minimum 3):**
  - **Alternative B.1:** Continuation of current fuel mix (100% coal + petcoke, no WHR, no biomass)
  - **Alternative B.2:** Switch to imported clinker (no domestic production, kiln mothballed)
  - **Alternative B.3:** Switch to petcoke only (no WHR, no biomass)
  - **Alternative B.4 (selected):** B.1 — most plausible per investment analysis and regulatory environment
- **§B.2 Emissions trajectory (10-year) for each alternative** — table with year-by-year tCO₂/yr, attached as `01C_baseline_alternatives.xlsx`
- **§B.3 Selected baseline justification:** 1-page narrative + the Combined Tool (TOOL10) analysis
- **§B.4 Common practice analysis:** table of all Nepali cement plants + kiln technologies + biomass use + WHR, attached as `01D_common_practice.xlsx`. Cite FNCCI 2023, DCSI 2024, UNEP/GEF 2018.
- **§B.5 Baseline emissions (annual):** `<<NNN,NNN>>` tCO₂/yr with Monte Carlo UQ (5,000+ samples, 95% CI)
- **§B.6 Baseline intensity:** `<<NNN>>` kg CO₂/t cement
- **§B.7 Baseline SEC:** `<<N,NNN>>` MJ/t clinker

**VVB Expectation:** **The 3-alternative analysis is the #1 rejection reason at Verra.** A 1-sentence "baseline_description" (as the current code generates) is **automatic rejection**. Provide a defensible emissions trajectory for each alternative.

### §C — Additionality
- **§C.1 Additionality tool used:** Verra Combined Tool (Tool01) — investment analysis + barrier test + common practice
- **§C.2 Investment analysis:**
  - IRR without carbon revenue: `<<X.X%>>` (negative or below WACC)
  - IRR with carbon revenue: `<<X.X%>>`
  - WACC benchmark: `<<12.0%>>` (Cement Industry Association of Nepal + Tribhuvan University 2023)
  - NPV at 10% discount: `<<$X.X million>>` (negative without credits)
  - Spreadsheet: `01E_investment_analysis.xlsx`
- **§C.3 Barrier test:**
  - **Investment barrier:** HCN has secured 60% of capex from NRB Green Finance Facility; balance is dependent on forward carbon revenue.
  - **Technological barrier:** No Nepali plant has integrated rice husk pre-drying + WHR; vendor (Loesche, FLSmidth) is foreign with limited local service.
  - **Institutional barrier:** Biomass supply chain is not yet developed in the Hetauda district; we are creating it.
  - Narrative: `01F_barrier_test.pdf`
- **§C.4 Common practice test:**
  - Survey of 6 Nepali cement plants (Hetauda, Udayapur, Hongshi, Shree, Ghorahi, Araniko) — none have biomass + WHR.
  - Table: `01D_common_practice.xlsx`
- **§C.5 Prior consideration:**
  - Pipeline publication date: `<<YYYY-MM-DD>>`
  - Plant capex commitment date: `<<YYYY-MM-DD>>` (must be after pipeline date)
  - Evidence: `01G_prior_consideration_evidence.pdf` (board minutes, RFP date, vendor contract date)
- **§C.6 Regulatory surplus:**
  - Nepal has no carbon tax, no emission performance standard, no cap.
  - The project is not mandated by any current or planned law as of `<<YYYY-MM-DD>>`.
  - Statement: `01H_regulatory_surplus.pdf`

**VVB Expectation:** All 5 tests are mandatory for ACM-class methodologies. Each test must produce a positive finding; if any test is inconclusive, the VVB rejects.

### §D — Leakage
- **§D.1 Leakage assessment per activity:**
  - Activity 1 (biomass sourcing): potential rice-husk competition with animal feed; mitigated by sourcing from mills, not farms. Estimated leakage: `<<1.5%>>`.
  - Activity 2 (WHR): no market displacement, no leakage. Estimated leakage: `<<0%>>`.
  - Aggregate leakage: `<<2.0%>>` (below 5% default, justified)
- **§D.2 Leakage calculation spreadsheet:** `01I_leakage.xlsx`
- **§D.3 Monitoring of leakage:** Annual rice-husk price survey in Hetauda district; recorded in monitoring report.

**VVB Expectation:** A flat 5% leakage (as the current code uses) is acceptable only with a one-page justification. A calculated per-activity leakage is preferred and is VVB-friendly.

### §E — Emission reductions
- **§E.1 Gross emission reductions (annual):** `<<NN,NNN>>` tCO₂/yr
- **§E.2 Leakage deduction:** `<<N,NNN>>` tCO₂/yr
- **§E.3 Net emission reductions (pre-buffer):** `<<NN,NNN>>` tCO₂/yr
- **§E.4 Buffer pool contribution:** `<<NN%>>` per risk classification (see §F.7)
- **§E.5 Net issuable credits (annual):** `<<NN,NNN>>` tCO₂/yr
- **§E.6 Total over crediting period:** `<<NNN,NNN>>` tCO₂e

### §F — Monitoring plan
- **§F.1 Parameter table:** see `01J_monitoring_parameter_table.xlsx`
- **§F.2 Monitoring frequencies:** see same spreadsheet
- **§F.3 QA/QC procedures:** `01K_qaqc_procedures.pdf`
- **§F.4 Sampling plan (if applicable):** `01L_sampling_plan.pdf`
- **§F.5 Data archive:** all raw data, sensor logs, calibration records retained for `<<5 years>>` post last issuance, in cloud (`<<PROVIDER>>`) + on-site encrypted NAS
- **§F.6 Calibration schedule:** quarterly for flow meters, annually for gas analyzers
- **§F.7 Buffer pool risk classification:** see `01M_buffer_classification.pdf` (5%, 10%, 15%, or 20% based on non-permanence risk)

**VVB Expectation:** The current code's "one-sentence monitoring plan" is **automatic rejection**. A 5+ page structured plan with parameter table is the minimum.

### §G — Stakeholder consultation
- **§G.1 Local stakeholders consulted:** plant workers, plant management, kiln workers' families, local government (Hetauda sub-metropolitan), civil society (FNCCI, CECI Nepal)
- **§G.2 Date(s) and location(s):** `<<YYYY-MM-DD>>` at `<<VENUE>>`
- **§G.3 Minutes of meeting:** `01N_stakeholder_minutes.pdf` (signed by attendees)
- **§G.4 Attendance sheet:** `01O_attendance.pdf` (with signatures)
- **§G.5 Photos:** `01P_stakeholder_photos/`
- **§G.6 Grievance mechanism:** `01Q_grievance_mechanism.pdf` (24/7 hotline, written log, response within 14 days)
- **§G.7 Free, prior, and informed consent (FPIC):** obtained `<<Y/N>>` (Y if Indigenous Peoples are affected)

**VVB Expectation:** A GS-style "multi-stakeholder consultation was conducted" sentence is **not** a stakeholder consultation. The VVB looks for minutes, attendance, photos, and a grievance mechanism.

### §H — Project proponent declaration
- Signed by Project Director and CFO
- Date: `<<YYYY-MM-DD>>`
- File: `01R_proponent_declaration.pdf`

---

## SECTION 2 — Validation Report (VVB-prepared, we supply draft)
**File:** `02_Validation_Report_v0.1_draft.docx` (VVB edits and signs)
**Owner:** Mavis drafts, TÜV SÜD edits

| VR Section | Content |
|---|---|
| §1 Executive summary | 1 page; VVB opinion (favorable / not favorable) |
| §2 Scope of validation | PDD version, methodology version, VCS Standard version |
| §3 VVB team | Names, roles, competence (CVs as `02A_vvb_team_cvs.pdf`), independence statement |
| §4 Methodology applied | ISO 14064-3:2019 + VCS Standard v4.6 + selected methodology |
| §5 Findings by PDD section | CAR / CL / FAR tracker with resolution status |
| §6 Risk-based assessment | Likelihood × impact matrix (5×5) for each material misstatement |
| §7 Sampling plan | Sample-based recalculation of N randomly-selected parameters |
| §8 Site visit report | `02B_site_visit_report.pdf`, dated `<<YYYY-MM-DD>>` |
| §9 Materiality threshold | 5% of gross reductions, justified |
| §10 Conclusion and VVB opinion | Signed by lead validator |
| §11 Appendices | All Section 1 files + recalculation evidence |

**VVB Expectation:** The VVB writes and signs the VR. We do not sign it. We *do* draft 90% of it to save VVB hours.

---

## SECTION 3 — Calculation Spreadsheet (VVB-style, transparent)
**File:** `03_calculation_spreadsheet.xlsx` (Excel) **+** `03_calculation_spreadsheet.pdf` (printable)
**Owner:** Mavis (CTO) + Nishchal (reviewer)

Spreadsheet must have one row per equation, with:
- Row 1: Equation description (e.g., "CO₂ from coal combustion = mass × NCV × EF / 1000")
- Row 2: IPCC equation reference (e.g., "Eq. 2.5, IPCC 2006 Vol.2 Ch.1")
- Row 3: Inputs (with units and source)
- Row 4: Intermediate calculation
- Row 5: Output (with units)
- Row 6: Cross-reference to `nepal_decarb_pro` JSON output

**Every cell** must show:
- The formula (not just the result)
- The input source (e.g., "plant.fuel_use[0].consumption_t = 120,000 t/yr, from plant survey Q4 2024")
- The EF source (e.g., "94.6 kg CO₂/GJ, from IPCC 2006 Vol.2 Ch.1 Table 2.2, default for other bituminous coal")

**VVB Expectation:** This is the document the VVB will re-calculate in Excel to verify. If the spreadsheet is opaque (formulas hidden, paste-of-result), it is a CAR.

---

## SECTION 4 — Emission Factor Source Table
**File:** `04_emission_factors.xlsx` (and `.pdf` for printing)
**Owner:** Mavis

| # | Parameter | Value | Unit | Source | Page / Equation | Date retrieved | Confidence |
|---|---|---|---|---|---|---|---|
| 1 | Coal (bituminous, NP) — NCV | 25.5 | GJ/t | IPCC 2006 Vol.2 Ch.1 Table 1.2 | Default — other bituminous | 2026-07-15 | High |
| 2 | Coal (bituminous, NP) — EF | 94.6 | kg CO₂/GJ | IPCC 2006 Vol.2 Ch.1 Table 1.4 | Default — other bituminous | 2026-07-15 | High |
| 3 | Petcoke — NCV | 32.0 | GJ/t | IPCC 2006 Vol.2 Ch.1 Table 1.2 | Petroleum coke | 2026-07-15 | High |
| 4 | Petcoke — EF | 97.5 | kg CO₂/GJ | IPCC 2006 Vol.2 Ch.1 Table 1.4 | Petroleum coke | 2026-07-15 | High |
| 5 | Diesel — NCV | 43.0 | GJ/t | IPCC 2006 Vol.2 Ch.1 Table 1.2 | Other petroleum — diesel | 2026-07-15 | High |
| 6 | Diesel — EF | 74.1 | kg CO₂/GJ | IPCC 2006 Vol.2 Ch.1 Table 1.4 | Other petroleum — diesel | 2026-07-15 | High |
| 7 | Rice husk — NCV | 13.4 | GJ/t | FAO/EBTP 2017 + field survey | n/a | 2024-09-12 | Medium |
| 8 | Rice husk — EF | 0.0 (biogenic) | kg CO₂/GJ | IPCC 2006 (biogenic CO₂ reported separately) | n/a | 2026-07-15 | High |
| 9 | NEA grid combined margin | 0.0256 | kg CO₂/kWh | NEA Annual Report 2023/24 + CDM ACM0012 | n/a | 2024-12-01 | Medium |
| 10 | NEA T&D loss | 0.225 | fraction | NEA Annual Report 2023/24 | Annex 4 | 2024-12-01 | High |
| 11 | CaO stoichiometric ratio | 0.7857 | t CO₂/t CaO | Stoichiometry (44/56) | n/a | n/a | High |
| 12 | MgO stoichiometric ratio | 1.092 | t CO₂/t MgO | Stoichiometry (44/40.3) | n/a | n/a | High |
| 13 | Clinker CaO content | 0.65 | fraction | Plant survey 2024 + IPCC 2006 default | n/a | 2024-12-15 | Medium |
| 14 | Clinker MgO content | 0.015 | fraction | Plant survey 2024 + IPCC 2006 default | n/a | 2024-12-15 | Medium |
| 15 | AR5 GWP — CH₄ | 28 | n/a | IPCC AR5 (100-yr) | Table 8.7 | 2026-07-15 | High |
| 16 | AR5 GWP — N₂O | 265 | n/a | IPCC AR5 (100-yr) | Table 8.7 | 2026-07-15 | High |

**VVB Expectation:** Every EF must have a citable, dated source. IPCC 2006 is the default. **GWP must be from a single, declared vintage (AR5 vs AR6)**, and the choice must be consistent across all calculations and reports. **The current code uses AR5 throughout; ISO 14064-1:2025 requires AR6** — migrate before validation.

---

## SECTION 5 — Internal Audit Report (ISO 14064-3 Stage 1)
**File:** `05_internal_audit_report.pdf`
**Owner:** Independent internal auditor (NOT the project team; not Mavis; not Nishchal)
**Format:** ISO 19011-style, ≤ 90 days old at submission date

Must include:
- Audit scope (whole GHG information system)
- Audit criteria (ISO 14064-1, ISO 14064-3, VCS Standard, methodology)
- Audit findings (conformities, non-conformities, observations)
- Auditor CV and independence statement
- Management response (Nishchal)
- Date, location, signatures

**VVB Expectation:** Without an internal audit ≤ 90 days old, the VVB will issue a CAR for "no internal audit evidence."

---

## SECTION 6 — Data Management Procedure
**File:** `06_data_management_procedure.pdf`
**Owner:** Mavis (CTO)

Procedure must cover:
1. **Input:** sensor types, MQTT broker, raw data ingestion (`io/csv_loader.py`, `io/mqtt_bridge.py`)
2. **Processing:** pydantic validation, audit-trail emission (`audit/trail.py` — see deliverable 4)
3. **Output:** Pydantic models, JSON serialization, PDF report generation
4. **Archive:** encrypted NAS, cloud backup (AWS S3 with versioning), 5-year retention
5. **Integrity:** SHA-256 hash on every input file, every calculation result, every report
6. **Access control:** role-based (operator, engineer, manager, VVB-read-only)
7. **Change management:** git SHA pinned in every audit entry; semantic versioning

**VVB Expectation:** The audit trail must be **immutable** (append-only, hash-chained). The current `audit_log` table is append-only but not hash-chained — see deliverable 4 for the proposed upgrade.

---

## SECTION 7 — Risk Assessment Matrix
**File:** `07_risk_assessment.xlsx` (and `.pdf`)
**Owner:** Mavis + Nishchal

5×5 likelihood × impact matrix for each material misstatement source. Examples:
- Misstated fuel consumption (high likelihood, high impact)
- Misapplied NEA grid EF (medium, high)
- Misstated baseline emissions (low, high)
- Misstated project emissions (medium, high)
- Inadequate stakeholder consultation (low, medium)
- Incorrect crediting period start (low, high)
- Buffer pool misclassified (low, medium)
- Leakage understated (medium, medium)

**VVB Expectation:** The risk matrix drives the VVB's sampling plan. If the matrix is missing, the VVB samples at maximum rigor (higher cost, longer timeline).

---

## SECTION 8 — Materiality Threshold Justification
**File:** `08_materiality_threshold.pdf`
**Owner:** Mavis

- Threshold: 5% of gross annual emission reductions (e.g., for Hetauda: 5% × 70,000 = 3,500 tCO₂/yr)
- Justification: VCS Standard §3.5.6 and ISO 14064-3 §5.3.4 both permit a 5% threshold for voluntary carbon markets; below this, the VVB aggregates the misstatement and reports as a single item.

---

## SECTION 9 — Site Visit Agenda and Logistics
**File:** `09_site_visit_agenda.pdf`
**Owner:** Nishchal (logistics) + Mavis (technical content)

- VVB lead validator + 1 technical reviewer
- 2 days on site at Hetauda
- Day 1: plant walkthrough, kiln inspection, WHR pre-construction, biomass supply chain
- Day 2: management interviews, data spot-checks, open findings meeting
- Travel, accommodation, security, COVID protocols (as applicable)

**VVB Expectation:** A site visit is **mandatory** for first-of-kind industrial projects. Skipping or shortening the site visit is a CAR.

---

## SECTION 10 — Operator Competence Statements
**File:** `10_operator_competence.pdf`
**Owner:** Hetauda Cement HR + Nishchal

CVs and competence statements for:
- Plant Manager (10+ years cement ops)
- Chief Engineer (kiln technology specialist)
- EHS Officer (ISO 14001 lead auditor preferred)
- HCN Project Director (Nishchal)
- HCN Lead Engineer (Mavis)
- HCN Carbon Accounting Lead (Mavis)

**VVB Expectation:** The VVB's ISO 14064-3 lead validator must also provide a competence statement. We do not certify the VVB, but the VVB certifies us.

---

## SECTION 11 — Audit Trail Export
**File:** `11_audit_trail.sqlite` (database) + `11_audit_trail.csv` (readable export)
**Owner:** Mavis (technical) + Nishchal (sign-off)

Every CALCULATE event must export with:
- `entry_id` (UUID)
- `tenant_id`
- `user_id`
- `action` (always `CALCULATE` for this section)
- `entity_type` (e.g., `cement_calculation_tier2`)
- `entity_id` (e.g., `hetauda_2024_baseline`)
- `input_hash` (SHA-256 of serialized input)
- `output_hash` (SHA-256 of serialized output)
- `code_version` (git SHA of `nepal_decarb_pro` at time of calc)
- `timestamp` (ISO 8601)
- `details` (JSON: input dict, output dict, parameters)

**VVB Expectation:** The VVB will select N random entries and re-run the calculation. If the hashes don't match, it's a CAR. **This is the single most important evidence file in the validation pack** and is the #1 missing piece in the current codebase.

---

## SECTION 12 — GWP Source Document
**File:** `12_gwp_source.pdf`
**Owner:** Mavis

State clearly: "GWP values used in this PDD are from IPCC AR5 (100-year) per ISO 14064-1:2018 §A.4. Migration to AR6 is planned for v1.1 of the platform."

If VVB pushes back (e.g., "ISO 14064-1:2025 is out, why AR5?"), have a one-page justification: "AR5 is the standard reference for the methodology version (<<METHOD>> v<<X.Y>>) and is consistent with the GWP values used in IPCC 2006/2019."

---

## SECTION 13 — Methodology Decision Memo
**File:** `13_methodology_decision_memo.pdf`
**Owner:** Mavis + senior methodology consultant

1-page memo explaining why we chose methodology `<<METHOD>>` over alternatives. For Hetauda, recommend: **AMS-III.H (alternative waste treatment / WHR component) + ACM0010 (low-carbon cement component)** — and **abandon the fictional VM0009**.

---

## SECTION 14 — VVB Engagement Letter
**File:** `14_vvb_engagement_letter_signed.pdf`
**Owner:** Nishchal (signatory)

See `VVB_ENGAGEMENT_LETTER_DRAFT.md` (deliverable 3). Must be signed before Stage 1.

---

## SECTION 15 — Prior Consideration Evidence
**File:** `15_prior_consideration.pdf`
**Owner:** Nishchal

Evidence that the project capex was not committed before the PDD pipeline publication:
- Board minutes authorizing capex (date `<<YYYY-MM-DD>>`)
- Vendor RFP or contract (date `<<YYYY-MM-DD>>`)
- Verra pipeline publication date (`<<YYYY-MM-DD>>`)

**VVB Expectation:** All three dates must be clearly visible. The pipeline date must be **earlier** than the capex commitment date. If the dates are reversed, the project is not eligible for VCS.

---

## SECTION 16 — Stakeholder Grievance Log
**File:** `16_grievance_log.xlsx` (ongoing)
**Owner:** Hetauda Plant EHS Officer

Even if no grievances have been received to date, the log must be set up and attached (empty is acceptable). The VVB checks the mechanism, not the volume.

---

## SECTION 17 — GHG Information System Diagram
**File:** `17_ghg_information_system_diagram.pdf`
**Owner:** Mavis

A clean architecture diagram showing:
```
[Mqtt Sensors] → [io/mqtt_bridge.py] → [SQLite audit_log]
                                              ↓
[Plant data] → [Pydantic validation] → [core/cement.py::calculate_cement_tier2/3]
                                              ↓
                                  [audit/trail.py] ← input/output hash
                                              ↓
                                [JSON output + hash]
                                              ↓
                       [reporting/pdf.py → Verra Monitoring Report PDF]
```

---

## SECTION 18 — Communication Plan
**File:** `18_communication_plan.pdf`
**Owner:** Nishchal

How HCN communicates with the VVB:
- Primary: email `<<HCN_VALIDATION@...>>`
- Backup: phone `<<+977-...>>`
- Response SLA: 24 hours on business days, 72 hours on weekends
- Escalation: Project Director → CFO → Board

---

## SECTION 19 — Project Schedule (Gantt)
**File:** `19_schedule.pdf` or `.mpp`
**Owner:** Nishchal

- Stage 1 (pre-validation): 10 working days
- Stage 2 (validation): 60 working days
- Verra pipeline publication: `<<YYYY-MM-DD>>`
- Verra public comment (30 days): `<<YYYY-MM-DD>>` to `<<YYYY-MM-DD>>`
- Verra review (60 days): `<<YYYY-MM-DD>>` to `<<YYYY-MM-DD>>`
- First credit issuance: `<<YYYY-MM-DD>>` (estimated)

---

## SECTION 20 — Cover Sheet / Index
**File:** `20_index.md`
**Owner:** Nishchal

```
Section | File name | Pages | Date | Author
0  | 00_cover_letter.pdf                  |  1  | <<>> | <<>>
1  | 01_PDD_v2.0.pdf                      | 60  | <<>> | <<>>
2  | 02_Validation_Report_v0.1_draft.docx | 30  | <<>> | <<>>
3  | 03_calculation_spreadsheet.xlsx      | 25  | <<>> | <<>>
4  | 04_emission_factors.xlsx             |  4  | <<>> | <<>>
5  | 05_internal_audit_report.pdf         | 15  | <<>> | <<>>
6  | 06_data_management_procedure.pdf     |  8  | <<>> | <<>>
7  | 07_risk_assessment.xlsx              |  3  | <<>> | <<>>
8  | 08_materiality_threshold.pdf         |  2  | <<>> | <<>>
9  | 09_site_visit_agenda.pdf             |  2  | <<>> | <<>>
10 | 10_operator_competence.pdf           |  6  | <<>> | <<>>
11 | 11_audit_trail.sqlite                | n/a | <<>> | <<>>
12 | 12_gwp_source.pdf                    |  1  | <<>> | <<>>
13 | 13_methodology_decision_memo.pdf     |  2  | <<>> | <<>>
14 | 14_vvb_engagement_letter_signed.pdf  |  4  | <<>> | <<>>
15 | 15_prior_consideration.pdf           |  3  | <<>> | <<>>
16 | 16_grievance_log.xlsx                |  1  | <<>> | <<>>
17 | 17_ghg_information_system_diagram.pdf|  1  | <<>> | <<>>
18 | 18_communication_plan.pdf            |  2  | <<>> | <<>>
19 | 19_schedule.pdf                      |  1  | <<>> | <<>>
20 | 20_index.md                          |  2  | <<>> | <<>>
```

---

## Closing Note

**Every empty `<<>>` is a CAR waiting to happen.** Fill each placeholder with content that is:
1. Specific (a number, a date, a person — not "TBD")
2. Sourced (cite the document, page, and date retrieved)
3. Verifiable (the VVB must be able to re-derive the value from the cited source)
4. Recent (≤ 90 days old for internal audit, ≤ 12 months for plant survey data)

Submit the pack to the VVB as a single ZIP (~50–200 MB) with a data room for the larger items (full audit trail DB, full video of stakeholder consultation, full engineering drawings).

— Mavis, CTO · 2026-07-22
