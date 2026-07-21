# Methodology Notes — nepal_mrv v0.1.0

This document provides the full scientific and accounting basis for the
calculations performed by `nepal_mrv`. It is the kind of document that
should accompany any Verra VCS or Gold Standard project submission.

## 1. System boundaries

The tool implements **cradle-to-gate** accounting for the cement sector and
**gate-to-gate** for the brick sector. Scope 3 emissions (upstream
extraction, transport, end-of-life) are optional and not enabled by default.

## 2. Cement sector

### 2.1 Process emissions (calcination)

**Source:** IPCC 2006 Vol. 3 Ch. 2 Tier 2 mass-balance

The chemical reactions releasing CO₂ in clinker production:
- CaCO₃ → CaO + CO₂ (main, ~525 kg CO₂/t clinker for OPC)
- MgCO₃ → MgO + CO₂ (minor, ~16 kg CO₂/t clinker)

**Equation:**
```
E_process = clinker_t × (frac_CaO × 0.7857 + frac_MgO × 1.092)
```

The stoichiometric coefficients 0.7857 and 1.092 are derived from molecular
weights (CO₂/CaO = 44.01/56.08, CO₂/MgO = 44.01/40.30).

For default OPC clinker (65% CaO, 1.5% MgO), this yields:
```
E_process = 0.65 × 0.7857 + 0.015 × 1.092 = 0.527 t CO₂ / t clinker
```

This matches the IPCC default and global cement industry benchmarks.

### 2.2 Fuel combustion

**Source:** IPCC 2006 Vol. 2 Ch. 1 stationary combustion

**Equation:**
```
E_fuel_i = fuel_t_i × NCV_i × EF_i
```

Where NCV is net calorific value (GJ/t) and EF is CO₂ emission factor (kg CO₂/GJ).

For Nepali bituminous coal (mostly Indian-imported from Jharkhand):
- NCV = 25.5 GJ/t (vs IPCC default 25.8 GJ/t)
- EF = 94.6 kg CO₂/GJ (matches IPCC bituminous default)

### 2.3 Grid electricity (Scope 2)

**Source:** NEA Annual Report 2023/24

**Equation:**
```
E_elec = elec_kWh × grid_EF × 1/(1 - T&D_loss)
```

- `grid_EF` = 0.0256 kg CO₂/kWh (combined margin)
- `T&D_loss` = 22.5% (Nepal system average)

The combined margin is used (per CDM ACM0012), computed as 0.5 × OM + 0.5 × BM:
- OM (operating margin) = 0.0217 kg CO₂/kWh
- BM (build margin) = 0.0295 kg CO₂/kWh

Nepal grid emissions are low because the system is >95% hydropower. They
are not zero because: (a) reservoir hydro has lifecycle emissions, (b) the
system imports power from India during peak hours (mix includes coal), and
(c) fossil peaker plants (diesel) run during dry season.

## 3. Brick sector

### 3.1 Kiln-type-specific coal consumption

**Source:** Field surveys of Nepali kilns; WBCSD / GCCA brick protocol

| Kiln | kg coal / 1000 bricks | Thermal eff. |
|---|---|---|
| Clamp (traditional) | 300 | 40% |
| Hoffman | 155 | 60% |
| Tunnel | 120 | 75% |
| Zigzag | 110 | 70% |
| Vertical shaft | 90 | 80% |

**Equation:**
```
E_brick = N_bricks/1000 × coal_t/1000 × NCV_coal × EF_coal
```

### 3.2 Biomass substitution

Biomass is treated as **biogenic** (carbon-neutral in this accounting, per
IPCC convention). Only the *fossil* component of mixed fuels (e.g. TDF) is
counted.

## 4. Project activity crediting

### 4.1 Verra VCS equation

```
ER_y = (BE_y - PE_y) × (1 - leakage_fraction) × (1 - buffer_pool)
```

Where:
- BE_y = baseline emissions in year y
- PE_y = project emissions in year y
- leakage_fraction = activity-shifting leakage (default 5%)
- buffer_pool = non-permanence risk buffer (default 15%)

### 4.2 Methodologies supported

| Sector | Methodology | Use case |
|---|---|---|
| Cement | Verra VCS AMS-III.H | Alternative fuels / WHR |
| Cement | Verra VCS VM0009 | Cement plant decarbonization |
| Brick | Gold Standard TPDDTEC | Clamp → zigzag |
| Brick | Verra VCS brick | Technology switch |

### 4.3 Additionality test

We apply a conservative test:
- **Cement:** NPV at $15/tCO₂e > 0 AND emission reduction > 5%
- **Brick:** emission reduction > 20% (Gold Standard minimum)

In a real Verra submission, additionality would also include:
- Regulatory test (project is not legally required)
- Common practice test (no other plant has done it)
- Investment analysis (with and without carbon revenue)

These are documented but not yet implemented; the tool is for pre-feasibility
and MRV monitoring, not full PDD generation.

## 5. Sensitivity & uncertainty

For a typical Nepali cement plant, parameter sensitivities (1σ → ΔE):
- Clinker CaO fraction (0.65 ± 0.02) → ±3.0%
- Coal NCV (25.5 ± 1.5 GJ/t) → ±5.9%
- Grid EF (0.0256 ± 0.005 kg/kWh) → ±1.0%
- T&D losses (22.5 ± 2%) → ±0.4%

Combined uncertainty: ~7% at 1σ for the total emissions estimate.

## 6. References

1. IPCC (2006). *2006 IPCC Guidelines for National Greenhouse Gas Inventories.*
   Volume 2, Chapter 1 (Stationary Combustion); Volume 3, Chapter 2 (Mineral Industry).
2. IPCC (2019). *2019 Refinement to the 2006 IPCC Guidelines.*
3. WBCSD / WRI (2017). *GHG Protocol Cement Scope 1+2 Guidance.*
4. GCCA (2022). *Sustainability Framework and Guidelines.*
5. Nepal Electricity Authority (2024). *Annual Report 2023/24.*
6. UNEP / GEF (2014). *Brick Kiln Efficiency Project: Nepal Country Report.*
7. FNCCI / NBSM (2022). *Nepal Brick Sector Survey 2022.*
8. DEFRA (2024). *Conversion Factors for Company Reporting.*
9. ecoinvent (2023). *ecoinvent Database v3.10.*

---

*Author: Nishchal Baniya, Himalayan Carbon Nepal*
*Version: 0.1.0 (Day 1, 2026-07-21)*
