"""
nepal-cooler-sim CLI.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .cooler_ode import (
    CoolerParameters, run_to_steady_state, compute_outputs, simulate_cooler,
)
from .kiln_link import coupled_kiln_cooler_steady_state
from .sensitivity import sensitivity_sweep
from .io import save_results_csv, save_results_json, export_matlab_script, export_octave_script


PRESETS = {
    "standard_5000tpd": dict(
        length_m=32.0, width_m=4.0, n_compartments=6,
        bed_depth_m=0.80, grate_speed_m_min=14.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_t_c=150.0,
        under_grate_air_velocity_m_s=1.6,
        under_grate_air_temp_c=35.0,
        clinker_throughput_t_h=210.0,
    ),
    "hetauda_small": dict(
        length_m=20.0, width_m=2.5, n_compartments=4,
        bed_depth_m=0.55, grate_speed_m_min=10.0,
        clinker_inlet_t_c=1380.0, clinker_outlet_t_c=180.0,
        under_grate_air_velocity_m_s=1.3,
        under_grate_air_temp_c=30.0,
        clinker_throughput_t_h=66.0,
    ),
    "udayapur": dict(
        length_m=26.0, width_m=3.2, n_compartments=5,
        bed_depth_m=0.65, grate_speed_m_min=12.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_t_c=160.0,
        under_grate_air_velocity_m_s=1.5,
        under_grate_air_temp_c=33.0,
        clinker_throughput_t_h=113.0,
    ),
}


def cmd_run(args):
    if args.preset:
        overrides = PRESETS[args.preset]
        p = CoolerParameters(**overrides)
    else:
        p = CoolerParameters()

    if args.grate_speed is not None:
        p = p.model_copy(update={"grate_speed_m_min": args.grate_speed})
    if args.air_velocity is not None:
        p = p.model_copy(update={"under_grate_air_velocity_m_s": args.air_velocity})
    if args.bed_depth is not None:
        p = p.model_copy(update={"bed_depth_m": args.bed_depth})

    print(f"[nepal-cooler-sim] preset={args.preset or 'default'}, "
          f"grate_speed={p.grate_speed_m_min} m/min, "
          f"air_vel={p.under_grate_air_velocity_m_s} m/s, "
          f"bed_depth={p.bed_depth_m} m")

    state = run_to_steady_state(p, max_t_s=p.t_end_s)
    outs = compute_outputs(state, p)

    print("\n=== Cooler steady-state ===")
    for k, v in outs.items():
        print(f"  {k:<30} = {v}")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        t, y, x = simulate_cooler(p)
        save_results_csv(out / "trajectory.csv", t, y, x, p)
        save_results_json(out / "outputs.json", state, p, outs)
        print(f"\nWrote: {out}/trajectory.csv, {out}/outputs.json")
    return 0


def cmd_coupled(args):
    overrides = PRESETS.get(args.preset, PRESETS["standard_5000tpd"])
    p = CoolerParameters(**overrides)
    result = coupled_kiln_cooler_steady_state(p, max_iter=args.max_iter)
    print(f"Converged:    {result.converged}")
    print(f"Iterations:   {result.iterations}")
    print(f"Sec air T:    {result.secondary_air_t_c:.0f} C")
    print(f"Cooler eff:   {result.cooler_efficiency*100:.1f} %")
    print(f"Recovered:    {result.secondary_air_recovered_kw:.0f} kW")
    print(f"Note:         {result.note}")
    return 0


def cmd_sensitivity(args):
    overrides = PRESETS.get(args.preset, PRESETS["standard_5000tpd"])
    base = CoolerParameters(**overrides)
    values = [float(v) for v in args.values.split(",")]
    rows = sensitivity_sweep(base, args.factor, values,
                             output_key=args.output or "cooler_efficiency")
    print(f"{'factor':<35} {'value':<10} {args.output or 'cooler_efficiency'}")
    print("-" * 75)
    for r in rows:
        print(f"{r['factor']:<35} {r['value']:<10.4f} {r['output']:.4f}")
    return 0


def cmd_export(args):
    overrides = PRESETS.get(args.preset, PRESETS["standard_5000tpd"])
    p = CoolerParameters(**overrides)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.format in ("matlab", "both"):
        path = export_matlab_script(str(out / "cooler_sim.m"), p)
        print(f"Wrote: {path}")
    if args.format in ("octave", "both"):
        path = export_octave_script(str(out / "cooler_sim.m"), p)
        print(f"Wrote: {path}")
    return 0


def cmd_presets(args):
    print(f"{'KEY':<22} {'CLINKER (t/h)':<14} {'LENGTH (m)':<11}")
    print("-" * 55)
    for k, v in PRESETS.items():
        print(f"{k:<22} {v['clinker_throughput_t_h']:<14} {v['length_m']:<11}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="nepal-cooler-sim",
                                 description="Day 3 — Grate clinker cooler simulator")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("presets", help="List cooler presets")
    sp.set_defaults(func=cmd_presets)

    sp = sub.add_parser("run", help="Run cooler simulation")
    sp.add_argument("--preset")
    sp.add_argument("--grate-speed", type=float)
    sp.add_argument("--air-velocity", type=float)
    sp.add_argument("--bed-depth", type=float)
    sp.add_argument("--out", help="Output directory")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("coupled", help="Coupled kiln-cooler iteration")
    sp.add_argument("--preset")
    sp.add_argument("--max-iter", type=int, default=8)
    sp.set_defaults(func=cmd_coupled)

    sp = sub.add_parser("sensitivity", help="OAT sensitivity")
    sp.add_argument("--preset")
    sp.add_argument("--factor", required=True)
    sp.add_argument("--values", required=True)
    sp.add_argument("--output")
    sp.set_defaults(func=cmd_sensitivity)

    sp = sub.add_parser("export", help="Export MATLAB/Octave scripts")
    sp.add_argument("--preset")
    sp.add_argument("--format", choices=["matlab", "octave", "both"], default="both")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_export)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args) or 0


if __name__ == "__main__":
    sys.exit(main())
