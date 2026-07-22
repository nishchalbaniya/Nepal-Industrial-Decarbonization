# Team Charter v2 — Nepal Industrial Decarbonization v1.0

> **Authored by Mavis (orchestrator) on 2026-07-22, after the Day 3 post-mortem.**
> v1 of the charter let the team sit unused while Mavis wrote Day 3 solo and shipped broken code wearing a green test badge. v2 makes ownership, review, and verification explicit.

## The 9 agents (with explicit per-day ownership)

| # | Agent | Role | Days owned (primary) | Days owned (reviewer) |
|---|---|---|---|---|
| 1 | **Mavis** (orchestrator) | Coordinate, integrate, ship, package | All (integration), 18 (desktop shell), 19 (docs), 20 (release) | All |
| 2 | **Aanya** (chem-eng-cement) | Cement chemistry, kinetics, MRV | 2 (kiln), 3 (cooler model), 5 (LC3 chemistry), 12 (PDD chemistry), 14 (LLM RAG over standards) | 4, 6, 11 |
| 3 | **Ramesh** (mech-eng-plant) | P&ID, equipment, CAD, plant KPIs | 3 (cooler compartments+KPI), 4 (CAD), 8 (P&ID), 9 (PFD), 10 (equipment), 11 (HAZOP) | 2, 6, 12 |
| 4 | **Maya** (cs-architect) | Packaging, FastAPI, Tauri, RBAC, CI, install | 7 (packaging standards), 13 (API), 17 (UI/UX), 18 (Tauri), 20 (CI/CD) | 2, 3, 6, 8, 14, 15, 16 |
| 5 | **Hiro** (data-scientist-uq) | MC, Sobol, calibration, forecasting | 2 (uncertainty), 3 (test robustness), 15 (digital twin UQ), 16 (forecasting) | 5, 13 |
| 6 | **Sofia** (ai-ml-engineer) | LLM, RAG, ML models, eval | 14 (LLM advisor), 15 (digital twin ML) | 13, 16 |
| 7 | **Kabita** (env-eng-permitting) | ISO 14064, GHG Protocol, audit, CBAM | 1 (MRV), 12 (CBAM), 19 (audit-ready docs) | 2, 3, 5, 11, 16 |

> **Note (2026-07-22):** Kabita's day-12 framework is **EU CBAM 2023/1773 + ISO 14064-2:2019**, not Verra VM0009. The cooler module's carbon-relevance runs through **Verra VM0009 v3.0 §5.3** (kiln baseline; secondary-air T is a required input) and **Gold Standard TPDDTEC v3.1 §4.2** (cooler secondary-air T as a project parameter) — those are **James's** (carbon-markets-expert) day-12 / day-13 frameworks. VM0009 v3.0 itself is a kiln-baseline methodology, not a cooler methodology. The day-3 PR `env-eng-permitting/data_quality_tiers.py` previously cited "Verra VM0009" as the cement-cooling methodology; that was a domain-area mis-cite (it is the kiln-baseline methodology that *consumes* the cooler fields). Corrected 2026-07-22.
| 8 | **James** (carbon-markets-expert) | Verra, Gold Standard, Article 6, solidity; **owns the VM0009 v3.0 kiln-baseline methodology** (cooler is a required input) | 13 (carbon market), 20 (registry integration) | 12, 19 |

> **Note (2026-07-22):** The CBAM 0.642 t CO₂/t clinker default value that appears in `env-eng-permitting/data_quality_tiers.py` and DAY-03-NEGOTIATION.md was **unverified** by Kabita. The PR note has been updated to mark the entry as UNVERIFIED and to point to the IPCC 2006 Vol.3 Ch.2 §2.3.2 stoichiometric default (0.527 t CO₂/t clinker with 1-2% CKD correction) as the safer interim value. **@James: re-verify the CBAM 2023/1773 Annex IV §4 row for CN 2523 10 00 (clinker) before any PDD or CBAM XML commit.**
| 9 | **Priya** (business-lead) | Sales, pilot, pricing, prioritization, comms | 19 (sales one-pager), 20 (commission pitch) | All — every day's "is this shippable?" review |
| 10 | **verifier** (built-in) | Final sign-off, evidence-anchored | Every day at end-of-day | — |

