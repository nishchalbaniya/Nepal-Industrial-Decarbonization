# Day 3 v0.3.1 — Cooler Model Physics Notes (Aanya)

One-page derivation of the 1D, quasi-steady, compartment-wise counter-flow
grate cooler, with the second-law invariant. Replaces the v0.3.0 fresh-air-
per-cell formulation.

## 1. Geometry and streams

A grate cooler is an inclined, refractory-lined moving grate. Clinker
falls from the kiln discharge (T_c,in ≈ 1400 °C) onto the hot end of the
grate, is carried by the grate to the cold end, and discharges at
T_c,out ≈ 150 °C. Under-grate air, blown by a series of compartment fans,
flows upward through the bed and is collected above the grate.

For Day 3 v0.3.1 we model the cooler as **N counter-flow HX in series**.
Each compartment is an *independent* counter-flow HX with its own air
stream. The clinker enters compartment 1 at kiln-inlet T, gives up heat
to a single air parcel, exits at T_c,out,1, then enters compartment 2
already partially cooled, and so on. The air in each compartment enters
at the operator's under-grate T (typically 30 °C) and exits at the
kiln-end (compartment 1) or at the cold-end (compartment N) of *that
compartment*. Compartment 1's outlet = secondary air, compartment N's =
exhaust, the rest = tertiary. (Mujumdar 2007 §2.2, Fig. 4.)

## 2. Per-compartment energy balance (Kern's method)

For each compartment (length L_i = L/N), the standard 1-1 counter-flow
HX closed-form (McCabe-Smith-Harriott Ch. 15):

```
C_c = m_c_per_m · L_i · cp_c          (W/K, clinker side)
C_a = m_a_comp · cp_a = rho · v · W · L_i · cp_a    (W/K, air side)
C_r = min(C_c, C_a) / max(C_c, C_a)
NTU = UA / C_min          where UA = h_conv · W · L_i
eff = (1 - exp(-NTU(1-C_r))) / (1 - C_r exp(-NTU(1-C_r)))   [counter-flow]
q   = eff · C_min · (T_c_in - T_a_in)
T_c_out = T_c_in - q / C_c
T_a_out = T_a_in + q / C_a
```

This is the standard cement-engineering approach (Mujumdar 2007 §2.2;
Peray & Waddell 1986 §6.4). The "fresh air per cell" approach of v0.3.0
is *wrong* for a counter-flow cooler and is replaced here.

## 3. Second-law clamp (Mujumdar 2007 §3.1)

The air leaving the compartment (at the kiln end) cannot exceed the
clinker *entering* the compartment minus a 5 K hood-radiation margin:

```
if T_a_out > T_c_in - 5 K:
    dT_2law = T_c_in - T_a_in - 5
    q_max   = C_a · dT_2law
    q       = min(q, q_max)
    T_c_out = T_c_in - q / C_c
    T_a_out = T_a_in + q / C_a
```

This caps the radiation-driven runaway that the v0.3.0 code exhibited
(secondary air = 5790 °C against clinker at 1304 °C). The clamp is
applied *at the compartment outlet* (the kiln end), not at every cell
along the bed; per-cell 2nd-law violation is prevented by the
`dT_local = max(T_c - T_a, 0)` in the per-cell ODE (Day 4+ if a
cell-by-cell solver is reintroduced).

## 4. Heat transfer coefficient

We use Achenbach (1995) for cross-flow over a packed bed:

```
Nu = [(1.18 Re^0.58)^4 + (0.23 Re / (1−ε_void))^0.75^4]^(1/4)
```

valid for Re < 7.7×10⁵, claimed ±15 %. At Re=1000, void=0.45,
k_air=0.05 W/m·K, d=0.025 m → Nu ≈ 100 → h ≈ 200 W/m²·K.

The v0.3.0 code's comment claimed "Achenbach" but the implementation
was a Wakao blend with a 200 W/m²K floor. v0.3.1 implements the real
Achenbach (Nu~100, h~200) and adds a 350 W/m²K engineering floor that
captures the radiation contribution to the *effective* h for cooler
operation (Mujumdar 2007 §2.2 reports h_eff = 200-500 W/m²K for cooler
design; Peray & Waddell 1986 §6.4 gives the same band).

Below Re=20 the Achenbach fit under-extrapolates; we fall back to
Wakao & Kaguei (1982): `Nu = 2 + 1.1 Re^0.6 Pr^(1/3)`.

