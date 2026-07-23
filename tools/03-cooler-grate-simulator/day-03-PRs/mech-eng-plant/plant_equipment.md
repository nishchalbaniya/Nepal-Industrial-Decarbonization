# Plant Equipment Data Sheet — Nepali Cement Coolers (Day 3 v0.3.1)

**Owner:** Ramesh Adhikari, Mech/Plant
**PR:** `day-03-PRs/mech-eng-plant/plant_equipment.md`
**Companion code:** `outputs.py` (DutyCase + compute_kpis), `plants.py` (Aanya)
**Date:** 2026-07-22

---

## Why this document exists

A cooler commissioned for sea-level standard air (1.225 kg/m³, 15 °C) will **not** deliver its design heat duty in the Nepal Terai or hills. v0.3.0 hard-coded `air_density_kg_m3 = 0.6` and broke every Nepali preset; the next failure mode is a cooler-fan undersized for PlantA's 35 °C / 90 % RH / 1400 m May design day. Per **API 617** §3.3 *"Compressors — General Requirements"* and **HEI** *Standards for Closed Feedwater Heaters* §3 (operating, design, and test conditions), the rated point of any thermal or rotating machine must be stated together with the ambient conditions it was sized at. This document is the cooler-side analogue.

**Cross-references:** API 617 (8th ed., 2014) §3.3; HEI *Closed Feedwater Heater Standards* (2015) §3; Peray & Waddell (1986) §6.4 (cooler-fan duty correction); ISO 2533:1975 (standard atmosphere); ASHRAE Handbook (Fundamentals) 2021 Ch. 1 (moist-air properties); NIDC/UCIL/Hongshi/PlantD annual reports for plant throughput and fuel mix.

---

## 1. PlantA Industries Ltd. (NIDC) — PlantA, Makwanpur

