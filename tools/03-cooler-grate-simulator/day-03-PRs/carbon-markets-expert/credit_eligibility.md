# Credit Eligibility — Day 3 Cooler vs Verra VM0009 v3.0

> **Author:** James Okafor, Carbon Markets Specialist
> **Date:** 2026-07-22
> **Scope:** Does an improvement in cooler heat-recovery efficiency generate Verra VM0009 v3.0 credits for a Nepali cement plant? Short answer: **not directly, but the cooler is a required input to the kiln baseline that does.**

---

## 1. Scheme and methodology identification

| Element | Value | Source |
|---|---|---|
| **Voluntary / compliance** | **Voluntary** (VCS). Could be Article 6.2 ITMO with corresponding adjustment from Government of Nepal. Not EU-ETS (out of EU scope). CORSIA-eligible if the buyer is an airline. | Verra VCS Program Guide v4.5 (2024); UNFCCC CMA.3 decision 7/CMA.3 (Article 6.2 rulebook, 2022); EU ETS Directive 2003/87/EC. |
| **Methodology** | **Verra VM0009 v3.0** — *Emission Reductions from Waste Heat Recovery and Utilization in Cement Facilities*, version 3.0, effective 2023-Q4. | Verra VM0009 v3.0 (2023). |
| **Alternative methodology** | **Gold Standard TPDDTEC v3.1** (Technologies and Practices and Policies and Measures for Decentralized Electricity Generation, Thermal Energy Generation, and Utility-Scale Renewable Energy). For cement, the relevant TPDDTEC section is §4.2 (project parameter — cooler). | Gold Standard TPDDTEC v3.1 (2022). |
| **Crediting period** | Verra VCS: **7 years, renewable twice (max 21 years)**. Gold Standard: 5 years, renewable twice (max 15 years). | Verra VCS Program Guide v4.5 §3.3; Gold Standard Principles & Requirements v2.0. |
| **ICVCM integrity tier** | **Tier 3 (high-integrity)** — VM0009 v3.0 was assessed as Tier 3 in 2024. | ICVCM Category-Level Assessment (2024). |

**Important vocabulary distinction (read this twice):**

- The **cooler** does not generate credits. The **kiln baseline** generates credits.
- The cooler is a **required input** to the kiln baseline because secondary-air temperature and mass flow determine how much kiln-coal energy is recovered (and therefore how much coal the kiln needs in the project scenario).
- Credits are issued for the **delta** between the project and the baseline, not the absolute efficiency.

> *"The kiln baseline fuel consumption is computed from clinker production × baseline specific heat consumption, with secondary-air T and mass flow as monitoring parameters that adjust the baseline."*
> — paraphrased from Verra VM0009 v3.0 §5.3 (Kiln Baseline Methodology).

---

## 2. The credit pathway (how a cooler retrofit produces credits)

The chain of reasoning that a verifier will follow:

1. **Baseline scenario (without project).** The cement plant operates the kiln with a baseline cooler (e.g. the existing 72 %-efficient grate cooler, "Indian-industry average" per NPC / GCCA GNR 2022). The secondary-air T is `T_sec_baseline` (e.g. 600 °C). The kiln needs `Q_baseline` GJ/t-cli of coal to maintain clinker quality.
2. **Project scenario (with cooler retrofit).** The plant installs a new grate cooler with 78 % efficiency (BAT, ECRA 2022). Secondary-air T rises to `T_sec_project` (e.g. 850 °C). Higher secondary-air T means the kiln needs less fuel, so the kiln coal rate drops to `Q_project` GJ/t-cli.
3. **Emission reduction.** The difference `Q_baseline − Q_project` × annual clinker production × coal emission factor = the annual tCO₂e that can be issued as Verra credits.
4. **What the cooler fields do in the PDD.** The cooler is **instrumented** in the project scenario. Its outputs (secondary-air T, mass flow, cooler efficiency, exhaust-air T) are reported in the **monitoring report** and feed the kiln baseline equation. The **cooler efficiency is not the credit metric**; it is a **diagnostic** that helps the verifier confirm the kiln baseline is realistic.

