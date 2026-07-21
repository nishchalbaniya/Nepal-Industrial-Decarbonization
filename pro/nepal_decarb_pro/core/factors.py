"""
Emission factors database — Nepal-specific, internationally traceable.

All values are calibrated to authoritative sources:
  - IPCC 2006 Guidelines for National GHG Inventories (Vols. 2 & 3)
  - IPCC 2019 Refinement
  - GCCA / WBCSD Cement Sustainability Initiative
  - DEFRA Conversion Factors 2024
  - ecoinvent v3.10
  - Nepal Electricity Authority (NEA) Annual Report 2023/24
  - UNEP/GEF Brick Kiln Efficiency Project
  - Field surveys of Nepali plants (2018-2024)
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import yaml


class Fuel(BaseModel):
    """A combustion fuel with NCV and emission factor."""
    name: str
    category: str                                  # coal | petcoke | gas | oil | biomass | waste
    ncvc_gj_per_t: float                           # Net calorific value (GJ/t)
    ef_kgco2_per_gj: float                         # kg CO2 per GJ (stationary combustion)
    biogenic_fraction: float = Field(0.0, ge=0, le=1)
    price_usd_per_t: float = Field(0, ge=0)        # Indicative Nepal 2024 CIF price
    ash_fraction: float = Field(0.0, ge=0, le=1)
    moisture_fraction: float = Field(0.0, ge=0, le=1)
    source: str

    @property
    def fossil_ef(self) -> float:
        return self.ef_kgco2_per_gj * (1 - self.biogenic_fraction)


class BrickKilnSpec(BaseModel):
    """Per-1000-brick spec for a kiln type."""
    name: str
    family: str                                    # traditional | continuous | modern
    coal_t_per_1000: float
    thermal_efficiency: float = Field(..., ge=0, le=1)
    specific_energy_mj_per_brick: float
    capital_cost_usd_per_kiln: float = Field(0)
    lifetime_years: int = Field(20)
    max_biomass_fraction_technical: float = Field(0.30, ge=0, le=1)
    notes: str


class ClinkerChemistry(BaseModel):
    """OPC clinker chemistry (mass fractions)."""
    cao: float = 0.65
    mgo: float = 0.015
    sio2: float = 0.21
    al2o3: float = 0.05
    fe2o3: float = 0.03
    k2o: float = 0.005
    na2o: float = 0.002
    so3: float = 0.005
    loi: float = 0.005
    free_lime: float = 0.01
    # Stoichiometric coefficients
    co2_per_t_cao: float = 0.7857
    co2_per_t_mgo: float = 1.092


class GridSpec(BaseModel):
    """Electricity grid emission factor (Nepal-specific)."""
    operating_margin: float            # kg CO2/kWh
    build_margin: float                # kg CO2/kWh
    combined_margin: float             # kg CO2/kWh
    residual_mix: float                # kg CO2/kWh
    t_and_d_loss: float                # fraction
    renewable_fraction: float          # 0..1
    name: str = "Nepal (NEA 2023/24)"

    @classmethod
    def nepal_default(cls) -> "GridSpec":
        return cls(
            operating_margin=0.0217,
            build_margin=0.0295,
            combined_margin=0.0256,
            residual_mix=0.0220,
            t_and_d_loss=0.225,
            renewable_fraction=0.95,
        )


class EmissionFactors(BaseModel):
    """Top-level emission factors container."""
    fuels: Dict[str, Fuel]
    brick_kilns: Dict[str, BrickKilnSpec]
    clinker_chemistry: ClinkerChemistry
    grid: GridSpec
    gwp: Dict[str, float] = Field(default_factory=lambda: {
        "co2": 1.0, "ch4": 28.0, "n2o": 265.0,
        "hfc": 1300.0, "pfc": 6630.0, "sf6": 23500.0,
    })
    gwp_source: str = "IPCC AR5 (100-year)"
    uncertainty: Dict[str, float] = Field(default_factory=lambda: {
        "coal_ncv_pct": 5.9,
        "coal_ef_pct": 7.0,
        "grid_ef_pct": 19.5,
        "cao_fraction_pct": 3.0,
        "mgo_fraction_pct": 20.0,
        "kiln_efficiency_pct": 5.0,
    })

    def fuel(self, name: str) -> Fuel:
        if name not in self.fuels:
            raise KeyError(f"Unknown fuel '{name}'. Available: {list(self.fuels)}")
        return self.fuels[name]

    def kiln(self, name: str) -> BrickKilnSpec:
        if name not in self.brick_kilns:
            raise KeyError(f"Unknown kiln '{name}'. Available: {list(self.brick_kilns)}")
        return self.brick_kilns[name]

    @classmethod
    def from_yaml(cls, path: Optional[Path] = None) -> "EmissionFactors":
        if path is None:
            candidates = [
                Path(__file__).parent.parent / "data" / "emission_factors.yaml",
                Path.cwd() / "data" / "emission_factors.yaml",
            ]
            for c in candidates:
                if c.exists():
                    path = c
                    break
            if path is None:
                raise FileNotFoundError("emission_factors.yaml not found")
        with open(path) as f:
            raw = yaml.safe_load(f)

        fuels = {
            k: Fuel(name=k, **v)
            for k, v in raw.get("fuels", {}).items()
        }
        kilns = {
            k: BrickKilnSpec(name=k, **v)
            for k, v in raw.get("brick_kiln", {}).items()
        }
        chem_data = raw.get("clinker", {})
        chem = ClinkerChemistry(
            cao=chem_data.get("cao_fraction_clinker", 0.65),
            mgo=chem_data.get("mgo_fraction_clinker", 0.015),
            co2_per_t_cao=chem_data.get("co2_per_t_cao", 0.7857),
            co2_per_t_mgo=chem_data.get("co2_per_t_mgo", 1.092),
        )
        grid_data = raw.get("grid_electricity_nepal", {})
        grid = GridSpec(
            operating_margin=grid_data.get("om_kgco2_per_kwh", 0.0217),
            build_margin=grid_data.get("bm_kgco2_per_kwh", 0.0295),
            combined_margin=grid_data.get("cm_kgco2_per_kwh", 0.0256),
            residual_mix=grid_data.get("residual_mix_kgco2_per_kwh", 0.0220),
            t_and_d_loss=grid_data.get("t_and_d_loss_fraction", 0.225),
            renewable_fraction=grid_data.get("renewable_fraction", 0.95),
        )
        return cls(
            fuels=fuels,
            brick_kilns=kilns,
            clinker_chemistry=chem,
            grid=grid,
            gwp_source=raw.get("gwp", {}).get("source", "IPCC AR5 (100-year)"),
            uncertainty=raw.get("uncertainty", cls.model_fields["uncertainty"].default_factory()),
        )


def default_factors() -> EmissionFactors:
    """Return a fully-populated EmissionFactors object built from bundled data."""
    return EmissionFactors.from_yaml()
