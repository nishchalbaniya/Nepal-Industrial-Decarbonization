# CBAM 2023/1773 Annex IV — Cement Clinker (CN 2523 10 00) Default-Value Re-Verification

**Reviewer:** James Okafor, carbon-markets-expert
**Task:** Re-verify the claim that "EU CBAM Implementing Reg 2023/1773 Annex IV specifies a default value of 0.642 t CO2/t clinker for the direct (Scope 1, calcination + kiln fuel) default for cement clinker under CBAM Annex IV."
**Sources read (live, this turn):** EUR-Lex 2023/1773 page; EC Taxation & Customs "Default values transitional period" PDF (Dec 2023, JRC); EC draft Implementing Regulation annexes (2025/2621 — definitive period); DEHSt VET 2021 report; UK gov.uk CBAM cement-sector guidance; CBAM guidance document (Nov 2023).

---

## 1. Verdict

**NOT-FOUND — the 0.642 t CO2/t clinker figure does not exist in Commission Implementing Regulation (EU) 2023/1773 Annex IV, nor in the published CBAM default-value tables for cement clinker (CN 2523 10 00), nor in the EU ETS product benchmark for grey cement clinker.** The figure cited in `DAY-03-NEGOTIATION.md` and `data_quality_tiers.py` cannot be traced to a primary CBAM source. The closest live CBAM numbers for cement clinker direct emissions are **0.83 t CO2e/t (transitional, JRC 2023)**, **0.870 t CO2e/t (2026 definitive, grey clinker)**, and **1.240 t CO2e/t (2028+ definitive, grey clinker, including 20% mark-up phase-in)**. Two further corrections are needed alongside the numeric fix: (a) the numeric CBAM defaults for non-electricity goods are NOT in 2023/1773's Annex IV at all — 2023/1773's Annex IV defines the **methodology** (system boundaries, production-route rules, "no distinction between grey and white clinker", calcination scope); the numeric tables live in a separate Commission publication; and (b) there is also a different "default value" universe under the post-2025 definitive regime in Implementing Regulation (EU) 2025/2621, with values that are country-specific and markedly higher than the transitional 0.83.

## 2. The 0.642 figure — where might it have come from?

The figure does not appear in any CBAM instrument I could locate. Plausible misattributions (none of which are CBAM Annex IV defaults for CN 2523 10 00):

- **0.693 t CO2/t** — EU ETS product benchmark for grey cement clinker (4th trading period, 2021-2025), per DEHSt VET 2021 report. This is the *free-allocation* benchmark, not a CBAM default.
- **0.766 t CO2/t** — EU ETS product benchmark for grey cement clinker in the prior period (2013-2020), per the same DEHSt VET 2021 source. Also a free-allocation benchmark, not CBAM.
- **0.793 t CO2/t** — Average specific emissions of 33 EU grey-cement-clinker installations in 2021 (DEHSt VET 2021, p.77). This is an *observed EU average*, not a default. The task description correctly notes that 0.793 is not the clinker default — but I want to flag that even 0.793 is a real ETS-installation number, whereas **0.642 is not a real ETS number, JRC number, or CBAM number I can locate**.
- **0.642** does not match any row in the transitional default table, the 2026 definitive defaults, the EU ETS benchmark, the CSI/GHG Protocol default (0.525 calcination only or 0.862 incl. fuel), the IPCC 2006 default (~0.510 calcination), or the EMEP/EEA guidebook Tier-1 factors. It is most likely a transcription/derivation error or a fabrication.

## 3. What 2023/1773 Annex IV actually says for cement clinker (CN 2523 10 00)

Source: Commission Implementing Regulation (EU) 2023/1773 of 17 August 2023, Annex IV, Section 3 ("Cement and clinker"), Section 3.3 ("Cement clinker"). EUR-Lex page: <https://eur-lex.europa.eu/eli/reg_impl/2023/1773/oj/eng>. The text published at <https://api.pks.rs/storage/assets/CBAM%20Implementing%20regulation%202023%2017732.pdf> (mirror of the OJ text) gives the relevant rows verbatim:

