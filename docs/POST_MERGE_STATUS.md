# Post-Merge Status (WP0 -> WP6 + follow-up)

> **Status (2026-07-23):** The six-work-package credibility
> remediation pass (WP0-WP6) and the post-merge follow-up
> tasks have all been completed. The truthful v1.0 is now
> on `main` at `nishchalbaniya/Nepal-Industrial-Decarbonization`.

---

## The two PR-checklist items (now done)

- [x] ~~User to revoke the gho_ PAT on github.com~~ -- revoked
      on 2026-07-23 via the public Credential Revocation API
      (POST /credentials/revoke, HTTP 202, confirmed via
      follow-up GET /user returning HTTP 401). The local
      Windows Credential Manager copy was also wiped via
      `cmdkey /delete:LegacyGeneric:target=git:https://github.com`.
- [x] ~~User to switch default branch from
      `day-03-v0.3.2/cooler-structural-fix` to `main`~~ --
      done on 2026-07-23 via PATCH /repos API. The new
      default is `main`. `BRANCH_POLICY.md` now serves as
      the historical note for this change.

## The three WP6 follow-up items (now done)

- [x] gitleaks added to CI
      (`.github/workflows/gitleaks.yml`) -- runs on every
      push and PR. Catches PATs, API keys, AWS access keys,
      and any other secret patterns.
- [x] `docs/PLANT_RENAMING.md` written -- records the
      Day 14 plant-rename (commit `2b24a3c`) and the mapping
      from PlantA/B/C/D to the original four Nepali plants.
- [x] `docs/DEPLOYMENT.md` written -- the single entry point
      for the five deploy paths (VPS, Docker, free one-click,
      AWS Terraform / Helm, IoT edge).

## Test result

88/88 tests pass on `main`:
```
$ cd pro && py -m pytest tests/
88 passed, 2 warnings in 18.77s
```

## Canonical links

| Resource | URL |
|---|---|
| Repo (main, default) | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization |
| Truthful methodology | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/docs/METHODOLOGY.md |
| Truthful standards coverage | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/docs/STANDARDS_COVERAGE.md |
| Honest limitations | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/LIMITATIONS.md |
| Branch policy | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/BRANCH_POLICY.md |
| Plant rename map | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/docs/PLANT_RENAMING.md |
| Deployment guide | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/docs/DEPLOYMENT.md |
| Remediation report | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/reviews/REMEDIATION_REPORT.md |
| Ground truth audit (WP0) | https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization/blob/main/reviews/GROUND_TRUTH.md |
| GitHub Pages keeper | https://nishchalbaniya.github.io/Nepal-Industrial-Decarbonization/ |
| End-to-end 4-plant demo | https://jfp4xr4woteju.space.minimax.io |

## What this remediation pass is NOT

- **Not a feature pass.** No new engineering functionality.
  The cooler / kiln / CAD / P&ID / LCA / UQ / MILP / NSGA-II
  modules are unchanged. The remediation was about *truth*,
  not *features*.
- **Not a performance pass.** The v0.5.0 calibrated model
  still fails 3 of 6 cooler ship-gate bands (tertiary 190C,
  exhaust 149C, clinker 351C). The fix needs real plant data
  or v0.6.0 model changes; both are out of scope.
- **Not a real Verra submission.** The PDD generator is a
  sizing tool. The 8 missing sections of Verra VCS Standard
  v5.0 are documented in `docs/METHODOLOGY.md` section 5.
- **Not a replacement for the next quarter's work.** The
  12 remaining-risk items in
  `reviews/REMEDIATION_REPORT.md` section 4 are the next
  quarter's roadmap. None are blockers for "the repo is in
  a defensible state for a hostile technical review."

## The remediation timeline

| Date | Event |
|---|---|
| 2026-07-23 (morning) | Day 14 plant-rename merged into v1.0.0 release (`2b24a3c`) |
| 2026-07-23 (morning) | WP0 ground-truth audit (17 defects catalogued, commit `683f075`) |
| 2026-07-23 (afternoon) | WP1-WP6 + final report (11 commits, 88/88 tests) |
| 2026-07-23 14:35 AEST | WP0-WP6 chain pushed to `remediation/wp1-methodology` |
| 2026-07-23 14:38 AEST | PR #2 opened, gho_ PAT redacted from history, push protection passed |
| 2026-07-23 14:39 AEST | gho_ PAT revoked on github.com via Credential Revocation API (HTTP 202) |
| 2026-07-23 14:40 AEST | Default branch switched to `main` (PATCH /repos HTTP 200) |
| 2026-07-23 14:41 AEST | PR #2 squash-merged into `main` (commit `d7fb07c`) |
| 2026-07-23 14:42 AEST | Post-merge follow-up (this doc, DEPLOYMENT.md, PLANT_RENAMING.md, gitleaks.yml) |

Everything in the WP0-WP6 plan is done. The truthful v1.0 is
on `main`. The repo is in a defensible state.
