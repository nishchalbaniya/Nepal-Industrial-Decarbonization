"""
Characterization factors for LCA impact categories.

Methods:
  - GWP100 (IPCC AR5)
  - AP (Acidification Potential, CML 2001)
  - EP (Eutrophication Potential, CML 2001)
  - POCP (Photochemical Ozone Creation, CML 2001)
  - ADP (Abiotic Resource Depletion, CML 2001)
  - HTP (Human Toxicity Potential, USEtox)

References:
  - IPCC AR5 (2014)
  - CML 2001 (Guinée et al.)
  - USEtox 2.0 (2017)
  - ecoinvent v3.10
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class ImpactCategory(BaseModel):
    """An LCA impact category with units and source."""
    code: str
    name: str
    unit: str
    method: str
    description: str


# Standard impact categories
IMPACT_CATEGORIES: Dict[str, ImpactCategory] = {
    "GWP100": ImpactCategory(
        code="GWP100",
        name="Global Warming Potential (100-year)",
        unit="kg CO2-eq",
        method="IPCC AR5",
        description="Radiative forcing over 100 years",
    ),
    "AP": ImpactCategory(
        code="AP",
        name="Acidification Potential",
        unit="kg SO2-eq",
        method="CML 2001",
        description="Acidifying emissions (SO2, NOx, NH3)",
    ),
    "EP": ImpactCategory(
        code="EP",
        name="Eutrophication Potential",
        unit="kg PO4-eq",
        method="CML 2001",
        description="Nutrient enrichment of water/soil",
    ),
    "POCP": ImpactCategory(
        code="POCP",
        name="Photochemical Ozone Creation Potential",
        unit="kg C2H4-eq (ethylene-eq)",
        method="CML 2001",
        description="Summer smog formation",
    ),
    "ADP": ImpactCategory(
        code="ADP",
        name="Abiotic Resource Depletion",
        unit="kg Sb-eq (antimony-eq)",
        method="CML 2001",
        description="Non-renewable resource extraction",
    ),
    "HTP": ImpactCategory(
        code="HTP",
        name="Human Toxicity Potential",
        unit="kg 1,4-DCB-eq",
        method="USEtox 2.0",
        description="Toxicity to humans",
    ),
}


def list_categories() -> List[str]:
    return list(IMPACT_CATEGORIES.keys())


class CharacterizationFactors(BaseModel):
    """Characterization factors per substance per impact category."""
    factors: Dict[str, Dict[str, float]] = Field(default_factory=dict)

    def get(self, substance: str, category: str) -> float:
        return self.factors.get(substance, {}).get(category, 0.0)

    def add(self, substance: str, category: str, value: float) -> None:
        if substance not in self.factors:
            self.factors[substance] = {}
        self.factors[substance][category] = value


# Standard characterization factors for cement & brick sector substances
# Values traceable to IPCC AR5, CML 2001, USEtox 2.0
def default_cf() -> CharacterizationFactors:
    cf = CharacterizationFactors()
    # Per kg of substance emitted
    cf.add("CO2", "GWP100", 1.0)
    cf.add("CH4", "GWP100", 28.0)
    cf.add("N2O", "GWP100", 265.0)
    cf.add("SO2", "AP", 1.0)
    cf.add("SO2", "GWP100", 0.0)
    cf.add("NOx", "AP", 0.7)
    cf.add("NOx", "GWP100", 0.0)
    cf.add("NOx", "EP", 0.13)
    cf.add("NOx", "POCP", 0.028)
    cf.add("NH3", "AP", 1.6)
    cf.add("NH3", "EP", 0.35)
    cf.add("CO", "GWP100", 1.57)
    cf.add("CO", "POCP", 0.027)
    cf.add("PM10", "HTP", 0.82)
    cf.add("PM2.5", "HTP", 1.21)
    cf.add("PM10", "POCP", 0.0)
    cf.add("VOC", "POCP", 0.416)
    cf.add("NMVOC", "POCP", 0.416)
    cf.add("Sb", "ADP", 1.0)
    cf.add("Cu", "ADP", 0.012)
    cf.add("Zn", "ADP", 0.0045)
    cf.add("Fe", "ADP", 0.0012)
    cf.add("Cr", "ADP", 0.085)
    cf.add("Ni", "ADP", 0.034)
    cf.add("coal_kg", "ADP", 0.0042)        # kg Sb-eq per kg coal (extraction)
    cf.add("limestone_kg", "ADP", 0.00011)
    cf.add("natural_gas_m3", "ADP", 0.0004)
    return cf


# Per-kg emission factors for substances per fuel (kg pollutant per kg fuel)
# Source: EMEP/EEA 2019 emission inventory guide, IPCC Tier 2 EF
SUBSTANCE_EF_PER_FUEL: Dict[str, Dict[str, float]] = {
    "coal_bituminous_NP": {
        "CO2": 2.41,                    # 25.5 * 94.6 / 1000
        "CO": 0.008,                    # 8 g/kg
        "NOx": 0.0045,                  # 4.5 g/kg (as NO2)
        "SO2": 0.011,                   # 11 g/kg (Indian bituminous 0.5% S)
        "PM10": 0.003,
        "PM2.5": 0.0015,
        "NMVOC": 0.0005,
        "CH4": 0.0001,
    },
    "petcoke": {
        "CO2": 3.12,
        "CO": 0.012,
        "NOx": 0.008,
        "SO2": 0.025,                   # High S petcoke
        "PM10": 0.001,
        "PM2.5": 0.0006,
        "NMVOC": 0.0003,
    },
    "diesel": {
        "CO2": 3.19,
        "CO": 0.008,
        "NOx": 0.012,
        "SO2": 0.0002,
        "PM10": 0.0008,
        "PM2.5": 0.0006,
        "NMVOC": 0.001,
    },
    "natural_gas": {
        "CO2": 2.69,
        "CO": 0.0004,
        "NOx": 0.002,
        "SO2": 0.0,
        "PM10": 0.0,
        "PM2.5": 0.0,
        "NMVOC": 0.0001,
    },
    "biomass_wood": {
        "CO2": 0.0,                    # Biogenic
        "CO": 0.005,
        "NOx": 0.001,
        "SO2": 0.0,
        "PM10": 0.002,
        "PM2.5": 0.0015,
        "NMVOC": 0.002,
        "CH4": 0.001,
    },
    "biomass_rice_husk": {
        "CO2": 0.0,
        "CO": 0.005,
        "NOx": 0.001,
        "SO2": 0.0,
        "PM10": 0.004,
        "PM2.5": 0.003,
        "NMVOC": 0.001,
        "CH4": 0.0005,
    },
    "tdf_tire": {
        "CO2": 2.72,                    # 32 * 85 / 1000
        "CO": 0.01,
        "NOx": 0.005,
        "SO2": 0.005,
        "PM10": 0.005,
        "PM2.5": 0.003,
        "NMVOC": 0.003,
        "Zn": 0.003,                    # Tire-derived Zn
    },
}


def get_cf() -> CharacterizationFactors:
    return default_cf()
