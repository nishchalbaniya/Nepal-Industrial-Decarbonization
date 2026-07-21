"""Nepal cement plant registry — sector-wide multi-tenant catalog."""
from .plants import (
    NEPAL_CEMENT_PLANTS,
    NEPAL_BRICK_KILNS,
    get_plant,
    list_plants,
    list_plants_by_province,
    list_plants_by_type,
    aggregate_industry_stats,
    register_new_plant,
    sector_summary,
)

__all__ = [
    "NEPAL_CEMENT_PLANTS",
    "NEPAL_BRICK_KILNS",
    "get_plant",
    "list_plants",
    "list_plants_by_province",
    "list_plants_by_type",
    "aggregate_industry_stats",
    "register_new_plant",
    "sector_summary",
]