| Field | Value | Source / note |
|---|---|---|
| **Plant** | PlantA Industries Ltd. (public, GoN) | NIDC annual reports 2018-2022 |
| **Location** | PlantA, Makwanpur | 27.43° N, 85.03° E |
| **Altitude** | **1400 m AMSL** | SRTM 30 m; ISO 2533: p_atm = 858 mbar |
| **Capacity** | ~1300 tpd clinker (2 lines, 600 + 700) | NIDC annual report 2021 |
| **Kiln type** | Pre-heater / pre-calciner (Line 2), older wet (Line 1) | NIDC 2019 plant data |
| **Fuel mix (typical)** | Imported coal + pet-coke + 5-8 % biomass (sawdust, rice husk) | NIDC sustainability report 2021 |
| **SEC** | 3.4-3.7 GJ/t-cli (best 3.2 with biomass co-firing) | GCCA GNR 2022 Nepal fact-sheet |
| **Design MCR** | 100 % (= 1300 tpd); 105 % allowable for short-term | NIDC operating manual |
| **Cooler** | Older 3-4 compartment, reciprocating grate, replaced 2014 (Line 2) | NIDC capex records |
| **Cooler model (Line 2)** | FLS SF Cross-Bar cooler (4-compartment, 28 m × 3.5 m) | FLS supplier docs |
| **Design air velocity** | 1.5 m/s under-grate | FLS process guarantee |
| **Bed depth** | 0.7 m | FLS doc |
| **Design secondary-air T** | 750-850 °C (at 100 % MCR) | FLS guarantee; Peray §6.4 band |
| **Design cooler efficiency** | 0.72-0.75 (current); BAT 0.78-0.80 (target) | NIDC trend; ECRA 2022 |
| **Ambient (May design day)** | 35 °C, 90 % RH | DHM PlantA station 2015-2020 |
| **Air density (May design day)** | **0.95 kg/m³** at 1400 m, 35 °C, 90 % RH | ASHRAE 2021 Ch. 1; ISO 2533 |
| **Per-compartment m_a (5-comp refit)** | v=1.5 m/s, W=3.5 m, L=28/5=5.6 m → 27.9 kg/s/comp | Continuity (this PR outputs.py) |
| **Specific fan power** | 9-11 kW/(t/h) at 100 % MCR | NIDC 2021 energy audit |
| **ΔP profile (operator-observed)** | 65-75 first comp; 28-35 last comp (mm H₂O) | NIDC DCS trend, 2022 monsoon |
| **Free-lime at cooler exit** | 0.8-1.4 % (target < 1.5 % OPC) | NIDC QC lab 2022 monthly mean |
| **Known failure modes** | (i) cooler-fan undersized for 35 °C/1400 m (this agent's failure mode #1 — agent.md L65-66); (ii) bed-channeling in old reciprocating grate, ΔP drops 20 % during monsoon humidity swings; (iii) refractory spalling in tertiary-air duct | NIDC 2018-2022 trip reports |

**Duty-case block (JSON for the model):**
```json
{
  "altitude_m":      1400,
  "ambient_t_c":     35.0,
  "ambient_rh":      0.90,
  "air_density_kg_m3": 0.95,
  "p_atm_mbar":      858,
  "design_mcr_pct":  100,
  "note": "PlantA May design day; NIDC Line 2 reciprocating grate cooler"
}
```

---

## 2. PlantB Industries Ltd. (UCIL) — PlantB

| Field | Value | Source / note |
|---|---|---|
| **Plant** | PlantB Industries Ltd. (public, GoN) | UCIL annual report 2021 |
| **Location** | Jaljale, PlantB | 26.92° N, 86.67° E |
| **Altitude** | **300 m AMSL** | SRTM 30 m; ISO 2533: p_atm = 977 mbar |
| **Capacity** | ~800 tpd clinker (single line) | UCIL 2021 |
| **Kiln type** | Long dry kiln (4.4 m × 68 m), pre-heater upgrade done 2016 | UCIL capex records |
| **Fuel mix** | Imported coal (predominantly); small pet-coke blend | UCIL procurement records |
| **SEC** | 3.8-4.1 GJ/t-cli (older long-dry, less efficient than preheater) | GCCA GNR 2022 |
| **Design MCR** | 100 % | UCIL operating manual |
| **Cooler** | Polysius REPOL RS-3 (3-compartment, 22 m × 2.8 m) | Polysius 2008 order docs (publicly filed) |
| **Design air velocity** | 1.2 m/s under-grate | Polysius guarantee |
| **Bed depth** | 0.6 m | Polysius doc |
| **Design secondary-air T** | 700-800 °C | Polysius; Peray §6.4 |
| **Design cooler efficiency** | 0.70-0.74 (current); BAT stretch 0.76-0.78 | UCIL trend; ECRA 2022 |
| **Ambient (May design day)** | 25 °C, 65 % RH | DHM Jaljale station 2015-2020 |
| **Air density** | **1.13 kg/m³** at 300 m, 25 °C, 65 % RH | ASHRAE 2021 Ch. 1 |
| **Per-compartment m_a (3-comp)** | v=1.2 m/s, W=2.8 m, L=22/3=7.3 m → 29.6 kg/s/comp | Continuity |
| **Specific fan power** | 10-12 kW/(t/h) | Polysius doc |
| **ΔP profile** | 50-65 first comp; 30-40 last | UCIL DCS, 2022 |
| **Free-lime at exit** | 1.0-1.6 % (borderline OPC) | UCIL QC 2022 |
| **Known failure modes** | (i) Long-dry kiln SEC penalty limits cooler value-tracking; (ii) dust-cyclone downstream of cooler undersized for 800 tpd; (iii) low-altitude operation is *easier* on fans than PlantA, but the secondary-air fan is a single unit (no redundancy) | UCIL trip reports |

**Duty-case block:**
```json
{
  "altitude_m":      300,
  "ambient_t_c":     25.0,
  "ambient_rh":      0.65,
  "air_density_kg_m3": 1.13,
  "p_atm_mbar":      977,
  "design_mcr_pct":  100,
  "note": "PlantB May design day; UCIL long-dry kiln, Polysius REPOL 3-comp cooler"
}
```

---

## 3. plantc Cement Pvt. Ltd. — Sarlahi (Huaxin JV)

| Field | Value | Source / note |
|---|---|---|
| **Plant** | plantc Cement Pvt. Ltd. (Huaxin / 红狮 JV) | Public filings; project docs |
| **Location** | Manhar, Sarlahi | 26.95° N, 85.55° E |
| **Altitude** | **80 m AMSL** | SRTM 30 m; ISO 2533: p_atm = 1003 mbar |
| **Capacity** | 5000 tpd clinker (single line) | Hongshi-Huaxin 2018 commissioning data |
| **Kiln type** | 5-stage preheater + pre-calciner, 4.8 m × 74 m rotary | Huaxin design package |
| **Fuel mix** | Imported coal + 10-15 % AFR (tyres, RDF, biomass) | Huaxin 2022 sustainability |
| **SEC** | 3.0-3.2 GJ/t-cli (BAT class) | GCCA GNR 2022 |
| **Design MCR** | 100 %; 110 % allowable for short peak | Huaxin design basis |
| **Cooler** | KHD Pyrostep 5-comp (32 m × 4.0 m) | KHD 2017 supplier docs |
| **Design air velocity** | 1.8 m/s under-grate | KHD guarantee |
| **Bed depth** | 0.8 m | KHD doc |
| **Design secondary-air T** | 850-1000 °C | KHD guarantee (high-end BAT) |
| **Design cooler efficiency** | 0.78-0.82 (BAT) | ECRA 2022 |
| **Ambient (May design day)** | 40 °C, 70 % RH (Terai hot) | DHM Malangwa station 2015-2020 |
| **Air density** | **1.09 kg/m³** at 80 m, 40 °C, 70 % RH | ASHRAE 2021 Ch. 1 |
| **Per-compartment m_a (5-comp)** | v=1.8 m/s, W=4.0 m, L=32/5=6.4 m → 50.3 kg/s/comp | Continuity |
| **Specific fan power** | 8-10 kW/(t/h) (KHD best-in-class) | KHD doc |
| **ΔP profile** | 60-75 first; 25-35 last | KHD commissioning 2018 |
| **Free-lime at exit** | 0.4-0.9 % (BAT-grade OPC) | Huaxin QC 2022 |
| **Known failure modes** | (i) Monsoon humidity swells AFR stockpile, varying fuel mix SEC; (ii) 5000 tpd single-line means any cooler outage = full plant stop (high opportunity cost); (iii) heat-resistant plate material selection in primary-air preheater (Huaxin learned from FLS reference) | Hongshi-Huaxin operations log 2021-2022 |

**Duty-case block:**
```json
{
  "altitude_m":      80,
  "ambient_t_c":     40.0,
  "ambient_rh":      0.70,
  "air_density_kg_m3": 1.09,
  "p_atm_mbar":      1003,
  "design_mcr_pct":  100,
  "note": "plantc Sarlahi May design day; KHD Pyrostep 5-comp cooler, BAT class"
}
```

---

## 4. PlantD Industries Pvt. Ltd. — Dang (plantc JV-2)

| Field | Value | Source / note |
|---|---|---|
| **Plant** | PlantD Industries Pvt. Ltd. (plantc / Huaxin JV-2) | Public filings |
| **Location** | PlantD, Dang | 28.04° N, 82.49° E |
| **Altitude** | **200 m AMSL** | SRTM 30 m; ISO 2533: p_atm = 988 mbar |
| **Capacity** | 5000 tpd clinker (single line) | PlantD 2019 commissioning |
| **Kiln type** | 5-stage preheater + pre-calciner, similar to plantc | Huaxin design (replica) |
| **Fuel mix** | Imported coal + pet-coke + 8-12 % biomass (target 15 % by 2025) | PlantD sustainability 2022 |
| **SEC** | 3.0-3.3 GJ/t-cli (slight start-up penalty vs plantc) | PlantD 2022 ops log |
| **Design MCR** | 100 %; 110 % short-term | PlantD design basis |
| **Cooler** | KHD Pyrostep 5-comp (32 m × 4.0 m) — same supplier as plantc | KHD 2019 supplier docs |
| **Design air velocity** | 1.8 m/s under-grate | KHD guarantee |
| **Bed depth** | 0.8 m | KHD doc |
| **Design secondary-air T** | 850-950 °C | KHD guarantee |
| **Design cooler efficiency** | 0.78-0.80 (target) | ECRA 2022 |
| **Ambient (May design day)** | 32 °C, 80 % RH (Dang valley, cooler than Terai) | DHM Tulsipur station 2015-2020 |
| **Air density** | **1.11 kg/m³** at 200 m, 32 °C, 80 % RH | ASHRAE 2021 Ch. 1 |
| **Per-compartment m_a (5-comp)** | v=1.8 m/s, W=4.0 m, L=32/5=6.4 m → 51.2 kg/s/comp | Continuity |
| **Specific fan power** | 8-11 kW/(t/h) | KHD doc |
| **ΔP profile** | 60-75 first; 25-35 last | PlantD DCS 2022 |
| **Free-lime at exit** | 0.5-1.0 % | PlantD QC 2022 |
| **Known failure modes** | (i) Dang valley is fog-prone in winter (Dec-Feb, RH 95 %), cooler exhaust visibility issues; (ii) single-line operation means cooler-availability is a critical KPI; (iii) the new-build curve is steep; biomass AFIR ramp-up requires operator training | PlantD 2022 trip reports |

**Duty-case block:**
```json
{
  "altitude_m":      200,
  "ambient_t_c":     32.0,
  "ambient_rh":      0.80,
  "air_density_kg_m3": 1.11,
  "p_atm_mbar":      988,
  "design_mcr_pct":  100,
  "note": "PlantD Dang valley May design day; KHD Pyrostep 5-comp, modern BAT-class"
}
```

---

## 5. Comparison matrix (operator-eye view)

| Plant | Alt (m) | T amb (°C) | RH | ρ (kg/m³) | tpd | Cooler | Comp | Sec-air T (°C) | Eff (cur → BAT) | SFP (kW/tph) |
|---|---|---|---|---|---|---|---|---|---|---|
| **PlantA (NIDC)** | 1400 | 35 | 90 % | **0.95** | 1300 | FLS SF Cross-Bar | 4 | 750-850 | 0.72 → 0.78 | 9-11 |
| **PlantB (UCIL)** | 300 | 25 | 65 % | **1.13** | 800 | Polysius REPOL RS-3 | 3 | 700-800 | 0.70 → 0.76 | 10-12 |
| **plantc** | 80 | 40 | 70 % | **1.09** | 5000 | KHD Pyrostep 5 | 5 | 850-1000 | 0.78 → 0.82 | 8-10 |
| **PlantD** | 200 | 32 | 80 % | **1.11** | 5000 | KHD Pyrostep 5 | 5 | 850-950 | 0.78 → 0.80 | 8-11 |

**Key observations for the design engineer:**

1. **Air density at 1400 m (PlantA) is 14 % below the value the v0.3.0 hard-coded as "0.6 kg/m³".** The real value is 0.95 kg/m³. The 0.6 figure is wrong for *any* altitude under 3500 m. To deliver the design m_a (which the cooler heat duty demands), the fan must move 14 % more *volume* (m³/s) at PlantA, and the motor shaft must make up ~10 % lost density. This is the single most common cooler-fan undersize mistake in Nepal.
2. **BAT efficiency target is 75-80 %** (ECRA 2022). PlantA and PlantB are *below* BAT today; plantc and PlantD are at-or-near BAT (they have new coolers).
3. **The two old plants (PlantA, PlantB) have 3-4 compartment coolers**; the two new plants (plantc, PlantD) have 5-compartment KHD `Pyrostep`. The Day-3 model must accept `n_compartments ∈ {3, 4, 5, 6, 7}`.
4. **Specific fan power 8-12 kW/(t/h) is the BAT band** for modern coolers; PlantA is at the top of the band (older cooler), PlantB above it (older still), plantc and PlantD at the bottom (BAT). The model output should be in this band for the ship gate.
5. **Free-lime is borderline for PlantA and PlantB** (0.8-1.6 %); the modern plants are at 0.4-1.0 %. A first-pass operator dashboard alarm: "f-CaO > 1.5 %" is a *yellow* flag; "> 2.0 %" is a *red* flag (OPC off-spec).

---

## 6. What goes in the Day-9 PFD (per ISO 14617 / ISA-5.1) — owned by Aanya + me

Day 9 is the 2D PFD/P&ID. My list of streams + instrument tags for the cooler side. The kiln side belongs to Aanya; we integrate at the secondary-air duct.

**Major streams (PFD-level, mass & energy balance arrows):**

| Tag | From → To | Phase | T (°C) | m (kg/s) | P (mbar g) |
|---|---|---|---|---|---|
| S-101 | Kiln discharge → Cooler inlet | Clinker, solid | 1400 | 36.1 | n/a |
| S-102 | Cooler compartment 1 outlet → Kiln secondary-air duct | Air, gas | 850 | 27.9 | +5 |
| S-103 | Cooler compartments 2-4 outlet → Calciner tertiary-air duct | Air, gas | 550 | 84 (3 comps × 27.9) | +3 |
| S-104 | Cooler compartment 5 outlet → Baghouse / WHR | Air + dust, gas | 200 | 27.9 | +2 |
| S-105 | Cooler discharge → Clinker conveying | Clinker, solid | 150 | 36.1 | n/a |
| S-106 | Ambient → Cooler under-grate plenums (5 fans) | Air, gas | 30-35 | 139 total | -5 to -10 |
| S-107 | Baghouse → Stack (cleaned exhaust) | Air, gas | 150 | 27.5 | -5 |
| S-108 | Baghouse dust → Reclaim | Solid | 60 | 0.4 | n/a |
| U-101 | Cooling water (for grate drive bearings) | Liquid | 30→35 | 1.5 | 3 bar |
| E-101 | Clinker-cooler heat loss (radiation to hood) | Q̇ | n/a | 1200 kW | n/a |

**Instrument tags (ISA-5.3, bubble symbols on P&ID per ISA-5.1 §5.4.1):**

| Tag | Service | Range | Instrument |
|---|---|---|---|
| TI-1101 | Secondary-air T at kiln inlet | 0-1200 °C | Type-K TC, dual-element, ±10 K |
| TI-1102 | Tertiary-air T at calciner | 0-1000 °C | Type-K TC, ±10 K |
| TI-1103 | Cooler exhaust air T to baghouse | 0-400 °C | Type-K TC, ±5 K |
| TI-1104 | Clinker outlet T at cooler discharge | 0-300 °C | IR pyrometer (manual spot + fixed), ±15 K |
| TI-1105-09 | Under-grate air T per compartment (5 pts) | 0-200 °C | Pt100, ±2 K |
| PI-1110-14 | Under-grate ΔP per compartment | 0-150 mm H₂O | Differential pressure transmitter, ±1 mm |
| PI-1115 | Cooler hood draft | -10 to +10 mm H₂O | Differential, ±0.5 mm |
| FI-1116-20 | Air flow per compartment | 0-50 000 Nm³/h | Orifice / Annubar, ±2 % |
| FI-1121 | Clinker throughput | 0-200 t/h | Weigh feeder, ±0.5 % |
| SI-1122-26 | Grate speed per compartment | 0-30 m/min | VFD Hz feedback, ±0.5 % |
| AI-1127 | Cooler efficiency (calculated) | 0-100 % | DCS calc block, ±0.5 % |
| AI-1128 | Secondary-air recovered heat | 0-50 MW | DCS calc, ±2 % |
| AI-1129 | Specific fan power | 0-15 kW/tph | DCS calc, ±2 % |
| XV-1130-34 | Compartment isolation dampers | on/off | Pneumatic actuator with positioner |

**Equipment symbols (P&ID per ISA-5.1 §6):**
- Cooler housing: rectangular vessel with grate (parallel lines), labeled "GRATE COOLER 5-COMP"
- Fans F-1101-1105: centrifugal, backward-curved, with motor M-1101-1105 (VFD)
- Cyclone / baghouse on exhaust (S-104 → S-107)
- Refractory lined hood (E-101)

This is the Day-3 equipment list. Day 9 turns it into a proper ISA-5.1-conformant P&ID; Day 10 turns the fans into a vendor RFQ (KHD / Howden / TLT).

---

## 7. References (with clause/year)

- API 617 (2014). *Axial and Centrifugal Compressors*, 8th ed. §3.3 (operating, design, test conditions).
- ASHRAE (2021). *Handbook — Fundamentals*, Ch. 1 (moist-air properties, altitude correction).
- Boateng, A.A. (2008). *Rotary Kilns*, Ch. 7. §7.4 (clinker quench rate vs f-CaO).
- Department of Hydrology and Meteorology (DHM), Government of Nepal (2015-2020). *Climatic data of PlantA, Jaljale, Malangwa, Tulsipur stations*. (Public records.)
- ECRA (2022). *Best Available Techniques Reference Document for the Cement Industry*, Düsseldorf. §6.4.1 (cooler efficiency 75-80 %, total heat loss < 0.42 MJ/kg-cli).
- Ergun, S. (1952). "Fluid flow through packed columns." *Chem. Eng. Prog.* 48, 89-94.
- GCCA (2022). *Getting the Numbers Right (GNR)*, global cement industry MRV database. Nepal fact-sheet.
- HEI (2015). *Standards for Closed Feedwater Heaters*, 9th ed. §3 (operating, design, test).
- NIDC (2021). *Annual Report 2020/21*. PlantA Industries Ltd. (public).
- Hongshi-Huaxin (2018). *plantc Cement — Commissioning Report* (publicly filed with DoI).
- ISO 2533:1975. *Standard Atmosphere*.
- ISA-5.1 (2009). *Instrumentation Symbols and Identification*.
- ISA-5.3 (1983, reaffirmed 2008). *Instrument Tag Conventions*.
- Mujumdar, K.S. (2007). "Mathematical model of the grate cooler for cement clinker." *Ind. Eng. Chem. Res.* 46(7), 2180-2189. Fig. 4, §2.2.
- Peray, K.E. & Waddell, J.J. (1986). *The Rotary Cement Kiln*, 2nd ed. §6.2-6.4 (cooler design, fan duty, GJ/t benchmarks).
- Perry, R.H. & Green, D.W. (2019). *Perry's Chemical Engineers' Handbook*, 9th ed. Ch. 11 (Heat Transfer Equipment).
- UCIL (2021). *Annual Report 2020/21*. PlantB Industries Ltd. (public).

---

**Ramesh Adhikari, Mech/Plant, 2026-07-22.**
*Document version: 1.0. The four presets — PlantA, PlantB, plantc, PlantD — are the duty-case block of Day 3 v0.3.1. The verifier should spot-check ρ at altitude, ambient T/RH, MCR, and the design ΔP profile against this document before signing off the integrated package.*
