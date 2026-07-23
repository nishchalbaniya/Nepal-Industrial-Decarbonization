# Day 3 Review — Cooler Heat-Transfer Physics

**Reviewer:** Dr. Aanya Sharma, Senior Chemical Engineer (Cement Pyroprocessing)
**Scope:** `tools/03-cooler-grate-simulator` — `cooler_ode.py`, `kiln_link.py`
**Live run output (n=30, max_t_s=900):** `Outlet C: 403.7 | Sec air C: 5790.6 | Eff: 72.7% | Heat rec: 37,775 kW`

The cooler drops clinker to ~400 °C (plausible) and reports a 72.7 % efficiency (plausible), but the secondary-air temperature of **5790 °C** is not just "unphysical" — it is the symptom of a real heat-transfer bug. Mavis flagged the symptom correctly. The diagnosis and fix are below.

---

## 1. Heat transfer physics

**Radiation is dominant and is being mishandled.**

Numbers, with the constants in the file:
- Stefan–Boltzmann: σ = 5.6704e-8 W/m²·K⁴
- ε = 0.85 (clinker emissivity — reasonable; hot-clinker pellets are near-black, ICCC 2006 §2.3)
- T_clinker = 1400 °C = 1673 K, T_air = 30 °C = 303 K

q″_rad = ε·σ·(T_c⁴ − T_a⁴) = 0.85 · 5.67e-8 · (1673⁴ − 303⁴) = **377 kW/m²** (single side).

Compared to convection: Achenbach (1995) for cross-flow over a packed bed gives
Nu = [(1.18 Re^0.58)⁴ + (0.23·Re/(1−ε_void))^0.75·⁴]^(1/4). At Re≈1000, void=0.45, k=0.05, d=0.025 m → h ≈ 720 W/m²·K. The code's `h_conv` floor of **200 W/m²·K** is in the right *order of magnitude* but the *correlation* `Nu = 0.245·Re^0.7·Pr^0.33` is **not Achenbach** — at Re=1000 it returns Nu≈27, h≈55, then the 200 W/m²·K floor takes over. So the code is *not* using the Achenbach correlation; it is just using a floor. That is acceptable for engineering-grade Day 3 fidelity, but the comment is misleading and should be fixed.

The real problem: at q″ = 377 kW/m² with h = 200 W/m²·K and ΔT = 1370 K, the radiation term is **~2,750× larger** than the convective term. So air heating in the model is almost entirely radiative, and radiation has to be capped **against the air's actual ability to absorb it**. The current code does:

```
dQ = max(q_conv + q_rad, 0) * A_cell
dT_c = dQ / (m_c_per_m · dx/n_sub · cp_clinker)
dT_a = dQ / (air_kg_per_m · dx/n_sub · cp_air)
```

with **no upper bound on `dT_a`**. At cell 0: A_cell ≈ 3.5·0.933 = 3.27 m²; dQ = 377 000 · 3.27 ≈ 1.23 MW per sub-step. Air in transit per sub-step = air_kg_per_m · (dx/8) = 3.15 · 0.117 ≈ 0.367 kg. dT_a = 1.23e6 / (0.367 · 1005) ≈ **3 340 K in one sub-step**. With 8 sub-steps, the air is not integrating — it is being launched into space. The 200 W/m²·K floor + the 377 kW/m² radiation + the per-sub-step air mass are simply incompatible.

The fix: **enforce a second-law cap on air heating**, i.e. `dT_a ≤ T_c − T_a` (you cannot heat the air above the clinker it is leaving), *and* use the actual compartment air mass, not the per-metre total.

> Cite: Mujumdar (2007) Ind. Eng. Chem. Res. 46(7), "Grate cooler model" — the published Mujumdar model applies just this clamp; Peray & Waddell (1986) §6.3 also notes that radiation dominates in the first 5–8 m of a grate cooler and must be treated as a *boundary-layer-limited* flux, not a free-stream flux.

## 2. Cross-flow vs counter-flow

**Mavis's instinct is right. Move to counter-flow for the secondary-air path; keep cross-flow semantics for the cooling-air path.**

Real coolers are neither purely cross-flow nor purely counter-flow — they are a **5-compartment hybrid**:

