# Competitor Landscape — Cement Cooler / SEC Software

> **Owner:** Priya Karki, Business Lead
> **Date:** 2026-07-22
> **Audience:** Internal team (Aanya, Ramesh, Hiro, Maya, Kabita, James) + future sales engineers
> **Goal:** A 1-page honest map of who else is in this space, what they have, and what we have that they don't. Be specific about gaps. Be specific about overlaps.

---

## Honest disclosure up front

The Day 3 brief named three competitors: **CementaSustent, SINTEF, ECRA**. After research, the landscape is messier than that. Two of the three are not commercial products, and a third (CementaSustent) does not appear to exist as a named software product in the public market. This document is honest about that and maps the *actual* competitive set.

- **CementaSustent** — name not found in any catalog, vendor directory, or industry publication in the 2024–2026 timeframe. The closest adjacent product is **alcemy** (alcemy.tech), a German AI software vendor for cement quality and CO₂ reduction, which addresses the *mill and quality* stage, not the cooler. There are also several Chilean / LatAm engineering consultancies that do *one-off* cement decarbonization studies (e.g. CSI Chile, Fundación Chile) — these are consultancies, not products. **Flag for the user**: I cannot substantiate "CementaSustent" as a competitor. If a name was meant (e.g. alcemy, Carbon Re, IFC tool), the brief should be updated.
- **SINTEF** — the Norwegian research institute. SINTEF runs the **CEMCAP** project (CO₂ capture from cement, H2020 EU) and develops **process models** for oxyfuel cement and CFD for coolers. **Not a commercial product**. SINTEF licenses models to research collaborators (e.g. via VDZ, TKIS) and does paid R&D for the cement majors. SINTEF is a *potential partner*, not a competitor. (Source: `sintef.no/globalassets/project/cemcap/...` and the CEMCAP D7.3 deliverable on oxyfuel CFD.)
- **ECRA** — the European Cement Research Academy, Düsseldorf. ECRA publishes the **ECRA Technology Papers** (2017, 2022) and the **ECRA CCS Phase II report** (carbon capture). **ECRA is a research consortium, not a software vendor.** Its publications define the *BAT ceiling* we cite (75–80 % cooler efficiency, 0.42 MJ/kg-cli total heat loss) but ECRA does not sell a cooler simulator. ECRA is a *reference standard*, not a competitor. (Source: `ecra-online.org`, `api.ecra-online.org/fileadmin/files/ECRA__Technical_Report_CCS_Phase_II.pdf`.)

So the *real* competitive set is **APC platforms** (Advanced Process Control, OEM-embedded), **AI digital-twin startups** (Carbon Re, alcemy, iFactory), and **DFIs / IFC tools** (free / advisory).

---

## The actual competitive map

### Tier 1 — APC platforms (the entrenched OEM-embedded control stack)

These are the platforms the plant *already has*. The buyer for these is the plant's process control engineer and the OEM (FLSmidth, KHD, Sinoma, ABB). They are sold as part of a new-kiln-line contract or as an aftermarket optimization add-on.

| Vendor | Product | What it does | What it doesn't do | Indicative price (public sources) |
|---|---|---|---|---|
| **ABB** | **ABB Ability™ Expert Optimizer (EO)** — kiln, calciner, **cooler control module** | Closed-loop control of cooler, kiln, calciner, mills. Direct integration with ABB 800xA DCS. Reports "Reduction in UGP2 variation" on cooler. | Does not publish per-compartment physics. Does not output a Verra-grade audit trail. Vendor lock-in to ABB DCS. | "Software only" license or "Turnkey" with engineering. Annual subscription. (Source: `search.abb.com/library/Download.aspx?DocumentID=9AKK107492A2268`) |
| **FLSmidth** | **ECS/ProcessExpert®** v9.1 (July 2024) | Stabilises kiln + cooler, reduces CO₂/NOₓ, increases alternative fuel utilisation. Embedded with FLSmidth kiln supply. | Closed-loop control only; not an open engineering model. Not accessible to plants with non-FLSmidth DCS without integration work. | Bundled with new kiln supply; aftermarket license + commissioning. (Source: `flsmidth-cement.com/products/ecs-processexpert-advanced-process-control-software`) |
| **Siemens** | **Sicement IT MCO** | Similar to ABB EO / FLSmidth ECS — closed-loop APC on cement pyroprocess. | Same as above — vendor lock-in, no open engineering model. | Bundled with Siemens DCS / kiln supply. (Source: industry survey, `oxmaint.com/industries/cement-plant/...`) |
| **KHD** | **Pyrocontrol** (in-house APC) | Bundled with KHD Pyrostep cooler / kiln supply. | Same as above. | Bundled with KHD supply. |

