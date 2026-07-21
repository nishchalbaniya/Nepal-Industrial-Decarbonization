"""
PCAF (Partnership for Carbon Accounting Financials) financed emissions.

For banks/lenders: calculate GHG emissions associated with loans and
investments in cement/brick companies.

PCAF Data Quality Score (1=best, 5=worst):
  1. Audited emissions
  2. Non-audited reported emissions
  3. Estimated using physical activity data
  4. Estimated using economic activity data
  5. Estimated using sector/region average
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from nepal_decarb_pro.core.cement import CementPlant
from nepal_decarb_pro.core.brick import BrickKiln


class PCAFEmission(BaseModel):
    """PCAF financed emission for one loan/investment."""
    company: str
    sector: str
    loan_amount_usd: float
    company_revenue_usd: float
    company_emissions_tco2: float
    attribution_factor: float                # loan / revenue (or EVIC)
    financed_emissions_tco2: float
    data_quality_score: int                  # 1-5
    attribution_method: str                  # "EVIC" | "Revenue" | "Physical"


def calculate_financed_emissions(
    loans: List[Dict],
    attribution: str = "Revenue",
) -> List[PCAFEmission]:
    """
    Calculate PCAF financed emissions.

    Parameters
    ----------
    loans : list of dict
        Each dict: {
            "company": str,
            "sector": str,
            "loan_amount_usd": float,
            "company_revenue_usd": float,
            "company_emissions_tco2": float,
            "data_quality_score": int (1-5),
        }
    attribution : str
        "Revenue" (default) or "EVIC" or "Physical"
    """
    results = []
    for loan in loans:
        if attribution == "Revenue":
            af = loan["loan_amount_usd"] / loan["company_revenue_usd"]
        elif attribution == "EVIC":
            af = loan.get("attribution_factor", 0.1)   # default 10%
        else:  # Physical
            af = loan.get("attribution_factor", 0.1)

        financed = loan["company_emissions_tco2"] * af

        results.append(PCAFEmission(
            company=loan["company"],
            sector=loan["sector"],
            loan_amount_usd=loan["loan_amount_usd"],
            company_revenue_usd=loan.get("company_revenue_usd", 0),
            company_emissions_tco2=loan["company_emissions_tco2"],
            attribution_factor=round(af, 4),
            financed_emissions_tco2=round(financed, 2),
            data_quality_score=loan.get("data_quality_score", 3),
            attribution_method=attribution,
        ))
    return results