**Day 3 ownership (current, retrospective)**: Aanya owns `cooler_ode.py` (model physics), Ramesh owns `compute_outputs` + compartments, Hiro owns tests, Maya owns `io.py` + `cli.py` + packaging. Mavis integrates and ships the patch.

## How a day actually works (v2)

```
00:00  Mavis posts STANDUP-<DAY>.md with: today's spec, owners, ship gate.
00:10  Each owner agent reads the spec, reads the relevant existing code,
       posts a one-paragraph "approach" before writing.
00:30  Owners PR their part as separate files in tools/03-.../day-03-PRs/
       (named {owner}-{topic}.py or .md). Each PR must include a self-test.
02:00  Cross-review: Hiro reviews Aanya's model with second-law test;
       Aanya reviews Ramesh's compartments; Maya reviews Hiro's tests;
       Ramesh reviews Maya's CLI. Disagreements posted as comments in PRs.
03:00  Mavis integrates the PRs, runs the full suite, posts Day 3 retro.
04:00  Verifier (built-in `verifier` agent) reviews the integrated package
       against the standup's ship gate. Either passes (commit + patch) or
       returns with specific evidence-anchored change requests.
04:30  Mavis commits and bundles format-patch for the user.
```

## Stop conditions (the ship gate)

A day's work is **not** done when:
- Tests pass (Hiro's lesson from Day 3: tests can pass for the wrong reason)
- Mavis thinks it's done
- The user asks if it's done

A day's work **is** done when:
- All owner PRs merged into `tools/<NN>-.../day-03-PRs/`
- The integrated package passes:
  - All earlier tests still green
  - The new day's tests written by Hiro, **and** Hiro's *fragility* tests pass
  - Second-law invariant test passes
  - Energy balance closure < 2% of Q_in
  - At least 1 property-based sweep (Hypothesis-style) over 32 samples
  - **verifier agent** signed off
- A 1-page retro posted: what shipped, what slipped, what changed in scope
- A `.patch` file ready for the user

## What went wrong on Day 3 (and how v2 prevents it)

Day 3 was Mavis's first solo build. Issues:
1. **Radiation runaway** — second-law clamp missing in `_solve_spatial`. Aanya catches this in 5 minutes.
2. **Cross-flow vs counter-flow confusion** — model treats air as "fresh per cell" which is wrong for a 5-compartment grate cooler. Ramesh catches this in 5 minutes.
3. **Tests pass for wrong reasons** — `efficiency ∈ [0.4, 0.95]` is too loose; monotonicity tests don't catch a runaway second-law violation. Hiro catches this in 5 minutes.
4. **Shape mismatch in I/O** — model returns spatial-only but `save_results_csv` expected time-trajectory. Maya catches this in 5 minutes.
5. **No second pair of eyes** — Mavis signed off on his own work. Verifier role added in v2.

v2 prevention:
- Each owner signs their part, not Mavis.
- Hiro writes the *fragility* tests, not the headline tests.
- verifier signs off the integrated package, not Mavis.
- Mavis coordinates only.

## Conflict resolution (v2)

1. **Within-scope** — owner decides, posts ADR.
2. **Cross-scope** — 24h comment thread on the PR; if no consensus, Mavis arbitrates.
3. **Schedule** — Priya arbitrates ("we ship what ships; the rest goes in v1.1").
4. **Hard principle** — log, defer, ship the boring version, revisit at v1.1.

## Async / when the user is offline

- Mavis does not block on user input during a day.
- A day's commit + patch is the unit of progress.
- The user gets a `.patch` and a 1-paragraph "what shipped" at end of each day.
- The user pushes when ready.

— Mavis, 2026-07-22
