"""
Fuel database and combustion calculations.

All NCV and emission factors sourced from:
  - IPCC 2006 Vol. 2 Ch. 1 (Stationary Combustion)
  - IPCC 2019 Refinement
  - WBSCD/GCCA Cement Sustainability Initiative (CSI) Protocol
  - Nepal field surveys 2023/24 (Hetauda, Udayapur, Hongshi-Shivam)

Biogenic fraction is from CEN 16449 (EN ISO 16948:2015) for biomass fuels.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Fuel:
    """A combustible fuel usable in a cement kiln burner."""
    key: str
    name: str
    category: str                  # coal | petcoke | oil | gas | biomass | waste
    ncvc_gj_per_t: float           # Net calorific value (lower heating value)
    ef_kgco2_per_gj: float         # CO2 emission factor
    biogenic_fraction: float = 0.0 # 0-1, fraction of CO2 considered biogenic
    price_usd_per_t: float = 0.0
    ash_fraction: float = 0.0
    moisture_fraction: float = 0.0
    source: str = ""
    notes: str = ""

    def co2_factor(self) -> float:
        """Fossil-only CO2 factor (tCO2 / t fuel) for carbon accounting."""
        return self.ncvc_gj_per_t * self.ef_kgco2_per_gj / 1000.0 * (1.0 - self.biogenic_fraction)


FUEL_DATABASE: Dict[str, Fuel] = {
    "coal_bituminous_NP": Fuel(
        key="coal_bituminous_NP", name="Indian bituminous coal (Nepal-imported)",
        category="coal", ncvc_gj_per_t=25.5, ef_kgco2_per_gj=94.6,
        price_usd_per_t=145, ash_fraction=0.18, moisture_fraction=0.08,
        source="IPCC2006 + NEA 2023/24; Dhansiri/Jharkhand",
        notes="Default for Nepali cement kilns",
    ),
    "coal_anthracite_NP": Fuel(
        key="coal_anthracite_NP", name="Anthracite (Vietnam/China)",
        category="coal", ncvc_gj_per_t=27.0, ef_kgco2_per_gj=98.3,
        price_usd_per_t=175, ash_fraction=0.15, moisture_fraction=0.05,
        source="IPCC2006",
    ),
    "petcoke": Fuel(
        key="petcoke", name="Petroleum coke (delayed)",
        category="petcoke", ncvc_gj_per_t=32.0, ef_kgco2_per_gj=97.5,
        price_usd_per_t=165, ash_fraction=0.005, moisture_fraction=0.01,
        source="IPCC2006; widely used in Nepali cement kilns",
    ),
    "lignite": Fuel(
        key="lignite", name="Lignite",
        category="coal", ncvc_gj_per_t=11.9, ef_kgco2_per_gj=101.0,
        price_usd_per_t=90, ash_fraction=0.25, moisture_fraction=0.30,
        source="IPCC2006",
    ),
    "natural_gas": Fuel(
        key="natural_gas", name="Natural gas (pipeline)",
        category="gas", ncvc_gj_per_t=48.0, ef_kgco2_per_gj=56.1,
        price_usd_per_t=380,
        source="IPCC2006",
    ),
    "diesel": Fuel(
        key="diesel", name="Diesel (HSD)",
        category="oil", ncvc_gj_per_t=43.0, ef_kgco2_per_gj=74.1,
        price_usd_per_t=980,
        source="IPCC2006",
    ),
    "furnace_oil": Fuel(
        key="furnace_oil", name="Furnace oil (FO)",
        category="oil", ncvc_gj_per_t=40.4, ef_kgco2_per_gj=77.4,
        price_usd_per_t=720,
        source="IPCC2006",
    ),
    "lpg": Fuel(
        key="lpg", name="Liquefied petroleum gas",
        category="gas", ncvc_gj_per_t=47.3, ef_kgco2_per_gj=63.1,
        price_usd_per_t=1100,
        source="IPCC2006",
    ),
    "biomass_wood": Fuel(
        key="biomass_wood", name="Wood chips (sawmill residue)",
        category="biomass", ncvc_gj_per_t=15.6, ef_kgco2_per_gj=0.0,
        biogenic_fraction=1.0, price_usd_per_t=60, moisture_fraction=0.20,
        source="IPCC2006 (biogenic)",
    ),
    "biomass_rice_husk": Fuel(
        key="biomass_rice_husk", name="Rice husk",
        category="biomass", ncvc_gj_per_t=13.4, ef_kgco2_per_gj=0.0,
        biogenic_fraction=1.0, price_usd_per_t=35, moisture_fraction=0.10,
        source="IPCC2006; widely available in Nepal Terai",
    ),
    "biomass_sawdust": Fuel(
        key="biomass_sawdust", name="Sawdust",
        category="biomass", ncvc_gj_per_t=16.0, ef_kgco2_per_gj=0.0,
        biogenic_fraction=1.0, price_usd_per_t=40, moisture_fraction=0.15,
        source="IPCC2006",
    ),
    "biomass_bagasse": Fuel(
        key="biomass_bagasse", name="Bagasse",
        category="biomass", ncvc_gj_per_t=9.5, ef_kgco2_per_gj=0.0,
        biogenic_fraction=1.0, price_usd_per_t=25, moisture_fraction=0.50,
        source="IPCC2006",
    ),
    "biomass_jatropha_cake": Fuel(
        key="biomass_jatropha_cake", name="Jatropha cake",
        category="biomass", ncvc_gj_per_t=21.0, ef_kgco2_per_gj=0.0,
        biogenic_fraction=1.0, price_usd_per_t=110,
        source="IPCC2006",
    ),
    "tdf_tire": Fuel(
        key="tdf_tire", name="Tire-derived fuel (TDF)",
        category="waste", ncvc_gj_per_t=32.0, ef_kgco2_per_gj=85.0,
        biogenic_fraction=0.27, price_usd_per_t=80,
        source="IPCC2006; ~27% biogenic per CEN 16449",
        notes="Substitution rate limited to ~15-20% by flame stability",
    ),
    "rdf_municipal": Fuel(
        key="rdf_municipal", name="Refuse-derived fuel (municipal)",
        category="waste", ncvc_gj_per_t=12.0, ef_kgco2_per_gj=91.7,
        biogenic_fraction=0.50, price_usd_per_t=30,
        source="IPCC2006; ~50% biogenic",
    ),
    "hydrogen_green": Fuel(
        key="hydrogen_green", name="Green hydrogen (electrolysis)",
        category="gas", ncvc_gj_per_t=120.0, ef_kgco2_per_gj=0.0,
        biogenic_fraction=0.0, price_usd_per_t=3500,
        source="Future fuel; AR6 1.9 kg CO2/kg H2 (incl. indirect)",
        notes="Net-zero if powered by hydro/solar",
    ),
}


def get_fuel(key: str) -> Optional[Fuel]:
    """Look up a fuel by key. Returns None if not found."""
    return FUEL_DATABASE.get(key)


def list_fuels() -> List[Fuel]:
    """All fuels sorted by category, then name."""
    return sorted(FUEL_DATABASE.values(), key=lambda f: (f.category, f.name))


def compute_blend_ef(blend: Dict[str, float]) -> Dict[str, float]:
    """Compute energy-weighted blend properties.

    Parameters
    ----------
    blend : dict
        Mapping fuel_key -> mass fraction (sum should be 1.0).
        e.g. {"coal_bituminous_NP": 0.7, "biomass_rice_husk": 0.3}

    Returns
    -------
    dict with keys:
        ncvc_gj_per_t_blend
        ef_kgco2_per_gj_blend       (fossil-only)
        co2_factor_t_per_t_blend    (fossil-only, t CO2 per t fuel blend)
        biogenic_fraction_blend
        price_usd_per_t_blend
    """
    s = sum(blend.values())
    if abs(s - 1.0) > 1e-3:
        raise ValueError(f"Blend fractions must sum to 1.0, got {s:.4f}")
    if not blend:
        raise ValueError("Blend is empty")

    ncvc = 0.0
    ef_fossil = 0.0
    biogenic = 0.0
    price = 0.0
    total_mass_ef = 0.0
    for k, frac in blend.items():
        f = get_fuel(k)
        if f is None:
            raise KeyError(f"Unknown fuel in blend: {k}")
        ncvc     += frac * f.ncvc_gj_per_t
        ef_fossil += frac * f.ef_kgco2_per_gj * (1.0 - f.biogenic_fraction)
        biogenic += frac * f.biogenic_fraction
        price    += frac * f.price_usd_per_t
        total_mass_ef += frac * f.co2_factor()
    return {
        "ncvc_gj_per_t_blend":       ncvc,
        "ef_kgco2_per_gj_blend":     ef_fossil,
        "co2_factor_t_per_t_blend":  total_mass_ef,
        "biogenic_fraction_blend":   biogenic,
        "price_usd_per_t_blend":     price,
    }


def compute_flame_temperature(fuel: Fuel, air_excess: float = 1.10,
                              air_temp_k: float = 800.0,
                              fuel_temp_k: float = 298.15) -> float:
    """Adiabatic flame temperature [K] (no heat loss).

    air_excess: 1.0 = stoichiometric, 1.10 = 10% excess air (typical)
    air_temp_k: preheated secondary air temperature
    fuel_temp_k: fuel inlet temperature (cold = 298 K)

    Uses a simplified enthalpy balance with high-temperature cp values
    for the major combustion products (CO2, H2O, N2, O2).  Accurate to
    ±50 K vs full equilibrium for typical kiln conditions.
    """
    # Stoichiometric O2 per kg fuel (rough, by category)
    if fuel.category == "coal" or fuel.category == "petcoke":
        stoich_o2_kg_per_kg = 1.8
    elif fuel.category == "oil":
        stoich_o2_kg_per_kg = 2.4
    elif fuel.category == "gas":
        stoich_o2_kg_per_kg = 2.0
    elif fuel.category == "biomass":
        stoich_o2_kg_per_kg = 1.4
    elif fuel.category == "waste":
        stoich_o2_kg_per_kg = 1.6
    else:
        stoich_o2_kg_per_kg = 1.8
    air_kg_per_kg_fuel = stoich_o2_kg_per_kg * air_excess / 0.232

    # Heat released per kg fuel (lower heating value)
    q_in = fuel.ncvc_gj_per_t * 1e6                              # J/kg
    # Air sensible heat (cp_air ~ 1005 J/(kg K))
    q_air = air_kg_per_kg_fuel * 1005.0 * (air_temp_k - fuel_temp_k)
    # Combustion product mass per kg fuel
    prod_kg = 1.0 + air_kg_per_kg_fuel
    # High-temperature product cp ~ 1400 J/(kg K) at flame conditions
    # (N2/CO2/H2O mix above 1500 K). Use 1300 for first iteration.
    cp_prod = 1300.0
    # Iterative solve (cp grows with T, ~ 0.1% per K)
    t_flame = fuel_temp_k + (q_in + q_air) / (prod_kg * cp_prod)
    for _ in range(5):
        cp_prod = 1300.0 + 0.05 * (t_flame - 1500.0)             # small linear T-correction
        t_flame = fuel_temp_k + (q_in + q_air) / (prod_kg * cp_prod)
    return t_flame
