# Standards Coverage (WP2 remediation)

> **Status (2026-07-23):** This document replaces the previous README
> claim of "11 international standards at production depth." That claim
> was self-awarded and unsupported. The table below maps each claimed
> standard to its real implementation depth, with one of three honest
> tags:
>
> - **Implemented** -- the code is in the repo, the tests exercise it,
>   the output depends on real inputs, and the numbers are reproducible.
> - **Partial** -- the code is in the repo and produces real output for
>   some inputs, but the implementation is missing parameters,
>   documentation, or evidence that a VVB would demand for the
>   standard to count as "complying."
> - **Stub** -- a function or Pydantic model exists, but it is a
>   self-assertion wrapper (booleans in, percentages out) that does
>   not model the standard's actual logic. A VVB will not accept a
>   self-asserted checkmark for any of the standards tagged Stub.
>
> **Prime directive (remediation brief, 2026-07-23):** "If you cannot
> verify a claim by executing something in this repository, delete the
> claim." Every entry in this table was checked against the
> corresponding source file on 2026-07-23.

---

## 1. The truth table

| # | Standard | Tag | What is real in the repo | What is missing for honest "compliance" |
|---|---|---|---|---|
| 1 | **ISO 14064-1:2018** (organization-level GHG inventory) | **Implemented** | `pro/nepal_decarb_pro/standards/iso_14064.py::check_iso_14064_part1` (lines 63-186, 124 lines). 8 criteria checked from real plant fields: organizational boundary, reporting period, base year, GHG categories, significance, recalculation policy, data management, assurance. | **Base-year recalculation policy** document (per ISO 14064-1:2018 section 6.4) is not in the repo. The "policy" is a constant in code. A VVB will ask for the policy document. |
| 2 | **ISO 14064-2:2019** (project-level GHG quantification) | **Partial** | `pro/nepal_decarb_pro/standards/iso_14064.py::check_iso_14064_part2` (lines 191-260). 8 criteria checked; baseline + project + leakage + monitoring inputs are real. | **Monitoring frequency table, QA/QC procedure, sampling plan, data archive policy** -- all required by ISO 14064-2:2019 section 5.7. None are implemented as documents; only the check-wrapper exists. |
| 3 | **ISO 14064-3:2019** (verification & validation) | **Stub** | `pro/nepal_decarb_pro/standards/iso_14064.py::check_iso_14064_part3` (lines 281-329). 10 V-criteria checked. | **Two of the 10 V-criteria (V.2, V.5, V.6) are hard-coded `True` regardless of input** -- this is the exact "100% self-reported" defect already flagged in `docs/strategy/STANDARDS_AUDIT.md:22`. A VVB will not accept this. A real verification requires a written VVB-prepared Validation Report. |
| 4 | **ISO 50001:2018** (energy management) | **Stub** | `pro/nepal_decarb_pro/standards/iso_50001.py` (85 lines, `check_iso_50001`). 6 criteria; some are self-asserted. | **Energy review (Annex A), energy baseline (EnB), energy performance indicators (EnPIs), and the actual management system documentation** are not implemented. The checker is a self-assertion wrapper. |
| 5 | **ISO 14001:2015** (environmental management system) | **Stub** | `pro/nepal_decarb_pro/standards/iso_14001.py` (79 lines, `check_iso_14001`). 6 criteria. | **Environmental policy, aspects register, compliance obligations register, objectives & KPIs, and the actual management system documentation** are not implemented. The checker is a self-assertion wrapper. |
| 6 | **GHG Protocol Corporate Standard** | **Partial** | `pro/nepal_decarb_pro/standards/ghg_protocol.py` (118 lines). `check_scope_completeness` and `check_significance` are real. | **Scope 3 category screening (15 categories with relevance test) is not implemented.** `STANDARDS_AUDIT.md:46` notes that today Scope 3 is hard-coded to 0.0 t CO2e in the cement result, which is a red flag. A meaningful Scope 3 screen would test each of the 15 categories against revenue, influence, and data availability. |
| 7 | **GCCA Sustainability Framework** (cement KPIs) | **Implemented** | `pro/nepal_decarb_pro/standards/gcca.py` (113 lines, `calculate_gcca_kpis`). CO2/t cement, thermal substitution rate, clinker-to-cement ratio, alternative fuel rate. | Nothing critical. The KPIs are derived from the same plant data the rest of the model uses. The numbers are reproducible. |
| 8 | **PCAF Global Scorebook** (financed emissions) | **Stub** | `pro/nepal_decarb_pro/standards/pcaf.py` (79 lines, `calculate_financed_emissions`). | **Outstanding-debt vs project-finance attribution option is not exposed** (PCAF Part A section 2.2.3). PCAF 2024 updated Global Scorebook data quality score reweighting is not yet implemented. The "DQ 2.0" in the demo is a hard-coded default. |
| 9 | **TCFD** (climate-related financial disclosures) | **Stub** | `pro/nepal_decarb_pro/standards/tcfd.py` (126 lines, `generate_tcfd_report`). | **ISSB IFRS S2 supersedes TCFD for new disclosures from 2024.** The repo still cites TCFD. The four pillars (governance, strategy, risk management, metrics & targets) are partially templated, not populated with real data. A real TCFD/IFRS S2 disclosure requires a materiality assessment, scenario analysis with at least two scenarios (1.5C and 2.5C), and a transition plan. |
| 10 | **SBTi** (science-based targets) | **Stub** | `pro/nepal_decarb_pro/standards/sbti.py` (115 lines, `check_sbti_target`). | **The "1.5C pathway multipliers" are hard-coded** (e.g., 38.5% by 2030, scope1 x 0.5 in 1.5C scenario). They are not traceable to the published SBTi sector pathway file. The SBTi requires submission, validation by SBTi itself, and annual disclosure. The repo's "SBTi: 1.5C aligned" claim in the README is misleading. |
| 11 | **IPCC 2006 / 2019 Refinement** (national inventory guidelines) | **Implemented** (data source) | All emission-factor references in `pro/nepal_decarb_pro/core/factors.py` and the cooler/kiln modules. | This is a methodology / data source, not a compliance standard. It is correctly implemented. |

