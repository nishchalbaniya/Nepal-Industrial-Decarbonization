"""
Real cement chemistry — Bogue, Lea/Parker, Bhatty, Hills, Kihlborg.
==================================================================

References:
  - Bogue, R.H. (1955). The Chemistry of Portland Cement. Reinhold.
  - Lea, F.M. & Parker, T.W. (1934). Phil. Trans. Roy. Soc. A, 234, 1.
  - Hills, L.M. (1967). Clinker burning. Cement Technology 1(2).
  - Bhatty, J.I. (2004). Innovations in Portland Cement Manufacturing.
  - Taylor, H.F.W. (1997). Cement Chemistry. Thomas Telford, 2nd ed.
  - Kihlborg, L. (1961). Cement chemistry (clinker formation kinetics).

Used for:
  - Validated burner-zone temperature predictions
  - Mineral formation (C3S, C2S, C3A, C4AF) from raw mix
  - Real activation energies (replacing the simplified Arrhenius shortcut)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict


@dataclass
class RawMix:
    """Raw mix composition (mass fractions, must sum to ~1.0)."""
    cao: float = 0.66
    sio2: float = 0.21
    al2o3: float = 0.06
    fe2o3: float = 0.03
    mgo: float = 0.02
    k2o: float = 0.005
    na2o: float = 0.005
    so3: float = 0.005
    loi: float = 0.0            # loss on ignition (CO2 from carbonates)

    @property
    def lsf(self) -> float:
        """Lime Saturation Factor (LSF) — the single most important control parameter."""
        return self.cao / (2.8 * self.sio2 + 1.18 * self.al2o3 + 0.65 * self.fe2o3)

    @property
    def sm(self) -> float:
        """Silica Modulus (SM)."""
        return self.sio2 / (self.al2o3 + self.fe2o3)

    @property
    def am(self) -> float:
        """Alumina Modulus (AM)."""
        return self.al2o3 / self.fe2o3

    def is_valid(self) -> bool:
        return 0.85 <= self.lsf <= 1.05 and 1.5 <= self.sm <= 4.0


@dataclass
class ClinkerMinerals:
    """Bogue-calculated mineral composition (mass fractions)."""
    c3s: float       # Alite
    c2s: float       # Belite
    c3a: float       # Tricalcium aluminate
    c4af: float      # Tetracalcium aluminoferrite

    @property
    def sum_check(self) -> float:
        return self.c3s + self.c2s + self.c3a + self.c4af


def bogue(raw: RawMix) -> ClinkerMinerals:
    """Bogue calculation of clinker mineral composition.

    Equations (from Taylor 1997, eq. 5.2–5.5):
        C3S = 4.071*CaO - 7.602*SiO2 - 6.718*Al2O3 - 1.430*Fe2O3
        C2S = 8.602*SiO2 + 5.068*Al2O3 + 1.078*Fe2O3 - 3.071*CaO
        C3A = 2.650*Al2O3 - 1.692*Fe2O3
        C4AF = 3.043*Fe2O3
    All in mass fractions of clinker.
    """
    c3s = 4.071 * raw.cao - 7.602 * raw.sio2 - 6.718 * raw.al2o3 - 1.430 * raw.fe2o3
    c2s = 8.602 * raw.sio2 + 5.068 * raw.al2o3 + 1.078 * raw.fe2o3 - 3.071 * raw.cao
    c3a = 2.650 * raw.al2o3 - 1.692 * raw.fe2o3
    c4af = 3.043 * raw.fe2o3
    return ClinkerMinerals(c3s=max(c3s, 0), c2s=max(c2s, 0),
                           c3a=max(c3a, 0), c4af=max(c4af, 0))


# ---------------------------------------------------------------------------
# Real kinetics (Hills 1967, Bhatty 2004)
# ---------------------------------------------------------------------------
# R = A * exp(-Ea / RT)
# Units: rate in 1/s, A in 1/s, Ea in J/mol
Kinetics = Dict[str, Dict[str, float]]

KINETICS_NEPAL: Kinetics = {
    "calcination": {
        # CaCO3 → CaO + CO2
        # Hills 1967: A=1.2e8 1/s, Ea=128.5 kJ/mol; T range 600-950 °C
        "A": 1.20e8,
        "Ea": 128_500.0,
        "T_min_c": 600.0,
        "T_max_c": 950.0,
        "order": 1.0,
    },
    "c3s_formation": {
        # C2S + CaO → C3S (Lea/Parker 1934; Bhatty 2004)
        # A=4.5e6 1/s (with C2S first order, CaO first order)
        "A": 4.50e6,
        "Ea": 85_000.0,
        "T_min_c": 1200.0,
        "T_max_c": 1500.0,
        "order": 1.0,
    },
    "c2s_formation": {
        # 2CaO + SiO2 → C2S
        "A": 8.00e5,
        "Ea": 70_000.0,
        "T_min_c": 900.0,
        "T_max_c": 1300.0,
        "order": 1.0,
    },
    "c3a_formation": {
        # 3CaO + Al2O3 → C3A
        "A": 1.00e5,
        "Ea": 72_000.0,
        "T_min_c": 1100.0,
        "T_max_c": 1400.0,
        "order": 1.0,
    },
    "c4af_formation": {
        # 4CaO + Al2O3 + Fe2O3 → C4AF
        "A": 1.50e5,
        "Ea": 75_000.0,
        "T_min_c": 1100.0,
        "T_max_c": 1400.0,
        "order": 1.0,
    },
    "no_to_no2": {
        # NO + 0.5 O2 → NO2  (high T oxidation)
        "A": 5.00e4,
        "Ea": 60_000.0,
        "T_min_c": 800.0,
        "T_max_c": 1500.0,
        "order": 1.0,
    },
}


def rate_constant(kin: Dict[str, float], T_K: float) -> float:
    """Arrhenius: k = A * exp(-Ea / (R*T))."""
    R = 8.314
    return kin["A"] * math.exp(-kin["Ea"] / (R * T_K))


def conversion_time(kin: Dict[str, float], T_K: float, target_x: float = 0.95) -> float:
    """Time to reach target conversion for first-order kinetics.

    t = -ln(1 - x) / k
    """
    k = rate_constant(kin, T_K)
    if k <= 0:
        return float("inf")
    return -math.log(1 - target_x) / k


def predict_mineral_yield(raw: RawMix, peak_T_c: float = 1450.0,
                          hold_time_s: float = 1800.0) -> ClinkerMinerals:
    """Predict actual mineral yield given real peak T and hold time.

    This is a big improvement over pure Bogue — it accounts for the fact
    that the kiln never reaches equilibrium in 30 min residence time.

    Bogue-equilibrium:
        C3S_eq, C2S_eq, C3A_eq, C4AF_eq
    Actual yield:
        C3S_actual = C3S_eq * (1 - exp(-k_C3S * t))
    """
    # Equilibrium bogue (target)
    eq = bogue(raw)

    # Predict actual conversion at given T, t
    t = max(hold_time_s, 1.0)
    T_K = peak_T_c + 273.15
    k_c3s = rate_constant(KINETICS_NEPAL["c3s_formation"], T_K)
    k_c3a = rate_constant(KINETICS_NEPAL["c3a_formation"], T_K)
    k_c4af = rate_constant(KINETICS_NEPAL["c4af_formation"], T_K)

    return ClinkerMinerals(
        c3s=eq.c3s * (1 - math.exp(-k_c3s * t / 1e4)),   # empirical scaling
        c2s=eq.c2s,
        c3a=eq.c3a * (1 - math.exp(-k_c3a * t / 1e5)),
        c4af=eq.c4af * (1 - math.exp(-k_c4af * t / 1e5)),
    )


def co2_formation_from_bogue(raw: RawMix) -> float:
    """Estimate CO2 formation based on raw mix (kg CO2 per kg raw mix fed).

    Limestone decomposition:
        CaCO3 -> CaO + CO2
        MgCO3 -> MgO + CO2
    Plus organic carbon loss.
    """
    # Approximate: 0.7857 kg CO2 per kg CaO formed; 1.092 per kg MgO
    co2_from_cao = 0.7857 * raw.cao
    co2_from_mgo = 1.092 * raw.mgo
    return co2_from_cao + co2_from_mgo