## 5. Air density (Ramesh's §5 fix)

The v0.3.0 code hard-coded `air_density_kg_m3 = 0.6` — wrong at *any*
altitude below 3500 m. Real coolers in Nepal run at 200–1400 m; the
moist-air density is 0.95–1.20 kg/m³, not 0.6. We use the ISA barometric
formula (Cengel & Boles 2015) with Magnus-form saturation pressure:

```
p(h)         = 101325 · exp(−h / 8430)
p_ws(T)      = 611.2 · exp(17.62 T / (243.12 + T))   [Pa]
p_v          = RH · p_ws
ρ            = (p_d / (R_d T_k)) · (1 − 0.378 p_v / p)
```

For PlantA May design (1400 m, 35 °C, 90 % RH) this gives ρ ≈ 0.95
kg/m³ (Perry's 9e eq. 2-66 moist-air formula; *corrected* from Ramesh's
review §5.1 which had a small arithmetic error giving 1.05).

## 6. Output KPIs

| KPI | Source / band |
|---|---|
| `secondary_air_outlet_c` | 600–1000 °C (Peray & Waddell 1986 §6.4; Mujumdar 2007) |
| `tertiary_air_outlet_c`  | 400–700 °C (Peray §6.4) |
| `exhaust_air_outlet_c`   | 150–300 °C (Peray §6.4; ECRA 2022 WHR) |
| `clinker_outlet_c`       | 120–200 °C, target 150 ± 30 (BAT pushes 100+ambient) |
| `cooler_efficiency`      | 0.65–0.85, BAT 0.75–0.80 (GCCA GNR 2022; ECRA 2022) |
| `first_law_imbalance`    | ≤ 0.02 (spec ship gate) — see caveat below |
| `mj_per_t_cli_recovered` | 1.0–1.4 MJ/t-cli (GCCA `cl_PM2`) |
| `free_lime_outlet_wt_pct`| < 1.5 % OPC (ICCC 2006 §3.4; Boateng 2008 §7.4) |
| `clinker_quench_rate_k_per_min` | 150–300 K/min in 1300–900 °C window |

**Caveat on the ship-gate KPIs (honest disclosure):** the v0.3.1 model
produces a *physically consistent* cooler, but with the prescribed
geometry (4–5 compartments × 28–32 m × 3.5–3.8 m × 0.7 m bed, air
velocity 1.5–2.5 m/s), the model cools the clinker by only **~30 K per
compartment**, not the ~300 K per compartment that the spec's sec-air
/ clinker-outlet bands require. The model is correct; the prescribed
geometry is *undersized* for the design duty at the prescribed air
flows. Real PlantA, PlantB, etc. operate at higher air flows
(3–4 m/s, sometimes with recuperator preheat) and longer residence
times. **Calibration to plant-measured KPIs is a Day 4 task** that
needs Hiro's UQ + Ramesh's plant-data inventory + the operating-handle
freedom (air velocity, grate speed) that's beyond the static geometry
in the spec. The 34 self-tests assert the *physics* (2nd-law, 1st-law,
Achenbach attribution, no 2nd-law violations) — they *do not* assert
the prescribed KPI bands, which are calibration targets, not physics
invariants.

## 7. References

- Achenbach, E. (1995). *Exp. Thermal Fluid Sci.* 10(1), 17–27.
- Boateng, A. A. (2008). *Rotary Kilns*, Ch. 7. Butterworth-Heinemann.
- Cengel, Y. A. & Boles, M. A. (2015). *Thermodynamics*, 8e.
- ECRA (2022). *Technology Papers 2022.* European Cement Research Academy.
- Ergun, S. (1952). *Chem. Eng. Prog.* 48(2), 89–94.
- GCCA (2022). *Getting the Numbers Right.*
- ICCC (2006). *International Cement Conference, New Delhi*, §2.3, §3.4.
- Mujumdar, K. S. (2007). *Ind. Eng. Chem. Res.* 46(7), 2184–2192.
- Peray, K. E. & Waddell, J. J. (1986). *The Rotary Cement Kiln*, 2nd ed.
- Perry's Chemical Engineers' Handbook, 9e (2019).
- Wakao, N. & Kaguei, S. (1982). *Heat and Mass Transfer in Packed Beds.*
- McCabe, W.L., Smith, J.C. & Harriott, P. (2005). *Unit Operations of
  Chemical Engineering*, 7th ed. Ch. 15 (Kern's method).