> **CN/TARIC code** — `2523 10 00`
> **Description** — `Cement clinkers`
> **Greenhouse gas** — `Carbon dioxide`
> ...
> **3.3.1. Special provisions** — "No distinction shall be made between grey and white cement clinker."
> **3.3.2. Production route** — "For cement clinker, direct emissions monitoring shall encompass: — Calcination of limestone and other carbonates in the raw materials, conventional fossil kiln fuels, alternative fossil-based kiln fuels and raw materials, biomass kiln fuels (such as waste-derived fuels), non-kiln fuels, non-carbonate carbon content of limestone and shales, or alternative raw materials such as fly ash used in the raw meal in the kiln and raw materials used for flue gas scrubbing. — The additional provisions of Section B.9.2 of Annex III shall apply. Relevant precursors: none."

That is the entirety of the clinker row in Annex IV. **There is no numeric default value in the cell.** Annex IV is the methodology annex — the data column is reserved for parameter definitions, not embedded-emission figures.

## 4. Where the numeric CBAM defaults actually live (with row text)

### 4.1 Transitional period (1 Oct 2023 – 31 Dec 2025)

Source: European Commission, Taxation and Customs DG, *Default values for the transitional period*, December 2023 (JRC 2023 estimates), Section 2.3, Table "Default values for the transitional period for cement". URL: <https://taxation-customs.ec.europa.eu/system/files/2023-12/Default%20values%20transitional%20period.pdf>. The clinker row reads (verbatim, with European decimal commas):

| Aggregated goods category | CN code | Description | Direct emissions (t CO2e/t) | Indirect emissions (t CO2e/t) | Total emissions (t CO2e/t) |
|---|---|---|---|---|---|
| **Cement clinker** | **2523 10 00** | **Cement clinkers**⁸ | **0,83** | **0,04** | **0,87** |

Footnote 8: "The default values are based on the JRC estimates for grey cement clinkers." This table is the authoritative numeric source for the transitional period. Same table, other cement rows: 2523 21 00 (white Portland) = 1.16 / 0.10 / 1.26; 2523 29 00 (other Portland) = 0.81 / 0.06 / 0.87; 2523 90 00 (other hydraulic) = 0.59 / 0.04 / 0.63; 2523 30 00 (aluminous) = 1.75 / 0.15 / 1.90. (None of these is 0.642.)

### 4.2 Definitive period (from 2026) — for completeness, since 2023/1773 itself is now superseded for numeric defaults

