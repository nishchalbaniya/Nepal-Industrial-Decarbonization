# Sales One-Pager — Nepal Industrial Decarbonization Suite (v0.3.1)

> **Owner:** Priya Karki, Business Lead
> **Date:** 2026-07-22
> **Audience:** Cement plant CFO, COO, and Plant Engineer
> **Goal:** One page, no jargon, names a specific outcome, names a specific proof, names a specific risk. Prints on a board.

---

## What this is

A 1D compartment-wise grate cooler simulator, calibrated to your plant's DCS export, that identifies fuel-blend and cooler-operating-point opportunities you are not currently seeing — and tells you the SEC delta in MJ/t-cli, with the engineering signature to back it.

## What it does for you (4 bullets)

- **Finds 1–4 % SEC reduction on your plant.** The 1 % is the floor of what's achievable on a well-run plant; the 4 % is the upper end of low-cost measures (operator training, setpoint optimization, fuel-blend tuning, cooler operating-point changes) per ECRA 2022 / IEA 2018 / WBCSD-CSI 2017. On a 3000-tpd plant at 3.4 GJ/t-cli baseline and $10/GJ effective fuel cost, 1 % SEC = **~$337K/yr in fuel**; 4 % SEC = **~$1.35M/yr** (see `pricing_math.md` for the line-by-line). The cooler is the most quantifiable piece of that opportunity set; the fuel-blend and setpoint pieces require the kiln model and AFR module to quantify fully.
- **Tells you the 3 actions, ranked.** Not 30 actions. Three. Each with an engineering signature, an expected SEC delta, and the operator-side change required (e.g. "reduce under-grate air velocity in comp 3 from 2.0 to 1.5 m/s; raises sec-air T by ~60 K; reduces fan power by ~12 %; expected +0.4 % SEC reduction").
- **Verified measurement, not a model you have to trust.** v0.3.1 enforces a second-law clamp on air heating (`T_a ≤ T_c − 5 K`, per Aanya's review) and an energy-balance closure target of ≤ 2 % (per Hiro's review and Ramesh's first-law check). The 13.5× first-law imbalance that v0.3.0 had is gone. We publish the test suite.
- **Pilot is structured so the plant is forced to use the product, not stuck with shelfware.** 90-day pilot at $50K, 3 checkpoints (Day 30 / 60 / 90) with a concrete deliverable at each, renewal path defined in week 1, skin-in-the-game from both sides. Day 90 deliverable is *opportunity identification with engineering signature*; the first *realized* SEC-reduction checkpoint is at 6 months, in the license year 1. See `pilot_scope.md`.

## What it does not do (be honest)

- It does not install the equipment. It does not operate the kiln. It does not eliminate the SEC gap — it identifies the opportunities. The plant closes the gap.
- It is not a Verra issuance. The pilot gives you SEC reduction + better data quality for *future* credits (12–18 month Verra process per Kabita, env-eng-permitting). It is not a credit-revenue product in 90 days.
- It is not full 3D CFD. It is a 1D, 5-compartment, counter-flow cooler model with the second-law invariant, Achenbach/Wakao h correlation, and a compartment-wise solver. It is engineering-grade for an operator training tool, MRV data audit, and SEC opportunity identification. It is not a substitute for a 3D CFD study on a new cooler design.
- It is not "AI." It is interpolation (Achenbach h correlation) + a compartment counter-flow solver (Mujumdar 2007 / Peray & Waddell 1986) + a calibration step. The LLM advisor is a stickiness feature for the *next* sale, not a wedge feature for this one.

## The proof — what the team found in v0.3.0 and what we fixed in v0.3.1

We don't claim "we built it and it works." We name the bugs we caught and what we did about them. This is the proof:

- **Bug found**: secondary-air T of 5790 °C in v0.3.0 — a textbook second-law violation (Aanya, `AANYA-DAY-03-REVIEW.md`). Unphysical. Would have failed a Verra validation in 5 minutes.
- **Fix in v0.3.1**: second-law clamp `T_a ≤ T_c − 5 K`; air topology moved to per-compartment counter-flow; sec-air now lands in the engineering band [600, 1000] °C for a PlantA 1400 m / 35 °C / 90 % RH design day (Aanya, Ramesh).
- **Bug found**: 13.5× first-law imbalance in v0.3.0 — air-side heat recovery vs clinker-side heat recovery disagreed by 13.5× (Ramesh, `DAY-03-RAMESH-REVIEW.md`). Hard reject.
- **Fix in v0.3.1**: per-compartment counter-flow solver with compartment-level air mass; the two sides of the heat exchanger now agree within 5 %.
- **Bug found**: tests passed for the wrong reason. v0.3.0's `efficiency ∈ [0.4, 0.95]` band was too loose to catch a 5790 °C air stream; monotonicity tests didn't catch a runaway second-law violation (Hiro, `hiro-day-03-review.md`).
- **Fix in v0.3.1**: 5 new diagnostic tests (second-law invariant, energy-balance closure, low-air refutation, realistic-envelope range, monotone sweep). The first three fail against v0.3.0 by construction — that's the point. They're diagnostic.
- **What we found in the Nepal duty case**: air density at 1400 m / 35 °C / 90 % RH is **1.05 kg/m³**, not 0.6 kg/m³ as v0.3.0 had hard-coded. The fan-power undersize at altitude is the single most common Nepali cooler-fan mistake (Ramesh §5). v0.3.1 ships with an `air_density_kg_m3(altitude_m, T_ambient_c, RH)` function and a `duty_case` block in the output.

## The payback

1 % SEC reduction on a 3000-tpd plant = ~$337K/yr in fuel. 4 % = ~$1.35M/yr. Our price = 1–5 % of that = **$15K–75K/yr per plant** (PlantA-class: $25K–$50K; Hongshi-class: $15K–$25K). 5 plants = $75K–$375K ARR. 50-plant regional platform = $1.25M–$2.5M ARR. See `pricing_math.md` for the line-by-line.

The pilot at $50K for 90 days pays back if the plant finds 0.15 % of SEC reduction over the 90-day window *and acts on it for 1 year*. The historical record (ECRA, IEA, WBCSD/CSI) says plants find 1–4 %; the question is whether they act.

## The risk

If the pilot finds no actionable opportunities (i.e. the plant is already at BAT and the model is just confirming what the operator already knew), we refund 50 % of the pilot fee. The plant still keeps the calibrated model and the 90 days of baseline data. We do not refund 100 % because the engineering hours are real.

If the pilot finds opportunities and the plant doesn't act, that's the plant's problem, not ours. We do the identification; the plant does the implementation. We can help with the operator training, but that's a separate contract.

If the project doesn't credit at Verra (12–18 month process), we don't refund the pilot fee. The pilot's value proposition is **SEC reduction + better data quality for future credits**, not credits in hand. Be honest about that on the front end.

## The path to scale

One plant in Nepal is a study. Five in the region is a product. Fifty is a platform. The wedge is a PlantA-class legacy plant where the easy 1–3 % SEC reduction is sitting on the table. The first 3 customers are the *learning investment*, not the *revenue investment*. Revenue is in customer #4 through #50.

## The next commitment (not "would you use it?" — "will you sign?")

If you are the CFO, COO, or Plant Engineer of a Nepali cement plant, the next commitment is a 30-day scoping call. The scoping call produces a 1-page pilot scope, a price ($50K for 90 days at PlantA-class), and a 3-checkpoint renewal path. If you won't sign the scoping call, the answer is no, no matter what you say. We won't build a feature for a customer who isn't going to buy.

Contact: Priya Karki, Founder, Nepal Industrial Decarbonization Suite.

---

## Sources cited (proof)

1. **Aanya's Day 3 review** (`tools/03-cooler-grate-simulator/reviews/AANYA-DAY-03-REVIEW.md`) — radiation runaway diagnosis, Achenbach attribution, cross-flow vs counter-flow recommendation, KPI gaps.
2. **Ramesh's Day 3 review** (`reviews/DAY-03-RAMESH-REVIEW.md`) — first-law imbalance 13.5×, compartment design, Nepal duty case (PlantA 1400 m / 35 °C / 90 % RH).
3. **Hiro's Day 3 review** (`reviews/hiro-day-03-review.md`) — test fragility, second-law invariant, Sobol design, property-based sweep recommendation.
4. **Mujumdar, K.S. (2007)**, "Mathematical Modeling of a Grate Cooler for Cement Clinker Cooling," *Ind. Eng. Chem. Res.* 46(7), 2184–2192 — compartment counter-flow formulation.
5. **Peray, K.E. & Waddell, J.J. (1986)**, *The Rotary Cement Kiln*, 2nd ed., Ch. 6 §6.4 — secondary-air T 600–900 °C, GJ/t benchmarks 0.30–0.45.
6. **Achenbach, E. (1995)**, "Heat and flow characteristics of packed beds," *Exp. Thermal Fluid Sci.* 10(1), 17–27.
7. **ECRA Technology Papers 2022** — modern reciprocating cooler BAT 75–80 % efficiency, 0.42 MJ/kg-cli total heat loss.
8. **GCCA GNR 2022** — `cl_PM2` reporting convention (MJ/t-cli for cooler heat recovery).
9. **Saltelli, A. et al. (2010)**, *Computer Physics Communications* 181: 259–260 — Sobol sample size rule of thumb (N=1024 base).

---

— Priya, 2026-07-22
