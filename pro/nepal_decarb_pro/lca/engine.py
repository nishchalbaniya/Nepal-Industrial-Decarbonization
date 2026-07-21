"""
LCA engine — cradle-to-gate for cement and brick, with multiple impact categories.

Implements:
  - Foreground: clinker, raw materials, fuels, electricity, transport
  - Background: ecoinvent v3.10 (simulated for offline operation)
  - Allocation: by mass (default) or economic (optional)
  - 6 impact categories: GWP100, AP, EP, POCP, ADP, HTP
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from nepal_decarb_pro.core.cement import CementPlant, CementEmissionsResult
from nepal_decarb_pro.core.brick import BrickKiln, BrickEmissionsResult
from nepal_decarb_pro.core.factors import EmissionFactors
from nepal_decarb_pro.lca.characterization import (
    CharacterizationFactors,
    get_cf,
    list_categories,
    IMPACT_CATEGORIES,
    SUBSTANCE_EF_PER_FUEL,
)


# Background data — units are t CO2-eq per unit (per kg material, per kWh, per tkm)
# Values are simplified ecoinvent v3.10 proxies.
BACKGROUND_PER_MATERIAL = {
    # Per kg material (kg CO2-eq/kg, written as fraction to keep dimensional consistency
    # in t CO2-eq per t cement when multiplied by tonnes)
    "limestone":  {"GWP100": 0.000029, "AP": 0.00000016, "EP": 0.00000002, "POCP": 0.00000001, "ADP": 0.0000001, "HTP": 0.000011},
    "clay":       {"GWP100": 0.000025, "AP": 0.00000014, "EP": 0.00000002, "POCP": 0.00000001, "ADP": 0.00000005, "HTP": 0.000008},
    "iron_ore":   {"GWP100": 0.000022, "AP": 0.00000012, "EP": 0.00000002, "POCP": 0.00000001, "ADP": 0.0000001, "HTP": 0.000010},
    "gypsum":     {"GWP100": 0.000020, "AP": 0.00000012, "EP": 0.00000002, "POCP": 0.00000001, "ADP": 0.00000008, "HTP": 0.000009},
    "coal":       {"GWP100": 0.00018,  "AP": 0.000001,   "EP": 0.0000001,  "POCP": 0.00000005, "ADP": 0.0000042, "HTP": 0.00004},
    "petcoke":    {"GWP100": 0.00032,  "AP": 0.0000014,  "EP": 0.0000001,  "POCP": 0.00000005, "ADP": 0.0000035, "HTP": 0.00005},
    "natural_gas":{"GWP100": 0.00055,  "AP": 0.0000006,  "EP": 0.00000005, "POCP": 0.00000003, "ADP": 0.000003,  "HTP": 0.00003},
    "biomass":    {"GWP100": 0.00003,  "AP": 0.0000003,  "EP": 0.00000005, "POCP": 0.00000001, "ADP": 0.0000002, "HTP": 0.000005},
    "diesel":     {"GWP100": 0.00045,  "AP": 0.0000013,  "EP": 0.0000001,  "POCP": 0.00000008, "ADP": 0.000003,  "HTP": 0.00004},
    # Per kWh (t CO2-eq / kWh)
    "electricity_NP": {"GWP100": 0.0000256, "AP": 0.00000008, "EP": 0.00000001, "POCP": 0.000000005, "ADP": 0.0000005, "HTP": 0.000008},
    # Per tkm (t CO2-eq per tonne-km)
    "transport_tkm":  {"GWP100": 0.000062,  "AP": 0.0000001,  "EP": 0.00000002, "POCP": 0.00000003, "ADP": 0.0000003, "HTP": 0.000015},
}


class LCAResult(BaseModel):
    """LCA result for one product system."""
    functional_unit: str
    product: str
    # Per-category impacts
    impacts: Dict[str, float]            # {category: kg-eq per functional unit}
    # Per-stage contributions
    stage_contributions: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    # Total
    total_impact_score: float
    # Normalization
    normalized: Dict[str, float] = Field(default_factory=dict)
    # Single score (if weighted)
    weighted_score: Optional[float] = None
    # Method
    method: str
    allocation: str
    boundary: str


def lca_cement(
    plant: CementPlant,
    ef: EmissionFactors,
    cement_type: str = "OPC",
    allocation: str = "mass",
    cf: Optional[CharacterizationFactors] = None,
    functional_unit: str = "1 tonne cement",
) -> LCAResult:
    """
    Cradle-to-gate LCA of a cement product.
    """
    if cf is None:
        cf = get_cf()
    cu = cf.factors

    # Material flows per tonne cement (typical for OPC)
    # 0.95 t clinker + 0.05 t gypsum + limestone for kiln + small other
    clinker_per_cement = plant.clinker_to_cement_ratio
    if allocation == "mass":
        limestone_per_cement = 1.55 * clinker_per_cement
        clay_per_cement = 0.05 * clinker_per_cement
        iron_ore_per_cement = 0.03 * clinker_per_cement
        gypsum_per_cement = (1.0 - clinker_per_cement)
    else:
        # Economic allocation (use placeholder ratios)
        limestone_per_cement = 1.55 * clinker_per_cement
        clay_per_cement = 0.05 * clinker_per_cement
        iron_ore_per_cement = 0.03 * clinker_per_cement
        gypsum_per_cement = (1.0 - clinker_per_cement)

    # Per-tonne-cement fuel use
    fuel_per_cement: Dict[str, float] = {}
    for fu in plant.fuel_use:
        per_t = fu.consumption_t / plant.cement_production_t
        fuel_per_cement[fu.fuel_name] = per_t

    elec_per_cement = plant.electricity_consumption_kwh / plant.cement_production_t
    elec_net = max(elec_per_cement - plant.whr_generation_kwh / plant.cement_production_t, 0)

    # Transport
    transport_per_cement = plant.transport_tkm / plant.cement_production_t

    # ---- Compute impacts ----
    impacts: Dict[str, float] = {cat: 0.0 for cat in list_categories()}
    stage_contributions: Dict[str, Dict[str, float]] = {
        "raw_materials": {cat: 0.0 for cat in list_categories()},
        "fuel_combustion": {cat: 0.0 for cat in list_categories()},
        "electricity": {cat: 0.0 for cat in list_categories()},
        "transport": {cat: 0.0 for cat in list_categories()},
        "process_emissions": {cat: 0.0 for cat in list_categories()},
    }

    # Process emissions (calcination) — only GWP100
    process_co2 = (
        (plant.cao_fraction_clinker or ef.clinker_chemistry.cao) * 0.7857
        + (plant.mgo_fraction_clinker or ef.clinker_chemistry.mgo) * 1.092
    ) * clinker_per_cement
    impacts["GWP100"] += process_co2
    stage_contributions["process_emissions"]["GWP100"] += process_co2

    # Raw materials
    for mat, qty in [
        ("limestone", limestone_per_cement),
        ("clay", clay_per_cement),
        ("iron_ore", iron_ore_per_cement),
        ("gypsum", gypsum_per_cement),
    ]:
        for cat, val in BACKGROUND_PER_MATERIAL[mat].items():
            contrib = qty * val
            impacts[cat] += contrib
            stage_contributions["raw_materials"][cat] += contrib

    # Fuel combustion (foreground: CO2 + CO + NOx + SO2 + PM + NMVOC + CH4)
    for fname, qty in fuel_per_cement.items():
        if fname in SUBSTANCE_EF_PER_FUEL:
            for subst, ef_subst_kg in SUBSTANCE_EF_PER_FUEL[fname].items():
                for cat in list_categories():
                    if subst in cu and cat in cu.get(subst, {}):
                        val = cu[subst][cat] * ef_subst_kg * qty
                        impacts[cat] += val
                        stage_contributions["fuel_combustion"][cat] += val
        # Background (extraction)
        bg_key = "biomass" if "biomass" in fname else (
            "petcoke" if "petcoke" in fname else (
                "natural_gas" if "natural_gas" in fname or "lpg" in fname else (
                    "diesel" if "diesel" in fname else "coal"
                )
            )
        )
        for cat, val in BACKGROUND_PER_MATERIAL[bg_key].items():
            contrib = qty * val
            impacts[cat] += contrib
            stage_contributions["fuel_combustion"][cat] += contrib

    # Electricity
    for cat, val in BACKGROUND_PER_MATERIAL["electricity_NP"].items():
        contrib = elec_net * val
        impacts[cat] += contrib
        stage_contributions["electricity"][cat] += contrib

    # Transport
    for cat, val in BACKGROUND_PER_MATERIAL["transport_tkm"].items():
        contrib = transport_per_cement * val
        impacts[cat] += contrib
        stage_contributions["transport"][cat] += contrib

    # Normalization (per-capita global averages, person-eq)
    # Per person per year reference values (rough)
    person_eq_per_yr = {
        "GWP100": 4700,         # kg CO2-eq/person/yr (2020 global avg)
        "AP": 56,               # kg SO2-eq
        "EP": 13,               # kg PO4-eq
        "POCP": 17.5,           # kg C2H4-eq
        "ADP": 75,              # kg Sb-eq
        "HTP": 470,             # kg 1,4-DCB-eq
    }
    normalized = {
        cat: impacts[cat] / person_eq_per_yr[cat] for cat in impacts
    }

    # Single score (simple equal weighting for now)
    weights = {cat: 1.0 / len(impacts) for cat in impacts}
    weighted = sum(impacts[cat] * weights[cat] for cat in impacts)

    return LCAResult(
        functional_unit=functional_unit,
        product=f"{cement_type} cement from {plant.name}",
        impacts={k: round(v, 4) for k, v in impacts.items()},
        stage_contributions={
            stage: {cat: round(v, 4) for cat, v in cats.items()}
            for stage, cats in stage_contributions.items()
        },
        total_impact_score=round(sum(impacts.values()), 4),
        normalized={k: round(v, 6) for k, v in normalized.items()},
        weighted_score=round(weighted, 4),
        method="CML 2001 + IPCC AR5",
        allocation=allocation,
        boundary="cradle-to-gate",
    )


def lca_brick(
    kiln: BrickKiln,
    ef: EmissionFactors,
    cf: Optional[CharacterizationFactors] = None,
    functional_unit: str = "1000 bricks",
) -> LCAResult:
    """Cradle-to-gate LCA of a brick product."""
    if cf is None:
        cf = get_cf()
    cu = cf.factors
    n_k = kiln.annual_brick_production / 1000.0

    # Per-1000-bricks material flows
    clay_per_1000 = 2.0  # tonnes clay / 1000 bricks (approx)
    water_per_1000 = 0.5  # tonnes

    # Per-1000-bricks fuel use
    fuel_per_1000: Dict[str, float] = {}
    if kiln.fuel_use:
        for fu in kiln.fuel_use:
            fuel_per_1000[fu.fuel_name] = fu.consumption_t / n_k
    else:
        coal_ef = ef.brick_kilns[kiln.kiln_type]
        fuel_per_1000["coal_bituminous_NP"] = coal_ef.coal_t_per_1000

    elec_per_1000 = kiln.electricity_consumption_kwh / n_k
    transport_per_1000 = kiln.transport_tkm / n_k

    # Compute impacts
    impacts = {cat: 0.0 for cat in list_categories()}
    stage_contributions: Dict[str, Dict[str, float]] = {
        "raw_materials": {cat: 0.0 for cat in list_categories()},
        "fuel_combustion": {cat: 0.0 for cat in list_categories()},
        "electricity": {cat: 0.0 for cat in list_categories()},
        "transport": {cat: 0.0 for cat in list_categories()},
    }

    # Raw materials
    for mat, qty in [("clay", clay_per_1000), ("limestone", 0.05)]:
        for cat, val in BACKGROUND_PER_MATERIAL[mat].items():
            contrib = qty * val
            impacts[cat] += contrib
            stage_contributions["raw_materials"][cat] += contrib

    # Fuel
    for fname, qty in fuel_per_1000.items():
        if fname in SUBSTANCE_EF_PER_FUEL:
            for subst, ef_subst_kg in SUBSTANCE_EF_PER_FUEL[fname].items():
                for cat in list_categories():
                    if subst in cu and cat in cu.get(subst, {}):
                        val = cu[subst][cat] * ef_subst_kg * qty
                        impacts[cat] += val
                        stage_contributions["fuel_combustion"][cat] += val
        bg_key = "biomass" if "biomass" in fname else (
            "petcoke" if "petcoke" in fname else (
                "natural_gas" if "natural_gas" in fname else (
                    "diesel" if "diesel" in fname else "coal"
                )
            )
        )
        for cat, val in BACKGROUND_PER_MATERIAL[bg_key].items():
            contrib = qty * val
            impacts[cat] += contrib
            stage_contributions["fuel_combustion"][cat] += contrib

    # Electricity
    for cat, val in BACKGROUND_PER_MATERIAL["electricity_NP"].items():
        contrib = elec_per_1000 * val
        impacts[cat] += contrib
        stage_contributions["electricity"][cat] += contrib

    # Transport
    for cat, val in BACKGROUND_PER_MATERIAL["transport_tkm"].items():
        contrib = transport_per_1000 * val
        impacts[cat] += contrib
        stage_contributions["transport"][cat] += contrib

    person_eq_per_yr = {
        "GWP100": 4700, "AP": 56, "EP": 13, "POCP": 17.5, "ADP": 75, "HTP": 470,
    }
    normalized = {cat: impacts[cat] / person_eq_per_yr[cat] for cat in impacts}
    weights = {cat: 1.0 / len(impacts) for cat in impacts}
    weighted = sum(impacts[cat] * weights[cat] for cat in impacts)

    return LCAResult(
        functional_unit=functional_unit,
        product=f"{kiln.kiln_type.replace('_', ' ').title()} bricks from {kiln.name}",
        impacts={k: round(v, 4) for k, v in impacts.items()},
        stage_contributions={
            stage: {cat: round(v, 4) for cat, v in cats.items()}
            for stage, cats in stage_contributions.items()
        },
        total_impact_score=round(sum(impacts.values()), 4),
        normalized={k: round(v, 6) for k, v in normalized.items()},
        weighted_score=round(weighted, 4),
        method="CML 2001 + IPCC AR5",
        allocation="mass",
        boundary="cradle-to-gate",
    )


def lca_compare(
    results: List[LCAResult],
) -> Dict[str, List[Dict[str, float]]]:
    """Compare multiple LCA results side by side."""
    comparison: Dict[str, List[Dict[str, float]]] = {}
    for cat in list_categories():
        comparison[cat] = [
            {"product": r.product, "value": r.impacts.get(cat, 0)}
            for r in results
        ]
    return comparison