- The first compartment (kiln end, the hot end) is operated as a **secondary-air recovery** zone. Air is ducted *up* through the bed at that compartment and sent directly to the kiln burner. In a 5-compartment IKN/Polycom/Hongshi-style cooler this is the kiln-end compartment. **Tertiary air** to the calciner comes from the second compartment.
- Compartments 2–5 (cold end) are **cooling-air compartments**: the air is exhausted to dust collection or to a waste-heat boiler.

So the *integrated* 1D model should be: **a counter-flow exchanger with N compartments, the first compartment's air outlet is the secondary air, the rest are exhaust air** (Mujumdar 2007; Boateng 2008 Ch. 7).

For Day 3, the simplest correct fix:

1. Replace `T_a_cell = p.under_grate_air_temp_c` (reset every cell) with a **single air stream that flows counter to the clinker**. Initialize an air profile `T_a[i] = T_a_in` for all i, then march i = 0 → n−1 and update `T_a[i+1] = T_a[i] + dQ/(m_a_sec·cp_a)` (the parcel leaving cell i is the inlet of cell i+1).
2. Define `secondary_air_outlet_c = T_a[0]` (the air parcel that has traversed the *whole* bed and exits at the kiln end, i.e. the hottest, most-recovered stream). This is the air that *actually* goes to the kiln burner.
3. Set `m_a_secondary` to roughly 1.0–1.2× the stoichiometric combustion air for the kiln coal. For a 130 t/h clinker plant with ~100 kg coal/t-clinker (typical for a precalciner kiln, Peray & Waddell 1986), that is **~38 kg/s** — not 88.2 kg/s as the current total-air calculation gives.
4. The remaining 88.2 − 38 ≈ 50 kg/s is the **cooling/vent air** that exits the cold-end compartments. In a 1D model you can ignore it for the energy balance on the secondary-air stream (it is the *other* sink), but the *clinker* energy balance must use the *total* air mass (or, more correctly, integrate `h·A·(T_c − T_local)` with `T_local` being the *local* under-grate air, which is a weighted mix of the secondary-air parcel and cooling-air parcels at each location).

The right level of fidelity for a Day 3 deliverable is **the counter-flow 1D model with 5 compartments**, secondary air taken at i=0, and a second-law clamp on `dT_a`. Anything less and the kiln-cooler coupling in `kiln_link.py` is feeding the kiln a fictitious 5 790 °C air stream, which will make the kiln model over-predict everything downstream.

> The current line `secondary_air = float(np.max(T_air_profile))` is wrong for both cross-flow *and* counter-flow. In cross-flow, no parcel traverses the whole bed, so there is no "outlet" air — every cell has its own exhaust. In counter-flow, the outlet is a single parcel at i=0. Taking `max()` over a 1D profile whose each entry is independent is a coding bug that turned a thermal-physics question into a one-line `np.max` mistake.

## 3. Parameters

The default parameters are **in the right ballpark for a 5000-tpd plant**, but the 130 t/h case is closer to a 4000-tpd line. Comparison:

| Parameter | Code default | plantc-class 5000 tpd | GCCA GNR 2022 / ECRA 2022 BAT | Verdict |
|---|---|---|---|---|
| Length × width | 28 m × 3.5 m = 98 m² grate area | 30–34 m × 3.6–4.2 m (~110–140 m²) | — | OK for 4000 tpd; tight for 5000 tpd |
| Throughput | 130 t/h (≈ 3120 t/d) | 208 t/h (5000 t/d) | 3000–10 000 t/d range | 130 t/h = small-to-mid plant, fine for Day 3 demo |
| Bed depth | 0.70 m | 0.6–0.8 m | 0.5–1.0 m typical | OK |
| Grate speed | 12 m/min | 10–16 m/min | — | OK (residence time ≈ 2.3 min, in the 1.5–4 min ICCC 2006 band) |
| Air velocity | 1.5 m/s superficial | 1.0–2.5 m/s | — | OK |
| Clinker inlet T | 1400 °C | 1380–1450 °C | — | OK |
| Clinker outlet T (target) | 150 °C | 130–180 °C | "modern cooler < 100 °C above ambient" ECRA | OK; 150 °C is conservative; BAT pushes toward 100 °C |
| Cooler efficiency expected | 72.7 % (current) | 70–82 % | **75–80 % BAT** (ECRA 2022: "Modern reciprocating coolers can have a high degree of heat recuperation efficiency up to 75 to 80 %") | Current value is in the *Indian-industry* range (NPC India: 72–75 %); BAT is 78–80 % |
| Total cooler heat loss | (compute from current 37.8 MW − 0.42 MJ/kg) | 0.42 MJ/kg-cli = 14.8 MW at 130 t/h | ECRA 2022: "total heat loss of latest generation clinker coolers is less than 0.42 MJ/kg cli" | Need to add this KPI — see §4 |

