# Plant Renaming (Day 14)

> **Status (2026-07-23):** This document records the Day 14
> plant-rename commit (`2b24a3c`) so that an outside reader
> can map the new generic names back to the original four
> Nepali plants the v1.0 release was scoped against.

---

## The mapping

For the v1.0 engineering release, the four specific Nepali
cement plants were renamed to generic placeholders so that the
public repository would not commit to any single plant's
performance numbers. The mapping is:

| New name (in repo) | Original Nepali plant | Notes |
|---|---|---|
| **PlantA** | (Hetauda Cement Industries Ltd, Nepalgunj) | The "headline" plant; 130 t/h cooler, 1100 tpd cement, 950 kt/yr clinker |
| **PlantB** | (Udayapur Cement Industries Ltd, Udayapur) | The second-largest; vertical-shaft kiln preheater, 800 tpd |
| **PlantC** | (Hongshi-Shivam Cement Pvt Ltd, Lumbini) | Chinese-technology dry-process, 6000 tpd; the largest by installed capacity |
| **PlantD** | (Ghorahi Cement Industries Pvt Ltd, Ghorahi) | The "newest" plant; preheater / precalciner, 2200 tpd |

The four names were chosen to keep:
- the **cooler** and **kiln** APIs working without changes to the
  math (the underlying parameters are plant-specific, not
  name-specific)
- the **4-plant sweep** that produces the CBAM 4,120 kt CO2e/yr
  exposure number
- the **P&ID drawing number** (HCIL-CLR-PID-001 -> NIDC-CLR-PID-001)
  for the Cooler P&ID

## What was renamed

The rename was applied across 172 files in commit `2b24a3c`
(`feat(tools/13): Day 14 -- rename 4 specific plant names to
generic PlantA/B/C/D`). The full set of changes:

| Old (in prior commit) | New (in current commit) |
|---|---|
| Hetauda (in any string) | PlantA |
| Udayapur (in any string) | PlantB |
| Hongshi-Shivam (in any string) | PlantC |
| Ghorahi (in any string) | PlantD |
| HCIL (in any string) | NIDC |
| HCIL-CLR-PID-001 (drawing number) | NIDC-CLR-PID-001 |
| synthetic_hetauda_*.csv (data files) | synthetic_planta_*.csv |
| 06_hetauda_kiln.step (CAD outputs) | 06_planta_kiln.step |
| 07_hetauda_cooler_pid.{step,svg,json} | 07_planta_cooler_pid.{step,svg,json} |
| `nepal_cooler_sim.hetauda()` (API) | `nepal_cooler_sim.planta()` (API break) |
| `hetauda()` in plants.py PRESETS dict | `planta()` etc. |
| PlantC (uppercase, in some docstrings) | plantc (lowercase, in function names) |

### Follow-up pass (2026-07-23, post-remediation)

The original Day 14 commit (`2b24a3c`) renamed 172 files but missed
a second batch of stragglers. The follow-up pass closed the gap:

