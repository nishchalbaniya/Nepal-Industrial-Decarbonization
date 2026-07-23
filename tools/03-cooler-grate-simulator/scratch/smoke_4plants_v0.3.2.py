"""Day 3 v0.3.2 — 4-plant ship-gate smoke test."""
import json
import time
from nepal_cooler_sim import (
    planta, plantb, plantc, plantd,
    solve_steady_state, compute_outputs,
    SEC_AIR_BAND_C, TERT_AIR_BAND_C, EXHAUST_AIR_BAND_C,
    CLINKER_OUTLET_BAND_C, COOLER_EFF_BAND,
)

print("=" * 78)
print("Day 3 v0.3.2 - 4 plant presets + ship-gate band check")
print("=" * 78)

results = []
for name, preset_fn in [
    ("PlantA (NIDC)", planta),
    ("PlantB (UCIL)", plantb),
    ("plantc", plantc),
    ("plantd", plantd),
]:
    t0 = time.perf_counter()
    p = preset_fn()
    s = solve_steady_state(p)
    o = compute_outputs(s, p)
    dt = time.perf_counter() - t0
    sec  = o["secondary_air_outlet_c"]
    tert = o["tertiary_air_outlet_c"]
    exh  = o["exhaust_air_outlet_c"]
    cli  = o["clinker_outlet_c"]
    eff  = o["cooler_efficiency"]
    fl   = o["first_law_imbalance"]
    srh  = o["sec_recovered_over_heat_recovered"]
    print()
    print(name)
    print(f"  tph={p.clinker_throughput_t_h} alt={p.altitude_m}m gratespd={p.grate_speed_m_min} m/min  ({dt:.2f}s)")
    print(f"  sec_air  = {sec:6.1f} C  [{int(SEC_AIR_BAND_C[0])}-{int(SEC_AIR_BAND_C[1])}]  pass={SEC_AIR_BAND_C[0]<=sec<=SEC_AIR_BAND_C[1]}")
    print(f"  tert_air = {tert:6.1f} C  [{int(TERT_AIR_BAND_C[0])}-{int(TERT_AIR_BAND_C[1])}]  pass={TERT_AIR_BAND_C[0]<=tert<=TERT_AIR_BAND_C[1]}")
    print(f"  exhaust  = {exh:6.1f} C  [{int(EXHAUST_AIR_BAND_C[0])}-{int(EXHAUST_AIR_BAND_C[1])}]  pass={EXHAUST_AIR_BAND_C[0]<=exh<=EXHAUST_AIR_BAND_C[1]}")
    print(f"  clinker  = {cli:6.1f} C  [{int(CLINKER_OUTLET_BAND_C[0])}-{int(CLINKER_OUTLET_BAND_C[1])}]  pass={CLINKER_OUTLET_BAND_C[0]<=cli<=CLINKER_OUTLET_BAND_C[1]}")
    print(f"  eff      = {eff:.3f}    [{COOLER_EFF_BAND[0]:.2f}-{COOLER_EFF_BAND[1]:.2f}]      pass={COOLER_EFF_BAND[0]<=eff<=COOLER_EFF_BAND[1]}")
    print(f"  1st-law  = {fl:.2e}  [<=0.02]                   pass={fl<=0.02}")
    print(f"  sec/heat = {srh:.3f}    [0.85-1.15]            pass={0.85<=srh<=1.15}")
    m_a_total = o["m_a_total_kg_s"]
    m_a_sec = o["m_a_sec_kg_s"]
    m_a_exh = o["m_a_exhaust_total_kg_s"]
    print(f"  m_a_total={m_a_total:.1f} m_a_sec={m_a_sec:.1f} m_a_exh_total={m_a_exh:.1f}")
    sanity = o["sanity"]
    print(f"  sanity air_above_clinker={sanity['air_above_clinker']} sec_in_band={sanity['sec_air_in_realistic_band']} cli_in_band={sanity['clinker_outlet_in_realistic_band']}")
    results.append((name, sec, tert, exh, cli, eff, fl, srh))

print()
print("=" * 78)
print("v0.3.2 honest summary (1/7 ship-gate bands pass on all 4 presets)")
print("=" * 78)
print("Band                                      PlantA  PlantB  PlantC  PlantD")
bands = [
    ("secondary_air_outlet_c [600-1000]", lambda r: r[1]),
    ("tertiary_air_outlet_c  [400-700]",  lambda r: r[2]),
    ("exhaust_air_outlet_c   [150-300]",  lambda r: r[3]),
    ("clinker_outlet_c       [120-200]",  lambda r: r[4]),
    ("cooler_efficiency      [0.65-0.85]",lambda r: r[5]),
    ("first_law_imbalance    [<=0.02]",   lambda r: r[6]),
    ("sec/heat               [0.85-1.15]",lambda r: r[7]),
]
for label, getter in bands:
    row = "  ".join(f"{getter(r):>8.2f}" for r in results)
    print(f"{label:<40} {row}")
