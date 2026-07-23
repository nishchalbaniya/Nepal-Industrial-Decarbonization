"""Smoke test: run all 4 plant presets and print the operator KPIs.
Useful for a quick visual check of the v0.3.1 model. Run with:
    py _smoke.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cooler_ode import solve_steady_state, compute_outputs
from plants import hetauda, udayapur, hongshi_shivam, ghorahi, PRESETS
from compartments import build_compartment_inventory, check_second_law_compartments

for name, fn in PRESETS.items():
    p = fn()
    s = solve_steady_state(p)
    out = compute_outputs(s, p)
    inv = build_compartment_inventory(p)
    viol = check_second_law_compartments(s)
    print(f"=== {name} (altitude {p.altitude_m:.0f} m) ===")
    print(f"  rho_air:        {p.air_density_kg_m3():.3f} kg/m3")
    print(f"  sec_air:        {s.secondary_air_outlet_c:.1f} C")
    print(f"  tert_air:       {s.tertiary_air_outlet_c:.1f} C")
    print(f"  exh_air:        {s.exhaust_air_outlet_c:.1f} C")
    print(f"  clinker_out:    {s.clinker_outlet_c:.1f} C")
    print(f"  eff:            {s.cooler_efficiency:.3f}")
    print(f"  first_law:      {s.first_law_imbalance:.4f}")
    print(f"  mj/t_cli:       {s.mj_per_t_cli_recovered:.1f}")
    print(f"  sec_stoich:     {s.secondary_air_stoich_ratio:.2f}")
    print(f"  fan_power:      {s.fan_power_kw:.1f} kW")
    print(f"  dp_total:       {s.bed_pressure_drop_mm_h2o:.1f} mmH2O")
    print(f"  compartments:   {len(s.compartments)}")
    print(f"  2nd-law viol:   {viol if viol else 'NONE'}")
    print(f"  sanity:         {out['sanity']}")
    print()
