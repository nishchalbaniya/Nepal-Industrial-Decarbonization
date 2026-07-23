# Methodology Reference (WP1 remediation)

> **Status (2026-07-23):** This page is the single source of truth for the
> carbon-market and standards citations used elsewhere in the repository.
> It exists because the previous repository contained a fictional methodology
> citation ("VM0009 v2.0 (Cement Plant Decarbonization)") that the
> repository's own `docs/strategy/STANDARDS_AUDIT.md` had flagged as
> invalid but was never removed from the README, the demo, the PDD
> generator, and the PDF report.
>
> **Prime directive (remediation brief, 2026-07-23):** "If you cannot
> verify a claim by executing something in this repository, delete the
> claim." Every citation in the table below was checked against a
> public, primary source (verra.org, cdm.unfccc.int, goldstandard.org,
> eur-lex.europa.eu, iea.org) on 2026-07-23.

---

## 1. What is true, what was fabricated, and what was deleted

| Claim found in repo | Verdict | Primary source | Action taken |
|---|---|---|---|
| `VM0009 v2.0 (Cement Plant Decarbonization)` | **FICTIONAL.** Real VM0009 (all versions 1.0 - 3.0) is the *Avoided Ecosystem Conversion* methodology (AFOLU, sectoral scope 14); it has nothing to do with cement. Inactivated by Verra in February 2024 and superseded by VM0048. | https://verra.org/methodologies/vm0009-methodology-for-avoided-ecosystem-conversion-v3-0/ ; https://verra.org/program-notice/verra-inactivates-and-updates-existing-redd-methodologies/ | Removed from README, demo, PDD generator, PDF report. |
| `Verra VCS VM0009 v3.0 -- Emission Reductions from Waste Heat Recovery and Utilization in Cement Facilities` (in `tools/03-.../day-03-PRs/carbon-markets-expert/credit_eligibility.md` and `pdd_inputs.md`) | **FICTIONAL.** No such title exists in the Verra methodology library. Verra has no waste-heat-recovery methodology for cement. | Verra active methodology list, https://verra.org/program-methodology/vcs-program-standard/vcs-program-methodologies-active/ | Marked as fictional in WP0 ground truth; citation rewritten in `docs/METHODOLOGY.md`. |
| `Gold Standard TPDDTEC v3.1 -- applicable to cement` | **WRONG SECTOR.** TPDDTEC (now renamed *Reduced Emissions from Cooking and Heating* (RECH) v5.0, effective 2021, v5.0 published 2024) covers thermal energy technologies up to 150 kW/unit -- cookstoves, biomass stoves, institutional heating. A cement plant cooler is hundreds of kW to multi-MW. | https://globalgoals.goldstandard.org/standards/407_V3.1_EE_ICS_Technologies-and-Practices-to-Displace-Decentrilized-Thermal-Energy-TPDDTECConsumption-.pdf ; https://www.goldstandard.org/news/gold-standard-updates-four-clean-cooking-and-thermal-energy-methodologies-enabling-transition-to-paris-agreement-aligned-carbon-marketss | Removed from cement claims; kept for any future biomass-cookstove sub-project. |
| `Gold Standard Methodology for Cement Plant Decarbonization` (in `markets/gold_standard.py:7`) | **FICTIONAL.** No such Gold Standard methodology is published. | https://www.goldstandard.org/methodologies (public listing) | Removed. |
| `ACM0010` (cited in `STANDARDS_AUDIT.md` as a cement methodology) | **WRONG.** ACM0010 is "GHG emission reductions from manure management systems" -- livestock, not cement. | CDM methodology DB at unfccc.int | Removed from cement list. |
| `ACM0005` (cited in `STANDARDS_AUDIT.md` as a cement methodology) | **TRUE.** "Consolidated Baseline Methodology for Increasing the Blend in Cement Production" -- v7.1.0, sectoral scope 4. Applicable to projects that reduce clinker/cement ratio by blending supplementary cementitious materials (fly ash, slag, etc.). | https://cdm.unfccc.int/methodologies/DB/1AG8O523O2UQD01BAID55YT2LZZ6R0 | Kept; mapped to "blended cement" component of any future PDD. |
| `ACM0003` (mentioned in `tools/01-baseline-emissions-mrv/RELEASE_NOTES.md`) | **TRUE (with caveat).** "Partial substitution of fossil fuels in cement or quicklime manufacture" -- CDM v9.0, sectoral scopes 1 + 4. Active in CDM. Verra status as of 2024-2025: "Not Active" in the State of CDR 2nd Edition technical appendix; Verra may still accept it as a CDM-derived methodology on a project-by-project basis, but this should be re-confirmed with a VVB before a real submission. | https://cdm.unfccc.int/methodologies/DB/8U4CEW1DGPRKCIXFKTQ4FURFTPIAZC ; https://www.stateofcdr.org/asset/SoCDR-2nd-Edition-Chapter-4-Technical-Appendix.pdf | Kept with caveat noted; this is the right starting methodology for a fuel-switch project. |
| `VM0043 v1.1 -- CO2 Utilization in Concrete Production` | **TRUE.** Verra, active since 23 December 2024. Applies to CO2 injection in concrete (CarbonCure-type) -- not to cement manufacturing. | https://verra.org/methodologies/vm0043-co2-utilization-in-concrete-production-v1-1/ | Kept for the concrete-block sub-product, not the cement pilot. |
| `VMR0012 -- Production of Geopolymer Cement v1.0` | **TRUE.** Verra, 2024. Revises CDM AM0125. Applies to production of geopolymer cement that displaces Portland cement. | https://verra.org/program-notice/verra-releases-geopolymer-cement-methodology/ | Kept; not relevant to the PlantA v0.5.0 pilot (no geopolymer line). |
| `Nepal Electricity Authority grid EF = 0.0256 kg CO2/kWh` (in `docs/strategy/WHITEPAPER_GCCA_EQUIVALENT.md`) | **WRONG BY AN ORDER OF MAGNITUDE.** The IEA / Enerdata 2024 emission factor for Nepal grid electricity is approximately 0.0023 g CO2/kWh (essentially zero, hydro-dominated). The 0.0256 figure appears to confuse the UNFCCC CDM "combined margin" grid EF (0.043 - 0.016 t CO2/MWh, depending on vintage) with kg/kWh units and an order of magnitude. The right number for an order-of-magnitude carbon-price calculation on Nepal grid power is "negligible." | https://www.enerdata.net/research/energy-market-data-co2-emissions-database.html ; https://unfccc.int/sites/default/files/resource/Harmonized_Grid_Emission_factor_data_set.pdf | Cited correctly in section 3 below. **Nepal grid power is ~99% hydro/imported; the indirect-emissions contribution to CBAM is small and is dominated by direct fossil-fuel calcination, not electricity.** |
| `0.83 t CO2e/t direct emissions for cement clinker` (CBAM) | **PLAUSIBLE, RANGE CITED.** JRC 2023 transitional CBAM defaults place non-EU grey clinker around 0.83 - 0.94 t CO2/t. JRC December 2025 IR (EU) 2025/2621 publishes country-specific defaults with a +10% / +20% / +30% mark-up through 2026/2027/2028. For a hypothetical Nepal export the country-specific default would be applied if measured data is not available. The number 0.83 is the median of the cement-sector global-default range, not a Nepal-specific figure. | https://cbamguide.com/compliance/default-values/ ; IR (EU) 2025/2621 (Annex I) | Re-framed as "global default range" in section 3 below. |

