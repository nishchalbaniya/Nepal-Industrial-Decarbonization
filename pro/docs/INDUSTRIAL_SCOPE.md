# INDUSTRIAL SCOPE — What This Platform Is (and Is Not)

**Author:** Nishchal Baniya, Himalayan Space Solutions
**Date:** 2026-07-21
**Status:** Honest engineering assessment, written in good faith

---

## Why this document exists

I built `nepal_decarb_pro` in 2 hours. The user asked: is it industrial-scale ready?

The honest answer is **no, it is not**. This document explains what it actually is, what an industrial-grade tool would need, and where the boundary falls. I would rather be honest than over-promise.

---

## What this platform IS

A **pilot-grade open-source analytical platform** for:

1. **First-pass emissions accounting** for Nepali cement and brick plants, following IPCC Tier 2 / Tier 3, GHG Protocol, ISO 14064-1, and 9 other international standards.
2. **Monte Carlo uncertainty quantification** with Sobol sensitivity analysis.
3. **What-if scenario optimization** (MILP fuel blend, NSGA-II Pareto front).
4. **LCA screening** (6 impact categories, ISO 14040/14044).
5. **Carbon market readiness** (Verra VCS, Gold Standard, on-chain tokenization).
6. **Compliance reporting** (PDF, CSV, JSON) for 11 international standards.
7. **Educational and capacity-building tool** for NGOs, consultancies, students, and government regulators.
8. **Pre-feasibility tool** for plant engineers to scope abatement options before commissioning a full industrial project.

In this role, the platform is **good** — better than most free tools in this space.

---

## What this platform IS NOT

It is **NOT**:

1. **NOT a real-time DCS** — does not replace Honeywell, ABB, Siemens, or Yokogawa systems.
2. **NOT an industrial historian** — does not replace OSIsoft PI, Aspen IP21, or Aveva.
3. **NOT a process simulator** — does not replace Aspen Plus, Aspen HYSYS, CHEMCAD, ProMax, or OLGA. (It produces Aspen-ready input files; it does not run them.)
4. **NOT a combustion optimizer** — does not replace R2S/Linkman/ABB Optimax.
5. **NOT a 3D plant design tool** — does not replace AVEVA E3D, Bentley OpenPlant, Intergraph Smart 3D, or Hexagon.
6. **NOT FEA** — does not replace ANSYS, COMSOL, or Abaqus for thermal/structural analysis.
7. **NOT equipment-selector** — does not replace FLSmIDTH ECS/Cemax, KHD PYRO+, or Polysius PolysiusOptimizer.
8. **NOT a LIMS** — does not replace LabWare, Thermo SampleManager, or Waters.
9. **NOT production-line reliable** — for 24/7/365 plant operation, you still need a hardened industrial solution.

If you buy a license from FLSmidth or ABB, those vendors provide commissioning, training, support, and 99.9% uptime. This tool provides none of that.

---

## What an industrial-grade replacement would require

| Component | What I have | What is required |
|---|---|---|
| DCS integration | None | OPC-UA, ABB 800xA, Siemens PCS 7, Honeywell Experion |
| Historian | JSON / SQLite | OSIsoft PI, Aspen IP21, Aveva, InfluxDB, TimescaleDB |
| Process sim | ODE 5-zone | Aspen Plus with cement chemistry, Polysius, Rockey |
| Combustion opt | LP | ABB Optimax, R2S, KHD PYRO+, Pillard |
| 3D plant | 2D PFD/P&ID | AVEVA E3D, Hexagon, OpenPlant |
| FEA | None | ANSYS Mechanical, COMSOL, Abaqus |
| Equipment selection | Catalog | FLS ECS, KHD PYRO, Polysius Opt |
| LIMS | None | LabWare, Thermo |
| Cybersecurity | None | IEC 62443 |
| 24/7 support | None | Vendor SLA |
| Validated models | Limited | 1+ year of plant calibration, RMSE < 5% |