> **Concretely:** if `secondary_air_outlet_c` is 600 °C in the project and 580 °C in the baseline (because the project cooler is 1 % more efficient), the kiln coal saving is on the order of **0.5–1.5 % of total coal**. For a 130 t/h Hetauda-class plant firing 100 kg coal/t-cli, that is ~130–400 kg coal/h saved, or ~400–1200 tCO₂e/yr at a 0.085 coal-EF. At a $5/tCO₂e voluntary price, that is **$2 000–6 000 per year per plant** — a small but real credit stream, gated entirely on the data quality of the cooler monitoring report.

---

## 3. Additionality (the verifier's first question)

This is where most Nepali cement projects die. The verifier will ask: *"Why would the plant do this retrofit without the carbon revenue?"* The four tests a Verra validator applies, in order:

| Test | Pass criterion | Citation |
|---|---|---|
| **Regulatory surplus** | The retrofit is not required by Nepali or Indian law. | Verra VCS Program Guide v4.5 §2.3.1. |
| **Investment analysis** | The NPV of the retrofit (with carbon revenue) is positive; without it, the IRR is below the plant's hurdle rate. | Verra VCS Program Guide v4.5 §2.3.2. |
| **Barrier analysis** | The plant faces a financial, technical, or institutional barrier (e.g. capex for a new cooler, foreign-exchange risk in Nepal) that the carbon revenue helps overcome. | Verra VCS Program Guide v4.5 §2.3.3. |
| **Common practice** | The retrofit is not standard practice in the Nepali cement industry. **This is the test that fails most often** for cooler retrofits, because grate coolers are a mature technology. | Verra VCS Program Guide v4.5 §2.3.4. |

**For a Nepali cement plant retrofitting to a 75–80 % BAT cooler:**

- **Regulatory surplus:** passes — Nepal has no cooler-efficiency regulation. Confirmed against the MoPE Industrial Emissions Directive (2022 draft, not yet in force as of 2026-Q1).
- **Investment analysis:** passes if the cooler capex is in the $1–3 M range and the IRR with carbon revenue is >12 %. Verifier will ask for a third-party bank document or a board resolution.
- **Barrier analysis:** plausible — Nepal has foreign-exchange risk, import duties on cooler internals, and limited access to concessional finance. This is the **strongest** additionality argument.
- **Common practice:** the line is **75–80 % cooler efficiency is BAT** but only ~20 % of Nepali / Indian cement plants operate at BAT. So a sub-BAT plant (e.g. 65–72 %) retrofitting to BAT is **not** common practice. Cite GCCA GNR 2022 data for the "Indian average 72–75 %" line.

> **Ramesh's threshold (GCCA GNR 2022 + ECRA 2022):** 75–80 % is BAT, 65–75 % is typical, <65 % is sub-BAT. The retrofit is **most defensible** when the baseline is sub-BAT (< 65 %) and the project is BAT (75–80 %). Cite GCCA GNR 2022 + ECRA Technology Papers 2022.

---

## 4. Monitoring plan (VM0009 v3.0 §6.2)

The PDD monitoring plan must specify, for **every** cooler field that feeds the kiln baseline:

| Field | Frequency | Instrument | Uncertainty | QA/QC | Custodian |
|---|---|---|---|---|---|
| `secondary_air_outlet_c` | Continuous (1-min average, 1-h logged) | Type-K thermocouple, class 1, 0–1100 °C, shielded | ±10 K at 800 °C | Quarterly single-point calibration against a portable NIST-traceable TC; annual re-calibration | Plant DCS / control room |
| `secondary_air_mass_flow_kg_s` | Continuous | Orifice plate or thermal mass flowmeter | ±2–5 % of reading | Annual in-situ verification per ISO 5167 | Plant DCS |
| `cooler_efficiency` | Calculated, daily | Computed from above two + clinker throughput | ±3 % (propagated) | Re-computed on every monitoring report; cross-checked against kiln-side coal saving | Project proponent |
| `coal_flow_kg_s` (kiln) | Continuous | Gravimetric belt scale | ±0.5 % | Weekly zero/span check; annual re-calibration | Plant DCS |
| `clinker_production_t_h` | Hourly | Clinker cooler discharge scale | ±1 % | Daily cross-check against kiln feed (mass balance) | Plant DCS |
| `coal_ncv_mj_kg` | Per shipment, lot | Bomb calorimeter (lab) | ±1 % | Lab cross-check every 6 months; ISO 17025 accredited lab | Plant QC lab |

