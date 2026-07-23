# CBAM Annex IV — James's Re-Verification (Summary)

**Date:** 2026-07-22
**Reviewer:** James Okafor (carbon-markets-expert)
**Status:** CORRECTED — the 0.642 t CO2/t clinker figure cited in
`data_quality_tiers.py` and `DAY-03-NEGOTIATION.md` was wrong.

## What was wrong

The Day 3 ship cited **0.642 t CO2/t clinker** as the CBAM 2023/1773
Annex IV default for cement clinker (CN 2523 10 00). That figure
**does not exist** in:

- Commission Implementing Regulation (EU) 2023/1773 Annex IV (the
  methodology annex — no numeric defaults are embedded there)
- The EC DG TAXUD Dec 2023 JRC transitional default table
- The EC 2025/2621 definitive period default values (adopted XLSX)
- The EU ETS product benchmark for grey cement clinker (0.766 in the
  prior period, 0.693 in the 4th trading period — both are free-
  allocation benchmarks, not CBAM defaults)
- The CSI / GHG Protocol defaults (0.525 calcination only, 0.862
  including fuel)
- The IPCC 2006 default (~0.510 calcination only)

The 0.642 was a training-data confabulation. **Removed from the
PR note.**

## What is correct (transitional period, 1 Oct 2023 – 31 Dec 2025)

For cement clinker (CN 2523 10 00, "Cement clinkers", no grey/white
distinction per Annex IV §3.3.1):

- **Direct emissions (calcination + kiln fuel): 0.83 t CO2e/t**
- Indirect emissions (electricity during clinker production): 0.04 t CO2e/t
- **Total: 0.87 t CO2e/t clinker**

Source: European Commission DG TAXUD, *Default values for the
transitional period*, December 2023 (JRC estimates), Section 2.3,
table "Default values for the transitional period for cement".

URL: <https://taxation-customs.ec.europa.eu/system/files/2023-12/Default%20values%20transitional%20period.pdf>

Footnote 8: "The default values are based on the JRC estimates for
grey cement clinkers."

## Methodology reference (for any CBAM XML)

Commission Implementing Regulation (EU) 2023/1773, Annex IV,
Section 3.3 (Cement clinker):

- CN/TARIC code: 2523 10 00
- Greenhouse gas: Carbon dioxide
- Production route: direct emissions encompass calcination of
  limestone and other carbonates; conventional fossil kiln fuels;
  alternative fossil-based kiln fuels and raw materials; biomass
  kiln fuels (waste-derived); non-kiln fuels; non-carbonate carbon
  content of limestone and shales; alternative raw materials such
  as fly ash; raw materials used for flue gas scrubbing.
- Special provision: "No distinction shall be made between grey
  and white cement clinker."

URL: <https://eur-lex.europa.eu/eli/reg_impl/2023/1773/oj/eng>

## What changes for 2026+ (definitive period, for Hetauda's pilot)

If Hetauda starts shipping clinker to the EU in 2026 or later, the
CBAM regime is different. The transitional JRC defaults (0.83) are
replaced by country-specific defaults with phased mark-ups:

- 2026: default + 10% mark-up
- 2027: default + 20% mark-up
- 2028+: default + 30% mark-up

The country-specific values for grey clinker (CN 2523 10 00)
in the adopted XLSX range 0.870 to 1.240 t CO2e/t direct across
EU member states. Nepal is not in the EU, so the relevant number
for Hetauda exports is the *rest-of-world* default; that row needs
a separate check before any 2026+ pilot PDD.

Source: EC adopted XLSX, *DVs as adopted_v20260204+*:
<https://taxation-customs.ec.europa.eu/document/download/1c05d211-80cb-4aaa-8ef0-e08005a95d7e_en?filename=DVs+as+adopted_v20260204+.xlsx>

## What changed in the codebase

`tools/03-cooler-grate-simulator/day-03-PRs/env-eng-permitting/data_quality_tiers.py`,
field `ef_cbam_default_clinker_t_co2_per_t`:

- Old: "0.642 t CO2/t clinker cited by analogy; @James to re-verify
  the row before PDD commit"
- New: "0.83 t CO2e/t direct + 0.04 t CO2e/t indirect = 0.87 t
  CO2e/t total, source: EC DG TAXUD transitional default values
  Dec 2023 (JRC), Section 2.3, row CN 2523 10 00"

Also added a sigma of 0.10 t CO2e/t absolute (≈ ±12% 1-sigma) to
cover the JRC estimate uncertainty and the country-specific spread
in the 2026+ adopted values.

## What is still open

- The 2026+ row for Nepal (rest-of-world) is not yet verified.
  This is a Day 12 (CBAM declaration) follow-up item, not a Day 3
  blocker. James will pick this up when the pilot scope includes
  an EU-bound shipment date.
- The full re-verification report is in
  `reviews/JAMES-CBAM-VERIFY.md` with all five primary sources
  read live this turn (EUR-Lex, EC DG TAXUD PDF, EC adopted XLSX,
  CBAM guidance Nov 2023, DEHSt VET 2021).

— James Okafor, 2026-07-22.