Source: draft annexes to the Commission Implementing Regulation laying down rules for default values (C(2025) 8552 final, published provisionally 16 Dec 2025; adoped file hosted at <https://taxation-customs.ec.europa.eu/document/download/1c05d211-80cb-4aaa-8ef0-e08005a95d7e_en?filename=DVs+as+adopted_v20260204+.xlsx>). The grey-clinker row under Albania (illustrative; values are country-specific in the 2026+ regime) reads:

| CN code | Description | Default Value | 10% mark-up | 20% mark-up | 30% mark-up | Production route |
|---|---|---|---|---|---|---|
| **2523 10 00** | **Grey clinker** | **0.870** | **0** | **0.870** | **0.957** | **1.044** | (A) |

And the 2028+ table (post full mark-up phase-in): grey clinker 1.240 direct + 0.040 indirect = 1.280, with 10/20/30% mark-ups of 1.408 / 1.536 / 1.664. (These are not in 2023/1773 Annex IV either — they sit in a new implementing act under Regulation (EU) 2023/956 Article 7(7).)

## 5. Indirect (Scope 2) default for cement clinker

For CBAM purposes, "indirect" emissions for cement mean **electricity consumed during clinker production**, multiplied by the country-of-origin grid emission factor (t CO2e/MWh) published in Annex II of the relevant implementing act. The transitional default for cement clinker is **0.04 t CO2e/t of clinker** (i.e. an assumed electricity intensity of roughly 0.05–0.10 MWh/t clinker at a ~0.4–0.8 t CO2e/MWh grid). The actual figure to use in any specific import is **`electricity_consumed_MWh_per_t_clinker × country_specific_grid_EF`**, not a flat per-tonne clinker number — but the published JRC proxy default is 0.04 t CO2e/t. This is a small fraction of the direct emissions (0.83) because clinker is fuel-and-calcination-dominated, not electricity-dominated; grinding is where most of the electricity goes and that happens in the *cement* step (CN 2523 21 / 2523 29), not at the clinker step.

## 6. Bottom-line corrections to feed back into DAY-03-NEGOTIATION.md and `data_quality_tiers.py`

1. **The 0.642 t CO2/t figure is wrong and should be removed.** It is not in 2023/1773 Annex IV, not in the Dec 2023 JRC transitional default table, and not in the 2025/2621 definitive defaults.
2. **Replace with the correct source and number.** For the transitional period (still relevant for any 2023–2025 quarterly reports), use **0.83 t CO2e/t direct + 0.04 t CO2e/t indirect = 0.87 t CO2e/t total** for CN 2523 10 00, source: <https://taxation-customs.ec.europa.eu/system/files/2023-12/Default%20values%20transitional%20period.pdf>, Section 2.3 cement table.
3. **Cite the correct legal instrument for the methodology.** The methodology (system boundary, calcination, kiln fuels, "no grey/white distinction", precursor rules) is in **Commission Implementing Regulation (EU) 2023/1773, Annex IV, Section 3.3** (EUR-Lex: <https://eur-lex.europa.eu/eli/reg_impl/2023/1773/oj/eng>). The numeric default values are a separate Commission publication, not part of 2023/1773 itself.
4. **If the project is modelling 2026+**, note the regime change: country-specific defaults with mark-ups (10% in 2026, 20% in 2027, 30% from 2028), per draft C(2025) 8552 final annexes / adopted file `DVs as adopted_v20260204+.xlsx` on the EC CBAM page.
5. **For "other cement" (CN 2523 29 00, "Other Portland cement"), the transitional direct default is 0.81 t CO2e/t, not 0.793** — close to but not equal to the 0.793 EU-installation average. The 0.793 figure in the task description is an EU ETS observed average (DEHSt VET 2021), not a CBAM default; it should not be cited as either.

## 7. Primary sources actually read this turn

- **EUR-Lex 2023/1773 landing page:** <https://eur-lex.europa.eu/eli/reg_impl/2023/1773/oj/eng> (confirms the regulation exists; Annex IV is the methodology annex, no numeric defaults embedded).
- **CBAM Implementing Regulation 2023/1773 (full text mirror):** <https://api.pks.rs/storage/assets/CBAM%20Implementing%20regulation%202023%2017732.pdf> — Annex IV Section 3.3 verbatim, including the "no distinction between grey and white cement clinker" special provision and the calcination + kiln-fuel production-route description.
- **EC Default values for the transitional period (Dec 2023, JRC):** <https://taxation-customs.ec.europa.eu/system/files/2023-12/Default%20values%20transitional%20period.pdf> — Section 2.3, row CN 2523 10 00 = 0.83 / 0.04 / 0.87.
- **EC adopted default values for the definitive period (2026 onwards, XLSX):** <https://taxation-customs.ec.europa.eu/document/download/1c05d211-80cb-4aaa-8ef0-e08005a95d7e_en?filename=DVs+as+adopted_v20260204+.xlsx> — CN 2523 10 00 grey clinker = 0.870 / 0 / 0.870 (2026 Albania example), 1.240 / 0.040 / 1.280 (2028+ grey clinker).
- **CBAM guidance document (Nov 2023):** <https://taxation-customs.ec.europa.eu/system/files/2023-11/CBAM%20Guidance_EU%20231121%20for%20web_0.pdf> — precursor definitions, indirect emissions rules.
- **DEHSt VET Report 2021 (for the 0.766 / 0.693 / 0.793 reference):** <https://www.dehst.de/SharedDocs/downloads/EN/publications/2021_VET-Report.pdf?__blob=publicationFile&v=3> — confirms these are EU ETS benchmark / observed values, not CBAM defaults.

— James Okafor, carbon-markets-expert
