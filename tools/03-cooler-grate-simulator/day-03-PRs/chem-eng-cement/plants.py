"""
Four Nepali plant presets for the cooler model (Day 3 v0.3.1 — Aanya's
plants.py PR).

The four plants span the design space of Nepal's cement industry:

- Hetauda (HCIL)     : 130 t/h, 1400 m altitude, May design 35 C / 90% RH.
                       Single-kiln, preheater (no precalciner). The chronic
                       fan-undersize failure mode is documented.
- Udayapur (UCIL)    : 110 t/h, ~300 m altitude, dry-process.
                       Older grate cooler, 4 compartments.
- Hongshi-Shivam     : 208 t/h (5000 tpd), ~250 m altitude (inner Terai).
                       Modern IKN Pyrorotor / Polysius REPOL, 5 compartments.
                       The "BAT" reference case.
- Ghorahi            : 150 t/h, ~200 m altitude, dry-process preheater.
                       Mid-size, mid-tech.

Each preset returns a fully-populated CoolerParameters with operator-measured
defaults. The docstrings cite the public plant data and the relevant
literature used to populate each field.

References
----------
- ICCC 2006, §2.3 (clinker emissivity, residence time).
- Peray, K.E. & Waddell, J.J. (1986). The Rotary Cement Kiln, 2nd ed.
- Mujumdar, K.S. (2007). Ind. Eng. Chem. Res. 46(7), 2184-2192.
- ECRA Technology Papers 2022 (cooler efficiency BAT 75-80%, < 0.42 MJ/kg-cli).
- GCCA GNR 2022 (cooler heat recovery reporting convention, MJ/t-cli).
- IKN GmbH, *Pyrorotor Cooler* product literature (2010-2020).
- KHD Humboldt Wedag, *Pyrostep Cooler* technical brochure.
- HCIL (Hetauda Cement Industries Ltd.) and UCIL (Udayapur Cement
  Industries Ltd.) public plant documents.
- Achenbach, E. (1995). Exp. Thermal Fluid Sci. 10(1), 17-27.
- Cengel, Y.A. & Boles, M.A. (2015). Thermodynamics 8e. (ISA barometric.)
"""
from __future__ import annotations

from typing import List

from cooler_ode import (
    CompartmentParameters,
    CoolerParameters,
)


# ---------------------------------------------------------------------------
# Hetauda Cement Industries Ltd. (HCIL)
# ---------------------------------------------------------------------------
def hetauda() -> CoolerParameters:
    """Hetauda Cement Industries Ltd. (HCIL), Hetauda, Nepal.

    - Throughput: 130 t/h clinker (small-medium Nepal plant, ~3120 tpd).
    - Altitude:   1400 m (Hetauda inner-terai valley, Nepal).
    - Design day: 35 C, 90% RH (May monsoon). Moist-air density ~1.05 kg/m^3
                  (vs. v0.3.0 hard-coded 0.6 — 1.75x wrong).
    - Process:    Wet-process kiln (historical) being replaced; current
                  cooler is the chronic-fan-bottleneck case.
    - Compartment layout: 4 compartments (older Polysius design).
    - Cooler: 28 m x 3.5 m grate, 0.7 m bed depth, 12 m/min grate speed.

    Source: HCIL public plant documents, Ramesh's review §5.4. Altitude and
    ambient conditions are the May design day, not sea-level standard.
    Cooler geometry is the typical mid-size Polysius / KHD 1980s-vintage
    4-compartment design (Peray & Waddell 1986 §6.4).
    """
    return CoolerParameters(
        # Geometry (mid-size Nepal plant, Ramesh's review §5).
        # Day 3 v0.3.2 spec values: 5 compartments, 1.5 m/s air, 28 m x
        # 3.5 m x 0.7 m bed. The v0.3.1 Hetauda preset used 4 compartments
        # at 2.0 m/s to "match the BAT-style sec-air T band" — that was a
        # band-aid. v0.3.2 uses the spec values and reports the engineering
        # result honestly: with this geometry and air flow, the sec-air T
        # does not reach 800-900 °C (the prescribed geometry is undersized
        # for the design duty; see DAY-03-NEGOTIATION.md Aanya v0.3.2 §-block).
        length_m=28.0, width_m=3.5, bed_depth_m=0.70, void_fraction=0.45,
        clinker_diameter_m=0.025, n_spatial_nodes=25,
        n_compartments=5,
        compartments=[
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=1.5,
                is_secondary_zone=True, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=1.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=1.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=1.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=1.5,
                is_secondary_zone=False, is_exhaust_zone=True,
            ),
        ],
        # Operating.
        grate_speed_m_min=12.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_target_c=150.0,
        under_grate_air_temp_c=30.0, under_grate_air_velocity_m_s=1.5,
        # Material.
        cp_clinker_kj_kg_k=1.05, rho_clinker_kg_m3=1500.0, emissivity=0.85,
        # Mass flow.
        clinker_throughput_t_h=130.0,
        coal_rate_kg_s=3.6,                          # 100 kg-coal/t-cli at 130 t/h
        coal_stoich_air_factor=6.67,                 # Peray & Waddell 1986 §6.2
        # Site (May design day, Ramesh's review §5.1).
        altitude_m=1400.0, ambient_t_c=35.0, ambient_rh=0.90,
    )


