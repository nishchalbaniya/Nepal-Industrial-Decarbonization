"""
Methodology — page 5
"""
import streamlit as st

st.set_page_config(page_title="Methodology", page_icon="📘", layout="wide")

st.title("📘 Methodology — How the calculations work")

st.markdown("""
## 1. Cement sector

### 1.1 Clinker process emissions (IPCC 2006 Vol.3 Ch.2 Tier 2)

The process CO₂ from clinker calcination is calculated using the mass-balance
approach, with default and kiln-specific CaO/MgO fractions:

```
E_process = clinker_t * (CaO_frac * 0.7857 + MgO_frac * 1.092)
```

Where:
- `0.7857` = stoichiometric mass of CO₂ per mass of CaO (CaCO₃ → CaO + CO₂)
- `1.092` = stoichiometric mass of CO₂ per mass of MgO (MgCO₃ → MgO + CO₂)

For typical OPC clinker (65% CaO, 1.5% MgO), this yields ~0.527 tCO₂/t clinker,
matching IPCC's default value.

### 1.2 Fuel combustion (IPCC 2006 Vol.2 Ch.1)

```
E_fuel_i = fuel_t_i * NCV_GJ_t * EF_kgCO2_GJ
```

Fuel-specific NCV and emission factors are from IPCC defaults, calibrated for
Nepali coal (mostly Indian bituminous from Dhansiri/Jharkhand coalfields).

### 1.3 Grid electricity (Scope 2)

```
E_elec = elec_kWh * grid_EF * (1 / (1 - T&D_loss))
```

- `grid_EF` = 0.0256 kg CO₂/kWh (NEA 2023/24 combined margin)
- `T&D_loss` = 22.5% (Nepal system average)

### 1.4 Benchmarking

| Benchmark | kg CO₂/t cement | Source |
|---|---|---|
| Global BAT | 700 | GCCA 2022 / WBCSD CSI |
| Nepal avg | 950 | Industry survey 2023 |

---

## 2. Brick sector

### 2.1 Kiln-type-specific approach

Per-1000-bricks coal consumption is taken from kiln-specific field data,
cross-validated against WBCSD/GCCA brick protocol:

| Kiln | Coal (t/1000) | Thermal eff. |
|---|---|---|
| Clamp (traditional) | 0.30 | 40% |
| Hoffman | 0.155 | 60% |
| Tunnel | 0.12 | 75% |
| Zigzag | 0.11 | 70% |
| Vertical shaft | 0.09 | 80% |

### 2.2 Emission factors

```
E_brick = (N_bricks/1000) * coal_t_1000 * NCV * EF
```

For biomass substitution (project case), the substituted fuel mass is treated
as biogenic (carbon-neutral under IPCC accounting). Only the residual coal
contributes to Scope 1.

---

## 3. Project activity (Verra VCS / Gold Standard)

The standard crediting equation:

```
ER = (BE - PE) * (1 - leakage) * (1 - buffer)
```

Where:
- **BE** = baseline emissions (no project)
- **PE** = project emissions (with technology change)
- **leakage** = activity-shifting leakage (default 5%)
- **buffer** = Verra non-permanence buffer (15% default)

### 3.1 Methodologies supported

| Sector | Methodology | Use case |
|---|---|---|
| Cement | Verra VCS AMS-III.H | Alternative fuels / WHR |
| Cement | Verra VCS VM0009 | Cement plant decarbonization |
| Brick | Gold Standard TPDDTEC | Clamp → zigzag |
| Brick | Verra VCS brick | Technology switch |

### 3.2 Additionality

- **Cement:** positive NPV at $15/tCO₂e + ≥5% emission reduction
- **Brick:** ≥20% emission reduction (Gold Standard minimum)

### 3.3 Revenue

```
NPV = sum over y in 1..T of (ER_y * price) / (1 + r)^y
```

At $15, $30, $50/tCO₂e sensitivity.

---

## 4. Data sources

- **IPCC 2006 Guidelines for National GHG Inventories, Vol. 2 Ch. 1** (stationary combustion)
- **IPCC 2006 Vol. 3 Ch. 2** (mineral industry)
- **IPCC 2019 Refinement**
- **GHG Protocol Cement Scope 1+2 Guidance** (WRI 2017)
- **GCCA Sustainability Framework** (2022)
- **NEA Annual Report 2023/24** (Nepal grid EF)
- **DEFRA Conversion Factors 2024** (cross-check)
- **ecoinvent v3.10** (LCA background)
- **Field surveys** of Nepali plants: Hetauda, Udayapur, Hongshi, Ghorahi, etc.

---

## 5. Limitations

- Real plant data should be obtained for final MRV submission. This tool uses
  representative values.
- Cement transport / Scope 3 is not the default. Add if required.
- Brick sector data are aggregate; kiln-specific surveys recommended.
- Carbon credit issuance requires third-party validation; this tool produces
  pre-validation estimates only.

---

## 6. License

- Code: MIT
- Data: CC-BY-4.0
- Documentation: CC-BY-4.0

© 2026 Nishchal Baniya · Himalayan Space Solutions
""")
