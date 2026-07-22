# Pitch Deck Outline — Himalayan Space Solutions

> 12 slides. Content only — no design. Each slide is one paragraph that
> would fit on a slide if the speaker were telling the same story live.
> Pull quotes and numbers are bolded. Suggested visuals are in
> `[brackets]`. Read this top to bottom; do not re-order.

---

## Slide 1 — Cover

**Himalayan Space Solutions.** *The decarbonization platform built for the
cement and brick plants that built Nepal.* `[Logo: placeholder — a single
bold wordmark "हिमालयन कार्बन" with a small mountain glyph, plus
"nepal_decarb_pro" subtitle in a monospace face — defer to Graphics
Designer]` `[Background: a real photo of a Nepali cement plant at dusk,
Bagmati province, kiln lit up — not a stock-photo collage]` Speaker
notes: state name, role, and the one sentence: "We are a Nepali
engineering team, and this deck is about why every cement and brick
plant in Nepal should be measuring and monetising their CO₂ in the next
twelve months."

## Slide 2 — The problem

Nepal's cement industry emits roughly **6 million tonnes of CO₂ a year
and the brick industry another 2 million — yet 0% of these plants have
an audited, standards-compliant emissions baseline.** Three pressures
are about to break that: **EU CBAM** in its definitive phase will levy
carbon tariffs on any cement exported to Europe, priced at the
difference between the EU ETS price and the plant's verified
intensity; **Nepal's NDC** legally commits the country to net-zero by
2045 and the Department of Environment needs an MRV system to track
it; and **banks** will require PCAF-aligned disclosures before lending
to industrial clients starting 2027. A plant with no measurement
system loses on three fronts at once: export access, government
cooperation, and financing cost. `[Map of Nepal, 6 cement plants + 10
brick clusters highlighted, tonnes/year labelled]`

## Slide 3 — Our solution

**Measure, certify, and monetise your cement plant's CO₂ — for free.**
`nepal_decarb_pro` is a single, open-source (MIT), bilingual
(English / नेपाली) platform that takes a plant from zero data to a
Verra-ready carbon credit PDD and a 100/100 ISO 14064-1 report in
30 days, on a $20/month server, with no foreign consultants. The
Hetauda pilot is already in production: 861,025 tCO₂/yr baseline,
783 kg CO₂/t cement intensity, 56,407 Verra credits/yr potential,
$22.5M NPV at EU ETS $65/t. `[Screenshot of the live Streamlit
dashboard, with Hetauda numbers visible]` Speaker notes: this is the
slide you leave on the screen during Q&A. One screenshot, real
numbers, no marketing language.

## Slide 4 — How it works (3 steps)

**Step 1 — Onboard in 15 minutes.** Plant manager creates a tenant,
adds their plant (cement_dry / brick_clamp / etc.), uploads 12 months
of historical production and fuel data as a CSV (or enters it
manually). The platform validates and stores it in an audit-trail DB.
**Step 2 — Compute in 30 seconds.** Select the methodology (IPCC
2006 Tier 2 or Tier 3), click "Compute baseline". The system runs the
mass-balance, the Monte Carlo uncertainty, the Sobol sensitivity,
and the LCA in one go. **Step 3 — Report in one afternoon.** The
platform auto-generates 5 reports (ISO 14064-1, Verra PDD, Gold
Standard PDD, TCFD, SBTi), all from the same data, all audit-ready.
Total time from signup to bankable report: 30 days for a full
historical import, 1 afternoon for a current-year refresh. `[Simple
3-block diagram: data in → engine → reports out]`

## Slide 5 — Hetauda case study

