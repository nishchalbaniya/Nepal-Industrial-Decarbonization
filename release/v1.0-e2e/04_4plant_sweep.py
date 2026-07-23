"""
Day 12 demo -- 4-plant sweep. Runs the cooler on all 4 cement plants
the v1.0 supports and writes a single JSON with the KPIs.
"""
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parent.parent / "repo"
for p in (str(_REPO / "pro" / "src"),
          str(_REPO / "tools" / "02-kiln-dynamics-simulator" / "src"),
          str(_REPO / "tools" / "03-cooler-grate-simulator" / "src")):
    sys.path.insert(0, p)

import nepal_cooler_sim
import nepal_kiln_sim

PLANTS = ["planta", "plantb", "plantc", "plantd"]
COOLER_PRESETS = {
    "planta":       nepal_cooler_sim.planta,
    "plantb":      nepal_cooler_sim.plantb,
    "plantc": nepal_cooler_sim.plantc,
    "plantd":       nepal_cooler_sim.plantd,
}
KILN_PRESETS = {
    "planta":       "planta",
    "plantb":      "plantb",
    "plantc": "plantc",
    "plantd":       "plantd",
}

# ship-gate bands
BANDS = {
    "secondary_air_outlet_c": (600, 1000),
    "tertiary_air_outlet_c":  (400, 700),
    "exhaust_air_outlet_c":   (150, 300),
    "clinker_outlet_c":       (120, 200),
    "cooler_efficiency":      (0.65, 0.85),
    "first_law_imbalance":    (0, 0.02),
}

def in_band(name, v):
    lo, hi = BANDS[name]
    if name == "first_law_imbalance":
        return v <= hi
    return lo <= v <= hi

results = {"plants": {}, "summary": {"n_plants": 0, "n_total_pass": 0, "n_total_bands": 0}}

for plant in PLANTS:
    # Cooler
    p = COOLER_PRESETS[plant]()
    cstate = nepal_cooler_sim.solve_steady_state(p)
    cout = nepal_cooler_sim.compute_outputs(cstate, p)
    # Kiln
    kp = nepal_kiln_sim.get_plant_preset(KILN_PRESETS[plant]).parameters
    kstate = nepal_kiln_sim.run_to_steady_state(kp)
    kout = nepal_kiln_sim.compute_outputs(kstate, kp)
    # CBAM (per JRC Dec 2023 transitional default for grey/white clinker)
    cbam_direct = 0.83   # t CO2e/t clinker
    cbam_indirect = 0.04 # t CO2e/t clinker
    cbam_total = cbam_direct + cbam_indirect
    # Annual footprint at 330 operating days
    tpd = p.clinker_throughput_t_h * 24
    annual_t = tpd * 330
    annual_cbam_kt = annual_t * cbam_total / 1000  # kt CO2e / year
    # Annual fuel savings vs uncalibrated baseline (assumption: 5% SEC reduction)
    sec_mj_t = kout.get("sec_mj_per_t_clinker", 0)  # MJ/t
    baseline_sec = 3269  # MJ/t industry avg (cement sustainability initiative 2018)
    sec_improvement_pct = max(0, (baseline_sec - sec_mj_t) / baseline_sec * 100)
    # Pass count
    bands_pass = {b: in_band(b, cout.get(b, float("nan"))) for b in BANDS}
    n_pass = sum(1 for v in bands_pass.values() if v)
    results["plants"][plant] = {
        "altitude_m":            p.altitude_m,
        "throughput_t_h":        p.clinker_throughput_t_h,
        "annual_t":              annual_t,
        "cooler": {
            "secondary_air_outlet_c": round(cout["secondary_air_outlet_c"], 1),
            "tertiary_air_outlet_c":  round(cout["tertiary_air_outlet_c"], 1),
            "exhaust_air_outlet_c":   round(cout["exhaust_air_outlet_c"], 1),
            "clinker_outlet_c":       round(cout["clinker_outlet_c"], 1),
            "cooler_efficiency":      round(cout["cooler_efficiency"], 3),
            "first_law_imbalance":    float(f"{cout['first_law_imbalance']:.2e}"),
            "mj_per_t_cli_recovered": round(cout["mj_per_t_cli_recovered"], 1),
        },
        "kiln": {
            "t_burning_zone_c":  round(kout["t_burning_zone_c"], 1),
            "thermal_efficiency": round(kout["thermal_efficiency"], 3),
            "sec_mj_per_t_clinker": round(kout.get("sec_mj_per_t_clinker", 0), 1),
            "co2_intensity_kg_per_t_clinker": round(kout.get("co2_intensity_kg_per_t_clinker", 0), 1),
        },
        "cbam": {
            "direct_t_co2e_t": cbam_direct,
            "indirect_t_co2e_t": cbam_indirect,
            "total_t_co2e_t": cbam_total,
            "annual_kt_co2e": round(annual_cbam_kt, 1),
            "cbam_price_eur_t": 80,  # mid-2026 EUA price
            "annual_cbam_cost_eur": round(annual_cbam_kt * 1000 * cbam_total * 80, 0),
        },
        "fuel_savings": {
            "current_sec_mj_t": round(sec_mj_t, 1),
            "baseline_sec_mj_t": baseline_sec,
            "improvement_pct": round(sec_improvement_pct, 1),
            "annual_fuel_savings_usd": round(annual_t * (baseline_sec - sec_mj_t) / 1000 * 0.015 * 330 / 330, 0),
        },
        "ship_gate_pass": bands_pass,
        "n_bands_pass": n_pass,
        "n_bands_total": 6,
    }
    results["summary"]["n_plants"] += 1
    results["summary"]["n_total_pass"] += n_pass
    results["summary"]["n_total_bands"] += 6