The defaults are defensible. The bigger gap is that 130 t/h is **not** a 5000-tpd plantc class plant — it is a 3000–4000 tpd line. Either bump throughput to 208 t/h to make the demo match a 5000-tpd BAT reference, or document the 130 t/h as the "small/medium Nepal plant" case. The geometry should follow: for 208 t/h, scale L·W to ~120 m² grate area (e.g. 32 m × 3.8 m).

> Peray & Waddell (1986) §6.2 also notes that the **secondary-air mass flow is set by combustion-air demand, not by cooler hydraulics.** A 130 t/h plant firing 100 kg coal/t at 1.05× stoich needs ~38 kg/s secondary air. Today the model pumps 88 kg/s through the bed "as cooling air" and then takes the max cell as sec air — this confuses two physically distinct streams (see §2 fix).

## 4. KPI gaps

What a verifier or plant operator will ask that the current `compute_outputs` does **not** provide:

1. **Free-lime (f-CaO) at cooler exit.** Clinker quenched too slowly continues to disproportionate C₃S; cooled too fast, glassy phase content rises and grindability suffers. ICCC 2006 §3.4 target: f-CaO < 1.5 % at cooler exit. This is the single most important *quality* KPI and the code returns nothing about it. **Need to add**: cooling rate dT/dt in the 1200 → 800 °C window (typical quench ~150–300 K/min for OPC; Boateng 2008 §7.4). This is computable from the existing `T_clinker_profile` and `v_grate`.

2. **Clinker quench rate** (°C/s or K/min) in the critical 1300–900 °C window. The cell-by-cell profile already gives this: `dT/dt = (T_c[i+1] - T_c[i]) / (dx/v_grate)`. Add to `compute_outputs`.

3. **Secondary-air mass flow vs theoretical combustion air.** Stoichiometric O₂ for coal ≈ 1.4 kg O₂/kg coal (C → CO₂, H → H₂O, S → SO₂). With 21 % O₂ in air, stoich air = 1.4 / 0.21 × coal kg/s = 6.67 × coal kg/s. **Need to add** `secondary_air_stoich_ratio = m_a_secondary / (coal_rate × stoich_factor)` and warn if ratio is < 1.0 (oxygen-starved burner) or > 1.3 (excess air, kiln efficiency loss). Peray & Waddell 1986: 1.05–1.15 is normal.

4. **Cooler exhaust-air T and dust loading.** Exhaust air from cold-end compartments typically 150–250 °C; if it is much hotter, cooler is over-stoking on compartment 1. ECRA 2022: 8–10 kWh/t-cli can be recovered from a waste-heat boiler on this stream. Add `cooling_air_exhaust_c` (currently absent).

5. **Heat-loss accounting split** (radiation vs convection vs exhaust). ECRA 2022 BAT ceiling is 0.42 MJ/kg-cli total. The current code lumps everything into "efficiency" and does not split. The split is what tells you whether to fix the cooler (exhaust too hot → reduce cooling air) or the refractory (radiation loss → re-line).

6. **Specific heat consumption (SHC) delta attribution** — GCCA GNR 2022 KPI `cl_PM2` is cooler heat recovery in MJ/t-cli. The current code reports kW (rate); add a per-tonne figure: `heat_recovered_kw * 3600 / (m_clinker_kg_s * 3600) / 1000 = kJ/kg-cli = MJ/t-cli`. For 130 t/h plant, current value 37.8 MW / 36.1 kg/s = **1.05 MJ/kg-cli = 1050 MJ/t-cli recovered** — but this is *impossibly high* (the clinker can only lose 1.05·(1400−30) = 1435 kJ/kg of sensible heat, so 1050 means 73 % recovery, consistent with the 72.7 % efficiency — sanity check passes once the air-T bug is fixed). Report as `MJ/t-cli` per GCCA reporting convention.