**The wedge for us**: APC platforms are **closed-loop controllers**. They *make* the setpoint changes. They do not produce a **defensible engineering audit trail** for a Verra validation, an EU CBAM filing, or a CFO who wants to know *which* 1 % SEC reduction was identified and *why*. The buyer for APC is the control room; the buyer for us is the CFO + the engineer who has to *justify* the SEC delta to a third-party validator.

### Tier 2 — AI / digital-twin startups (the "new thing")

| Vendor | Product | What it claims | What it actually delivers (public sources) | Indicative price |
|---|---|---|---|---|
| **Carbon Re** (UK) | **Delta Zero** (announced 2024) | "Up to 5 % fuel reduction / 10 % SEC reduction" on the pyroprocess (preheater through cooler). Closed-loop AI agents. | AI / reinforcement learning on top of APC. Requires integration with the plant's APC (ABB Ability, FLSmidth ECS). Marketing material claims 50 ktCO₂/yr reduction per plant — *not yet substantiated by independent validation in public sources*. Targets the same buyer as APC (process control engineer). | Not public. Likely enterprise SaaS, $100K–$500K/yr/plant (estimate; not confirmed). (Source: `gigaton.co/files/ai-in-cement-white-paper-1-2`, `news.sustainability-directory.com/innovation/ai-digital-twin-software-optimizes-cement-kilns`) |
| **alcemy** (Germany) | AI software for **cement quality and CO₂** | Predicts 2-day and 28-day strength, fineness recommendations. Real-time consistency. Targets the *mill and quality* stage, not the cooler. | Strong on cement mill optimization. No cooler physics. CSV-based data input — no DCS integration required. | SaaS, plant-size-based pricing (not public). (Source: `alcemy.tech`) |
| **iFactory** (consultancy / SaaS) | **Cement digital twin for WAGES** (Water, Air, Gas, Electricity, Steam) | "Documented WAGES savings" of $1.2–3M/yr/plant for a 1–2 MTPA plant; specific heat reductions of 25–55 kcal/kg-cli = ~0.7–1.5 % SEC. Targets 6–12 month historical baseline construction. | Claims "thermal SEC scenario" modeling (kiln + preheater). 4D digital twin. Less cooler-physics depth than Mujumdar / Peray. | Enterprise SaaS. Not public. (Source: `ifactoryapp.com/industries/cement-plant/cement-plant-digital-twin-energy`) |

**The wedge for us**: Carbon Re and iFactory sell **enterprise SaaS to the cement majors** (Heidelberg, Holcim, Titan, Dyckerhoff). They are not designed for a **single Nepali plant paying $50K for a 90-day pilot**. The sales motion is wrong. Their price point is wrong (5–10× ours). And their physics is *closed-source AI* — a CFO can't audit "the model said 1 % SEC reduction" against Mujumdar 2007 and Peray & Waddell 1986. We publish the underlying physics, the test suite, the failure modes. That's the audit-trail advantage.

### Tier 3 — DFI / advisory tools (free, not productized)

| Tool | Provider | What it does | What it doesn't do | Source |
|---|---|---|---|---|
| **IFC Cement Decarbonization Tool** | International Finance Corporation (World Bank Group) | Plant-level analysis of 5 decarbonization strategies: alternative fuels, WHR, electric supply mix, equipment changes, blended cement. Produces a Marginal Abatement Cost Curve. Initial estimates; quality "within acceptable ranges" per ECRA 2022. | Strategic / CAPEX-level, not operational. Not a cooler simulator. Not a pilot tool. | `ifc.org/en/what-we-do/sector-expertise/manufacturing/advancing-production-of-construction-and-other-base-materials/cement-decarbonization-tool` |
| **GCCA GNR** (Getting the Numbers Right) | Global Cement and Concrete Association | Annual industry-wide benchmarking. Defines the `cl_PM2` KPI (cooler heat recovery in MJ/t-cli). | Benchmarking only, not a plant-level simulator. Free. | `gccassoc.org` (GCCA GNR reports) |
| **WBCSD / IEA / ECRA** Cement Technology Papers | Industry consortia | BAT reference (75–80 % cooler eff, 0.42 MJ/kg-cli ceiling). | Reference only. | `docs.wbcsd.org/2017/06/CSI_ECRA_Technology_Papers_2017.pdf` |

