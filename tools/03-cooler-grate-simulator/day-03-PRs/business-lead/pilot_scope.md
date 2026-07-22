# Pilot Scope — 90-day Pilot at Hetauda Cement Industries Ltd (HCIL)

> **Owner:** Priya Karki, Business Lead
> **Date:** 2026-07-22
> **Audience:** HCIL plant management + internal team (Aanya, Ramesh, Hiro, Maya, Kabita, James, Sofia)
> **Goal:** A pilot contract that forces the plant to use the product, not stuck with shelfware. 90 days, $50K, 3 checkpoints, defined success metric at each, renewal path defined in week 1.

---

## Whose problem is this?

**HCIL Hetauda** operates a wet-process kiln with a cooler that was not designed for the site's altitude. The plant has historically under-performed on cooler heat recovery because:
1. The fan is undersized for the May design day (35 °C / 1400 m / 90 % RH) — the single most common Nepali cooler-fan mistake (Ramesh §5).
2. The plant does not have a calibrated baseline for SEC-by-cooler-compartment; the operator runs the cooler by feel.
3. The 1–3 % SEC reduction is sitting on the table as un-identified opportunities.

This is the buyer's problem. They know they have a fuel bill. They don't know the size of the un-identified opportunity or the cost of closing it.

## The next commitment (not "would you use it?" — "will you sign?")

**Price**: $50,000 USD (or NPR equivalent) for a 90-day pilot.
**Duration**: 90 calendar days from DCS data-access start date.
**Skin in the game from HCIL**: 1 dedicated plant operator (≥25 % of their time), 1 plant engineer (≥10 %), real-time DCS export of cooler-relevant tags, monthly raw-mill and kiln-coal samples for proximate/ultimate analysis, monthly clinker free-lime (f-CaO) at cooler exit.
**Skin in the game from us**: 1 sales engineer / 1 calibration engineer (visiting monthly), the calibrated model, the 3 ranked SEC-reduction opportunities, and a written engineering report at Day 90.

## The 3 checkpoints (defined in week 1, not "we'll see how it goes")

