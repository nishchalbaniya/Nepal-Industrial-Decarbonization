"""Helper: test _solve_compartment in isolation. Used during debugging.
Not part of the PR.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cooler_ode import _solve_compartment
from plants import planta
import numpy as np

p = planta()
comps = p.effective_compartments()
comp = comps[0]
rho_air = p.air_density_kg_m3()
T_c_in = p.clinker_inlet_t_c
T_a_in = comp.inlet_air_t_c
T_c_out, T_a_out, x_loc, Tc, Ta = _solve_compartment(
    T_c_in, T_a_in, p.length_m/4, 5, p, comp, rho_air,
)
print(f"T_c_in={T_c_in}, T_a_in={T_a_in}")
print(f"T_c_out={T_c_out}, T_a_out={T_a_out}")