We proved the platform on the largest public reference we could find:
**Hetauda Cement Industries Ltd, Makwanpur, Bagmati — installed
1990, 1.1 Mt/yr capacity, dry process.** Pilot results from the
2024 baseline: **861,025 tCO₂/yr total**, of which 511,307 tCO₂
process emissions (from CaO and MgO calcination) and 346,911 tCO₂
fuel combustion (predominantly bituminous coal and petcoke). Intensity
**783 kg CO₂/t cement** — better than the Nepali average of ~950
but 12% above the GCCA global benchmark. After applying a
biomass-cofiring + WHR project scenario, the net annual emission
reductions are **56,407 tCO₂/yr**, which at EU ETS $65/t is **$3.67M
revenue per year** and a **$22.5M NPV** over the 10-year Verra
crediting period. ISO 14064-1 score: **100/100 on all 20 criteria**.
The full PDD is in `pro/reports/hetauda_pilot_results.json`. `[3
small charts: pie of emissions sources, intensity vs benchmark, NPV
sensitivity to carbon price]`

## Slide 6 — 11 international standards, one platform

The single biggest reason a Nepali plant today pays $50k–$500k to a
foreign consultant is that no in-house team can cover all 11
standards the bank, the buyer, and the regulator ask for. We do
them all, in one codebase, with line-by-line criteria checkers and
live scores: **ISO 14064-1, ISO 14064-2, ISO 14064-3, ISO 50001,
ISO 14001, ISO 14040/14044 (LCA), TCFD, SBTi, GCCA, PCAF, GHG
Protocol** — plus **IPCC 2006/2019** at Tier 2 and Tier 3 for the
engine, and **Verra VCS** plus **Gold Standard** for the carbon
markets. The Hetauda pilot scores 100/100 on every one of these
checkers. The 9.78/10 international rating on the platform is
the proof that the engineering depth is there — but the real point
of the slide is: one platform, one set of data, eleven different
reports, no consultant. `[Icon grid: 11 standard logos in 4×3 layout]`

## Slide 7 — Product screenshots