| File / location | Old | New |
|---|---|---|
| `tools/02-kiln-dynamics-simulator/src/nepal_kiln_sim/plants.py` | `_hongshi` variable, "plantc Cement" comment | `_plantc` variable, "PlantC" comment |
| `pro/nepal_decarb_pro/data/nepal_plants.yaml` | `operator: "Sino-Nepalese JV (Hongshi Group, China)"` (on PlantC) | `operator: "Sino-Nepalese JV (PlantC majority owner)"` |
| `pro/app/pages/1_Cement_Baseline.py` | `"Hongshi (Nawalparasi)"` dict key | `"PlantC"` dict key |
| `tools/01-baseline-emissions-mrv/app/pages/1_Cement_Baseline.py` | same dict key | `"PlantC"` |
| `tools/01-baseline-emissions-mrv/app/pages/4_Sector_Benchmarking.py` | same dict key | `"PlantC"` |
| `tools/01-baseline-emissions-mrv/CHANGELOG.md`, `app/pages/5_Methodology.py` | "Hongshi" in plant-list | "PlantC" |
| `tools/03-cooler-grate-simulator/README.md`, `scratch/smoke_4plants_v0.3.2.py` | "Hongshi" column header | "PlantC" |
| `tools/03-cooler-grate-simulator/src/nepal_cooler_sim/cooler_ode.py` and the `day-03-PRs/chem-eng-cement/cooler_ode.py` copy | "Hongshi\nShivam-class" engineering note | "PlantC-class" |
| `tools/03-cooler-grate-simulator/src/nepal_cooler_sim/cooler_ode.py` and the `day-03-PRs/chem-eng-cement/cooler_ode.py` copy | "IKN/KHD/Polysius/Hongshi default" (compartment count) | "IKN/KHD/Polysius/modern-Chinese-OEM default" |
| `tools/03-cooler-grate-simulator/day-03-PRs/mech-eng-plant/*`, `business-lead/*`, `carbon-markets-expert/pdd_json_schema.json`, `reviews/AANYA-DAY-03-REVIEW.md` | "Hongshi-class", "Shivam-class", "IKN/Polycom/Hongshi" | "PlantC-class", "modern-Chinese-OEM-class" |
| `docs/org/brand/POSITIONING.md` | "PlantA Industries Ltd, PlantB, Hongshi (Shivam Cement)" | "PlantA Industries Ltd, PlantB, PlantC" |
| `docs/org/release/v1.0-e2e/DEPLOY-AND-SELL.md` | "PlantA + PlantB + Hongshi + PlantD" sweep listing, "PlantD (Shivam)" (the parenthetical was wrong; Shivam = PlantC, not PlantD) | "PlantA + PlantB + PlantC + PlantD" sweep listing, "PlantD" |
| `docs/org/release/v1.0-e2e/cad/06_planta_kiln.step` | `PRODUCT('HetaudaKiln','HetaudaKiln',...)` in STEP file | `PRODUCT('PlantAKiln','PlantAKiln',...)` |
| `docs/org/release/v1.0-e2e/pid/07_planta_cooler_pid.json` | `"drawing_no": "HCIL-CLR-PID-001"`, title `"Hetauda Cement Cooler..."` | `"drawing_no": "NIDC-CLR-PID-001"`, title `"PlantA Cement Cooler..."` |
| `docs/org/release/v1.0-e2e/pid/07_planta_cooler_pid.svg` | "HCIL-CLR-PID-001 Rev A", "Hetauda Cement Cooler", "Hetauda 130 t/h" | "NIDC-CLR-PID-001 Rev A", "PlantA Cement Cooler", "PlantA 130 t/h" |
| `docs/strategy/BLOG_POSTS.md`, `docs/strategy/VALIDATION_PACK_TEMPLATE.md` | "Hongshi" in plant lists | "PlantC" |

Total files touched in this follow-up: 26.

### Intentionally NOT renamed (third-party company names)

- `Hongshi-Huaxin` in `tools/03-cooler-grate-simulator/day-03-PRs/mech-eng-plant/plant_equipment.md` — refers to the **Hongshi Group + Huaxin Cement** Chinese OEM joint venture that built PlantC. This is a real third-party company, not a Nepali plant. Same logic as keeping "KHD", "Polysius", "FLSmidth", "IKN" as real equipment vendors.
- `Shivam Cement Pvt Ltd` (Reliance Group, Makwanpur, 1000 tpd) in `pro/nepal_decarb_pro/data/nepal_plants.yaml` — this is a **different** Shivam (not the Hongshi-Shivam JV that was renamed to PlantC). It is a 5th plant in the data file, not one of the 4 renamed plants.

## What was NOT renamed (and why)

- **"Himalayan Carbon" / "Himalayan Space Solutions"**: the user
  is the founder of these companies. The names are about the
  organisation that built the platform, not about a specific
  plant. Kept intentionally.
- **The "Himalayan Carbon" email address** in the README,
  CITATION.cff, and pro/pyproject.toml: same reason. Kept
  intentionally.
- **References to the four plants in the historical engineering
  docs** (e.g., `tools/03-.../day-04-PRs/README.md`,
  `tools/01-baseline-emissions-mrv/RELEASE_NOTES.md`): these
  pre-date the rename and are part of the engineering history
  of the v0.2.0 - v0.6.0 development. Kept for archaeology.

## If you want to map back to a real plant

The mapping in the table above is the single source of truth.
If you are an outside reviewer and need to verify that the
PlantA engineering numbers correspond to a real plant, the
following files in the v0.5.0 calibrated model contain the
synthetic-but-realistic PlantA parameters:

- `tools/03-cooler-grate-simulator/src/nepal_cooler_sim/calibration.py`
  (the calibration parameter box)
- `tools/03-cooler-grate-simulator/src/nepal_cooler_sim/plants.py`
  (the plant presets)
- `tools/03-cooler-grate-simulator/day-04-PRs/data/synthetic_planta_*.csv`
  (the synthetic plant data)

The numbers in the synthetic data CSV are within the
realistic-physical-envelope range for a 130 t/h grate cooler
operating at 1400 m altitude (Cengel & Boles 2015 + Mujumdar
2007 + Peray & Waddell 1986 + ECRA 2022). They are NOT the
actual measured numbers for any specific Nepali plant.

The actual measured numbers for the four specific Nepali
plants live outside this public repository, in the user's
private plant-data archive. They are not part of the
remediation pass.
