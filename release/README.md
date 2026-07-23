# Nepal Industrial Decarbonization v1.0.0 — Release

**Tag:** v1.0.0
**Date:** 2026-07-23
**Status:** ✅ Shipped (engineering readiness, not commercial readiness)
**License:** MIT

---

## What this release contains

This is the v1.0 cut of the Nepal Industrial Decarbonization
product. It is the result of 12 days of work (Day 1 baseline MRV
+ Days 2-12 incremental builds) on a 4-plant Nepali cement
platform: Hetauda (Himalayan Carbon flagship), Udayapur,
Hongshi-Shivam, and Ghorahi.

### Engineering deliverables (all in `release/v1.0-e2e/`)

- **Cooler STEP file** — 22.7 KB, 11 parts, 36.3m × 3.5m × 2.8m
  bounding box, ISO 10303-21 AP214, opens in FreeCAD / Onshape /
  Fusion 360 / 3dviewer.net
- **Hetauda kiln STEP file** — 66.5 KB, 17 parts, 65.8m × 7m ×
  60m, 4 tire-and-roller stations, primary burner, preheater
  tower, girth gear
- **Cooler P&ID** — 10.4 KB SVG per ISA-5.1, 8 instrument tags
  (TI-1101..1105, PI-1101, FT-1101, SC-1101), 6 process streams,
  drawing number HCIL-CLR-PID-001 Rev A
- **Calibration JSON** — v0.5.0 L-BFGS-B posterior (10 parameters,
  loss 233.72 → 5.00, RMSE sec_air 10.2 K / clinker 0.7 K /
  exhaust 24.0 K)
- **4-plant sweep JSON** — 4,736 kt/yr clinker → 4,120 kt CO₂e/yr
  CBAM exposure (~€330M/yr at €80 EUA)
- **DEPLOY-AND-SELL.md** — full walkthrough: how to run, what
  to tell the regulator, what to tell the plant manager, what
  to tell the auditor

### Software (in the repo at v1.0.0)

- **Cooler v0.5.0** — 4 plant presets, 10-parameter calibration
  (7 operating + 3 geometry), first-law energy balance ≤ 1e-15
- **Kiln v0.2.0** — 6 plant presets, 3 fuel types, CBAM-aligned
  CO₂ intensity
- **CAD/P&ID v0.6.0 - v0.9.0** — FreeCAD STEP export, cooler
  P&ID per ISA-5.1
- **FastAPI server v0.7.0** — 14 endpoints, browser dashboard,
  Swagger UI
- **Turnkey installer v0.7.0** — Desktop .lnk shortcuts
  (Dashboard, Run Demo, Uninstall), NEPAL_DECARB_ROOT in HKCU

### Tests

- **102/102 tests green** — 47 cooler + 46 kiln + 9 pro v1.0
- 0 synthetic-helper bypasses (per Aanya / Ramesh / verifier
  feedback loop)
- 0 < 10× first-law test threshold (per Aanya v0.3.2 fix)

---

## How to install (zero to dashboard in 5 minutes)

```bash
# 1. Clone (you already have this)
git clone https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization.git
cd Nepal-Industrial-Decarbonization

# 2. Set PYTHONPATH
$env:PYTHONPATH = "pro\src;tools\02-kiln-dynamics-simulator\src;tools\03-cooler-grate-simulator\src"

# 3. Install
python -m nepal_decarb_pro.cli setup --port 8000

# 4. Double-click Desktop\NepalDecarb Dashboard.lnk
```

You get:
- 3 real Windows shortcuts on Desktop (Dashboard, Run Demo, Uninstall)
- 3 matching shortcuts in Start Menu under NepalDecarb
- NEPAL_DECARB_ROOT registered in HKCU\Environment
- FastAPI server at http://127.0.0.1:8000/

---

## Honest disclosure: what this v1.0 is NOT

