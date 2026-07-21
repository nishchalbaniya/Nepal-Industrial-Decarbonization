"""LCA engine: cradle-to-gate for cement and brick, multiple impact categories."""
from nepal_decarb_pro.lca.engine import (
    LCAResult,
    lca_cement,
    lca_brick,
    lca_compare,
)
from nepal_decarb_pro.lca.characterization import (
    ImpactCategory,
    CharacterizationFactors,
    get_cf,
    list_categories,
)

__all__ = [
    "LCAResult",
    "ImpactCategory",
    "lca_cement",
    "lca_brick",
    "lca_compare",
    "CharacterizationFactors",
    "get_cf",
    "list_categories",
]
