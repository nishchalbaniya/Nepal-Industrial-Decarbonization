"""
Emission factors database loader.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
import yaml
from pydantic import BaseModel, Field


class FuelEF(BaseModel):
    """Emission factor record for a fuel."""
    name: str
    ncvc_gj_per_t: float = Field(..., description="Net calorific value (GJ/t)")
    ef_kgco2_per_gj: float = Field(..., description="kg CO2 per GJ (combustion)")
    source: str
    biogenic: bool = Field(False, description="True if biomass / biogenic")


class BrickKilnEF(BaseModel):
    """Per-1000-bricks emission and energy factor for a kiln type."""
    name: str
    coal_t_per_1000_bricks: float
    ef_kgco2_per_1000_bricks: float
    thermal_efficiency: float
    specific_energy_mj_per_brick: float
    notes: str


class EmissionFactors(BaseModel):
    """Top-level emission factors container."""
    # Cement clinker
    co2_per_t_clinker_process: float
    cao_fraction_clinker: float
    mgo_fraction_clinker: float
    co2_per_t_cao: float
    co2_per_t_mgo: float
    co2_per_t_limestone: float

    # Fuels & grid & brick kiln lookup
    fuels: Dict[str, FuelEF]
    grid_om: float
    grid_cm: float
    grid_td_loss: float
    brick_kilns: Dict[str, BrickKilnEF]

    # Benchmarks
    sec_bat_clinker: float
    sec_bat_cement: float
    sec_nepal_avg_clinker: float
    sec_nepal_avg_cement: float

    @classmethod
    def from_yaml(cls, path: Optional[Path] = None) -> "EmissionFactors":
        if path is None:
            # Look in: src/nepal_mrv/../../data, src/../data, data (CWD)
            candidates = [
                Path(__file__).parent.parent.parent / "data" / "emission_factors.yaml",
                Path(__file__).parent.parent / "data" / "emission_factors.yaml",
                Path.cwd() / "data" / "emission_factors.yaml",
            ]
            for c in candidates:
                if c.exists():
                    path = c
                    break
            if path is None:
                raise FileNotFoundError(
                    f"emission_factors.yaml not found. Searched: {candidates}"
                )
        with open(path) as f:
            raw = yaml.safe_load(f)

        # Parse fuels
        fuels = {
            k: FuelEF(name=k, **v)
            for k, v in raw["fuels"].items()
        }
        brick_kilns = {
            k: BrickKilnEF(name=k, **v)
            for k, v in raw["brick_kiln"].items()
        }
        return cls(
            co2_per_t_clinker_process=raw["clinker"]["co2_per_t_clinker_process"],
            cao_fraction_clinker=raw["clinker"]["cao_fraction_clinker"],
            mgo_fraction_clinker=raw["clinker"]["mgo_fraction_clinker"],
            co2_per_t_cao=raw["clinker"]["co2_per_t_cao"],
            co2_per_t_mgo=raw["clinker"]["co2_per_t_mgo"],
            co2_per_t_limestone=raw["clinker"]["co2_per_t_limestone"],
            fuels=fuels,
            grid_om=raw["grid_electricity_nepal"]["om_kgco2_per_kwh"],
            grid_cm=raw["grid_electricity_nepal"]["cm_kgco2_per_kwh"],
            grid_td_loss=raw["grid_electricity_nepal"]["t_and_d_loss_fraction"],
            brick_kilns=brick_kilns,
            sec_bat_clinker=raw["sec_benchmarks"]["cement_opc_global_bat"]["sec_mj_per_t_clinker"],
            sec_bat_cement=raw["sec_benchmarks"]["cement_opc_global_bat"]["sec_mj_per_t_cement"],
            sec_nepal_avg_clinker=raw["sec_benchmarks"]["cement_nepal_average"]["sec_mj_per_t_clinker"],
            sec_nepal_avg_cement=raw["sec_benchmarks"]["cement_nepal_average"]["sec_mj_per_t_cement"],
        )

    def fuel(self, name: str) -> FuelEF:
        """Lookup a fuel record by name (raises KeyError)."""
        if name not in self.fuels:
            raise KeyError(
                f"Unknown fuel '{name}'. Available: {list(self.fuels)}"
            )
        return self.fuels[name]

    def kiln(self, kind: str) -> BrickKilnEF:
        if kind not in self.brick_kilns:
            raise KeyError(
                f"Unknown kiln '{kind}'. Available: {list(self.brick_kilns)}"
            )
        return self.brick_kilns[kind]
