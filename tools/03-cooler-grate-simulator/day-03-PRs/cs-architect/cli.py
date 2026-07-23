"""
nepal-cooler-sim CLI — v0.3.1.

Subcommands
-----------
* ``presets``    — list the cooler presets (PlantA, PlantB, etc.)
* ``run``        — solve a single cooler steady state and print KPIs
* ``coupled``    — kiln-cooler coupled iteration
* ``sensitivity`` — one-at-a-time sensitivity sweep
* ``export``     — write MATLAB / Octave scripts
* ``diagnose``   — JSON or human-readable readout of a single result
                   (Priya's ask: ``--json`` for piping, ``--human`` for
                   eyeballing; default is JSON so ``jq`` works)

Type-hints
----------
Every public function is type-hinted. The CLI dispatcher returns
``int`` (POSIX exit code) so it composes with shell pipelines.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO

# Force UTF-8 on stdout/stderr so the °C and ≤ glyphs in the
# diagnose --human output render correctly on Windows consoles
# (default cp1252 cannot encode them).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# Try a relative import first (production); fall back to absolute
# (smoke tests, ad-hoc imports, pytest collection).
try:
    from .cooler_types import solve_steady_state  # type: ignore[import-not-found]
    from .cooler_ode import (  # type: ignore[import-not-found]
        CoolerParameters, compute_outputs, run_to_steady_state,
        simulate_cooler,
    )
    from .io import (  # type: ignore[import-not-found]
        export_matlab_script, export_octave_script, save_results_csv,
        save_results_csv_legacy, save_results_json, save_results_pickle,
        to_natural_language, to_pdd_json,
    )
    from .kiln_link import coupled_kiln_cooler_steady_state  # type: ignore[import-not-found]
    from .sensitivity import sensitivity_sweep  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover — smoke-test path
    from nepal_cooler_sim.cooler_types import (  # type: ignore[no-redef]
        solve_steady_state,
    )
    from nepal_cooler_sim.cooler_ode import (  # type: ignore[no-redef]
        CoolerParameters, compute_outputs, run_to_steady_state,
        simulate_cooler,
    )
    from nepal_cooler_sim.io import (  # type: ignore[no-redef]
        export_matlab_script, export_octave_script, save_results_csv,
        save_results_csv_legacy, save_results_json, save_results_pickle,
        to_natural_language, to_pdd_json,
    )
    from nepal_cooler_sim.kiln_link import (  # type: ignore[no-redef]
        coupled_kiln_cooler_steady_state,
    )
    from nepal_cooler_sim.sensitivity import (  # type: ignore[no-redef]
        sensitivity_sweep,
    )

# ---------------------------------------------------------------------------
# Presets — PlantA duty case (Ramesh §5), PlantB (lower altitude),
# plantc-class 5000 tpd, PlantD.
# ---------------------------------------------------------------------------

PRESETS: dict[str, dict[str, Any]] = {
    "planta": dict(
        length_m=20.0, width_m=2.5, n_compartments=4,
        bed_depth_m=0.55, grate_speed_m_min=10.0,
        clinker_inlet_t_c=1380.0, clinker_outlet_t_c=180.0,
        under_grate_air_velocity_m_s=1.3,
        under_grate_air_temp_c=35.0,        # PlantA May design day
        clinker_throughput_t_h=66.0,
    ),
    "plantb": dict(
        length_m=26.0, width_m=3.2, n_compartments=5,
        bed_depth_m=0.65, grate_speed_m_min=12.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_t_c=160.0,
        under_grate_air_velocity_m_s=1.5,
        under_grate_air_temp_c=33.0,
        clinker_throughput_t_h=113.0,
    ),
    "plantc": dict(
        length_m=32.0, width_m=4.0, n_compartments=6,
        bed_depth_m=0.80, grate_speed_m_min=14.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_t_c=150.0,
        under_grate_air_velocity_m_s=1.6,
        under_grate_air_temp_c=30.0,
        clinker_throughput_t_h=210.0,
    ),
    "plantd": dict(
        length_m=24.0, width_m=3.0, n_compartments=5,
        bed_depth_m=0.60, grate_speed_m_min=11.0,
        clinker_inlet_t_c=1390.0, clinker_outlet_t_c=170.0,
        under_grate_air_velocity_m_s=1.4,
        under_grate_air_temp_c=32.0,
        clinker_throughput_t_h=90.0,
    ),
    # Legacy alias for v0.3.0 back-compat.
    "standard_5000tpd": dict(
        length_m=32.0, width_m=4.0, n_compartments=6,
        bed_depth_m=0.80, grate_speed_m_min=14.0,
        clinker_inlet_t_c=1400.0, clinker_outlet_t_c=150.0,
        under_grate_air_velocity_m_s=1.6,
        under_grate_air_temp_c=35.0,
        clinker_throughput_t_h=210.0,
    ),
    "planta_small": dict(
        length_m=20.0, width_m=2.5, n_compartments=4,
        bed_depth_m=0.55, grate_speed_m_min=10.0,
        clinker_inlet_t_c=1380.0, clinker_outlet_t_c=180.0,
        under_grate_air_velocity_m_s=1.3,
        under_grate_air_temp_c=30.0,
        clinker_throughput_t_h=66.0,
    ),
}


def _build_parameters(args: argparse.Namespace) -> CoolerParameters:
    """Build a CoolerParameters from preset + CLI overrides."""
    if args.preset:
        if args.preset not in PRESETS:
            raise SystemExit(
                f"Unknown preset {args.preset!r}. "
                f"Available: {', '.join(sorted(PRESETS))}"
            )
        p = CoolerParameters(**PRESETS[args.preset])
    else:
        p = CoolerParameters()

    if getattr(args, "grate_speed", None) is not None:
        p = p.model_copy(update={"grate_speed_m_min": args.grate_speed})
    if getattr(args, "air_velocity", None) is not None:
        p = p.model_copy(update={"under_grate_air_velocity_m_s": args.air_velocity})
    if getattr(args, "bed_depth", None) is not None:
        p = p.model_copy(update={"bed_depth_m": args.bed_depth})
    return p


# ---------------------------------------------------------------------------
# Subcommand handlers
# ---------------------------------------------------------------------------


def cmd_presets(args: argparse.Namespace) -> int:
    """List the cooler presets."""
    print(f"{'KEY':<22} {'CLINKER (t/h)':<14} {'LENGTH (m)':<11} {'COMPARTMENTS':<14}")
    print("-" * 65)
    for k, v in PRESETS.items():
        print(
            f"{k:<22} {v['clinker_throughput_t_h']:<14} "
            f"{v['length_m']:<11} {v['n_compartments']:<14}"
        )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Run a cooler steady-state solve and print / save KPIs."""
    p = _build_parameters(args)
    print(
        f"[nepal-cooler-sim] preset={args.preset or 'default'}, "
        f"grate_speed={p.grate_speed_m_min} m/min, "
        f"air_vel={p.under_grate_air_velocity_m_s} m/s, "
        f"bed_depth={p.bed_depth_m} m"
    )

    result = solve_steady_state(p)
    state = run_to_steady_state(p, max_t_s=p.t_end_s)
    outs = compute_outputs(state, p)

    print("\n=== Cooler steady-state (v0.3.1) ===")
    for k, v in outs.items():
        print(f"  {k:<32} = {v}")
    print(f"  first_law_imbalance           = {result.first_law_imbalance:.4f}")

    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        # v0.3.1 canonical CSV
        save_results_csv(out / "profile.csv", result, p)
        # Legacy (t, y, x) CSV for kiln-link compat. v0.3.0's
        # `simulate_cooler` is known-broken (the second-law clamp
        # and the column-stack shape do not match its own docstring);
        # the legacy CSV write can throw on the v0.3.0 solver, so
        # we tolerate that and continue. Once Aanya's compartment
        # solver lands in Day 3.5, this fallback goes away.
        try:
            t, y, x = simulate_cooler(p)
            save_results_csv_legacy(out / "trajectory.csv", t, y, x, p)
            legacy_written = True
        except (IndexError, ValueError) as exc:  # pragma: no cover
            print(
                f"\n[nepal-cooler-sim] NOTE: legacy (t, y, x) CSV write "
                f"skipped — v0.3.0 simulate_cooler() returned a shape "
                f"that does not match its own docstring ({exc}). "
                f"The v0.3.1 canonical files are still written."
            )
            legacy_written = False
        # JSON with both the v0.3.0 state_summary and the v0.3.1 result
        save_results_json(out / "outputs.json", state, p, outs, result=result)
        # Pickle for the verifier
        save_results_pickle(out / "result.pkl", result, p)
        files = [
            "profile.csv", "outputs.json", "result.pkl",
            *( ["trajectory.csv"] if legacy_written else [] ),
        ]
        print(f"\nWrote: {', '.join(str(out / f) for f in files)}")
    return 0


