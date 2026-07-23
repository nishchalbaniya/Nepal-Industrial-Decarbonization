# Limitations (WP3)

> **Status (2026-07-23):** This document is the honest list of
> what the repository cannot yet do. Every limitation is
> reproducible (a `py -m pytest` or a code-read confirms it).
> Aspirational items live in `ROADMAP.md`, not here.

---

## Engineering simulators

### Three of the six cooler ship-gate bands fail on v0.5.0
- **Tertiary air outlet**: 190 C vs band 400-700 C (FAIL)
- **Exhaust air outlet**: 149 C vs band 150-300 C (FAIL by 1 C)
- **Clinker outlet**: 351 C vs band 120-200 C (FAIL)

The v0.5.0 model physics at 130 t/h cannot deliver these bands
because (a) the model is calibrated against synthetic data, not
real plant data, and (b) the model is not yet subdivided to the
compartment level needed to match real cooler temperature
profiles. For the open-source release, the three failing bands
are labelled **"Worked example"**, not "Verified."

**What unblocks this:** (a) a real plant-data CSV from PlantA in
the format specified in
`tools/03-cooler-grate-simulator/day-04-PRs/data_quality_spec.md`,
or (b) v0.6.0 model changes (compartment subdivision, lower
throughput). Neither is in scope for v1.0.0.

### No real plant data has been ingested
All four plant presets (PlantA, PlantB, PlantC, PlantD) are
synthetic. The names are placeholders for the original four
Nepali plants the v1.0 release was scoped against; the rename
to PlantA/B/C/D is documented in
`tools/13-rename-plants/rename_plants.py` and was applied in
commit `2b24a3c` (Day 14).

### No CEMS / DCS integration
The IoT layer (`pro/nepal_decarb_pro/io/mqtt_bridge.py`,
`opcua_client.py`, `modbus_client.py`, `historian.py`) is
implemented but has not been wired to a real CEMS or DCS
export. The interface is there; the integration is not.

---

## Standards modules

See `docs/STANDARDS_COVERAGE.md` for the per-standard honest
tag. The short version: 2 of the 11 claimed standards are
fully Implemented; 2 are Partial; 7 are Stub. None of the
Stub standards constitute real compliance.

### The previous "100/100" self-assessments are deleted
The previous README and the PDF report had self-asserted check
marks for ISO 14064-1, ISO 14064-2, ISO 14064-3, ISO 50001, ISO
14001, TCFD, SBTi, GCCA, PCAF, GHG Protocol, Verra VCS, Gold
Standard. The truth is in `docs/STANDARDS_COVERAGE.md`. A VVB
will not accept the self-asserted check marks; this document
and the standards coverage document are the honest replacement.

### ISO 14064-3 V.2/V.5/V.6 hard-coded `True` was fixed in WP2
The `check_iso_14064_part3` function previously hard-coded
three of the ten verification criteria to `True` regardless of
input. A user could not flag those criteria as not met. WP2
made them explicit function parameters. Verified by running
the function manually:

- Default: `pass=True score=100.0 met=10/10`
- V.2=False: `pass=False score=90.0 met=9/10`
- V.2+V.5+V.6=False: `pass=False score=70.0 met=7/10`

---

## Carbon markets

See `docs/METHODOLOGY.md` for the full gap list. The short
version: the PDD generator is a sizing tool, not a submittable
PDD. The fictional "VM0009 v2.0 (Cement Plant Decarbonization)"
citation that the previous copy used has been removed in WP1.

### The "fictional" citations removed in WP1
- `VM0009 v2.0 (Cement Plant Decarbonization)` -- FICTIONAL.
  Real VM0009 is Avoided Ecosystem Conversion (AFOLU, scope 14).
- `Gold Standard Methodology for Cement Plant Decarbonization` --
  FICTIONAL. Gold Standard has no published cement methodology.
- `TPDDTEC applicable to cement` -- WRONG SECTOR. TPDDTEC
  (now RECH v5.0) is for cookstoves / institutional heating
  (<= 150 kW/unit). Not applicable to industrial cement kilns.
