"""Helper: check air-temperature profile across the bed. Used during
debugging. Not part of the PR.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cooler_ode import solve_steady_state
from plants import planta
import numpy as np

p = planta()
state = solve_steady_state(p)
print("compartments:")
for c in state.compartments:
    print(f"  c{c.index}: T_c_in={c.t_clinker_in_c:.1f} -> T_c_out={c.t_clinker_out_c:.1f}, "
          f"T_a_in={c.t_air_in_c:.1f} -> T_a_out={c.t_air_out_c:.1f}")
print()
print("T_a profile (full):")
print(state.t_air_c)
print()
print("T_c profile (full):")
print(state.t_clinker_c)
print()
print("T_a - T_c (positive = 2nd law violation):")
diff = state.t_air_c - state.t_clinker_c
print(diff)
print(f"max T_a - T_c: {diff.max():.1f}")