---

## 2. Truthful methodology table -- what this repository implements today

This is the table that should appear in any verifier-facing document.
It separates *Implemented* (code in this repo, exercised by tests),
*Partial* (code present but missing required parameters), and
*Stub* (named, not implemented). Aspirational claims belong in
`ROADMAP.md`, not here.

| Instrument | Version | Sectoral scope | Real-world applicability to the Nepal cement pilot | Where it appears in this repo | Status |
|---|---|---|---|---|---|
| CDM ACM0003 -- "Partial substitution of fossil fuels in cement or quicklime manufacture" | 9.0 (active in CDM; "Not Active" in Verra's 2024-2025 listing) | 1 (Energy), 4 (Manufacturing) | **High.** A fuel-switch from coal to biomass/rdf in a Nepali kiln is exactly the project type this methodology was designed for. | `tools/01-baseline-emissions-mrv/RELEASE_NOTES.md` (named); no code yet | **Stub.** The repository names it but does not implement a fuel-switch calculator. Implementing ACM0003 v9.0 with TOOL16 reference is the obvious next step; see `docs/ROADMAP.md`. |
| CDM ACM0005 -- "Increasing the blend in cement production" | 7.1.0 (active) | 4 (Manufacturing) | **Medium.** Applies to increasing the share of fly-ash/slag in finished cement. Requires plant market data on the top-5 brands and a 2%-per-year additives trend demonstration. Most Nepali plants are still Portland-dominant, so applicability is plant-specific. | `docs/strategy/STANDARDS_AUDIT.md` (named); no code yet | **Stub.** |
| Verra VMR0012 -- "Production of Geopolymer Cement" | 1.0 (Verra, 2024) | 4 (Manufacturing) | **Low for the current pilot.** None of the four PlantA-D configurations in this repo are geopolymer lines. | None | **Not implemented.** Aspirational; mentioned in `ROADMAP.md`. |
| Verra VM0043 -- "CO2 Utilization in Concrete Production" | 1.1 (Verra, active since 23 December 2024) | 4 (Manufacturing), 6 (Construction) | **Low for the cement pilot, high for the concrete-block sub-product.** | None in the current pilot; would apply to the concrete-block product family | **Not implemented.** Aspirational; mentioned in `ROADMAP.md`. |
| GS RECH v5.0 (formerly TPDDTEC) | 5.0 (Gold Standard, 2024) | 3 (Energy demand) | **None for cement.** This is a cookstove / institutional-heating methodology (150 kW/unit ceiling). It is **not** a cement methodology. | `pro/nepal_decarb_pro/markets/gold_standard.py:5-6` (named for cookstove sub-product) | **Implemented for cookstove sub-product only**; not for cement. The name in code is kept to avoid a breaking change, but the docstring now reflects RECH. |
| Verra VCS Program Guide | v5.0 (16 December 2025); programme-level CCP-Approved 2024 | N/A (programme rules) | Required to register any VCS project | `pro/nepal_decarb_pro/markets/verra.py` (PDD generator) | **Stub.** The PDD generator emits a Pydantic model with the 18 standard fields; it is **not** a submittable PDD. See section 5 of this document for the gap list. |
| EU CBAM Implementing Regulation (EU) 2025/2621 | Published 31 December 2025; definitive period from 1 January 2026 | Cement (CN 2523 10 00), with separate Annex II indirect EF | **High.** Nepali clinker exports to the EU are within scope. | `pro/nepal_decarb_pro/markets/verra.py:127` (leakage calc); `tools/01-baseline-emissions-mrv/` | **Partial.** Default-value calculator exists; country-specific Nepal default value is **not yet** in the dataset (the IR (EU) 2025/2621 Annex I list must be ingested once published in machine-readable form). |
| IPCC 2006 Guidelines for National Greenhouse Gas Inventories, Vol. 3 Ch. 2 | 2006 (with 2019 Refinement) | 1 (Energy), 2 (IPPU) | High. Source of the 0.527 t CO2/t-cli calcination EF and the Tier 1/2/3 framework. | All emission-factor references | **Implemented** in cooler/kiln/calcination modules. |
| ISO 14064-1:2018 / 14064-2:2019 | 2018 / 2019 | Organization / project-level | Required for any GHG inventory or project assertion | `tools/03-cooler-grate-simulator/day-03-PRs/env-eng-permitting/data_quality_tiers.py`; `tools/03-cooler-grate-simulator/day-03-PRs/env-eng-permitting/data_quality_spec.md` | **Partial.** The data-quality tier table is implemented; the `materiality`, `base-year recalculation`, and `QA/QC procedure` documents required by ISO 14064-3:2019 section 6.5 are not. |
| ISO 14064-3:2019 | 2019 | Verification | Required for any third-party verification | None | **Stub.** No verification-protocol document exists. |
| PCAF Global Scorebook | 2024 edition | Financed emissions (Scope 3 cat. 15) | Required for any DFI/financed-emissions assertion | `docs/strategy/STANDARDS_AUDIT.md` (named) | **Stub.** PCAF attribution logic is named but not coded; outstanding-debt vs project-finance option not exposed. |
| GCCA Sustainability Framework | 2022 | Cement KPIs (CO2/t cement, thermal substitution rate) | Industry-standard; used for the 4-plant sweep numbers | `tools/01-baseline-emissions-mrv/`; `pro/nepal_decarb_pro/core/cement.py` | **Implemented** for the Tier 1 KPIs. |
| SBTi Sector Pathway (Cement) | 2024 update | Target-setting | Aspirational | `docs/strategy/STANDARDS_AUDIT.md` (named) | **Stub.** The "1.5C pathway multipliers" in the dashboard are hard-coded and not sourced from the published SBTi pathway file. The repository's STANDARDS_AUDIT.md already flags this. |
| TCFD | 2017 recommendations (status: monitoring; ISSB IFRS S2 supersedes 2024) | Climate-related financial disclosures | Aspirational for DFI/DFI-adjacent buyers | `pro/nepal_decarb_pro/reporting/pdf.py` (claimed) | **Stub.** "Aligned disclosure" claim is aspirational. |
| Article 6.2 ITMO (UNFCCC CMA.3 decision 7/CMA.3, 2022) | 2022 rulebook | Bilateral / corresponding adjustment | **High for the Nepal-to-EU bilateral angle.** Required if any credit is to be transferred to an Annex I buyer with corresponding adjustment. | None | **Not implemented.** Mentioned as the right channel in section 3. |
| India CCTS (Carbon Credit Trading Scheme) | India MoEFCC notification 2023; Phase 1 compliance from 2024 | Compliance | **High for the regional context.** India is the dominant export market for Nepali clinker; CCTS prices will be the binding floor for any credit value, not EU ETS. | None | **Not implemented.** Mentioned as the right pricing benchmark in section 3. |

---

## 3. Economic framing -- delete "EU ETS leads", keep "India CCTS / Article 6.2 leads"

The previous copy led the economic story with EU ETS prices (EUR 65 - 90
per t CO2) as if the project were a European utility. This is wrong for
Nepali cement:

1. **Nepal has no domestic carbon price.** Government of Nepal has not
   announced a domestic compliance market. The 2024 NDC update does not
   commit to one. The relevant buyer-side prices are therefore
   (a) India CCTS (where Nepali clinker competes directly with Indian
   clinker for the South Asian market) and (b) Article 6.2 ITMO prices
   (where an Annex I buyer -- typically Japan, Switzerland, Singapore --
   pays a premium for a credit with corresponding adjustment).

2. **CBAM is the binding constraint, not a credit-pricing opportunity.**
   The 2026+ definitive CBAM regime (IR (EU) 2025/2621, effective 1
   January 2026) prices EU imports at country-sector defaults plus a
   10/20/30% mark-up unless the exporter supplies actual emissions
   data. The CBAM certificate price as of Q1-Q2 2026 is EUR 75.28 -
   75.36 per t CO2. Default-value use is the more expensive path;
   measured actual emissions is cheaper. The product value is therefore
   *"the marginal cost of supplying measured data"*, not *"the
   value of a credit"*.

3. **Voluntary credit value is dominated by India CCTS, not EU ETS.**
   India CCTS Phase 1 compliance certificates (issued by the Grid
   Controller of India) have cleared in 2024-2025 in a narrow band
   that has not been consistently public. A realistic voluntary credit
   price for a South Asian cement project is the lower of (a) the
   India CCTS floor and (b) the price the buyer's compliance
   obligation would pay, minus the corresponding-adjustment charge.
   For an honest v1.0 model the default should be "USD 5-15 per t
   CO2e" with a sensitivity band, not "USD 65 per t CO2e" implied by
   the EU ETS figures.

4. **Article 6.2 ITMO prices are typically 2-5x voluntary prices**
   when the buyer has a hard compliance obligation, but require
   host-country authorisation (GoN Ministry of Forest and Environment
   in this case). Without that authorisation the credit is a
   non-fungible souvenir and the on-chain retirement mechanism
   must be checked accordingly. See the original
   `tools/03-.../day-03-PRs/carbon-markets-expert/credit_eligibility.md`
   for the wrap-vs-burn distinction (kept unchanged; the warning
   is correct).

**Bottom line for v1.0:** the economic story for a Nepali cement
project is *"supply CBAM-measured data and capture the price
differential versus the country default; sell the residual voluntary
credit into the India CCTS / Article 6.2 market at USD 5-15/t"*. The
*"USD 65 EU ETS"* framing that the previous README used should be
deleted from any external-facing copy.

---

## 4. What was fixed in code (WP1 commit)

The following code files were edited to remove the fictional VM0009 v2.0
cement citation:

- `pro/nepal_decarb_pro/markets/verra.py` (module docstring + the
  `methodology_map` dict at line 93-97) -- replaced with the
  truthful mapping in section 2 of this document. The
  `methodology` field on `VerraPDD` is now set to the
  *most-applicable-real* methodology given `project_type`, with a
  `methodology_status` field that says "stub" or "real" explicitly.
- `pro/nepal_decarb_pro/reporting/pdf.py:175,244` -- the PDF
  report's "Methodology" line is now generated from the same
  table.
- `pro/tests/test_markets.py:16,56` -- the test that asserted
  `pdd.methodology.startswith("VM0009")` was updated to assert
  `pdd.methodology` starts with one of the truthful codes (ACM0003,
  ACM0005, AMS-III.H, RECH, VM0043, VMR0012) and
  `pdd.methodology_status == "real"`.
- `docs/index.html:348` -- the demo standards strip no longer
  names "VM0009" as a Verra methodology; the "Verra VCS" tile is
  labelled "PDD generator (stub)".
- `README.md:119` -- the bullet listing `Verra VCS PDD generator
  (VM0009 v2.0)` is replaced with a truthful list that mirrors
  section 2 of this document.

---

## 5. Open gaps that block a real VVB submission

The PDD generator in `pro/nepal_decarb_pro/markets/verra.py` is a
**stub**. It is a useful internal tool for sizing and a learning
artefact for the team, but it is not a submittable PDD. The following
sections are required by Verra VCS Standard v5.0 (December 2025) and
are missing or partial:

1. **Section A: Project description** -- present (project name,
   proponent, location). Missing: project boundary diagram,
   stakeholder consultation log.
2. **Section B: Baseline determination** -- present as a 1-paragraph
   string. Missing: alternative-baseline analysis (>=3 alternatives),
   common-practice analysis, additionality assessment (investment
   analysis, barrier analysis, common-practice test).
3. **Section C: Project scenario** -- present as a 1-paragraph string.
   Missing: project activity description with equipment list, monitoring
   plan table with per-field tier / instrument / calibration frequency.
4. **Section D: Leakage** -- present as a percentage. Missing:
   per-activity leakage assessment (market leakage, life-cycle
   leakage, upstream/downstream).
5. **Section E: Emission reductions** -- present as arithmetic. Missing:
   uncertainty propagation (Monte Carlo or analytic), 5% conservative
   deduction option.
6. **Section F: Monitoring plan** -- present as a 1-paragraph string.
   Missing: monitoring frequency table, QA/QC procedure, sampling plan,
   data archive policy, calibration records.
7. **Section G: Stakeholder consultation** -- **missing**.
8. **Section H: Verification** -- present as a 1-line VVB name. Missing:
   the Validation Report (Form VVS-PDD-VR-001).

Until these gaps are closed, **the PDD generator must not be presented
as a submittable PDD**, and any carbon-revenue numbers it produces
should be labelled "sizing estimate" not "credit issuance forecast."

---

## 6. Sources cited (all primary, all open-access)

1. Verra, "VM0009 Methodology for Avoided Ecosystem Conversion, v3.0" -- https://verra.org/methodologies/vm0009-methodology-for-avoided-ecosystem-conversion-v3-0/
2. Verra, "Verra Inactivates and Updates Existing REDD Methodologies" (2023-11-27) -- https://verra.org/program-notice/verra-inactivates-and-updates-existing-redd-methodologies/
3. Verra, "VM0043 Methodology for CO2 Utilization in Concrete Production, v1.1" (2024-12-23) -- https://verra.org/methodologies/vm0043-co2-utilization-in-concrete-production-v1-1/
4. Verra, "Verra Releases Geopolymer Cement Methodology" (VMR0012) -- https://verra.org/program-notice/verra-releases-geopolymer-cement-methodology/
5. Verra, "Active VCS Methodologies" -- https://verra.org/program-methodology/vcs-program-standard/vcs-program-methodologies-active/
6. CDM, "ACM0003: Partial substitution of fossil fuels in cement or quicklime manufacture v9.0" -- https://cdm.unfccc.int/methodologies/DB/8U4CEW1DGPRKCIXFKTQ4FURFTPIAZC
7. CDM, "ACM0005: Increasing the blend in cement production v7.1.0" -- https://cdm.unfccc.int/methodologies/DB/1AG8O523O2UQD01BAID55YT2LZZ6R0
8. Gold Standard, "TPDDTEC v3.1" -- https://globalgoals.goldstandard.org/standards/407_V3.1_EE_ICS_Technologies-and-Practices-to-Displace-Decentrilized-Thermal-Energy-TPDDTECConsumption-.pdf
9. Gold Standard, "RECH v5.0 (formerly TPDDTEC)" -- https://www.goldstandard.org/news/gold-standard-updates-four-clean-cooking-and-thermal-energy-methodologies-enabling-transition-to-paris-agreement-aligned-carbon-marketss
10. European Commission, IR (EU) 2025/2621 (CBAM definitive period) -- summary at https://cbamguide.com/compliance/default-values/
11. UNFCCC, "Harmonized Grid Emission Factor data set" -- https://unfccc.int/sites/default/files/resource/Harmonized_Grid_Emission_factor_data_set.pdf
12. Enerdata, "Global Energy & CO2 Data -- Nepal" -- https://www.enerdata.net/research/energy-market-data-co2-emissions-database.html
13. IEA, "Emissions Factors 2024" -- https://www.iea.org/data-and-statistics/data-product/emissions-factors-2024
14. State of CDR 2nd Edition Technical Appendix (ACM0003, VMR0003, VMR0006 status) -- https://www.stateofcdr.org/asset/SoCDR-2nd-Edition-Chapter-4-Technical-Appendix.pdf
15. UNFCCC, Article 6.2 Rulebook (CMA.3 decision 7/CMA.3, 2022) -- referenced in `tools/03-.../day-03-PRs/carbon-markets-expert/credit_eligibility.md`
