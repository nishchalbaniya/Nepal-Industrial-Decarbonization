"""
Nepal Industrial Decarbonization Platform — Pro Edition
========================================================

World-class, open-source decarbonization platform for Nepal's cement and brick
industry. Implements international standards at the highest tier.

Modules
-------
core           : Tier 2/3 emissions engine, Monte Carlo UQ
optimization   : MILP fuel-blend, multi-objective Pareto
lca            : Cradle-to-gate LCA with GWP/AP/EP/POCP/ADP
pinch          : Process integration, composite curves, MER targeting
markets        : Verra VCS, Gold Standard, pricing, tokenization
standards      : ISO 14064, TCFD, SBTi, GCCA, PCAF, GHG Protocol
forecasting    : Time-series forecasting (ARIMA, ETS, ML)
dt             : Digital twin (state estimation, Kalman, anomaly)
i18n           : Bilingual (English + Nepali)
io             : CSV/Excel/MQTT/database I/O
api            : FastAPI + WebSocket
reporting      : Verra PDD, monitoring report, TCFD, bilingual PDFs
contracts      : On-chain carbon credit token (Solidity)
firmware       : ESP32 IoT sensor firmware (C++/Arduino)

Author: Nishchal Baniya <nishchal.baniya@himalayancarbonnepal.com>
Org:    Himalayan Carbon Nepal
License: MIT (code), CC-BY-4.0 (data & docs)
"""
from __future__ import annotations

__version__ = "1.0.0"
__author__ = "Nishchal Baniya"
__email__ = "nishchal.baniya@himalayancarbonnepal.com"
__organization__ = "Himalayan Carbon Nepal"
__license__ = "MIT"

# Lazy import pattern: top-level imports are kept light to avoid pulling
# in heavy dependencies. Import submodules explicitly as needed.
__all__ = [
    "__version__",
    "__author__",
    "__email__",
    "__organization__",
    "__license__",
]