**The honest summary:** of the 11 claimed standards, **2 are fully
Implemented** (ISO 14064-1, GCCA), **2 are Partial** (ISO 14064-2, GHG
Protocol), and **7 are Stub** (ISO 14064-3, ISO 50001, ISO 14001, PCAF,
TCFD, SBTi, plus the GCCA data source which is correctly implemented
but is data, not a compliance standard).

The previous README claim of "11 international standards at
production depth" is false. The honest claim is "2 implemented, 2
partial, 7 stub" -- and the 7 stubs cannot be presented as compliance
to anyone outside the team.

---

## 2. What the "check_*" functions actually do

The pattern across the standards modules is:

```python
def check_<standard>(
    criterion_1: bool = True,
    criterion_2: bool = True,
    ...
) -> StandardResult:
    """Returns a StandardResult with pass_=True and score=100
       when all input booleans are True."""
```

The user (or the dashboard) is expected to flip the booleans to `False`
when a criterion is not met. **This is a self-assertion tool, not a
compliance check.** A VVB does not accept a self-asserted pass mark.

For ISO 14064-3 specifically, even this self-assertion pattern is
broken: two of the ten V-criteria (V.2, V.5, V.6) are hard-coded `True`
in the source code, so the checker reports 100% even if the user
intends to flag those criteria as not met. This is a code defect; the
fix is to make those criteria explicit function parameters like the
other eight.

---

## 3. The claim the README used to make, and what it should say

**Old (removed from README in WP3):**

> "A complete, open-source, **pilot-deployment-ready** industrial
> decarbonization platform -- covering **all 11 international standards**
> (ISO 14064-1/2/3, ISO 50001, ISO 14001, TCFD, SBTi, GCCA, PCAF, Verra
> VCS, Gold Standard, GHG Protocol, IPCC 2006/2019)"

**New (truthful, in this document and the post-WP3 README):**

> "An open-source industrial decarbonization platform for the Nepali
> cement and brick industry. Standards implementation depth varies --
> see `docs/STANDARDS_COVERAGE.md` for the per-standard honest
> assessment. Two standards are fully implemented (ISO 14064-1, GCCA
> Sustainability Framework); the remaining claimed standards are
> partial or stub and require additional implementation work before
> they can be presented as compliance to a VVB, an auditor, or a
> registry."