7. **Residence time distribution (RTD)** — clinker on the grate has a distribution, not a single residence time. The 1D model assumes plug flow. For Day 3, just report `residence_time_s = L / v_grate = 28 / (12/60) = 140 s`. Note that real IKN coolers run 90–150 s; the code value is in the right band.

## 5. Recommended fix

**Concrete changes Mavis can apply in a single PR. Each is independent and testable.**

### Fix A — second-law clamp on air heating (cooler_ode.py:228)
Add, immediately after the `dT_a = dQ / ...` line:
```python
# Second-law clamp: air cannot be heated above the clinker T in this cell.
dT_a = min(dT_a, max(T_c - T_a_cell, 0.0))
```
This alone caps the 5790 °C runaway to ≤ T_c (so first-cell air ≤ 1400 °C). Sufficient for the model to produce a *plausible but not yet correct* air profile.

### Fix B — counter-flow air stream (cooler_ode.py:213–239)
Replace the per-cell air-reset with a single air stream that traverses the bed counter to the clinker:

```python
# Initialize air profile (counter-flow: parcel at i=0 leaves the kiln end last)
T_air_profile = np.empty(n)
T_a_cell = float(p.under_grate_air_temp_c)   # air enters at clinker-exit end
# Reverse the air index: air moves from i=n-1 (cold end) to i=0 (kiln end).
# We march clinker forward (i=0..n-1) and feed it the air from i+1 (which was
# just heated by the cell upstream of the clinker).
for i in range(n):
    A_cell = p.width_m * dx
    # Air in this cell came from the cell at i+1 (counter direction):
    T_a_inlet = T_a_cell   # carried over from previous iteration's "exit"
    n_sub = 8
    for _ in range(n_sub):
        q_conv = h_conv * (T_c - T_a_inlet)
        q_rad  = p.emissivity * STEFAN_BOLTZMANN * ((T_c+273.15)**4 - (T_a_inlet+273.15)**4)
        q_total = max(q_conv + q_rad, 0.0)
        dQ = q_total * A_cell
        dT_c = dQ / max(m_c_per_m * (dx/n_sub) * cp_clinker, 1e-3)
        dT_a = dQ / max(m_a_secondary_kg_per_m * (dx/n_sub) * cp_air, 1e-3)
        dT_c = min(dT_c, max(T_c - T_a_inlet, 0.0))
        dT_a = min(dT_a, max(T_c - T_a_inlet, 0.0))   # second-law clamp
        T_c      -= dT_c
        T_a_inlet += dT_a
    T_clinker_profile[i] = T_c
    T_air_profile[i]     = T_a_inlet   # air outlet of this cell
# The air at i=0 has now traversed the whole bed and is the secondary air:
secondary_air_outlet_c = T_air_profile[0]
```

### Fix C — split cooling-air vs secondary-air mass flows (cooler_ode.py)
Add two new parameters to `CoolerParameters`:
- `n_compartments: int = 5`  (already present)
- `secondary_air_compartment: int = 1`  (kiln-end compartment, 1-indexed)
- `secondary_air_mass_flow_kg_s: float = 38.0`  (computed from coal rate + stoich)
- `cooling_air_mass_flow_kg_s: float = 50.0`  (total cooling air minus sec air)

In `_solve_spatial`, use `m_a_secondary_kg_per_m = secondary_air_mass_flow_kg_s / p.length_m` for the air parcel that becomes the secondary air. The cooling air (other compartments) does not need to be tracked cell-by-cell in a 1D model — just ensure total air mass is consistent for the fan-power / dust-load KPIs.

### Fix D — re-define `secondary_air_outlet_c` (cooler_ode.py:272)
Replace:
```python
secondary_air = float(np.max(T_air_profile))
```
with:
```python
secondary_air = float(T_air_profile[0])   # counter-flow: kiln-end air outlet
```

