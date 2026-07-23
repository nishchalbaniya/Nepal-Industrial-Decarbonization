"""Helper: inspect per-compartment solve for one compartment.
Used during debugging the v0.3.0 -> v0.3.1 migration. Not part of the PR.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cooler_ode import solve_steady_state
from plants import hetauda
import numpy as np

p = hetauda()
state = solve_steady_state(p)
print("compartments (in-spatial-order):")
for c in state.compartments:
    print(f"  c{c.index}: T_c_in={c.t_clinker_in_c:.1f} -> T_c_out={c.t_clinker_out_c:.1f}, "
          f"T_a_in={c.t_air_in_c:.1f} -> T_a_out={c.t_air_out_c:.1f}, "
          f"is_sec={c.is_secondary_zone}, is_exh={c.is_exhaust_zone}")
print()
print(f"t_clinker profile (sample): {state.t_clinker_c}")
print(f"t_air profile (sample): {state.t_air_c}")
print(f"clinker_outlet_c: {state.clinker_outlet_c}")
print(f"sec_air: {state.secondary_air_outlet_c}, exh_air: {state.exhaust_air_outlet_c}")
print(f"tertiary: {state.tertiary_air_outlet_c}")