**The wedge for us**: IFC / GCCA / ECRA define the *language* the plant uses (MJ/t-cli, BAT ceiling, ECRA Technology Papers). We cite them. We don't compete with them. The IFC tool is a *strategic roadmap* tool, not an *operational* tool. We sit downstream of it.

### Tier 4 — Research / open-source (the academic substrate we build on)

| Project | What it is | License | Relevance to us |
|---|---|---|---|
| **Mujumdar 2007** (Ind. Eng. Chem. Res. 46(7)) | 1D compartment counter-flow cooler model | Academic paper — no license restriction on the *math* | We implement this directly. Cite. |
| **Peray & Waddell 1986** (Ch. 6) | Industry reference for cooler design | Book | Cite. Defines sec-air T band, GJ/t benchmarks. |
| **Achenbach 1995** (Exp. Thermal Fluid Sci. 10(1)) | Packed-bed h correlation | Academic paper | We implement this directly. Cite. |
| **RoCKS** (Rotary Cement Kiln Simulator, *ChEnS* 2007) | Integrated preheater + calciner + kiln + cooler simulator from IIT Bombay / others. 2D cooler. | Academic | Research prototype. Not commercial. Confirms our 1D model is the right level of fidelity for an operator training tool. |
| **arXiv 2409.09076** (2024) "A Dynamic Cooler Model for Cement Clinker Production" | 2D index-1 DAE cooler model | Open-access academic | Research prototype. Confirms 1D-2D boundary; we are at the right fidelity for the use case. |

---

## What we have that they don't (the honest delta)

| Dimension | APC platforms (ABB / FLSmidth / Siemens / KHD) | AI startups (Carbon Re / iFactory) | IFC / GCCA / ECRA (advisory) | **Us (v0.3.1)** |
|---|---|---|---|---|
| **Closed-loop control of cooler** | ✅ Yes (primary function) | ✅ Yes (Carbon Re, iFactory) | ❌ No | ❌ No — by design. We identify opportunities; the plant (or its APC) acts. |
| **Open, citable physics** | ❌ Closed-source control law | ❌ Closed-source AI model | ⚠️ Reference docs only | ✅ Mujumdar 2007 + Peray & Waddell 1986 + Achenbach 1995, cited in code + report. |
| **Per-compartment counter-flow model** | ⚠️ Internal, not published | ❌ Black-box AI | ❌ Reference docs only | ✅ 1D, 5-compartment, second-law-clamped. Spec: `DAY-03-SPEC.md`. |
| **Verra-grade audit trail** | ❌ No | ⚠️ Possible (not public) | N/A | ✅ `duty_case` block + round-trip CSV/JSON + energy balance closure ≤ 2 %. Kabita, please confirm. |
| **EU CBAM data path** | ⚠️ Possible via OEM | ⚠️ Possible | ⚠️ Reference docs | ✅ Compatible — per-KPI reporting in MJ/t-cli per GCCA `cl_PM2`. |
| **Pilot at $50K for 90 days** | ❌ No (enterprise only) | ❌ No (enterprise only) | N/A | ✅ Yes. 3 checkpoints, defined success metrics, defined renewal. |
| **Nepal / South Asia duty case** | ❌ Not a target market | ❌ Not a target market | ⚠️ IFC covers it | ✅ Hetauda 1400 m / 35 °C / 90 % RH preset. Ramesh §5. |
| **First-law imbalance ≤ 2 %** | Unknown | Unknown | N/A | ✅ Enforced + tested (Hiro §2.2). |
| **Refutation tests (Sobol, property-based)** | Unknown | Unknown | N/A | ✅ Hiro §2.3–2.5. N=1024 base, ~8192 model evals. |
| **Open test suite, publish failures** | ❌ | ❌ | N/A | ✅ 5 new diagnostic tests; first 3 fail against v0.3.0 by construction. |
| **License price point** | $500K+ capex (turnkey) or annual subscription | $100K–$500K/yr/plant (estimate) | Free | $50K pilot → $50K–75K/yr license = 5–10× cheaper. |
| **Sales motion** | 9–18 month OEM-led | 6–12 month enterprise SaaS | Advisory (no sale) | 30-day scoping call → 90-day pilot → 3-year license. |

