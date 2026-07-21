"""Nepal cement plant registry — sector-wide multi-tenant catalog."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class CementPlantRecord:
    """Public record of a Nepali cement plant."""
    id: str
    name: str
    operator: str
    district: str
    province: str
    city: str
    plant_type: str                           # integrated, grinding_only
    capacity_tpd: int
    annual_production_t: float
    kiln_type: Optional[str] = None
    commissioned_year: Optional[int] = None
    modernization_year: Optional[int] = None
    public_emissions_tco2_yr: Optional[float] = None
    grid_connection_kv: Optional[int] = None
    notes: str = ""
    source: str = ""
    is_registered: bool = False               # whether the plant has self-registered
    tenant_id: Optional[str] = None           # multi-tenant id if registered

    def province_code(self) -> int:
        provinces = ["Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]
        return provinces.index(self.province) + 1 if self.province in provinces else 0

    def estimated_intensity(self) -> float:
        """kg CO2 per t cement, rough estimate by plant type."""
        if not self.public_emissions_tco2_yr or not self.annual_production_t:
            return 700
        return self.public_emissions_tco2_yr * 1000 / self.annual_production_t


@dataclass
class BrickKilnRecord:
    """Public record of a Nepali brick kiln (cluster)."""
    id: str
    name: str
    location: str
    province: str
    kiln_type: str                            # clamp_traditional, zigzag, hoffmann, tunnel
    cluster_size: int                         # number of kilns in cluster
    annual_brick_production: float
    estimated_emissions_tco2_yr: float


# ---------------------------------------------------------------------------
# Load registry from YAML
# ---------------------------------------------------------------------------
_DATA_PATH = Path(__file__).parent.parent / "data" / "nepal_plants.yaml"


def _load() -> Dict:
    if not _DATA_PATH.exists():
        return {"plants": [], "industry_aggregates": {}, "brick_kilns": []}
    with _DATA_PATH.open() as f:
        return yaml.safe_load(f) or {}


_DATA = _load()

NEPAL_CEMENT_PLANTS: List[CementPlantRecord] = []
for p in _DATA.get("plants", []):
    loc = p.get("location", {})
    NEPAL_CEMENT_PLANTS.append(CementPlantRecord(
        id=p["id"],
        name=p["name"],
        operator=p.get("operator", ""),
        district=loc.get("district", ""),
        province=loc.get("province", ""),
        city=loc.get("city", ""),
        plant_type=p.get("plant_type", "unknown"),
        capacity_tpd=int(p.get("capacity_tpd", 0)),
        annual_production_t=float(p.get("annual_production_t", 0)),
        kiln_type=p.get("kiln_type"),
        commissioned_year=p.get("commissioned_year"),
        modernization_year=p.get("modernization_year"),
        public_emissions_tco2_yr=p.get("public_emissions_tco2_yr"),
        grid_connection_kv=p.get("grid_connection_kv"),
        notes=p.get("notes", ""),
        source=p.get("source", ""),
    ))

# Approximate brick kiln clusters (UNEP/GEF Nepal estimates)
NEPAL_BRICK_KILNS: List[BrickKilnRecord] = [
    BrickKilnRecord("bhairahawa_clamp", "Bhairahawa", "Lumbini", "clamp_traditional", 25, 1.8e8, 130_000),
    BrickKilnRecord("kathmandu_clamp", "Bhaktapur cluster", "Bagmati", "clamp_traditional", 80, 4.5e8, 320_000),
    BrickKilnRecord("janakpur_clamp", "Janakpur cluster", "Madhesh", "clamp_traditional", 30, 1.2e8, 90_000),
    BrickKilnRecord("chitwan_zigzag", "Chitwan zigzag", "Bagmati", "zigzag", 5, 3.5e7, 8_400),
    BrickKilnRecord("butwal_tunnel", "Butwal tunnel", "Lumbini", "tunnel", 3, 4.5e7, 9_500),
    BrickKilnRecord("dang_clamp", "Dang cluster", "Lumbini", "clamp_traditional", 18, 1.0e8, 75_000),
    BrickKilnRecord("nepalgunj_clamp", "Nepalgunj cluster", "Lumbini", "clamp_traditional", 22, 1.4e8, 100_000),
    BrickKilnRecord("morang_clamp", "Morang cluster", "Koshi", "clamp_traditional", 35, 1.7e8, 130_000),
    BrickKilnRecord("rupandehi_clamp", "Rupandehi cluster", "Lumbini", "clamp_traditional", 28, 1.5e8, 110_000),
    BrickKilnRecord("kailali_clamp", "Kailali cluster", "Sudurpashchim", "clamp_traditional", 12, 6.0e7, 45_000),
    BrickKilnRecord("jhapa_clamp", "Jhapa cluster", "Koshi", "clamp_traditional", 26, 1.3e8, 100_000),
    BrickKilnRecord("sarlahi_clamp", "Sarlahi cluster", "Madhesh", "clamp_traditional", 24, 1.2e8, 90_000),
    BrickKilnRecord("dhanusha_clamp", "Dhanusha cluster", "Madhesh", "clamp_traditional", 20, 9.5e7, 70_000),
    BrickKilnRecord("mahottari_clamp", "Mahottari cluster", "Madhesh", "clamp_traditional", 16, 7.5e7, 55_000),
    BrickKilnRecord("rautahat_clamp", "Rautahat cluster", "Madhesh", "clamp_traditional", 14, 7.0e7, 50_000),
]


# ---------------------------------------------------------------------------
# Lookup / query
# ---------------------------------------------------------------------------
def get_plant(plant_id: str) -> Optional[CementPlantRecord]:
    for p in NEPAL_CEMENT_PLANTS:
        if p.id == plant_id:
            return p
    return None


def list_plants() -> List[CementPlantRecord]:
    return NEPAL_CEMENT_PLANTS


def list_plants_by_province(province: str) -> List[CementPlantRecord]:
    return [p for p in NEPAL_CEMENT_PLANTS if p.province == province]


def list_plants_by_type(plant_type: str) -> List[CementPlantRecord]:
    return [p for p in NEPAL_CEMENT_PLANTS if p.plant_type == plant_type]


def register_new_plant(plant: CementPlantRecord) -> CementPlantRecord:
    """Register a new plant (not yet in YAML)."""
    plant.is_registered = True
    plant.tenant_id = str(uuid.uuid4())
    NEPAL_CEMENT_PLANTS.append(plant)
    return plant


# ---------------------------------------------------------------------------
# Industry aggregates
# ---------------------------------------------------------------------------
INDUSTRY_AGGREGATES = _DATA.get("industry_aggregates", {})


def aggregate_industry_stats() -> Dict:
    """Compute sector-wide statistics from registry."""
    total_capacity = sum(p.capacity_tpd for p in NEPAL_CEMENT_PLANTS)
    total_production = sum(p.annual_production_t for p in NEPAL_CEMENT_PLANTS)
    total_emissions = sum(p.public_emissions_tco2_yr or 0 for p in NEPAL_CEMENT_PLANTS)
    by_province: Dict[str, Dict] = {}
    for p in NEPAL_CEMENT_PLANTS:
        d = by_province.setdefault(p.province, {"plants": 0, "capacity_tpd": 0, "production_t": 0, "emissions_t": 0})
        d["plants"] += 1
        d["capacity_tpd"] += p.capacity_tpd
        d["production_t"] += p.annual_production_t
        d["emissions_t"] += p.public_emissions_tco2_yr or 0
    by_type: Dict[str, int] = {}
    for p in NEPAL_CEMENT_PLANTS:
        by_type[p.plant_type] = by_type.get(p.plant_type, 0) + 1
    return {
        "total_plants_in_registry": len(NEPAL_CEMENT_PLANTS),
        "total_clinker_capacity_tpd": total_capacity,
        "total_annual_clinker_production_t": total_production,
        "total_estimated_emissions_tco2_yr": total_emissions,
        "weighted_avg_intensity_kgco2_per_t_cement": (total_emissions * 1000 / total_production) if total_production else 0,
        "by_province": by_province,
        "by_plant_type": by_type,
        "industry_aggregates_yaml": INDUSTRY_AGGREGATES,
    }


def sector_summary() -> str:
    s = aggregate_industry_stats()
    return (
        f"Nepal cement sector: {s['total_plants_in_registry']} plants in registry, "
        f"{s['total_clinker_capacity_tpd']:,} TPD capacity, "
        f"{s['total_estimated_emissions_tco2_yr']/1e6:.2f} Mt CO₂/yr estimated, "
        f"intensity {s['weighted_avg_intensity_kgco2_per_t_cement']:.0f} kg CO₂/t cement"
    )