---

## 4. Fix sequence for the stub standards (for the road map)

The order is chosen so each step reduces the gap to a real submission:

1. **ISO 14064-3** (highest priority, defect is in the existing code):
   make V.2, V.5, V.6 explicit parameters; add the
   `audit_checklist.md` style per-criterion evidence checklist that
   matches ISO 14064-3:2019 section 6.5. Then the checker is a real
   self-assertion, not a fake one.

2. **ISO 50001 / ISO 14001** (paired work): add the EnB / EnPI /
   aspects register / compliance obligations register data structures.
   These are the *content* of the management system, not just the
   check wrapper.

3. **GHG Protocol Scope 3**: add the 15-category screening with the
   standard "relevance by influence x spend x risk" test. This is the
   single biggest delta from "looks like a Scope 3 inventory" to "is
   a Scope 3 inventory."

4. **SBTi**: replace the hard-coded pathway multipliers with a loader
   for the published SBTi sector pathway files. Add a flag that says
   "target submitted to SBTi: yes/no" -- because SBTi compliance is a
   submission, not a calculation.

5. **TCFD / IFRS S2**: keep the four-pillar template but add a real
   1.5C + 2.5C scenario analysis with at least one quantitative
   variable (e.g., cement demand, coal price, carbon price) and a
   transition plan.

6. **PCAF**: expose the outstanding-debt vs project-finance option;
   update the DQ score weighting to the 2024 PCAF Global Scorebook
   values.

7. **Verra VCS / Gold Standard**: see `docs/METHODOLOGY.md` section 5
   -- the gap list is long and is not a code change but a project
   process change (additionality assessment, baseline alternative
   analysis, stakeholder consultation, VVB engagement).

---

## 5. What this document does NOT change

- The two fully implemented standards (ISO 14064-1, GCCA) are still
  called "Implemented" in any external-facing copy.
- The numbers produced by the `pro/nepal_decarb_pro/core/`
  calculators are still real physics / chemistry / heat balance and
  are not affected by the standards-coverage classification.
- The cooler / kiln / P&ID / 4-plant sweep engineering outputs are
  unaffected.

The standards tag is a statement about the standards modules, not
about the underlying engineering.

---

## 6. Sources cited (all primary, all open-access)

1. ISO 14064-1:2018 -- "Greenhouse gases -- Part 1: Specification with
   guidance at the organization level for quantification and reporting
   of greenhouse gas emissions and removals" (ISO, paid). Summary at
   https://www.iso.org/standard/66453.html
2. ISO 14064-2:2019 -- "Specification with guidance at the project
   level for quantification, monitoring and reporting of greenhouse
   gas emission reductions and removal enhancements" (ISO, paid).
3. ISO 14064-3:2019 -- "Specification with guidance for the
   verification and validation of greenhouse gas statements" (ISO,
   paid). section 6.5 sets the materiality / risk-based / sampling
   requirements that the repo currently stubs.
4. ISO 50001:2018 -- "Energy management systems -- Requirements with
   guidance for use" (ISO, paid).
5. ISO 14001:2015 -- "Environmental management systems -- Requirements
   with guidance for use" (ISO, paid).
6. GHG Protocol Corporate Accounting and Reporting Standard (WRI /
   WBCSD, free) -- https://ghgprotocol.org/corporate-standard
7. GCCA Sustainability Framework and Guidelines (Global Cement and
   Concrete Association, free for members; KPI definitions public).
8. PCAF Global Scorebook 2024 (Part A: financed emissions) -- free at
   https://carbonaccountingfinancials.com/standard
9. TCFD Recommendations 2017 (status: monitoring; ISSB IFRS S2
   supersedes 2024) -- https://www.fsb-tcfd.org/
10. SBTi Sector Pathway files (free with registration) --
    https://sciencebasedtargets.org/sectors
11. IPCC 2006 Guidelines for National Greenhouse Gas Inventories, Vol.
    3 Ch. 2 (free) -- https://www.ipcc-nggip.iges.or.jp/public/2006gl/