- `Nepal grid EF 0.0256 kg CO2/kWh` -- WRONG by four orders of
  magnitude. The real value per IEA / Enerdata 2024 is
  ~0.0023 g CO2/kWh (hydro-dominated, essentially zero).

### The economic story is reframed
The previous README led with EU ETS prices (USD 65/t) as the
central case for Nepali cement. The correct framing is:
India CCTS and Article 6.2 ITMO at USD 5-15/t are the binding
prices. EU ETS at USD 65-90/t is a sensitivity upper bound,
not the central case. See `docs/METHODOLOGY.md` section 3.

---

## Tests

### Pre-existing failures (not new in WP1-WP5)
- `tests/test_sim.py` -- imports `nepal_decarb_pro.sim` and
  `nepal_decarb_pro.standards` submodules that exist but the
  test depends on `matplotlib` and `reportlab` optional
  dependencies.
- `tests/test_standards.py` -- same root cause.
- 9 tests in `test_extended.py` fail due to working-directory
  assumptions for `helm/Chart.yaml`, `docker-compose.yml`,
  `pro/pyproject.toml`, etc. when the test is run from
  outside the `pro/` directory.
- `tests/test_server.py` -- FastAPI smoke test, requires the
  server process to be up.

The CI pipeline (`/.github/workflows/ci.yml`) runs only the
tests known to pass cleanly today (`tests/test_markets.py`,
`test_full_standards_scorecard`); the full suite runs
non-blocking with `continue-on-error: true`. Fixing the
pre-existing failures is the WP6 work package.

### The "78/78 tests" claim is deleted
The previous README claimed 78/78 tests passed. The actual
count after WP0 is: 8/8 markets tests pass cleanly; 1/1
standards scorecard test passes; the remaining 30+ tests
have pre-existing failures documented above. The "78/78"
shield badge is removed in WP3.

---

## Infrastructure

### Dead demo links
- `https://fnj58e5yu30lp.space.minimax.io` -- DEAD (session URL expired)
- `https://harvey-aside-striking-spas.trycloudflare.com` -- DEAD (session URL expired)

The current live demos are:
- `https://jfp4xr4woteju.space.minimax.io` (4-plant end-to-end)
- `https://nishchalbaniya.github.io/Nepal-Industrial-Decarbonization/` (GitHub Pages, keeper)

Removed from the README in WP3. Full cleanup of all references
in `pro/LIVE_DEPLOYMENT.md`, `pro/explorer.html`, and
`pro/site/index.html` is in WP6.

### Default branch is `day-03-v0.3.2/cooler-structural-fix`
The default branch on github.com points to a historical
engineering branch, not `main`. This is documented in
`BRANCH_POLICY.md` and is the WP4 follow-up; it requires
GitHub repo admin access (the user is the admin, not the
assistant).

### Placeholder clone URL removed
The previous README used `himalayan-carbon-nepal/nepal_decarb_pro`
(404) and three `YOUR_USERNAME` placeholders. Both are fixed
in WP3 to `nishchalbaniya/Nepal-Industrial-Decarbonization`.

---

## Security

### PAT was committed in a prior session
A `gho_` PAT was accidentally committed in a prior session
(commit `53dbe26`). It was wiped locally via
`git filter-repo` and the history was rewritten. The remote
is at `8282d29` (a commit without the credential) and was
never pushed with the credential. **The user should still
revoke the PAT on github.com as defense-in-depth** (URL:
`https://github.com/settings/tokens`).

### No new credentials have been introduced in WP1-WP5
The remediation work has not added any new secrets, API keys,
or PATs. All external HTTP calls (e.g., to github.com) use
the existing local toolchain.

---

## Summary

The v1.0.0 release is **engineering-good but presentation-weak**,
and in carbon MRV, presentation is the product. WP1-WP6 close
the presentation gaps (fictional citations, self-awarded scores,
dead links, broken tests, missing docs). The engineering gaps
(three failing ship-gate bands, no real plant data, ISO 14064-3
still a stub) remain and are documented here for transparency.
