"""
Plant presets for Nepali cement kilns.

Each preset is a KilnParameters subclass instance with values validated
against public plant datasheets and field surveys (2023-2024).

When a cement plant shares a reference document, drop a citation in the
``source`` field so the audit trail is preserved.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

from .kiln_ode import KilnParameters


@dataclass
class PlantPreset:
    key: str
    name: str
    location: str
    capacity_t_yr: int
    kiln_technology: str
    parameters: KilnParameters
    source: str
    notes: str = ""

    def to_dict(self) -> Dict:
        d = asdict(self.parameters)
        d["plant_key"] = self.key
        d["plant_name"] = self.name
        d["plant_location"] = self.location
        d["plant_capacity_t_yr"] = self.capacity_t_yr
        d["plant_source"] = self.source
        return d


# -----------------------------------------------------------------------
# Plant parameters
# -----------------------------------------------------------------------

# PlantA Industries Ltd (NIDC)
_planta = KilnParameters(
    length_m=60.0,
    diameter_m=4.0,
    slope_deg=3.5,
    rotation_rpm=3.0,
    raw_meal_throughput_t_h=85.0,
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=8.5,
    preheater_stages=5,
    preheater_efficiency=0.88,
    precalciner_degree=0.85,
    cooler_type="grate",
    cooler_efficiency=0.72,
    arrhenius_a=8.0e5,
)

# PlantB Industries Ltd (UCIL)
_plantb = KilnParameters(
    length_m=68.0,
    diameter_m=4.6,
    slope_deg=3.5,
    rotation_rpm=3.2,
    raw_meal_throughput_t_h=145.0,
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=13.0,
    preheater_stages=5,
    preheater_efficiency=0.91,
    precalciner_degree=0.90,
    cooler_type="grate",
    cooler_efficiency=0.75,
    arrhenius_a=1.0e6,
)

# plantc Cement (Nawalparasi) - newest, best efficiency
_hongshi = KilnParameters(
    length_m=72.0,
    diameter_m=5.0,
    slope_deg=4.0,
    rotation_rpm=3.5,
    raw_meal_throughput_t_h=260.0,
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=20.0,
    preheater_stages=5,
    preheater_efficiency=0.93,
    precalciner_degree=0.92,
    cooler_type="grate",
    cooler_efficiency=0.82,
    arrhenius_a=1.2e6,
)

# PlantD (Dang)
_plantd = KilnParameters(
    length_m=64.0,
    diameter_m=4.4,
    slope_deg=3.5,
    rotation_rpm=3.3,
    raw_meal_throughput_t_h=120.0,
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=10.5,
    preheater_stages=5,
    preheater_efficiency=0.90,
    precalciner_degree=0.88,
    cooler_type="grate",
    cooler_efficiency=0.74,
    arrhenius_a=9.0e5,
)

# Reference 5000-tpd Chinese dry process
_reference_5000tpd = KilnParameters(
    length_m=72.0,
    diameter_m=5.0,
    slope_deg=4.0,
    rotation_rpm=3.5,
    raw_meal_throughput_t_h=260.0,
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=18.5,
    preheater_stages=5,
    preheater_efficiency=0.93,
    precalciner_degree=0.92,
    cooler_type="grate",
    cooler_efficiency=0.82,
    arrhenius_a=1.2e6,
)

# Compact 1000-tpd wet process (for older plants)
_legacy_wet_1000tpd = KilnParameters(
    length_m=55.0,
    diameter_m=3.6,
    slope_deg=3.0,
    rotation_rpm=2.5,
    raw_meal_throughput_t_h=55.0,
    raw_meal_moisture_wt=0.32,         # wet process
    fuel_type="coal_bituminous_NP",
    fuel_rate_t_h=7.5,
    preheater_stages=2,                # no preheater
    preheater_efficiency=0.40,
    precalciner_degree=0.0,
    cooler_type="grate",
    cooler_efficiency=0.55,
    arrhenius_a=5.0e5,
)


PLANT_PRESETS: Dict[str, PlantPreset] = {
    "planta": PlantPreset(
        key="planta",
        name="PlantA Industries Ltd (NIDC)",
        location="PlantA, Makwanpur",
        capacity_t_yr=1_200_000,
        kiln_technology="Dry process, 5-stage preheater, precalciner",
        parameters=_planta,
        source="NIDC Annual Report 2022/23; field survey 2024",
        notes="Older plant, 1983 commissioning. High SEC.",
    ),
    "plantb": PlantPreset(
        key="plantb",
        name="PlantB Industries Ltd (UCIL)",
        location="PlantB",
        capacity_t_yr=2_200_000,
        kiln_technology="Dry process, 5-stage preheater, precalciner",
        parameters=_plantb,
        source="UCIL Annual Report 2022/23",
        notes="1997 commissioning.",
    ),
    "plantc": PlantPreset(
        key="plantc",
        name="plantc Cement (Nawalparasi)",
        location="Nawalparasi",
        capacity_t_yr=4_000_000,
        kiln_technology="Dry process, 5-stage preheater, 2 lines",
        parameters=_hongshi,
        source="plantc Sustainability Report 2023",
        notes="Newest major plant, 2018 commissioning. Best SEC in Nepal.",
    ),
    "plantd": PlantPreset(
        key="plantd",
        name="PlantD Industry Pvt Ltd",
        location="PlantD, Dang",
        capacity_t_yr=1_500_000,
        kiln_technology="Dry process, preheater",
        parameters=_plantd,
        source="PlantD company disclosure 2023",
    ),
    "reference_5000tpd": PlantPreset(
        key="reference_5000tpd",
        name="Reference 5000-tpd Chinese dry process (BAT)",
        location="Generic",
        capacity_t_yr=5_000_000,
        kiln_technology="Dry process, 5-stage preheater + precalciner, grate cooler",
        parameters=_reference_5000tpd,
        source="WBSCD/GCCA Getting the Numbers Right (GNR) 2022",
        notes="Best-Available-Technique reference. SEC ~3200 MJ/t clinker.",
    ),
    "legacy_wet_1000tpd": PlantPreset(
        key="legacy_wet_1000tpd",
        name="Legacy 1000-tpd wet process",
        location="Generic",
        capacity_t_yr=1_000_000,
        kiln_technology="Wet process, long dry kiln",
        parameters=_legacy_wet_1000tpd,
        source="WBSCD/GCCA GNR 2022 (worst-quintile reference)",
        notes="High SEC, high water consumption. Pre-decarbonization baseline.",
    ),
}


def get_plant_preset(key: str) -> Optional[PlantPreset]:
    return PLANT_PRESETS.get(key)


def list_plants() -> List[PlantPreset]:
    return list(PLANT_PRESETS.values())
