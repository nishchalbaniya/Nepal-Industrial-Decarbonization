"""
Data quality tier definitions for the cooler MRV module (Day 3 v0.3.1).

> Authored by Dr. Kabita Thapa, env-eng-permitting, 2026-07-22.
> Audience: the verifier (ISO 14064-3:2019, Verra VM0009, Gold Standard TPDDTEC,
> EU CBAM 2023/1773) and the UQ layer (Hiro).

Conventions
-----------
- ``Tier`` follows the IPCC 2006 Vol.1 Ch.3 tier convention, extended with
  ``measured`` for instrument-read activity data. The four values are::

      Tier1   = global default EF (lowest credit weighting)
      Tier2   = country / industry / plant-class EF
      Tier3   = plant-specific engineering estimate (lowest credit weighting,
                 may trigger VCS Program Guide v4.5 §3.4 downgrade)
      measured = plant DCS / instrument direct read (highest credit weighting)

  Vocabulary note: "Tier X" applies to EFs; "measured" is reserved for activity
  data. See ``data_quality_spec.md`` for the per-field rationale and citations.

- ``DataQualityEntry`` carries (tier, source, year, sigma_1) per the GHG
  Protocol Corporate Standard §5.2 and ISO 14064-1:2018 §6.5 data-quality
  principles (relevance, completeness, consistency, accuracy, transparency).

- ``cooler_module_data_quality`` is the per-field mapping that drops into
  ``compute_outputs(...)`` as ``_data_quality: dict[str, DataQualityEntry]``.

Usage
-----
>>> from data_quality_tiers import cooler_module_data_quality, Tier
>>> entry = cooler_module_data_quality["secondary_air_outlet_c"]
>>> entry.tier
<Tier.measured: 'measured'>
>>> entry.sigma_1
20.0

Pydantic compatibility
----------------------
Pydantic v2 supports ``Literal[...]`` enum-style values directly. To use this
mapping as a Pydantic field, wrap it in a ``BaseModel``:

    from pydantic import BaseModel
    from typing import Literal, Optional

    Tier = Literal["Tier1", "Tier2", "Tier3", "measured"]

    class DataQualityEntryModel(BaseModel):
        tier: Tier
        source: str
        year: int
        sigma_1: Optional[float] = None
        sigma_unit: Optional[str] = None
        clause: Optional[str] = None
        note: Optional[str] = None

@Maya: confirm that ``compute_outputs`` is a Pydantic ``BaseModel`` (or convert
the sidecar ``_data_quality`` dict to Pydantic-friendly ``DataQualityEntryModel``
when integrating). The dict form here is round-trip-safe through CSV/JSON/pickle
in Maya's ``io.py``; the Pydantic form is round-trip-safe through Pydantic's
``model_dump_json``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


# ---------------------------------------------------------------------------
# Tier vocabulary
# ---------------------------------------------------------------------------

class Tier(str, Enum):
    """IPCC 2006 Vol.1 Ch.3 tier convention, extended with 'measured'.

    The string value is the canonical form (matches GHG Protocol vocabulary
    and Pydantic ``Literal[...]``).
    """
    Tier1 = "Tier1"
    Tier2 = "Tier2"
    Tier3 = "Tier3"
    measured = "measured"


# ---------------------------------------------------------------------------
# Per-field entry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DataQualityEntry:
    """Per-field data-quality record.

    Attributes
    ----------
    tier : Tier
        IPCC tier (Tier1 / Tier2 / Tier3) for EFs; ``measured`` for activity
        data from plant DCS.
    source : str
        Bibliographic citation or plant-DCS tag. Must be machine-parseable
        for the verifier. Examples::

            "ICCC 2006 §2.3"
            "Peray & Waddell 1986 §6.4"
            "plant_DCS:TICA-2101"        # tag-style for measured
            "EU_2023_1773_Annex_IV_§4"   # for CBAM defaults
    year : int
        Year of the EF / instrument. For ``measured``, year of the data;
        for defaults, year of the publication.
    sigma_1 : Optional[float]
        1-sigma uncertainty in absolute units (e.g. K, %, kg/s). ``None`` for
        categorical fields.
    sigma_unit : Optional[str]
        Unit string for ``sigma_1``. Examples: "K", "%", "kg/s", "t CO2/t cli".
    clause : Optional[str]
        Methodology clause supporting the tier choice. Examples::

            "ISO 14064-1:2018 §6.5"
            "VM0009 v3.0 §5.3.3"
            "IPCC 2006 Vol.3 Ch.2 §2.3.2"
    note : Optional[str]
        Free-text note for the verifier. Use sparingly; cite instead.

    Examples
    --------
    >>> DataQualityEntry(
    ...     tier=Tier.measured,
    ...     source="plant_DCS:TI-2103",
    ...     year=2024,
    ...     sigma_1=20.0,
    ...     sigma_unit="K",
    ...     clause="Peray & Waddell 1986 §6.4",
    ...     note="Type-K TC at kiln-burner air duct",
    ... )
    """
    tier: Tier
    source: str
    year: int
    sigma_1: Optional[float] = None
    sigma_unit: Optional[str] = None
    clause: Optional[str] = None
    note: Optional[str] = None


# ---------------------------------------------------------------------------
# Per-field mapping for the cooler module
# ---------------------------------------------------------------------------

# This is the single source of truth for the per-field tier + 1-sigma + source
# that lands in ``compute_outputs`` as ``_data_quality``. It is the input to
# the ISO 14064-1:2018 §6.5 data-quality assessment and the Verra VM0009 v3.0
# §5.3.3 monitoring parameter table.
#
# Authoritative source: data_quality_spec.md (this PR folder).
# Cite per field; do not paraphrase.

cooler_module_data_quality: Dict[str, DataQualityEntry] = {

    # --- Inputs: measured (plant DCS / instrument) ------------------------

    "clinker_inlet_t_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_kiln_discharge",
        year=2024,                    # plant-year; update on data refresh
        sigma_1=25.0,
        sigma_unit="K",
        clause="ICCC 2006 §2.2",
        note="Kiln-discharge pyrometer, ±25 K 1-sigma at 1400 °C",
    ),

    "clinker_outlet_t_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_cooler_exit",
        year=2024,
        sigma_1=15.0,
        sigma_unit="K",
        clause="ICCC 2006 §3.4",
        note="IR spot pyrometer at cooler exit, ±15 K 1-sigma",
    ),

    "secondary_air_outlet_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_sec_air_to_kiln",
        year=2024,
        sigma_1=20.0,
        sigma_unit="K",
        clause="Peray & Waddell 1986 §6.4",
        note="Type-K TC at kiln-burner air duct, ±20 K 1-sigma at 800 °C",
    ),

    "tertiary_air_outlet_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_ter_air_to_calciner",
        year=2024,
        sigma_1=20.0,
        sigma_unit="K",
        clause="Peray & Waddell 1986 §6.4",
        note="Type-K TC in calciner air line, ±20 K 1-sigma at 600 °C",
    ),

    "exhaust_air_outlet_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_exhaust_plenum",
        year=2024,
        sigma_1=10.0,
        sigma_unit="K",
        clause="Peray & Waddell 1986 §6.4",
        note="TC in cooler exhaust plenum, ±10 K 1-sigma at 200 °C",
    ),

    "under_grate_air_temp_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:TI_undergrate_plenum",
        year=2024,
        sigma_1=2.0,
        sigma_unit="K",
        clause="ISO 14064-1:2018 §6.5",
        note="PT100 RTD in plenum, ±2 K 1-sigma",
    ),

    "under_grate_air_velocity_m_s": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:FT_undergrate_air",
        year=2024,
        sigma_1=10.0,
        sigma_unit="%",
        clause="Peray & Waddell 1986 §6.4",
        note="Annubar / flow nozzle; ±10 % 1-sigma; if no instrument, fall "
             "back to Tier 2 (fan-curve-derived, ±20 %)",
    ),

    "clinker_throughput_t_h": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:WT_clinker",
        year=2024,
        sigma_1=2.0,
        sigma_unit="%",
        clause="ISA RP 31.1",
        note="Belt weighfeeder per ISA 1975, ±2 % 1-sigma of span",
    ),

    "grate_speed_m_min": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:SC_grate_VFD",
        year=2024,
        sigma_1=2.0,
        sigma_unit="%",
        clause="ISO 14064-1:2018 §6.5",
        note="VFD Hz → m/min, encoder feedback, ±2 % 1-sigma",
    ),

    "secondary_air_mass_flow_kg_s": DataQualityEntry(
        tier=Tier.measured,
        source="plant_DCS:FT_sec_air",
        year=2024,
        sigma_1=5.0,
        sigma_unit="%",
        clause="Peray & Waddell 1986 §6.2",
        note="Orifice / annubar on sec-air line, ±5 % 1-sigma",
    ),

    "altitude_m": DataQualityEntry(
        tier=Tier.measured,
        source="plant_met_station",
        year=2024,
        sigma_1=10.0,
        sigma_unit="m",
        clause="ISO 14064-1:2018 §6.5",
        note="GPS / met station; affects air density ±1.2 % at 1400 m",
    ),

    "ambient_t_c": DataQualityEntry(
        tier=Tier.measured,
        source="plant_met_station",
        year=2024,
        sigma_1=1.0,
        sigma_unit="K",
        clause="ISO 14064-1:2018 §6.5",
        note="RTD or calibrated met sensor, ±1 K 1-sigma",
    ),

    "ambient_rh": DataQualityEntry(
        tier=Tier.measured,
        source="plant_met_station",
        year=2024,
        sigma_1=5.0,
        sigma_unit="%RH",
        clause="ISO 14064-1:2018 §6.5",
        note="Capacitive RH sensor, ±5 %RH 1-sigma",
    ),

    # --- Inputs: literature / plant-class (Tier 1 / Tier 2) --------------

    "clinker_diameter_m": DataQualityEntry(
        tier=Tier.Tier2,
        source="ICCC 2006 §2.4",
        year=2006,
        sigma_1=20.0,
        sigma_unit="%",
        clause="ICCC 2006 §2.4",
        note="Sieve analysis; 1-sigma on log-normal pellet-size distribution",
    ),

    "cp_clinker_kj_kg_k": DataQualityEntry(
        tier=Tier.Tier1,
        source="Boateng 2008 Ch.7",
        year=2008,
        sigma_1=5.0,
        sigma_unit="%",
        clause="IPCC 2006 Vol.3 Ch.2 Annex 2.2.1",
        note="Literature default 1.05 kJ/(kg·K); ±5 % 1-sigma covers "
             "composition spread",
    ),

    "rho_clinker_kg_m3": DataQualityEntry(
        tier=Tier.Tier2,
        source="Peray & Waddell 1986 §6.1",
        year=1986,
        sigma_1=10.0,
        sigma_unit="%",
        clause="Peray & Waddell 1986 §6.1",
        note="Loose-packed bulk density, 1500 kg/m³; ±10 % 1-sigma",
    ),

    "emissivity": DataQualityEntry(
        tier=Tier.Tier1,
        source="ICCC 2006 §2.3",
        year=2006,
        sigma_1=10.0,
        sigma_unit="%",
        clause="ICCC 2006 §2.3",
        note="Hot-clinker pellets near-black, default 0.85; ±10 % 1-sigma",
    ),

    "n_compartments": DataQualityEntry(
        tier=Tier.Tier2,
        source="plant_engineering_design",
        year=2024,
        sigma_1=None,
        sigma_unit=None,
        clause="Peray & Waddell 1986 §6.4",
        note="Categorical (integer 4-7); no uncertainty",
    ),

    # --- Outputs: derived (Tier 2 engineering-grade model) ----------------

    "clinker_outlet_c_predicted": DataQualityEntry(
        tier=Tier.Tier2,
        source="Aanya cooler_ode.py model",
        year=2024,
        sigma_1=30.0,
        sigma_unit="K",
        clause="Mujumdar 2007",
        note="Model prediction; ±30 K 1-sigma combined (numerical + parameter)",
    ),

    "secondary_air_outlet_c_predicted": DataQualityEntry(
        tier=Tier.Tier2,
        source="Aanya cooler_ode.py model",
        year=2024,
        sigma_1=50.0,
        sigma_unit="K",
        clause="Mujumdar 2007",
        note="Model prediction; ±50 K 1-sigma (compartment-flow modelling "
             "choice dominates)",
    ),

    "cooler_efficiency": DataQualityEntry(
        tier=Tier.Tier2,
        source="derived: heat_recovered_kw / heat_in_kw",
        year=2024,
        sigma_1=3.0,
        sigma_unit="% absolute",
        clause="ISO 14064-1:2018 §6.5",
        note="Energy-balance ratio; RSS propagation of numerator and "
             "denominator uncertainties",
    ),

    "heat_recovered_kw": DataQualityEntry(
        tier=Tier.Tier2,
        source="derived: m_a * cp_a * dT",
        year=2024,
        sigma_1=5.0,
        sigma_unit="%",
        clause="ISO 14064-1:2018 §6.5",
        note="Air-side heat uptake; depends on measured m_a and Tier-2 dT",
    ),

    "clinker_quench_rate_k_per_min": DataQualityEntry(
        tier=Tier.Tier2,
        source="derived: dT/dt in 1300-900 °C window",
        year=2024,
        sigma_1=10.0,
        sigma_unit="%",
        clause="Ramesh Patch E",
        note="Grate speed ±2 % × outlet T ±30 K → ±10 % conservative",
    ),

    "secondary_air_stoich_ratio": DataQualityEntry(
        tier=Tier.measured,            # ratio of two measured quantities
        source="derived: m_a_sec / (coal_rate * 6.67)",
        year=2024,
        sigma_1=5.0,
        sigma_unit="%",
        clause="Peray & Waddell 1986 §6.2",
        note="Numerator measured ±5 %; denominator coal rate ±2 %; RSS ~5.4 %",
    ),

    "mj_per_t_cli_recovered": DataQualityEntry(
        tier=Tier.Tier2,
        source="derived: heat_recovered_kw * 3.6 / clinker_throughput_t_h",
        year=2024,
        sigma_1=6.0,
        sigma_unit="%",
        clause="GCCA GNR 2022 (cl_PM2)",
        note="RSS of numerator (5 %) and denominator (2 %)",
    ),

    "residence_time_s": DataQualityEntry(
        tier=Tier.measured,            # L (engineering) / v_grate (measured)
        source="derived: L / v_grate",
        year=2024,
        sigma_1=2.0,
        sigma_unit="%",
        clause="Ramesh Patch E",
        note="L is engineering (no uncertainty), v_grate is measured ±2 %",
    ),

    "first_law_imbalance": DataQualityEntry(
        tier=Tier.Tier2,
        source="derived: energy balance residual",
        year=2024,
        sigma_1=None,
        sigma_unit="%",
        clause="ISO 14064-3:2019 §6.4.3",
        note="Diagnostic; not a KPI; should be ≤ 2 % of Q_in per spec",
    ),

    # --- Emission factors (for CBAM embedded-emissions chain) -------------

    "ef_clinker_calcination_t_co2_per_t": DataQualityEntry(
        tier=Tier.Tier1,
        source="IPCC 2006 Vol.3 Ch.2 §2.3.2",
        year=2006,
        sigma_1=5.0,
        sigma_unit="%",
        clause="IPCC 2006 Vol.3 Ch.2 §2.3.2",
        note="Stoichiometric 0.527 t CO2/t clinker; ±5 % 1-sigma covers "
             "CaO-content variation (0.60-0.67 t CaO/t cli)",
    ),

    "ef_calcination_correction_pct": DataQualityEntry(
        tier=Tier.Tier2,
        source="IPCC 2019 Refinement §2.3.1",
        year=2019,
        sigma_1=0.5,
        sigma_unit="% absolute",
        clause="IPCC 2019 Refinement §2.3.1",
        note="CKD / bypass correction; -1 to -2 % typical; ±0.5 % 1-sigma",
    ),

    "ef_cbam_default_clinker_t_co2_per_t": DataQualityEntry(
        tier=Tier.Tier1,
        source="EU 2023/1773 Annex IV §4 (row 2523 10 00)",
        year=2023,
        sigma_1=None,
        sigma_unit=None,
        clause="EU Implementing Reg 2023/1773 Annex IV §4",
        note=(
            "UNVERIFIED 2026-07-22: 0.642 t CO2/t clinker is the cited "
            "direct-emissions default for CBAM cement clinker (CN 2523 "
            "10 00) but the row was not re-verified by the author against "
            "the published Annex IV table before this PR was filed. "
            "Kabita (env-eng) flagged this in DAY-03-NEGOTIATION.md. "
            "Do NOT commit to a Verra VM0009 v3.0 PDD or a CBAM quarterly "
            "XML until James (carbon-markets) re-verifies the row against "
            "the Implementing Regulation 2023/1773 published text. The "
            "IPCC 2006 Vol.3 Ch.2 §2.3.2 stoichiometric default of 0.527 t "
            "CO2/t clinker (with the 2019 Refinement §2.3.1 1-2% downward "
            "CKD/bypass correction) is the safer interim value for any "
            "claim that requires a cite."
        ),
    ),

    "ef_coal_combustion_t_co2_per_t": DataQualityEntry(
        tier=Tier.Tier2,
        source="IPCC 2006 Vol.2 Ch.1 §1.2",
        year=2006,
        sigma_1=5.0,
        sigma_unit="%",
        clause="IPCC 2006 Vol.2 Ch.1 §1.2",
        note="Default coal 2.42 t CO2/t; ±5 % 1-sigma for Nepal mixed coal; "
             "2019 Refinement if plant coal-CV data available",
    ),

    "ef_nepal_grid_t_co2_per_mwh": DataQualityEntry(
        tier=Tier.Tier2,
        source="Nepal Electricity Authority / CEA 2022",
        year=2022,
        sigma_1=20.0,
        sigma_unit="%",
        clause="ISO 14064-1:2018 §6.5",
        note="Nepal grid ~99 % hydro; ~0.05 t CO2/MWh; ±20 % 1-sigma "
             "covers small thermal backup and import-mix uncertainty",
    ),
}


# ---------------------------------------------------------------------------
# Sanity helpers (verifier-facing)
# ---------------------------------------------------------------------------

def fields_above_tier(tier: Tier) -> list[str]:
    """Return fields whose tier is *at or above* the given tier.

    "At or above" in the IPCC sense means *more data-quality-assured*:
    ``measured`` > ``Tier1`` > ``Tier2`` > ``Tier3``.

    Examples
    --------
    >>> fields_above_tier(Tier.measured)
    []  # nothing is above measured
    >>> fields_above_tier(Tier.Tier1)
    ['clinker_inlet_t_c', 'clinker_outlet_t_c', ...]  # all measured fields
    """
    rank = {Tier.Tier3: 0, Tier.Tier2: 1, Tier.Tier1: 2, Tier.measured: 3}
    threshold = rank[tier]
    return [f for f, e in cooler_module_data_quality.items()
            if rank[e.tier] >= threshold and rank[e.tier] < rank[Tier.measured]]


def fields_with_uncertainty() -> list[str]:
    """Return fields that have a 1-sigma declared. For ISO 14064-3:2019 §6.4.3."""
    return [f for f, e in cooler_module_data_quality.items() if e.sigma_1 is not None]


def audit_summary() -> dict:
    """Ver-readable summary of the data-quality distribution.

    Returns a dict with counts per tier and a list of fields lacking
    uncertainty. The verifier expects to see this block in the
    ``compute_outputs`` output or in a separate audit-trail report.
    """
    from collections import Counter
    tier_counts = Counter(e.tier.value for e in cooler_module_data_quality.values())
    missing_uncertainty = [
        f for f, e in cooler_module_data_quality.items()
        if e.sigma_1 is None and e.tier != Tier.Tier3
        # Tier 3 is allowed to have no σ (engineering estimate with no
        # quantitative band), but Tier 1 / Tier 2 / measured all must.
        and f not in {"n_compartments", "ef_cbam_default_clinker_t_co2_per_t"}
    ]
    return {
        "n_fields": len(cooler_module_data_quality),
        "tier_counts": dict(tier_counts),
        "fields_with_uncertainty": fields_with_uncertainty(),
        "fields_missing_uncertainty": missing_uncertainty,
        "framework_cited": [
            "ISO 14064-1:2018 §6.5",
            "IPCC 2006 Vol.1 Ch.3",
            "Verra VM0009 v3.0 §5.3.3",
            "EU CBAM 2023/1773 Annex IV §4",
        ],
    }


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------

__all__ = [
    "Tier",
    "DataQualityEntry",
    "cooler_module_data_quality",
    "fields_above_tier",
    "fields_with_uncertainty",
    "audit_summary",
]