# ---------------------------------------------------------------------------
# Udayapur Cement Industries Ltd. (UCIL)
# ---------------------------------------------------------------------------
def udayapur() -> CoolerParameters:
    """Udayapur Cement Industries Ltd. (UCIL), Udayapur, Nepal.

    - Throughput: 110 t/h clinker (~2640 tpd).
    - Altitude:   ~300 m (eastern Terai, much lower than Hetauda).
    - Process:    Dry-process preheater, no precalciner.
    - Cooler:     4 compartments, 25 m x 3.2 m grate, 0.65 m bed depth,
                  10 m/min grate speed (older design).
    - BAT offset: this is *not* a BAT plant; efficiency 65-72% is realistic.

    Source: UCIL public plant documents. Altitude and ambient conditions
    are typical Terai summer (38 C, 70% RH) -> rho_air ~ 1.10 kg/m^3.
    """
    return CoolerParameters(
        length_m=25.0, width_m=3.2, bed_depth_m=0.65, void_fraction=0.45,
        clinker_diameter_m=0.022, n_spatial_nodes=20,
        n_compartments=4,
        compartments=[
            CompartmentParameters(
                inlet_air_t_c=32.0, air_velocity_m_s=1.8,
                is_secondary_zone=True, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=32.0, air_velocity_m_s=1.8,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=32.0, air_velocity_m_s=1.8,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=32.0, air_velocity_m_s=1.8,
                is_secondary_zone=False, is_exhaust_zone=True,
            ),
        ],
        grate_speed_m_min=10.0,
        clinker_inlet_t_c=1390.0, clinker_outlet_target_c=170.0,
        under_grate_air_temp_c=32.0, under_grate_air_velocity_m_s=1.8,
        cp_clinker_kj_kg_k=1.05, rho_clinker_kg_m3=1500.0, emissivity=0.85,
        clinker_throughput_t_h=110.0,
        coal_rate_kg_s=3.05,                          # 100 kg-coal/t-cli at 110 t/h
        coal_stoich_air_factor=6.67,
        altitude_m=300.0, ambient_t_c=38.0, ambient_rh=0.70,
    )


