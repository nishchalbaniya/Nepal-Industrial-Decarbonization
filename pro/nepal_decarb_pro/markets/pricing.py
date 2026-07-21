"""
Carbon pricing scenarios for Nepal and global voluntary markets.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class CarbonPriceScenario(BaseModel):
    """Carbon price scenario for a region and time."""
    region: str
    market: str
    year: int
    price_usd_per_tco2: float
    price_low_usd_per_tco2: float
    price_high_usd_per_tco2: float
    source: str
    notes: str = ""


# Historical & projected carbon prices
CARBON_PRICES: Dict[str, List[CarbonPriceScenario]] = {
    "EU_ETS": [
        CarbonPriceScenario(region="EU", market="compliance", year=2020,
                            price_usd_per_tco2=24.7, price_low_usd_per_tco2=16.6,
                            price_high_usd_per_tco2=33.6, source="World Bank 2024",
                            notes="COVID dip"),
        CarbonPriceScenario(region="EU", market="compliance", year=2021,
                            price_usd_per_tco2=53.5, price_low_usd_per_tco2=32.8,
                            price_high_usd_per_tco2=80.0, source="World Bank 2024",
                            notes="Recovery"),
        CarbonPriceScenario(region="EU", market="compliance", year=2022,
                            price_usd_per_tco2=80.0, price_low_usd_per_tco2=50.0,
                            price_high_usd_per_tco2=99.0, source="World Bank 2024",
                            notes="Energy crisis"),
        CarbonPriceScenario(region="EU", market="compliance", year=2023,
                            price_usd_per_tco2=83.7, price_low_usd_per_tco2=60.0,
                            price_high_usd_per_tco2=99.5, source="World Bank 2024", notes=""),
        CarbonPriceScenario(region="EU", market="compliance", year=2024,
                            price_usd_per_tco2=65.0, price_low_usd_per_tco2=50.0,
                            price_high_usd_per_tco2=80.0, source="World Bank 2024",
                            notes="Slight pullback"),
    ],
    "Voluntary_Global": [
        CarbonPriceScenario(region="Global", market="voluntary", year=2020,
                            price_usd_per_tco2=3.0, price_low_usd_per_tco2=0.5,
                            price_high_usd_per_tco2=8.0, source="Ecosystem Marketplace 2023",
                            notes=""),
        CarbonPriceScenario(region="Global", market="voluntary", year=2021,
                            price_usd_per_tco2=4.0, price_low_usd_per_tco2=0.5,
                            price_high_usd_per_tco2=12.0, source="Ecosystem Marketplace 2023",
                            notes=""),
        CarbonPriceScenario(region="Global", market="voluntary", year=2022,
                            price_usd_per_tco2=8.0, price_low_usd_per_tco2=2.0,
                            price_high_usd_per_tco2=20.0, source="Ecosystem Marketplace 2023",
                            notes="Peak"),
        CarbonPriceScenario(region="Global", market="voluntary", year=2023,
                            price_usd_per_tco2=6.5, price_low_usd_per_tco2=2.0,
                            price_high_usd_per_tco2=18.0, source="Ecosystem Marketplace 2023",
                            notes=""),
        CarbonPriceScenario(region="Global", market="voluntary", year=2024,
                            price_usd_per_tco2=8.5, price_low_usd_per_tco2=3.0,
                            price_high_usd_per_tco2=22.0, source="Ecosystem Marketplace 2024",
                            notes="Recovery"),
    ],
    "Verra_VCS": [
        CarbonPriceScenario(region="Global", market="voluntary", year=2023,
                            price_usd_per_tco2=7.5, price_low_usd_per_tco2=3.0,
                            price_high_usd_per_tco2=15.0, source="Verra registry 2024",
                            notes="Nature-based premium"),
        CarbonPriceScenario(region="Global", market="voluntary", year=2024,
                            price_usd_per_tco2=9.0, price_low_usd_per_tco2=4.0,
                            price_high_usd_per_tco2=18.0, source="Verra registry 2024",
                            notes="Tech-based credit"),
    ],
    "Gold_Standard": [
        CarbonPriceScenario(region="Global", market="voluntary", year=2023,
                            price_usd_per_tco2=11.0, price_low_usd_per_tco2=5.0,
                            price_high_usd_per_tco2=25.0, source="GS registry 2024",
                            notes="Premium for co-benefits"),
        CarbonPriceScenario(region="Global", market="voluntary", year=2024,
                            price_usd_per_tco2=13.0, price_low_usd_per_tco2=6.0,
                            price_high_usd_per_tco2=28.0, source="GS registry 2024",
                            notes=""),
    ],
    "India_CCTS": [
        CarbonPriceScenario(region="India", market="compliance", year=2024,
                            price_usd_per_tco2=8.0, price_low_usd_per_tco2=6.0,
                            price_high_usd_per_tco2=12.0, source="India CCTS 2024",
                            notes="New market"),
    ],
    "China_ETS": [
        CarbonPriceScenario(region="China", market="compliance", year=2024,
                            price_usd_per_tco2=9.0, price_low_usd_per_tco2=7.0,
                            price_high_usd_per_tco2=11.0, source="China ETS 2024",
                            notes="National ETS"),
    ],
    "Nepal_projected": [
        CarbonPriceScenario(region="Nepal", market="compliance", year=2025,
                            price_usd_per_tco2=0.0, price_low_usd_per_tco2=0.0,
                            price_high_usd_per_tco2=0.0, source="Nepal MoF 2024",
                            notes="No domestic carbon tax yet"),
        CarbonPriceScenario(region="Nepal", market="compliance", year=2030,
                            price_usd_per_tco2=15.0, price_low_usd_per_tco2=5.0,
                            price_high_usd_per_tco2=30.0, source="World Bank Nepal CCA 2023",
                            notes="Projected"),
        CarbonPriceScenario(region="Nepal", market="compliance", year=2040,
                            price_usd_per_tco2=50.0, price_low_usd_per_tco2=30.0,
                            price_high_usd_per_tco2=80.0, source="World Bank Nepal CCA 2023",
                            notes="Projected"),
    ],
}


def get_carbon_price(market: str, year: int) -> CarbonPriceScenario:
    """Get carbon price for a market and year."""
    if market not in CARBON_PRICES:
        raise KeyError(f"Unknown market: {market}. Available: {list(CARBON_PRICES)}")
    scenarios = CARBON_PRICES[market]
    scenarios_sorted = sorted(scenarios, key=lambda s: abs(s.year - year))
    return scenarios_sorted[0]


def get_revenue_scenarios(
    annual_emission_reduction_tco2: float,
    crediting_period_years: int = 10,
    discount_rate: float = 0.10,
) -> Dict[str, Dict[str, float]]:
    """Calculate NPV revenue across multiple carbon price scenarios."""
    scenarios = {
        "Verra VCS voluntary ($9)": 9.0,
        "Gold Standard voluntary ($13)": 13.0,
        "EU ETS compliance ($65)": 65.0,
        "India CCTS ($8)": 8.0,
        "Mid ($30)": 30.0,
        "Conservative ($15)": 15.0,
        "Optimistic ($50)": 50.0,
    }
    results = {}
    for name, price in scenarios.items():
        npv = sum(
            annual_emission_reduction_tco2 * price / ((1 + discount_rate) ** y)
            for y in range(1, crediting_period_years + 1)
        )
        annual = annual_emission_reduction_tco2 * price
        cumulative = annual * crediting_period_years
        results[name] = {
            "price_usd_per_tco2": price,
            "annual_revenue_usd": annual,
            "cumulative_revenue_usd": cumulative,
            "npv_revenue_usd": npv,
        }
    return results