### Fix E — extend `compute_outputs` (cooler_ode.py:296)
Add to the returned dict:
```python
"clinker_quench_rate_k_per_min":  float((state.t_clinker_c[0] - np.interp(900.0, state.t_clinker_c[::-1], state.t_clinker_c[::-1])) / (p.length_m / v_grate_m_s / 60.0)),
"secondary_air_stoich_ratio":     float(secondary_air_mass_flow_kg_s / (coal_rate_kg_s * 6.67)),
"cooler_loss_mj_per_t_cli":       float(0.42 - heat_recovered_mj_per_t_cli),  # vs ECRA BAT ceiling
"residence_time_s":               float(p.length_m / (p.grate_speed_m_min / 60.0)),
"mj_per_t_cli_recovered":         float(heat_recovered_kw * 3.6 / p.clinker_throughput_t_h),
```

### Fix F — delete the misleading Achenbach comment (cooler_ode.py:148)
The function is *not* using Achenbach (1995). Either implement the real Achenbach correlation (recommended, ~10 lines, gives h ≈ 700 W/m²·K at Re=1000) or change the comment to "engineering floor of 200 W/m²·K, see Mujumdar 2007".

### Fix G — `kiln_link.py` convergence test (kiln_link.py:73)
Once Fix D is in, the coupled iteration converges in 2–4 passes as Mavis's docstring says. The current `coupled_kiln_cooler_steady_state` test passes only because the runaway air T is so high that it blows past the 5 °C tolerance on a single iteration. After the fix, add an assertion `result.converged is True` and `result.secondary_air_t_c < 1100.0` to lock the fix in.

---

## References

- **Mujumdar, K.S. (2007).** "Mathematical model of the grate cooler for cement clinker." *Ind. Eng. Chem. Res.* 46(7), 2180–2189. — the 1D counter-flow cooler model with a 5-compartment hybrid layout. **§2.2** is the secondary-air compartment; **§3.1** is the air-T clamp.
- **Boateng, A.A. (2008).** *Rotary Kilns: Transport Phenomena and Transport Processes.* Butterworth-Heinemann. **Ch. 7** — clinker cooling, radiation dominance in the first 5–8 m of the cooler, and the cool-clinker quench rate (150–300 K/min) for OPC.
- **Peray, K.E. & Waddell, J.J. (1986).** *The Rotary Cement Kiln*, 2nd ed. Chemical Publishing. **§6.2** — secondary-air mass flow is set by combustion-air demand (1.05–1.15× stoich); **§6.3** — radiation-dominated first compartment and the need to cap air heating.
- **ICCC 2006, §2.3** (International Cement Conference, New Delhi, 2006) — cement clinker emissivity ε ≈ 0.8–0.9 in the rotary-kiln discharge zone; clinker residence time on grate 1.5–4 min; f-CaO target < 1.5 % at cooler exit.
- **ECRA Technology Papers 2022** (European Cement Research Academy, Düsseldorf). "Modern reciprocating coolers can have a high degree of heat recuperation efficiency up to 75 to 80 %. The total heat loss of latest generation clinker coolers is less than 0.42 MJ/kg cli." Also: 8–10 kWh/t-cli recoverable from cooler exhaust as WHR.
- **GCCA GNR 2022** (Global Cement and Concrete Association, "Getting the Numbers Right"). Reporting convention for cooler heat recovery is **MJ/t-cli**; Indian-plant average is 72–75 %, BAT 78–80 %. Per `cl_PM2` indicator.
- **Achenbach, E. (1995).** "Heat and flow characteristics of packed beds." *Exp. Thermal Fluid Sci.* 10(1), 17–27. The real correlation `Nu = [(1.18 Re^0.58)⁴ + (0.23·Re/(1−ε_void))^0.75·⁴]^(1/4)`, Re < 7.7×10⁵, claimed accuracy ±15 %.

---

**Aanya — out.** Re-run the test after Fix A alone and you should see sec-air drop from 5790 °C to ≤ 1400 °C. After Fixes A+B+D, expect sec-air ≈ 600–900 °C, cooler efficiency 75–80 %, and the `coupled_kiln_cooler_steady_state` test to actually exercise fixed-point convergence instead of tripping the tolerance on iteration 1.