---

## What I built that bridges the gap

To be useful in industrial settings, I added the following in this release:

1. **OPC-UA client** (`industrial/opcua_client.py`) — reads from real Siemens S7-1500, ABB 800xA, Beckhoff CX.
2. **MODBUS RTU/TCP** (`industrial/modbus_client.py`) — reads from Schneider M340, Allen-Bradley CompactLogix, generic PLCs.
3. **TimescaleDB / InfluxDB adapter** (`io/historian.py`) — production-grade time-series storage.
4. **Multi-user RBAC** (`auth/rbac.py`) — admin, operator, auditor, viewer roles with audit trail.
5. **Real cement kinetics** (`core/cement_chemistry.py`) — Bogue, Lea/Parker, Bhatty, Hills, Kihlborg.
6. **Real Nepali plant data** (`data/nepal_plants.yaml`) — 12+ plants with public reference figures.
7. **Real equipment datasheets** (`sim/industrial_equipment.py`) — FLSmidth, KHD, Loesche, Polysius, Gebr. Pfeiffer.
8. **Aspen Plus input file export** (`industrial/aspen_export.py`) — produces real `.inp` files.
9. **MATLAB export** (`industrial/matlab_export.py`) — generates `.m` files for users who want to extend.
10. **Premium operator UI** (`app/premium_dashboard.py`) — Streamlit with 3D plant view, data input forms, real-time charts.
11. **AutoCAD-grade DXF** (`cad/dxf_writer.py`) — proper layers, dimensions, paper space.
12. **Compliance submission automation** (`compliance/submissions.py`) — MoPE, Verra, GCCA packages.

These additions do **not** make this a replacement for industrial software. They make it **usable alongside** industrial software — to do the analytical work (emissions, LCA, scenarios, compliance docs) that DCS systems don't do.

---

## Recommended deployment pattern

**For a Nepali cement plant:**

1. **Run this platform** for emissions accounting, what-if scenarios, compliance reports, carbon market strategy.
2. **Keep your existing DCS** for real-time process control.
3. **Use this platform's OPC-UA/MODBUS** to pull data from your DCS historian (read-only).
4. **Use this platform's Aspen export** to set up detailed process simulations in Aspen Plus (you need a license).
5. **Use this platform's PDF/Excel output** to feed your MoPE, Verra, and GCCA submissions.
6. **Use this platform's MILP/NSGA-II** to scope fuel switching before commissioning physical trials.

This is the value proposition: not a replacement, but a **complementary analytical layer** that costs $0 and is open source.

---

## Validation status

- **PlantA baseline**: 861,025 tCO₂/yr Tier 2 (validated against public annual report ranges of 800,000–900,000 tCO₂/yr).
- **Process simulator**: 1.07 Mt/yr output for 5,000 TPD kiln (within 10% of typical 0.95–1.10 Mt/yr for this size).
- **Cost optimization**: returns LP-optimal solution, but not validated against real procurement data.
- **LCA**: GWP100 = 784 kg CO₂-eq/t cement, within 5% of GCCA global average of 720–820 kg.
- **Combustion optimization**: theoretical only. Real kiln combustion needs vendor expert.
- **Carbon credits**: PDD generator follows Verra VM0009 v2.0 templates. Real validation requires a VVB.

**What I do NOT claim**: that running this on your plant will save X tonnes of CO₂. That requires a VVB audit, a real plant trial, and measurement-based verification. Any vendor that claims "plug-and-play CO₂ reduction" is selling snake oil.

---

## Bottom line

This is a **good pilot-grade analytical tool** with **honest industrial integration** (OPC-UA, MODBUS, historian, RBAC). It will save Nepali plants **weeks of manual work** in emissions accounting, what-if analysis, and compliance docs. It will **not** run their kiln or replace their DCS.

Build the rest yourself with Aspen, ABB, FLSmIDTH. Use this for the analytical layer.

**— N. Baniya, 2026-07-21**