---

## The honest deltas where we are *worse* (be honest about gaps)

- **No closed-loop control.** We are not a replacement for ABB EO or FLSmidth ECS. The plant still needs its APC. We feed the APC the *setpoint recommendations*; the APC executes.
- **No 2D / 3D physics.** Mujumdar 2007 is 1D. Real coolers have width effects (edge cooling, side-wall loss). For Day 3 fidelity this is fine; for a new-cooler design it is not.
- **Single-plant calibration.** Our model calibrates to *one* plant. Carbon Re and iFactory claim multi-plant learning (which can be a feature or a bug, depending on how the data is used).
- **No mill / quality module.** alcemy has this; we don't. Out of scope for Day 3.
- **Sales motion still has to be built.** APC vendors have OEM sales channels. We don't. The first 3 customers are direct sales by the founder.

---

## What this means for the pitch

1. **Don't compete on "AI" or "digital twin."** Carbon Re and iFactory own that vocabulary. The plant hears "another AI digital twin" and rolls eyes.
2. **Compete on "1 % SEC reduction, here are the 3 actions, here is the verified measurement."** That's the audit-trail pitch. APC can't do it. AI startups can't do it publicly. Advisory tools can't do it operationally.
3. **Compete on price.** $50K pilot + $50K–75K/yr license is 5–10× cheaper than the enterprise SaaS. For a Nepali plant, that's the entire conversation.
4. **Compete on Nepal duty case.** No one else is doing Hetauda 1400 m / 35 °C / 90 % RH. No one else has the HCIL preset.
5. **Don't name the competitors in the customer-facing material.** The buyer doesn't care who else is in the space. The buyer cares about the SEC delta, the payback, and the risk. Name the *outcome*, not the *vendor*.

---

## Sources cited

1. **ABB Ability™ Expert Optimizer for cement** — `search.abb.com/library/Download.aspx?DocumentID=9AKK107492A2268` and `new.abb.com/cement/systems-and-solutions/advanced-process-control/abb-ability-expert-optimizer-cement`
2. **FLSmidth ECS/ProcessExpert®** — `flsmidth-cement.com/products/ecs-processexpert-advanced-process-control-software`
3. **Siemens Sicement IT MCO** — industry survey `oxmaint.com/industries/cement-plant/cement-plant-process-control-apc-expert-systems`
4. **Carbon Re Delta Zero** — `gigaton.co/files/ai-in-cement-white-paper-1-2` and `news.sustainability-directory.com/innovation/ai-digital-twin-software-optimizes-cement-kilns`
5. **alcemy** — `alcemy.tech` and `alcemy.tech/produktnew/zement-np`
6. **iFactory** — `ifactoryapp.com/industries/cement-plant/cement-plant-digital-twin-energy` and `ifactoryapp.com/industries/cement-plant/specific-energy-consumption-benchmarking-cement`
7. **IFC Cement Decarbonization Tool** — `ifc.org/en/what-we-do/sector-expertise/manufacturing/advancing-production-of-construction-and-other-base-materials/cement-decarbonization-tool`
8. **ECRA Technology Papers 2017 / 2022** — `docs.wbcsd.org/2017/06/CSI_ECRA_Technology_Papers_2017.pdf` and `ecra-online.org`
9. **ECRA CCS Phase II report** — `api.ecra-online.org/fileadmin/files/ECRA__Technical_Report_CCS_Phase_II.pdf`
10. **SINTEF CEMCAP** — `sintef.no/globalassets/project/cemcap/30-11-18-cemcap/32_modeling-of-full-scale-oxyfuel-cement-rotary-kiln-ditaranto-workshop.pdf`
11. **Mujumdar 2007** — *Ind. Eng. Chem. Res.* 46(7), 2184–2192
12. **Peray & Waddell 1986** — *The Rotary Cement Kiln*, 2nd ed., Ch. 6
13. **Achenbach 1995** — *Exp. Thermal Fluid Sci.* 10(1), 17–27
14. **RoCKS (IIT Bombay et al., 2007)** — *Chemical Engineering Science* 62, 2590
15. **arXiv 2409.09076 (2024)** — "A Dynamic Cooler Model for Cement Clinker Production"
16. **Cement industry digital twin survey 2025** — `cementinsights.org/successful-cement-plant-energy-efficiency-projects-in-2025/`

---

— Priya, 2026-07-22
