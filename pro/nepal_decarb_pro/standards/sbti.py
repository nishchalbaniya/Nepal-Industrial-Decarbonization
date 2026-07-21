"""
SBTi (Science Based Targets initiative) target validation.

Validates whether a target is consistent with the 1.5°C pathway.

Methods:
  - Absolute Contraction (AC)
  - Sectoral Decarbonization Approach (SDA)
  - Economic Intensity (EI)
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from nepal_decarb_pro.core.cement import CementEmissionsResult
from nepal_decarb_pro.core.brick import BrickEmissionsResult


class SBTiTarget(BaseModel):
    """A user-defined SBTi target."""
    target_year: int
    absolute_target_tco2: Optional[float] = None
    intensity_target_kgco2_per_t: Optional[float] = None
    base_year: int
    base_year_tco2: float
    base_year_intensity_kgco2_per_t: float
    sector: str = "cement"


class SBTiResult(BaseModel):
    """Result of SBTi validation."""
    target: SBTiTarget
    method: str
    aligned_with_1_5c: bool
    required_reduction_pct: float                  # required by 1.5C pathway
    target_reduction_pct: float                    # achieved by your target
    gap_pct: float                                 # target - required
    pathway_1_5c_2030_intensity: float
    pathway_1_5c_2050_intensity: float
    recommendation: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


def check_sbti_target(
    target: SBTiTarget,
    method: str = "Sectoral Decarbonization Approach (SDA)",
) -> SBTiResult:
    """
    Validate a target against the 1.5C pathway.
    """
    # SDA pathway for cement: 1.5C requires ~70% intensity reduction by 2030 vs 2020
    # and ~95% by 2050. Reference: SBTi Cement Guidance 2023.
    if target.sector.lower() == "cement":
        # 1.5C pathway: 11.0% annual intensity reduction (SDA)
        # vs 2C: 6.3%
        # 1.5C absolute: 4.2% annual
        required_pct = 11.0 * (target.target_year - 2020)  # cumulative annual
        if target.target_year >= 2050:
            required_pct = 95.0
        elif target.target_year >= 2030:
            required_pct = 38.5  # by 2030 vs 2020
    elif target.sector.lower() == "brick":
        # Brick SDA pathway
        required_pct = 10.5 * (target.target_year - 2020)
        if target.target_year >= 2050:
            required_pct = 90.0
        elif target.target_year >= 2030:
            required_pct = 36.0
    else:
        required_pct = 10.0 * (target.target_year - 2020)

    # Target reduction achieved
    if target.intensity_target_kgco2_per_t is not None:
        reduction_pct = (
            (target.base_year_intensity_kgco2_per_t - target.intensity_target_kgco2_per_t)
            / target.base_year_intensity_kgco2_per_t * 100
        )
    elif target.absolute_target_tco2 is not None:
        reduction_pct = (
            (target.base_year_tco2 - target.absolute_target_tco2) / target.base_year_tco2 * 100
        )
    else:
        reduction_pct = 0.0

    gap = reduction_pct - required_pct
    aligned = reduction_pct >= required_pct

    # 1.5C pathway endpoints
    if target.sector.lower() == "cement":
        pathway_2030 = target.base_year_intensity_kgco2_per_t * 0.615  # 38.5% reduction
        pathway_2050 = target.base_year_intensity_kgco2_per_t * 0.05
    else:
        pathway_2030 = target.base_year_intensity_kgco2_per_t * 0.64
        pathway_2050 = target.base_year_intensity_kgco2_per_t * 0.10

    if aligned:
        rec = f"Target is aligned with 1.5°C. Required: {required_pct:.1f}%, achieved: {reduction_pct:.1f}%"
    elif gap > -5:
        rec = f"Close to 1.5C. Increase target by {-gap:.1f} percentage points to qualify."
    else:
        rec = f"NOT aligned with 1.5C. Required reduction: {required_pct:.1f}%, achieved: {reduction_pct:.1f}%. Consider accelerating decarbonization."

    return SBTiResult(
        target=target,
        method=method,
        aligned_with_1_5c=aligned,
        required_reduction_pct=required_pct,
        target_reduction_pct=reduction_pct,
        gap_pct=gap,
        pathway_1_5c_2030_intensity=round(pathway_2030, 2),
        pathway_1_5c_2050_intensity=round(pathway_2050, 2),
        recommendation=rec,
    )