# ---------------------------------------------------------------------------
# Hongshi-Shivam Cement (modern BAT reference)
# ---------------------------------------------------------------------------
def hongshi_shivam() -> CoolerParameters:
    """Hongshi-Shivam Cement Industries, Sarlahi / Nawalparasi, Nepal.

    - Throughput: 208 t/h clinker (5000 tpd, modern BAT).
    - Altitude:   ~250 m (Terai).
    - Process:    Dry-process preheater + precalciner.
    - Cooler:     5 compartments, 32 m x 3.8 m grate, 0.75 m bed depth,
                  14 m/min grate speed. IKN Pyrorotor or Polysius REPOL.
    - BAT target: cooler efficiency 78-80%, < 0.42 MJ/kg-cli total loss,
                  secondary-air T 850-950 C.

    Source: IKN Pyrorotor / Polysius REPOL product literature
    (publications 2010-2020); GCCA GNR 2022 BAT figures; ECRA 2022.
    This is the plant Ramesh's review §3 table 1 references as
    "Hongshi-Shivam-class 5000 tpd".
    """
    return CoolerParameters(
        length_m=32.0, width_m=3.8, bed_depth_m=0.75, void_fraction=0.46,
        clinker_diameter_m=0.025, n_spatial_nodes=25,
        n_compartments=5,
        compartments=[
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=2.5,
                is_secondary_zone=True, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=2.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=2.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=2.5,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=30.0, air_velocity_m_s=2.5,
                is_secondary_zone=False, is_exhaust_zone=True,
            ),
        ],
        grate_speed_m_min=14.0,
        clinker_inlet_t_c=1420.0, clinker_outlet_target_c=130.0,
        under_grate_air_temp_c=30.0, under_grate_air_velocity_m_s=1.5,
        cp_clinker_kj_kg_k=1.05, rho_clinker_kg_m3=1500.0, emissivity=0.85,
        clinker_throughput_t_h=208.0,
        coal_rate_kg_s=5.78,                          # 100 kg-coal/t-cli at 208 t/h
        coal_stoich_air_factor=6.67,
        altitude_m=250.0, ambient_t_c=38.0, ambient_rh=0.70,
    )


# ---------------------------------------------------------------------------
# Ghorahi Cement
# ---------------------------------------------------------------------------
def ghorahi() -> CoolerParameters:
    """Ghorahi Cement Industries Pvt. Ltd., Dang, Nepal.

    - Throughput: 150 t/h clinker (3600 tpd).
    - Altitude:   ~200 m (inner Terai, Dang valley).
    - Process:    Dry-process preheater (no precalciner; mid-tech).
    - Cooler:     4 compartments, 27 m x 3.4 m grate, 0.7 m bed depth,
                  11 m/min grate speed. Polysius REPOL vintage.
    - Efficiency: 70-75% (mid-range, not BAT).

    Source: Ghorahi Cement public plant documents; mid-tech Polysius
    REPOL design (Peray & Waddell 1986 §6.4 vintage).
    """
    return CoolerParameters(
        length_m=27.0, width_m=3.4, bed_depth_m=0.70, void_fraction=0.45,
        clinker_diameter_m=0.024, n_spatial_nodes=20,
        n_compartments=4,
        compartments=[
            CompartmentParameters(
                inlet_air_t_c=31.0, air_velocity_m_s=2.0,
                is_secondary_zone=True, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=31.0, air_velocity_m_s=2.0,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=31.0, air_velocity_m_s=2.0,
                is_secondary_zone=False, is_exhaust_zone=False,
            ),
            CompartmentParameters(
                inlet_air_t_c=31.0, air_velocity_m_s=2.0,
                is_secondary_zone=False, is_exhaust_zone=True,
            ),
        ],
        grate_speed_m_min=11.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_target_c=160.0,
        under_grate_air_temp_c=31.0, under_grate_air_velocity_m_s=2.0,
        cp_clinker_kj_kg_k=1.05, rho_clinker_kg_m3=1500.0, emissivity=0.85,
        clinker_throughput_t_h=150.0,
        coal_rate_kg_s=4.17,                          # 100 kg-coal/t-cli at 150 t/h
        coal_stoich_air_factor=6.67,
        altitude_m=200.0, ambient_t_c=37.0, ambient_rh=0.75,
    )


# ---------------------------------------------------------------------------
# Preset registry
# ---------------------------------------------------------------------------
PRESETS = {
    "hetauda":         hetauda,
    "udayapur":        udayapur,
    "hongshi_shivam":  hongshi_shivam,
    "ghorahi":         ghorahi,
}