Four screens from the live product. **(1) Cement baseline dashboard**:
Tier 2 / Tier 3 toggle, Monte Carlo 5,000-sample distribution
shown as a histogram with 50/90/95% confidence bands, Sobol
sensitivity bar chart on the right showing the top 3 drivers
(coal share, CaO fraction, electricity). **(2) ISO 14064-1
checker**: 20 criteria, all green, with a "Download report" button
that produces a 20-page PDF identical in structure to what a VVB
expects. **(3) Verra PDD preview**: 6 sections filled in from the
plant data (project boundary, baseline, additionality, monitoring
plan, leakage, buffer) — the boilerplate a consultant would
normally charge for. **(4) LLM advisor in नेपाली**: a chat box
where a kiln operator types "किन CO2 बढी छ?" and gets an answer
grounded in their own plant's data, with citations. `[4-panel grid,
each panel a real screenshot from the live demo]`

## Slide 8 — Business model (3 pricing tiers)

**Free — Express.** One plant, current month only, manual data entry,
basic dashboard, ISO 14064-1 PDF. Free forever, for any Nepali
cement or brick plant. **Pro — Full.** Unlimited plants in a
tenant, 3–5 years of historical data via CSV, IoT sensor stack
(ESP32 + DHT22 + MQ-7 + MQ-135 + MAX31855, MQTT-bridged),
real-time dashboard, all 5 reports auto-generated, API access.
**NPR 250,000 / year per plant** (≈ USD 1,875), or NPR 1.2M for a
5-plant tenant. **Enterprise — NCMA cohort / national rollout.**
White-label as "NCMA Carbon Platform", bulk onboarding, dedicated
VVB liaison, custom data-sharing agreement with the Department of
Environment, on-site support. **NPR 5M+ per cohort**, with a
10-cement-plant pilot available now. Open-source (MIT) means the
code is never the lock-in — the value is in the data, the
methodology, and the team. `[3-column pricing table, with the
"Free" column emphasised in brand color]`

## Slide 9 — Traction

We are early and we say so. **Today:** the Hetauda pilot is in
production on a $20/month VPS, the live demo is up at
`nepalcarbon.org.np`, the codebase is 78/78 tests passing on 11
standards, and the open-source release v1.0.1 is on GitHub. **In
the pipeline:** an LOI from one of the 6 major cement plants to
extend the Hetauda methodology to a second site; an outreach
letter in front of NCMA proposing a free cohort of 20 plants; a
brief in front of the Department of Environment proposing a
national MRV system under the NDC; an application to the World
Bank Climate Innovation Fund for the brick-kiln migration work.
**In the next 12 months:** 5 paying Pro customers (NPR 6.25M ARR),
1 NCMA-cohort Enterprise deal (NPR 5M+), 1 grant-funded national
rollout. We are not claiming hockey-stick growth. We are claiming
a credible first customer and a clear path to 20 plants. `[Timeline
graphic: Q3 2026 = Hetauda live; Q4 = 5 Pro; Q1 2027 = NCMA cohort;
Q2 = national pilot]`

## Slide 10 — Team

**Nishchal Baniya, Founder.** Nepali engineer, builder of
`nepal_decarb_pro` end-to-end. Sales, partnerships, fundraising,
customer success. **Open roles recruiting now (Month 1–3):**
part-time chemical engineer (cement process domain), part-time
business developer (NCMA + DoE + first 5 customers), project-based
graphics designer (brand, deck, marketing site), full-time software
engineer (Month 2, production hardening), environmental engineer
(Month 2, VVB-readiness), AI/ML engineer (Month 3, LLM fine-tune
on Qwen2.5-7B for Nepali), data engineer (Month 3, Postgres + IoT
at scale), marketing lead (Month 3, content + email + PR). **We
are intentionally lean and intentionally local.** We are not
hiring a sales team in Singapore. We are hiring a chemical engineer
who has walked a Nepali kiln floor. `[Founder photo, 1 line per
open role with the "what we need you for in week 1" line]`

## Slide 11 — The ask

We are raising a **NPR 25M seed round (≈ USD 190k)** to convert
the Hetauda pilot into 5 paying Pro customers, 1 NCMA-cohort
Enterprise contract, and a national-pilot grant application. Use of
funds: **40% engineering hires** (1 software, 1 environmental, 1
data — the people who harden the platform for 50+ plants), **30%
on-site customer success** (travel to Hetauda, Udayapur, Palpa,
Kathmandu valley for the first 5 onboardings), **20% VVB
partnership development** (engage TÜV NORD or DNV for the first
independent ISO 14064-3 verification, ~$20–30k), **10% brand and
marketing** (logo, deck, site, this content). Alternative paths
we will also accept: **(a) a strategic partner** — a cement plant
or a bank that wants the platform white-labelled and is willing to
fund the engineering in exchange for first-mover access; **(b) a
grant partnership** — co-applicant on a World Bank, GCF, or GGGI
proposal for the national rollout. We are not picky about the
structure. We are picky about getting the first 5 plants live in
the next 12 months. `[3-box "what we need" / "what you get" /
"what we promise"]`

## Slide 12 — Contact

**Nishchal Baniya**, Founder, Himalayan Space Solutions.
`nishchal.baniya@himalayancarbonnepal.com`. Phone + WhatsApp:
+977-98XXXXXXXX. Live demo: `nepalcarbon.org.np`. GitHub:
`github.com/himalayan-carbon-nepal/nepal_decarb_pro`. Office:
Kathmandu, Bagmati. Working hours: 9am–6pm NPT, but we answer
WhatsApp at 11pm because kilns don't sleep. If you are a plant
manager, an NCMA board member, a Department of Environment
official, a VVB, a bank, or a funder reading this slide — the
single best next step is a 30-minute call. Bring your data. We
will bring the platform. We will have your baseline by the end
of the meeting. `[Plain text, large font, no marketing imagery —
just a name, an email, a phone, and a one-line "reply to book a
call"]`

---

*This deck is the master narrative. Every blog post, every email,
every cold call should sound like a different chapter of the same
story told on these 12 slides. If a piece of marketing cannot be
traced back to a slide, throw it out.*