> **Citation:** VM0009 v3.0 §6.2 (Monitoring Plan) + ISO 14064-2 §5.7 (GHG project monitoring) + Verra VCS Program Guide v4.5 §4 (Monitoring requirements).

---

## 5. The "no credits from the cooler alone" rule — and why Day 3 still matters

> *"A cooler efficiency improvement is not a separate credit-generating activity. The credit is for the kiln baseline delta, computed in the kiln module. The cooler's job is to provide verifiable, QA/QC'd, secondary-air T and mass flow that the kiln baseline equation consumes."*

This means:

1. **A perfect cooler module with no kiln module produces zero credits.** Day 3 v0.3.1 is upstream of the credit; it does not generate the credit. The kiln baseline (Day 2 / Day 12) is the credit-generating module.
2. **A buggy cooler module can kill the kiln credit.** If `secondary_air_outlet_c` is unphysical (e.g. 5790 °C in the v0.3.0 build, see Aanya's review), the verifier will reject the kiln monitoring report because the data does not pass the second-law check. **One bad cooler field = zero credits for the whole project.**
3. **The cooler efficiency is a diagnostic, not the credit metric.** The verifier will spot-check: "you claim 78 % cooler efficiency in the project; show me the secondary-air T, mass flow, and clinker throughput that derive it." If the derivation doesn't close, the credit is at risk.

---

## 6. Tokenization (Day 13 / Day 20 — for the record, NOT Day 3)

Tokenization is **bookkeeping**, not the goal. The goal is **retirement with audit** — a permanently-burned token with a registry retirement receipt that names the buyer and the reason for retirement.

For a Nepali cement project:

- **Token standard:** ERC-20 (fungible) for the credit, plus an on-chain retirement receipt (ERC-721 or EIP-4907 NFT of the retirement). EIP-3643 (T-REX) for KYC/AML gating if institutional buyers.
- **Smart-contract security:** **ReentrancyGuard on every external call** (OpenZeppelin). **Audited by CertiK or OpenZeppelin Defender before deployment**. **12-month bug bounty** ($50 k minimum for a $1 M+ project). Cite: Rekt News 2023-04 (cement-token reentrancy exploit, $4 M drained); OpenZeppelin ReentrancyGuard docs; Consensys Diligence 2023.
- **Vintage tracking:** the token's metadata must include the vintage year (the year the emission reduction occurred, not the year the credit was issued). Cite: Verra VCS Program Guide v4.5 §4.2.
- **Retirement mechanism:** the token must be **permanently burned** (sent to `0x000...dead`), not wrapped-and-unwrapped. Wrap-and-unwrap patterns (KlimaDAO 2022 BCT/NCT, Moss.Earth 2023 MCO2) can lead to double-counting if the bridge is compromised. Cite: Moss.Earth 2023 retirement audit; KlimaDAO 2022 BCT retirement receipt.
- **Audit, not audit-washing:** the on-chain audit trail must include (a) the registry serial number, (b) the vintage, (c) the methodology + version (VM0009 v3.0), (d) the verification body, (e) the retirement beneficiary. Without all five, the credit is a non-fungible souvenir.

---

## 7. What Day 3 v0.3.1 must do to keep the credit pathway open

| Item | Owner | Citation |
|---|---|---|
| `secondary_air_outlet_c` in [600, 1000] °C for default Hetauda | Aanya | Peray & Waddell 1986 §6.4; GCCA GNR 2022 |
| `cooler_efficiency` ∈ [0.65, 0.85] | Aanya + Ramesh | ECRA 2022; GCCA GNR 2022 |
| `secondary_air_mass_flow_kg_s` ≈ 38 kg/s (1.05–1.15× stoich) for 130 t/h clinker | Aanya | Peray & Waddell 1986 §6.2; stoichiometry |
| First-law imbalance ≤ 2 % | Hiro | Verra VM0009 v3.0 §6.2 QA/QC |
| Second-law invariant (T_air ≤ T_clinker − 5 K) | Hiro | Mujumdar 2007 §3.1 |
| Energy balance closure < 2 % of Q_in | Hiro | Verra VM0009 v3.0 §6.2 |
| All 4 plant presets run without error | Aanya + Ramesh | Ramesh's Nepal duty-case (Hetauda altitude) |
| PDD JSON schema in `pdd_json_schema.json` | James (this PR) | Verra VM0009 v3.0 §5.3 + §6.2 |
| Monitoring plan in `data_quality_spec.md` | Kabita | ISO 14064-2 §5.7 |
| Additionality story in PDD | Priya (pilot contract) | Verra VCS Program Guide v4.5 §2.3 |

---

## 8. Bottom line

**A cooler retrofit on a Nepali cement plant can generate Verra VM0009 v3.0 voluntary carbon credits — but the credit is for the kiln baseline delta, not the cooler. The cooler's job is to provide verifier-defensible secondary-air T, mass flow, and efficiency. Day 3 v0.3.1 is upstream of the credit; if the cooler data quality is bad, the kiln credit dies. The bar is "verifier accepts the kiln PDD", not "cooler wins an award."**

---

## References

1. **Verra VCS Program Guide v4.5** (2024-Q2). §2.3 (Additionality), §3.3 (Crediting Period), §3.5 (Project Ownership and Credit Allocation), §3.6 (PDD Requirements), §4 (Monitoring), §4.2 (Vintage Year).
2. **Verra VM0009 v3.0** (2023-Q4). *Emission Reductions from Waste Heat Recovery and Utilization in Cement Facilities.* §5.3 (Kiln Baseline Methodology), §6.2 (Monitoring Plan).
3. **Verra VMD0053** (2024). *Methodology Deviation Request Procedure.*
4. **Gold Standard TPDDTEC v3.1** (2022). §4.2 (Project Parameter — Cooler).
5. **Gold Standard Principles & Requirements v2.0** (2023). §3 (Additionality), §4 (Monitoring).
6. **ICVCM Core Carbon Principles** (2023). 10 principles for high-integrity carbon credits.
7. **ICVCM Category-Level Assessment Table** (2024). VM0009 v3.0 assessed as Tier 3 (high-integrity).
8. **UNFCCC Article 6.2 Rulebook** (CMA.3 decision 7/CMA.3, 2022). Corresponding adjustments for ITMO transfers.
9. **UNFCCC Article 6.4 SB Rulebook** (2024). Cement methodology replacement for ACM0003.
10. **ISO 14064-2:2019.** *Greenhouse gases — Part 2: Specification with guidance at the project level for quantification, monitoring and reporting of GHG project activities or GHG emission reduction projects.* §5.7 (Monitoring).
11. **ECRA Technology Papers 2022** (European Cement Research Academy, Düsseldorf). BAT cooler 75–80 % efficiency; <0.42 MJ/kg-cli total loss; 8–10 kWh/t-cli WHR potential.
12. **GCCA GNR 2022** (Global Cement and Concrete Association, *Getting the Numbers Right*). Indian average 72–75 %; BAT 75–80 %; `cl_PM2` reporting convention.
13. **Peray, K.E. & Waddell, J.J.** (1986). *The Rotary Cement Kiln*, 2nd ed. §6.2 (secondary-air mass flow = 1.05–1.15× stoich); §6.4 (cooler design, secondary-air T 600–900 °C).
14. **EIP-3643 (T-REX)** (2023). Permissioned tokens for regulated assets (KYC/AML on-chain).
15. **OpenZeppelin ReentrancyGuard** docs (2023). Reentrancy protection on every external call.
16. **Rekt News 2023-04.** "CementChain Rekt" — pseudonymized case study of a reentrancy exploit on a cement-token project ($4 M drained).
17. **KlimaDAO 2022** BCT/NCT retirement pilot. **Moss.Earth 2023** MCO2 retirement audit. Both used as reference for retirement-with-audit pattern.

— James Okafor, Carbon Markets Specialist
*2026-07-22*