1. **3 of 6 ship-gate bands still fail** on the v0.5.0 calibrated
   Hetauda model (tertiary 190°C, exhaust 149°C, clinker 351°C).
   The model physics at 130 t/h cannot deliver all 3
   simultaneously. Unblock requires either:
   - (a) real Hetauda plant data (CSV with 4h shifts — see
     `tools/03-cooler-grate-simulator/day-04-PRs/data/` for the
     column spec), OR
   - (b) v0.6.0 model changes (compartment subdivision within
     compartment, or lower-throughput operation).

2. **No LLM advisor yet** (Day 14, deferred).

3. **Calibration was on synthetic data, not real Hetauda.** The
   calibration framework is real and the gradient is in the right
   direction; the numbers will change when real plant data is
   used.

4. **Octave kiln cross-language check pending** — UAC prompt for
   the Octave installer still on screen, not yet clicked through.

5. **No commercial pilot terms** — engineering readiness, not
   commercial readiness. To sell: Rina drafts Hetauda MoU, James
   drafts VMD0053 methodology deviation request, Priya refines
   50-plant ARR model.

---

## Citation graph (audit trail)

| Source | Used in |
|--------|---------|
| Achenbach 1995 | h_rad_equiv linearization |
| Mujumdar 2007 §2.2 | cross-flow packed-bed heat transfer |
| Mujumdar & Ranade 2006 | cement cooler fundamentals |
| Peray & Waddell 1986 | cooler geometry conventions |
| Boateng 2008 | rotary kiln PDEs |
| Sass 1967 | cement chemistry |
| Cengel & Boles 2015 | moist air, ISA barometric, Magnus |
| Byrd et al. 1995 | L-BFGS-B constrained optimization |
| Saltelli 2010 | Sobol' sensitivity |
| EC DG TAXUD Dec 2023 (JRC) | CBAM 0.83 t CO₂e/t direct |
| Implementing Reg 2025/2621 | 2026+ mark-ups |
| Verra VM0009 v3.0 §5.3 | cooler in kiln baseline |
| ISO 10303-21 AP214 | STEP file format |
| ISA-5.1 / ISA-5.3 | P&ID conventions |
| Cement Sustainability Initiative 2018 | SEC baseline 3269 MJ/t |

---

## Git history (12 days, 11 commits)

```
69499f0 docs: Day 12 -- update START-HERE.txt
a422ddd feat(pro): Day 12 -- real Windows .lnk Desktop shortcuts
cbd5c19 fix(pro): Day 11 setup -- register NEPAL_DECARB_ROOT
7a51acd feat(pro): Day 10 v1.0.0 -- FastAPI server + turnkey installer
bc39327 feat(tools/03 + pro): Day 9 v0.9.0 -- cooler P&ID
f9b58d2 feat(tools/02 + pro): Day 8 v0.8.0 -- kiln STEP export
6341fd1 feat(pro): Day 7 v0.7.0 -- unified nepal-decarb CLI
55f14e2 feat(tools/03): Day 6 v0.6.0 -- FreeCAD STEP export
2aa918c feat(tools/03): Day 5 v0.5.0 -- operating-handle freedom
83b0533 feat(tools/03): Day 4 v0.4.0 -- L-BFGS-B calibration
86dc577 fix(tools/03): CBAM 0.642 -> 0.83 t CO2e/t (James re-verify)
d8aea52 docs: Day 4 spec -- cooler calibration to Hetauda plant data
49fe94d feat(tools/03): cooler grate simulator v0.3.2
5742b8d feat(tools/02): kiln dynamics simulator -- Day 2/20
```

---

## Live URLs

- **Public v1.0 pilot site:** https://0qybaybtii6dt.space.minimax.io
- **Public e2e demo:** https://jfp4xr4woteju.space.minimax.io
- **GitHub:** https://github.com/nishchalbaniya/Nepal-Industrial-Decarbonization

---

## Contact

Nishchal Baniya, Himalayan Carbon Nepal
Email: nishchal.baniya@gmail.com
Built 2026-07-22/23 with Mavis (mavis local), open source, MIT.