### Day 30 — Data pipeline works end-to-end
**Success metric**: ≥95 % DCS tag coverage for cooler-relevant tags over the full 30-day window, validated against plant historian; model runs on the data with no manual intervention; first-law imbalance ≤ 5 % on the 30-day data; CLI `nepal-cooler-sim diagnose --human` produces a clean KPI table from the calibrated run (per Maya's CLI spec in the negotiation room, 2026-07-22).
**Pass / fail**: Pass = proceed to Day 60. Fail = pilot terminates; we refund 50 % of the pilot fee (the engineering hours are real, but the data pipeline didn't work).
**Why this is Day 30, not Day 60**: if we can't get the data, we should know in 30 days, not 60. The plant doesn't need us for 60 days of failed data plumbing.

### Day 60 — Baseline SEC established to ±2 %
**Success metric**: the model's predicted SEC, calibrated against the 30-day baseline, is within ±2 % of the plant's reported monthly SEC (mass balance) over the 60-day window; secondary-air T and clinker-outlet T are within engineering bands (sec-air 600–1000 °C; clinker-outlet 120–200 °C, target 150 ± 30).
**Pass / fail**: Pass = proceed to Day 90. Fail = pilot extends by 30 days at no additional cost to HCIL, or terminates with 50 % refund at HCIL's option.
**Why this is Day 60**: the baseline is the single most important output of the pilot. If we get the baseline wrong, the identified opportunities are wrong. We need 60 days of clean data, not 30.

### Day 90 — Identified SEC-reduction opportunities, ranked
**Success metric**: a written engineering report, signed by a chartered chemical engineer (Aanya or equivalent) and a chartered mechanical engineer (Ramesh or equivalent), listing 3–5 specific SEC-reduction opportunities, each with:
- Engineering description (what changes, where, by how much)
- Expected SEC delta in MJ/t-cli and % of current SEC
- Expected payback in months at HCIL's current fuel cost
- Required operator / engineer action
- Required capex (if any) and opex impact
- Risk assessment (what could go wrong if the plant acts on this)
- The plant's engineering team has reviewed the report and signed off on at least 3 of the opportunities as technically actionable within HCIL's operating envelope.

**Per Ramesh's negotiation-room answer (2026-07-22)**: the 90-day target is a *Phase-1 stretch*. The realistic SEC-reduction target for cooler tuning alone is **1.5 % at Hetauda in 6 months** (180 days), not 90 days. The pilot's Day-90 deliverable is therefore *opportunity identification with engineering signature*, not *realized SEC reduction*. The 6-month milestone is the first realized-savings checkpoint in the 3-year license.

**Pass / fail**: Pass = the renewal path opens (see below). Fail = we have learned what we need to learn; we keep the report; the pilot closes; HCIL keeps the calibrated model and the 90 days of baseline data; no additional fee.

**Why "signed by a chartered engineer"**: this is the proof a plant CFO and a plant COO will both read. The CFO buys the SEC delta. The COO buys the engineering signature. Aanya, Ramesh — please confirm you are willing to put your PE/Chartered signature on the Day 90 report for the right plant. (If the answer is "no," the pilot cannot be a Hetauda pilot at this stage; we go to a plant where the answer is "yes.")

## The renewal path (defined in week 1, not the end of the pilot)

If the Day 90 report identifies ≥ 1 % SEC reduction opportunity that the plant is willing to act on within 6 months:

- **HCIL signs a 3-year license** at $50K–75K/yr (depending on plant size, see `pricing_math.md`).
- **Year 1**: licensed use of the calibrated model + monthly re-calibration against the DCS export + quarterly opportunity refresh.
- **Year 2**: same, plus access to the LLM advisor (production version) for the operator control room.
- **Year 3**: same, plus the Verra PDD package (if HCIL chooses to issue credits; co-developed with the carbon-markets-expert, James, and the env-eng-permitting, Kabita).
- **60-day renewal notice** at the end of each year. **No auto-renew** without a written kickoff of the next-year scope. The data-ownership clause is in the contract: HCIL owns the data; we own the calibrated model. We do not train on HCIL's data without written consent.
- **Exclusivity**: 12-month exclusivity on HCIL's plant in the Nepali market. We do not sell the same calibrated model to another Nepali plant during the 12-month exclusivity window.
- **Credit ownership (per James, carbon-markets-expert, negotiation room 2026-07-22)**: if the cooler-tuning opportunities realized in years 1–3 of the license lead to a Verra / Gold Standard / Article 6.4 issuance, **the credits are owned by HCIL** (or shared per a pre-agreed split documented in the PDD per VCS Program Guide v4.5 §3.5 and ICVCM Core Carbon Principles 2023 §3). We do not retire HCIL's credits against a third-party offsetting commitment. The PDD and monitoring plan will document this explicitly. The failure mode to avoid is "developer retires first, plant never gets the retirement receipt" — James has seen this in three Toucan-pooled issuances in 2023.

If the Day 90 report identifies < 1 % SEC reduction opportunity (the plant is already at BAT), the renewal path does not open. The pilot closes. HCIL keeps the calibrated model and the 90 days of baseline data. We refund 25 % of the pilot fee as a thank-you for the time.

## What we are NOT promising in the pilot

We are not promising:
- A specific % SEC reduction at the end of the 90 days. We are promising 3–5 *identified* opportunities, ranked, with engineering signature. Whether the plant acts is the plant's call.
- A Verra issuance at Day 90. Verra takes 12–18 months. The pilot gives SEC reduction + better data quality for *future* credits, not credits in hand. (Kabita, confirm in the negotiation room.)
- Implementation of the identified opportunities. We identify. The plant acts.
- Cooler mechanical / fan selection. That's Day 10 of the suite, a separate engagement.
- 3D CFD on a new cooler design. That's a 5-day project, not a pilot.

## What the plant gets at the end of the 90 days (regardless of pass/fail)

- The calibrated 1D, 5-compartment, counter-flow grate cooler model.
- 90 days of validated, plant-specific baseline data (SEC-by-compartment, sec-air T profile, clinker-outlet T profile, fan-power profile).
- The Day 90 engineering report.
- The data in the plant's preferred format (CSV, JSON, or a print-ready PDF; the sales engineer will confirm in the scoping call).
- The 3–5 identified opportunities, ranked, with engineering signature.
- A 12-month data-archive commitment (we keep the data, encrypted, for 12 months in case the plant wants to revisit).
- A **data-quality assurance section** in the pilot contract (per Kabita, env-eng-permitting, negotiation room 2026-07-22) that documents the per-field Tier (Tier 1 / Tier 2 / Tier 3 / measured) and the 1σ uncertainty, per **Verra VCS Program Guide v4.5 §3.4** (data quality requirements) and **Gold Standard TPDDTEC v3.1 §4.2** (project parameter requirements). This is what makes the pilot's output usable as a Verra / CBAM monitoring input downstream.

## What the pilot costs us (rough)

- 1 sales engineer × 30 days × $500/day = $15K
- 1 calibration engineer × 20 days × $700/day = $14K
- Server / compute for 90 days (MC + Sobol) = $2K
- Travel (3 site visits, Kathmandu → Hetauda) = $4K
- Engineering report (Aanya + Ramesh, 3 days each at $1K/day) = $6K
- Contingency / LLM inference / overhead = $9K
- **Total cost ~ $50K**. We are not making margin on the pilot. We are learning and we are earning the right to a 3-year license.

If we get to the 3-year license at $50K/yr for 3 years = $150K LTV on this customer. If we don't, we have learned what we needed to learn for customer #2, #3, and #50.

## Why Hetauda, not Hongshi-Shivam or Ghorahi

- **Hetauda** is a legacy plant with 1–3 % SEC reduction on the table. The plant is the right size (3000 tpd class) and the right altitude to expose the fan-power / duty-case issue (Ramesh §5). HCIL has historical operating data and a control room that exports DCS. The plant is a 4-hour drive from Kathmandu; site visits are cheap.
- **Udayapur** is similar (UCIL), at a lower altitude (~300 m). The pitch is similar but the duty case is easier. Pilot #2, not pilot #1.
- **Hongshi-Shivam** is a new plant (post-2018). The easy wins are gone; the pitch is "0.5–1 % SEC reduction on a Chinese-built plant, plus the data quality for future credits." Different price, different pitch. Pilot #3, not pilot #1.
- **Ghorahi** is mid-life, 1–2 % SEC reduction. Good pilot #4.

We do pilot #1 at Hetauda. We do not start with Hongshi-Shivam. The first customer is the cheapest to acquire and the most expensive to support; we want a customer who will *use* the product, not a customer who will *evaluate* it for 6 months and decide.

## What we need from the team before we go to HCIL

- **Aanya**: confirm the 1–4 % range is the honest engineering claim for a Hetauda-class plant.
- **Ramesh**: confirm the Hetauda 1400 m / 35 °C / 90 % RH duty case is the right design day for the pilot.
- **Hiro**: confirm the Day 30 / 60 / 90 success metrics are measurable on HCIL's actual DCS export.
- **Maya**: confirm the Day 90 report format is a signed PDF + CSV + JSON round-trip, not a dashboard.
- **Kabita**: confirm the pilot's value proposition is SEC reduction + data quality, not credits in hand.
- **James**: confirm the renewal license structure (3-year, 12-month exclusivity, data ownership) is consistent with VCS market practice.
- **Sofia**: confirm the LLM advisor is *out of scope* for the 90-day pilot (it would muddy the success metric).

If any of the seven cannot confirm, we do not go to HCIL with this scope. We revise and re-post.

---

## Sources cited (proof, not aspirational)

1. **Aanya's Day 3 review** (`tools/03-cooler-grate-simulator/reviews/AANYA-DAY-03-REVIEW.md`) — engineering claim 1–4 % range anchored to ECRA BAT (75–80 % cooler efficiency) and Mujumdar 2007 compartment model.
2. **Ramesh's Day 3 review** (`reviews/DAY-03-RAMESH-REVIEW.md`) — Hetauda 1400 m / 35 °C / 90 % RH duty case, first-law check, compartment design.
3. **Hiro's Day 3 review** (`reviews/hiro-day-03-review.md`) — test fragility, refutation tests, sample-size discipline.
4. **Mujumdar, K.S. (2007)**, *Ind. Eng. Chem. Res.* 46(7) — 1D compartment counter-flow cooler model.
5. **Peray, K.E. & Waddell, J.J. (1986)**, *The Rotary Cement Kiln*, 2nd ed. — secondary-air T band, GJ/t benchmarks.
6. **ECRA Technology Papers 2022** — modern cooler BAT ceiling.
7. **GCCA GNR 2022** — `cl_PM2` reporting convention.

---

— Priya, 2026-07-22