# Total addressable footprint
total_annual_t = sum(d["annual_t"] for d in results["plants"].values())
total_cbam_kt = sum(d["cbam"]["annual_kt_co2e"] for d in results["plants"].values())
results["summary"]["total_annual_throughput_t"] = total_annual_t
results["summary"]["total_annual_co2e_kt"] = round(total_cbam_kt, 1)
results["summary"]["band_definition"] = BANDS
results["notes"] = {
    "calibration": "v0.5.0 default preset (not plant-specific; see calibrate cooler --target csv)",
    "cbam_source": "EC DG TAXUD 'Default values for the transitional period' Dec 2023 (JRC), Section 2.3 cement table",
    "cbam_direct": "0.83 t CO2e/t clinker for grey/white clinker (CN 2523 10 00)",
    "cbam_indirect": "0.04 t CO2e/t clinker (electricity at 2023 Nepal grid factor ~0.02 t/MWh)",
    "cbam_2026+": "Country-specific values with 10/20/30% mark-up (Implementing Reg 2025/2621)",
    "sec_baseline": "3269 MJ/t per Cement Sustainability Initiative 2018 (Getting the Numbers Right)",
    "ship_gate_failing_bands_honest": "3/6 bands fail on default-preset v0.5.0 PlantA model (tertiary, exhaust, clinker). Unblocked with real plant data or v0.6.0 model changes.",
}

out_path = _HERE / "json" / "04_4plant_sweep.json"
out_path.write_text(json.dumps(results, indent=2))
print(f"wrote {out_path}")
print(f"\n4-plant sweep ({results['summary']['n_plants']} plants, {results['summary']['n_total_bands']} band slots):")
for plant, d in results["plants"].items():
    print(f"  {plant:18s} {d['throughput_t_h']:5.0f} t/h  annual {d['annual_t']/1000:6.0f} kt  "
          f"sec_air {d['cooler']['secondary_air_outlet_c']:5.0f}  "
          f"eff {d['cooler']['cooler_efficiency']:.2f}  "
          f"CBAM {d['cbam']['annual_kt_co2e']:5.1f} kt CO2e/yr  "
          f"ship-gate {d['n_bands_pass']}/6")
print(f"\nTotal annual throughput: {total_annual_t/1000:.0f} kt clinker")
print(f"Total CBAM exposure:     {total_cbam_kt:.0f} kt CO2e/yr")
