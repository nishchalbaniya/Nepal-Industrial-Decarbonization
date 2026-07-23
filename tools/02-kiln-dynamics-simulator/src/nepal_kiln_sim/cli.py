"""
nepal-kiln-sim CLI.

Usage examples:

    nepal-kiln-sim plants --list
    nepal-kiln-sim fuels --list
    nepal-kiln-sim run --plant planta --fuel coal_bituminous_NP --out ./out
    nepal-kiln-sim sensitivity --plant planta --factor fuel_rate_t_h --values 8,10,12,14
    nepal-kiln-sim calibrate --plant planta --sec 3850 --co2-intensity 880
    nepal-kiln-sim export-matlab --plant planta --out ./matlab
    nepal-kiln-sim export-octave --plant planta --out ./matlab
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

from .kiln_ode import KilnParameters, run_to_steady_state, compute_outputs, simulate_kiln
from .plants import PLANT_PRESETS, get_plant_preset, list_plants
from .fuels import FUEL_DATABASE, get_fuel, list_fuels, compute_blend_ef, compute_flame_temperature
from .sensitivity import sensitivity_sweep, morris_elementary_effects
from .calibration import calibrate_to_plant
from .io import save_results_csv, save_results_json, export_matlab_script, export_octave_script


def cmd_plants(args) -> int:
    if args.list:
        print(f"{'KEY':<22} {'NAME':<48} {'CAPACITY (t/yr)':<14} {'LOCATION'}")
        print("-" * 100)
        for p in list_plants():
            print(f"{p.key:<22} {p.name[:46]:<48} {p.capacity_t_yr:<14} {p.location}")
        return 0
    return 1


def cmd_fuels(args) -> int:
    if args.list:
        print(f"{'KEY':<24} {'CATEGORY':<10} {'NCV (GJ/t)':<12} {'EF (kgCO2/GJ)':<14} {'BIOGENIC':<10} {'PRICE (USD/t)':<14}")
        print("-" * 95)
        for f in list_fuels():
            print(f"{f.key:<24} {f.category:<10} {f.ncvc_gj_per_t:<12.2f} {f.ef_kgco2_per_gj:<14.2f} {f.biogenic_fraction:<10.2f} {f.price_usd_per_t:<14.0f}")
        return 0
    if args.flame:
        f = get_fuel(args.flame)
        if f is None:
            print(f"Unknown fuel: {args.flame}", file=sys.stderr)
            return 2
        t = compute_flame_temperature(f, air_excess=args.excess, air_temp_k=args.air_temp)
        print(f"Fuel: {f.name}")
        print(f"Adiabatic flame temperature: {t:.1f} K ({t - 273.15:.1f} °C)")
        return 0
    if args.blend:
        # e.g. --blend coal_bituminous_NP:0.7,biomass_rice_husk:0.3
        pairs = [x.strip() for x in args.blend.split(",")]
        blend = {}
        for pair in pairs:
            k, v = pair.split(":")
            blend[k.strip()] = float(v)
        result = compute_blend_ef(blend)
        print(json.dumps(result, indent=2))
        return 0
    return 1


def cmd_run(args) -> int:
    if args.plant:
        preset = get_plant_preset(args.plant)
        if preset is None:
            print(f"Unknown plant: {args.plant}", file=sys.stderr)
            return 2
        p = preset.parameters
    else:
        p = KilnParameters()

    if args.fuel:
        p = p.model_copy(update={"fuel_type": args.fuel})
    if args.fuel_rate is not None:
        p = p.model_copy(update={"fuel_rate_t_h": args.fuel_rate})
    if args.raw_meal is not None:
        p = p.model_copy(update={"raw_meal_throughput_t_h": args.raw_meal})
    if args.t_end is not None:
        p = p.model_copy(update={"t_end_s": args.t_end})

    print(f"[nepal-kiln-sim] plant={args.plant or 'default'}, fuel={p.fuel_type}, t_end={p.t_end_s}s")

    state = run_to_steady_state(p, max_t_s=p.t_end_s)
    outs = compute_outputs(state, p)

    print("\n=== Steady-state outputs ===")
    for k, v in outs.items():
        print(f"  {k:<35} = {v:.4g}")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        t, y, x = simulate_kiln(p)
        save_results_csv(out / "trajectory.csv", t, y, x, p)
        save_results_json(out / "outputs.json", state, p, outs)
        print(f"\nWrote: {out}/trajectory.csv, {out}/outputs.json")
    return 0


def cmd_sensitivity(args) -> int:
    preset = get_plant_preset(args.plant) if args.plant else None
    base = preset.parameters if preset else KilnParameters()
    values = [float(v) for v in args.values.split(",")]
    rows = sensitivity_sweep(base, args.factor, values,
                             output_key=args.output or "sec_mj_per_t_clinker")
    print(f"{'factor':<22} {'value':<10} {args.output or 'sec_mj_per_t_clinker'}")
    print("-" * 60)
    for r in rows:
        print(f"{r['factor']:<22} {r['value']:<10.4f} {r['output']:.4g}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(rows, f, indent=2)
        print(f"Wrote: {args.out}")
    return 0


def cmd_calibrate(args) -> int:
    preset = get_plant_preset(args.plant) if args.plant else None
    base = preset.parameters if preset else KilnParameters()
    observed = {}
    if args.sec is not None:
        observed["sec_mj_per_t_clinker"] = args.sec
    if args.co2_intensity is not None:
        observed["co2_intensity_kg_per_t_clinker"] = args.co2_intensity
    if args.burning_zone_c is not None:
        observed["t_burning_zone_c"] = args.burning_zone_c
    if not observed:
        print("Provide at least one of --sec, --co2-intensity, --burning-zone-c",
              file=sys.stderr)
        return 2
    result = calibrate_to_plant(base, observed, maxiter=args.maxiter)
    print(f"Success: {result.success}")
    print(f"RMSE:   {result.rmse:.4g}")
    print(f"Iters:  {result.n_iterations}")
    print(f"Msg:    {result.message}")
    print("\n--- Calibrated parameters ---")
    for k, v in result.best_params.model_dump().items():
        if k in base.model_dump() and base.model_dump()[k] != v:
            print(f"  {k}: {base.model_dump()[k]} -> {v}")
    print("\n--- Observed vs Simulated ---")
    for k in observed:
        print(f"  {k:<35} obs={observed[k]:<10.4g}  sim={result.simulated.get(k, 0.0):<10.4g}")
    return 0 if result.success else 3


def cmd_export(args) -> int:
    preset = get_plant_preset(args.plant) if args.plant else None
    p = preset.parameters if preset else KilnParameters()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.format in ("matlab", "both"):
        path = export_matlab_script(str(out / "kiln_sim.m"), p)
        print(f"Wrote: {path}")
    if args.format in ("octave", "both"):
        path = export_octave_script(str(out / "kiln_sim.m"), p)
        print(f"Wrote: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nepal-kiln-sim",
                                 description="Day 2 — Rotary cement kiln dynamics simulator")
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("plants", help="List plant presets")
    sp.add_argument("--list", action="store_true")
    sp.set_defaults(func=cmd_plants)

    sp = sub.add_parser("fuels", help="List fuels or compute flame T / blend")
    sp.add_argument("--list", action="store_true")
    sp.add_argument("--flame", help="Fuel key to compute flame temperature")
    sp.add_argument("--excess", type=float, default=1.10)
    sp.add_argument("--air-temp", type=float, default=800.0)
    sp.add_argument("--blend", help="fuel:frac,fuel:frac ...")
    sp.set_defaults(func=cmd_fuels)

    sp = sub.add_parser("run", help="Run a single simulation")
    sp.add_argument("--plant")
    sp.add_argument("--fuel")
    sp.add_argument("--fuel-rate", type=float)
    sp.add_argument("--raw-meal", type=float)
    sp.add_argument("--t-end", type=float)
    sp.add_argument("--out", help="Output directory")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("sensitivity", help="One-at-a-time sensitivity")
    sp.add_argument("--plant")
    sp.add_argument("--factor", required=True)
    sp.add_argument("--values", required=True, help="Comma-separated values")
    sp.add_argument("--output", help="Output key (default sec_mj_per_t_clinker)")
    sp.add_argument("--out", help="JSON output path")
    sp.set_defaults(func=cmd_sensitivity)

    sp = sub.add_parser("calibrate", help="Calibrate to plant KPIs")
    sp.add_argument("--plant")
    sp.add_argument("--sec", type=float)
    sp.add_argument("--co2-intensity", type=float)
    sp.add_argument("--burning-zone-c", type=float)
    sp.add_argument("--maxiter", type=int, default=30)
    sp.set_defaults(func=cmd_calibrate)

    sp = sub.add_parser("export", help="Export MATLAB/Octave scripts")
    sp.add_argument("--plant")
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