def cmd_coupled(args: argparse.Namespace) -> int:
    """Coupled kiln-cooler iteration."""
    p = _build_parameters(args)
    result = coupled_kiln_cooler_steady_state(p, max_iter=args.max_iter)
    print(f"Converged:    {result.converged}")
    print(f"Iterations:   {result.iterations}")
    print(f"Sec air T:    {result.secondary_air_t_c:.0f} C")
    print(f"Cooler eff:   {result.cooler_efficiency * 100.0:.1f} %")
    print(f"Recovered:    {result.secondary_air_recovered_kw:.0f} kW")
    print(f"Note:         {result.note}")
    return 0


def cmd_sensitivity(args: argparse.Namespace) -> int:
    """One-at-a-time sensitivity sweep."""
    p = _build_parameters(args)
    values = [float(v) for v in args.values.split(",")]
    rows = sensitivity_sweep(
        p, args.factor, values, output_key=args.output or "cooler_efficiency"
    )
    out_key = args.output or "cooler_efficiency"
    print(f"{'factor':<35} {'value':<10} {out_key}")
    print("-" * 75)
    for r in rows:
        print(f"{r['factor']:<35} {r['value']:<10.4f} {r['output']:.4f}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    """Export MATLAB / Octave scripts."""
    p = _build_parameters(args)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    if args.format in ("matlab", "both"):
        path = export_matlab_script(str(out / "cooler_sim.m"), p)
        print(f"Wrote: {path}")
    if args.format in ("octave", "both"):
        path = export_octave_script(str(out / "cooler_sim.m"), p)
        print(f"Wrote: {path}")
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    """Print a diagnose readout — JSON by default, --human for table.

    Default JSON so a sales engineer can pipe into ``jq`` for the
    pilot deck. ``--human`` flips to a fixed-width table for the
    floor / control room.
    """
    p = _build_parameters(args)
    result = solve_steady_state(p)
    state = run_to_steady_state(p, max_t_s=p.t_end_s)
    outs = compute_outputs(state, p)

    if args.human:
        print(f"Cooler diagnose ({p.length_m:.1f} m × {p.width_m:.1f} m, "
              f"{p.n_compartments} compartments)")
        print("-" * 70)
        print(f"  {'Clinker inlet':<32} : {p.clinker_inlet_t_c:>8.1f} °C")
        print(f"  {'Clinker outlet':<32} : {result.clinker_outlet_c:>8.1f} °C"
              f"   (target {p.clinker_outlet_t_c:.0f} °C)")
        print(f"  {'Secondary air outlet':<32} : {result.secondary_air_outlet_c:>8.1f} °C")
        print(f"  {'Cooler efficiency':<32} : {result.cooler_efficiency * 100.0:>8.1f} %")
        print(f"  {'First-law imbalance':<32} : "
              f"{result.first_law_imbalance * 100.0:>8.2f} %")
        print(f"  {'Air mass flow':<32} : {result.air_flow_kg_s:>8.1f} kg/s")
        print(f"  {'Clinker mass flow':<32} : {result.mass_flow_kg_s:>8.1f} kg/s")
        print()
        print(to_natural_language(result, p))
        return 0

    # JSON to stdout
    payload: dict[str, Any] = {
        "tool": "nepal_cooler_sim",
        "schema_version": "0.3.1",
        "parameters": json.loads(p.model_dump_json()),
        "result": result.to_dict(),
        "outputs": outs,
        "natural_language": to_natural_language(result, p),
        "pdd_json_preview": to_pdd_json(result, p),
    }
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    p = argparse.ArgumentParser(
        prog="nepal-cooler-sim",
        description=(
            "Day 3 v0.3.1 — 1-D grate clinker cooler simulator. "
            "Subcommands: presets, run, coupled, sensitivity, export, diagnose."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # presets
    sp = sub.add_parser("presets", help="List cooler presets")
    sp.set_defaults(func=cmd_presets)

    # run
    sp = sub.add_parser("run", help="Run cooler simulation (canonical v0.3.1)")
    sp.add_argument("--preset", choices=sorted(PRESETS))
    sp.add_argument("--grate-speed", type=float)
    sp.add_argument("--air-velocity", type=float)
    sp.add_argument("--bed-depth", type=float)
    sp.add_argument("--out", help="Output directory (CSV, JSON, pickle)")
    sp.set_defaults(func=cmd_run)

    # coupled
    sp = sub.add_parser("coupled", help="Coupled kiln-cooler iteration")
    sp.add_argument("--preset", choices=sorted(PRESETS))
    sp.add_argument("--max-iter", type=int, default=8)
    sp.set_defaults(func=cmd_coupled)

    # sensitivity
    sp = sub.add_parser("sensitivity", help="OAT sensitivity sweep")
    sp.add_argument("--preset", choices=sorted(PRESETS))
    sp.add_argument("--factor", required=True)
    sp.add_argument("--values", required=True,
                    help="Comma-separated values, e.g. 0.5,1.0,1.5,2.0")
    sp.add_argument("--output")
    sp.set_defaults(func=cmd_sensitivity)

    # export
    sp = sub.add_parser("export", help="Export MATLAB / Octave scripts")
    sp.add_argument("--preset", choices=sorted(PRESETS))
    sp.add_argument("--format", choices=["matlab", "octave", "both"], default="both")
    sp.add_argument("--out", required=True)
    sp.set_defaults(func=cmd_export)

    # diagnose (Priya)
    sp = sub.add_parser(
        "diagnose",
        help="Print a diagnose readout (JSON default, --human for table)",
    )
    sp.add_argument("--preset", choices=sorted(PRESETS))
    sp.add_argument("--grate-speed", type=float)
    sp.add_argument("--air-velocity", type=float)
    sp.add_argument("--bed-depth", type=float)
    sp.add_argument("--human", action="store_true",
                    help="Print a human-readable table instead of JSON")
    sp.set_defaults(func=cmd_diagnose)

    return p


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point. Returns the POSIX exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
