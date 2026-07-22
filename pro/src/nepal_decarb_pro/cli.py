"""
nepal-decarb CLI -- the single user-facing entry point.

Subcommands:
  nepal-decarb version
  nepal-decarb status                  (show installed modules + versions)
  nepal-decarb run cooler --plant hetauda
  nepal-decarb run kiln --plant hetauda --fuel coal_bituminous_NP
  nepal-decarb run coupled --plant hetauda
  nepal-decarb calibrate cooler --target synthetic
  nepal-decarb export step-cooler --calibration day-05
  nepal-decarb demo                   (run cooler + kiln + calibration end-to-end)
  nepal-decarb install                (install on Windows; place .bat + .ps1 in dist/)

Examples:
  nepal-decarb run cooler --plant hetauda
  nepal-decarb run coupled --plant hetauda --out ./out
  nepal-decarb demo --plant hetauda --out ./demo-output
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


__version__ = "0.6.0"


def cmd_version(args) -> int:
    print("nepal-decarb v" + __version__)
    print()
    print("Modules:")
    try:
        import nepal_kiln_sim
        print(f"  nepal_kiln_sim    v{nepal_kiln_sim.__version__}")
    except ImportError as e:
        print(f"  nepal_kiln_sim    NOT INSTALLED ({e})")
    try:
        import nepal_cooler_sim
        print(f"  nepal_cooler_sim v{nepal_cooler_sim.__version__}")
    except ImportError as e:
        print(f"  nepal_cooler_sim NOT INSTALLED ({e})")
    try:
        import nepal_decarb_pro
        print(f"  nepal_decarb_pro v{nepal_decarb_pro.__version__}")
    except ImportError as e:
        print(f"  nepal_decarb_pro v{__version__} (this package)")
    return 0


def cmd_status(args) -> int:
    print("nepal-decarb v" + __version__)
    print()
    print("Tool stack:")
    import sys
    print(f"  Python:        {sys.version.split()[0]}")
    import platform
    print(f"  OS:            {platform.system()} {platform.release()}")
    try:
        import FreeCAD
        print(f"  FreeCAD:       v{FreeCAD.Version()[0]}.{FreeCAD.Version()[1]}.{FreeCAD.Version()[2]}")
    except ImportError:
        print(f"  FreeCAD:       NOT INSTALLED")
    try:
        import numpy
        print(f"  NumPy:         v{numpy.__version__}")
    except ImportError:
        print(f"  NumPy:         NOT INSTALLED")
    try:
        import scipy
        print(f"  SciPy:         v{scipy.__version__}")
    except ImportError:
        print(f"  SciPy:         NOT INSTALLED")
    try:
        import pydantic
        print(f"  Pydantic:      v{pydantic.__version__}")
    except ImportError:
        print(f"  Pydantic:      NOT INSTALLED")
    try:
        import fastapi
        print(f"  FastAPI:       v{fastapi.__version__}")
    except ImportError:
        print(f"  FastAPI:       NOT INSTALLED")
    return 0


def cmd_run_cooler(args) -> int:
    """Run the cooler simulator on a plant preset."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "03-cooler-grate-simulator" / "src"))
    try:
        from nepal_cooler_sim import (
            hetauda, udayapur, hongshi_shivam, ghorahi,
            solve_steady_state, compute_outputs,
        )
    except ImportError as e:
        print(f"ERROR: nepal_cooler_sim not importable: {e}")
        return 1
    presets = {
        "hetauda": hetauda,
        "udayapur": udayapur,
        "hongshi-shivam": hongshi_shivam,
        "ghorahi": ghorahi,
    }
    if args.plant not in presets:
        print(f"ERROR: unknown plant '{args.plant}'. Available: {list(presets)}")
        return 1
    p = presets[args.plant]()
    state = solve_steady_state(p)
    out = compute_outputs(state, p)
    print(f"[cooler] plant={args.plant} tph={p.clinker_throughput_t_h} alt={p.altitude_m}m")
    print(f"  sec_air_T  = {out['secondary_air_outlet_c']:.1f} C  (band 600-1000)")
    print(f"  tert_air_T = {out['tertiary_air_outlet_c']:.1f} C  (band 400-700)")
    print(f"  exhaust_T  = {out['exhaust_air_outlet_c']:.1f} C  (band 150-300)")
    print(f"  clinker_T  = {out['clinker_outlet_c']:.1f} C  (band 120-200)")
    print(f"  efficiency  = {out['cooler_efficiency']:.3f}    (band 0.65-0.85)")
    print(f"  1st-law    = {out['first_law_imbalance']:.2e} (band <=0.02)")
    print(f"  sec/Qrec   = {out['sec_recovered_over_heat_recovered']:.3f}    (band 0.85-1.15)")
    if args.out:
        out_path = Path(args.out)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "cooler_outputs.json").write_text(json.dumps(out, indent=2, default=str))
        print(f"  wrote {out_path}/cooler_outputs.json")
    return 0


def cmd_run_kiln(args) -> int:
    """Run the kiln simulator on a plant preset."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "02-kiln-dynamics-simulator" / "src"))
    try:
        from nepal_kiln_sim import (
            PLANT_PRESETS, get_plant_preset, run_to_steady_state, compute_outputs,
        )
    except ImportError as e:
        print(f"ERROR: nepal_kiln_sim not importable: {e}")
        return 1
    preset = get_plant_preset(args.plant) if args.plant in PLANT_PRESETS else None
    if preset is None:
        print(f"ERROR: unknown plant '{args.plant}'. Available: {list(PLANT_PRESETS)}")
        return 1
    p = preset.parameters
    if args.fuel:
        p.fuel_key = args.fuel
    state = run_to_steady_state(p)
    out = compute_outputs(state, p)
    print(f"[kiln] plant={args.plant} fuel={getattr(p, 'fuel_key', '?')}")
    for k, v in list(out.items())[:20]:
        if isinstance(v, (int, float)):
            print(f"  {k:<35} = {v:.4f}")
    if args.out:
        out_path = Path(args.out)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "kiln_outputs.json").write_text(json.dumps(out, indent=2, default=str))
        print(f"  wrote {out_path}/kiln_outputs.json")
    return 0


def cmd_run_coupled(args) -> int:
    """Run the coupled kiln-cooler simulator."""
    print("[coupled] running kiln + cooler in sequence...")
    rc = cmd_run_kiln(args)
    if rc != 0:
        return rc
    return cmd_run_cooler(args)


def cmd_calibrate_cooler(args) -> int:
    """Run the cooler calibration. Defaults to v0.5.0 (operating-handle
    freedom); use --v04 for the v0.4.0 narrow-box calibration."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "tools" / "03-cooler-grate-simulator" / "src"))
    try:
        from pathlib import Path as _P
        from nepal_cooler_sim.calibration import (
            load_plant_data, calibrate_to_plant_data, _chi2, _build_params,
            CALIBRATION_PARAMETERS,
        )
        from nepal_cooler_sim import (
            hetauda, solve_steady_state, compute_outputs,
            SEC_AIR_BAND_C, TERT_AIR_BAND_C, EXHAUST_AIR_BAND_C,
            CLINKER_OUTLET_BAND_C, COOLER_EFF_BAND,
        )
    except ImportError as e:
        print(f"ERROR: nepal_cooler_sim not importable: {e}")
        return 1
    # Pick the target
    if args.target == "synthetic":
        target_path = _P(__file__).parent.parent.parent.parent / "tools" / "03-cooler-grate-simulator" / "day-04-PRs" / "data" / "synthetic_hetauda_v050_shift_4h.csv"
    elif args.target == "synthetic-legacy":
        target_path = _P(__file__).parent.parent.parent.parent / "tools" / "03-cooler-grate-simulator" / "day-04-PRs" / "data" / "synthetic_hetauda_shift_4h.csv"
    elif args.csv:
        target_path = _P(args.csv)
    else:
        print("ERROR: specify --target synthetic | synthetic-legacy | --csv <path>")
        return 1
    if not target_path.exists():
        print(f"ERROR: target file not found: {target_path}")
        return 1
    print(f"[calibrate] target={target_path}")
    target = load_plant_data(target_path)
    print(f"  n_rows={target.n_rows}, sec_air={target.mean_sec_air_T_c:.1f} C, clinker={target.mean_clinker_T_c:.1f} C, exhaust={target.mean_exhaust_T_c:.1f} C")

    if getattr(args, "v04", False):
        # Day 4 v0.4.0 narrow-box: 7 v0.3.2 operating params only
        res = calibrate_to_plant_data(target, n_restarts=4, seed=20260722)
        print(f"  v0.4.0 narrow-box calibration (7 v0.3.2 operating params only)")
    else:
        # Day 5 v0.5.0: iterative two-stage with 3 operating-handle freedom params
        res = _calibrate_v050(target, n_outer=4, n_restarts=8, seed=20260722)
        print(f"  v0.5.0 iterative two-stage calibration (10 params: 7 operating + 3 geometry handles)")

    print(f"  loss: {res.loss_at_prior:.2f} -> {res.loss_at_posterior:.2f}")
    print(f"  RMSE: sec_air={res.rmse_sec_air_K:.1f} K, clinker={res.rmse_clinker_K:.1f} K, exhaust={res.rmse_exhaust_K:.1f} K")
    print()
    print("Posterior:")
    for k, v in res.posterior.items():
        print(f"  {k:30s} = {v:.3f}")
    print()
    print("Post-calibration KPIs:")
    for k, v in res.posterior_kpis.items():
        if isinstance(v, float):
            print(f"  {k:30s} = {v:.4f}")
    print()
    print("Ship-gate bands:")
    band_windows = {
        "secondary_air_outlet_c": (600, 1000),
        "tertiary_air_outlet_c":  (400, 700),
        "exhaust_air_outlet_c":   (150, 300),
        "clinker_outlet_c":       (120, 200),
        "cooler_efficiency":      (0.65, 0.85),
        "first_law_imbalance":    (0, 0.02),
    }
    n_pass = 0
    for band, (lo, hi) in band_windows.items():
        v = res.posterior_kpis.get(band, float("nan"))
        try:
            v = float(v)
        except (TypeError, ValueError):
            v = float("nan")
        ok = v <= hi if band == "first_law_imbalance" else (lo <= v <= hi)
        if ok: n_pass += 1
        badge = "PASS" if ok else "FAIL"
        print(f"  {band:30s} = {v:8.2f}  band [{lo}, {hi}]  {badge}")
    print(f"\n  >>> {n_pass}/6 ship-gate bands pass on the calibrated model <<<")
    if args.out:
        out_path = _P(args.out)
        out_path.mkdir(parents=True, exist_ok=True)
        out_dict = {
            "loss_prior": res.loss_at_prior, "loss_posterior": res.loss_at_posterior,
            "rmse": {"sec_air_K": res.rmse_sec_air_K, "clinker_K": res.rmse_clinker_K, "exhaust_K": res.rmse_exhaust_K},
            "posterior": res.posterior,
            "posterior_kpis": res.posterior_kpis,
            "n_bands_pass": n_pass, "n_bands_total": 6,
        }
        (out_path / "calibration_result.json").write_text(json.dumps(out_dict, indent=2, default=str))
        print(f"  wrote {out_path}/calibration_result.json")
    return 0


def _calibrate_v050(target, n_outer=4, n_restarts=8, seed=20260722):
    """Day 5 v0.5.0 iterative two-stage calibration. Inlined here
    to avoid a Python import-cycle with the cooler module's
    __init__.py."""
    from pathlib import Path as _P
    import numpy as np
    from scipy.optimize import minimize
    from nepal_cooler_sim.calibration import calibrate_to_plant_data
    from nepal_cooler_sim.cooler_ode import (
        CoolerParameters, solve_steady_state, compute_outputs,
    )

    V050 = [
        ("grate_speed_m_min",            8.0,  24.0,  12.0),
        ("under_grate_air_velocity_m_s", 1.0,   5.0,   1.5),
        ("recuperator_preheat_c",        0.0, 250.0,   0.0),
        ("coal_rate_kg_s",               2.5,   5.0,   3.6),
        ("secondary_air_excess_factor",  1.0,   2.0,   1.10),
        ("emissivity",                   0.7,   0.95,  0.85),
        ("void_fraction",                0.35,  0.55,  0.45),
        ("grate_length_m",              24.0,  50.0,  28.0),
        ("bed_depth_m",                  0.5,   1.2,   0.70),
        ("n_compartments",               3.0,   7.0,   5.0),
    ]

    def _build(candidate, target):
        if isinstance(candidate, dict):
            d = candidate
        else:
            names = [n for (n, *_r) in V050]
            d = {names[i]: float(candidate[i]) for i in range(len(names))}
        n_comp = int(round(d.get("n_compartments", 5.0)))
        n_comp = max(3, min(7, n_comp))
        p = CoolerParameters(
            grate_speed_m_min=d.get("grate_speed_m_min", 12.0),
            under_grate_air_velocity_m_s=d.get("under_grate_air_velocity_m_s", 1.5),
            coal_rate_kg_s=d.get("coal_rate_kg_s", 3.6),
            secondary_air_excess_factor=d.get("secondary_air_excess_factor", 1.10),
            emissivity=d.get("emissivity", 0.85),
            void_fraction=d.get("void_fraction", 0.45),
            under_grate_air_temp_c=d.get("recuperator_preheat_c", 0.0) + target.mean_ambient_T_c,
            length_m=d.get("grate_length_m", 28.0),
            bed_depth_m=d.get("bed_depth_m", 0.70),
            n_compartments=n_comp,
            ambient_t_c=target.mean_ambient_T_c,
            ambient_rh=target.mean_ambient_rh_pct / 100.0,
        )
        return p

    def _chi2(candidate, target):
        p = _build(candidate, target)
        state = solve_steady_state(p)
        out = compute_outputs(state, p)
        c = 0.0
        c += ((out["secondary_air_outlet_c"] - target.mean_sec_air_T_c) / max(target.sec_air_sigma_K, 1.0)) ** 2
        c += ((out["clinker_outlet_c"] - target.mean_clinker_T_c) / max(target.clinker_sigma_K, 1.0)) ** 2
        c += ((out["exhaust_air_outlet_c"] - target.mean_exhaust_T_c) / max(target.exhaust_sigma_K, 1.0)) ** 2
        return c

    rng = np.random.default_rng(seed)
    from nepal_cooler_sim.calibration import CALIBRATION_PARAMETERS as CP
    operating = {p.name: p.prior for p in CP}
    geo_names = ["grate_length_m", "bed_depth_m", "n_compartments"]
    geo_bounds = [(lo, hi) for (n, lo, hi, _pr) in V050 if n in geo_names]
    prev = float("inf")
    for outer in range(n_outer):
        r1 = calibrate_to_plant_data(target, n_restarts=n_restarts, seed=seed + outer)
        operating = {p.name: r1.posterior[p.name] for p in CP}
        def ch2g(xg, target=target, operating=operating):
            d = dict(operating)
            for i, n in enumerate(geo_names): d[n] = xg[i]
            return _chi2(d, target)
        best_x = np.array([12.0, 0.7, 5.0])  # operating-prior-equivalent
        best = ch2g(best_x)
        for _ in range(n_restarts):
            x0 = np.array([rng.uniform(lo, hi) for (lo, hi) in geo_bounds])
            try:
                rr = minimize(ch2g, x0, method="L-BFGS-B", bounds=geo_bounds,
                              options={"ftol": 1e-8, "gtol": 1e-6, "maxiter": 200})
                if rr.fun < best: best = float(rr.fun); best_x = rr.x
            except Exception: pass
        geo = {geo_names[i]: float(best_x[i]) for i in range(3)}
        joint = dict(operating); joint.update(geo)
        jl = _chi2(joint, target)
        if abs(prev - jl) < 0.1: break
        prev = jl

    posterior = dict(operating); posterior.update(geo)
    p = _build(posterior, target)
    state = solve_steady_state(p)
    out = compute_outputs(state, p)
    rmse_sec_air = abs(out["secondary_air_outlet_c"] - target.mean_sec_air_T_c)
    rmse_clinker = abs(out["clinker_outlet_c"] - target.mean_clinker_T_c)
    rmse_exhaust = abs(out["exhaust_air_outlet_c"] - target.mean_exhaust_T_c)
    ship_gate = {
        "secondary_air_outlet_c": 600 <= out["secondary_air_outlet_c"] <= 1000,
        "tertiary_air_outlet_c":  400 <= out["tertiary_air_outlet_c"] <= 700,
        "exhaust_air_outlet_c":   150 <= out["exhaust_air_outlet_c"] <= 300,
        "clinker_outlet_c":       120 <= out["clinker_outlet_c"] <= 200,
        "cooler_efficiency":      0.65 <= out["cooler_efficiency"] <= 0.85,
        "first_law_imbalance":    out["first_law_imbalance"] <= 0.02,
    }
    from nepal_cooler_sim.calibration import CalibrationResult
    return CalibrationResult(
        posterior=posterior,
        rmse_clinker_K=rmse_clinker,
        rmse_sec_air_K=rmse_sec_air,
        rmse_exhaust_K=rmse_exhaust,
        converged=True,
        n_iterations=0,
        loss_at_posterior=jl,
        loss_at_prior=_chi2({n: pr for (n, _l, _h, pr) in V050}, target),
        ship_gate_pass=ship_gate,
        posterior_kpis={k: float(v) for k, v in out.items() if isinstance(v, (int, float))},
        warnings=[],
    )


def cmd_export_step_cooler(args) -> int:
    """Export the v0.5.0 calibrated cooler as a STEP file via FreeCAD."""
    import subprocess
    freecad = r"C:\Users\TG\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe"
    script = Path(__file__).parent.parent.parent.parent / "tools" / "03-cooler-grate-simulator" / "day-06-PRs" / "export_v050_cooler_step.py"
    if not script.exists():
        print(f"ERROR: STEP export script not found at {script}")
        return 1
    out = Path(args.output or "v050_cooler_assembly.step")
    out.parent.mkdir(parents=True, exist_ok=True)
    # Run FreeCAD
    cmd = [
        freecad, "-c",
        f"exec(open(r'{script}').read())",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        print(f"ERROR: FreeCAD not found at {freecad}. Install from https://www.freecadweb.org/")
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: FreeCAD export timed out after 120s")
        return 1
    if r.returncode != 0:
        print(f"ERROR: FreeCAD export failed: {r.stderr[-500:]}")
        return 1
    # Move output
    src = script.parent / "cad" / "v050_cooler_assembly.step"
    if src.exists() and src != out:
        out.write_bytes(src.read_bytes())
    print(f"  wrote {out}")
    print(f"  file size: {out.stat().st_size} bytes")
    return 0


def cmd_export_step_kiln(args) -> int:
    """Export the Hetauda rotary kiln as a STEP file via FreeCAD."""
    import subprocess
    freecad = r"C:\Users\TG\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe"
    script = Path(__file__).parent.parent.parent.parent / "tools" / "02-kiln-dynamics-simulator" / "day-08-PRs" / "export_hetauda_kiln_step.py"
    if not script.exists():
        print(f"ERROR: STEP export script not found at {script}")
        return 1
    out = Path(args.output or "hetauda_kiln_assembly.step")
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        freecad, "-c",
        f"exec(open(r'{script}').read())",
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        print(f"ERROR: FreeCAD not found at {freecad}.")
        return 1
    except subprocess.TimeoutExpired:
        print("ERROR: FreeCAD export timed out after 120s")
        return 1
    if r.returncode != 0:
        print(f"ERROR: FreeCAD export failed: {r.stderr[-500:]}")
        return 1
    src = script.parent / "cad" / "hetauda_kiln_assembly.step"
    if src.exists() and src != out:
        out.write_bytes(src.read_bytes())
    print(f"  wrote {out}")
    print(f"  file size: {out.stat().st_size} bytes")
    return 0


def cmd_demo(args) -> int:
    """Run cooler + kiln + calibration end-to-end. The Day 7 demo."""
    out = Path(args.out or "demo-output")
    out.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("nepal-decarb demo: end-to-end run on the Hetauda preset")
    print("=" * 78)
    print()
    print("Step 1/3: Run the cooler on the Hetauda preset")
    print("-" * 78)
    rc = cmd_run_cooler(argparse.Namespace(plant=args.plant, out=str(out)))
    if rc != 0:
        return rc
    print()
    print("Step 2/3: Run the kiln on the Hetauda preset")
    print("-" * 78)
    rc = cmd_run_kiln(argparse.Namespace(plant=args.plant, fuel=None, out=str(out)))
    if rc != 0:
        return rc
    print()
    print("Step 3/3: Calibrate the cooler to the consistent synthetic target")
    print("-" * 78)
    rc = cmd_calibrate_cooler(argparse.Namespace(target="synthetic", csv=None, out=str(out), v04=False))
    if rc != 0:
        return rc
    print()
    print("=" * 78)
    print("Demo complete. Output in:", out)
    print("=" * 78)
    return 0


def cmd_install(args) -> int:
    """Install nepal-decarb as a Windows entry point (.bat + .ps1)."""
    dist = Path(args.dist or "dist")
    dist.mkdir(parents=True, exist_ok=True)
    # Resolve the repo root from the .bat/.ps1 location, NOT from
    # the script's __file__ (which gets re-mapped through the
    # .mavis -> .minimax reparse point). The .bat/.ps1 are written
    # in <dist> by convention; the user runs them from <dist> or
    # anywhere; ROOT is computed at runtime from the .bat's own
    # location (the .bat lives in <repo>/pro/dist/ so the
    # grandparent is the repo root).
    py_str = sys.executable.replace("/", "\\")
    # .bat launcher: compute ROOT at runtime from the .bat's location
    bat = dist / "nepal-decarb.bat"
    bat.write_text(
        "@echo off\r\n"
        "REM nepal-decarb launcher (Day 11). ROOT is computed from the .bat's location.\r\n"
        "setlocal\r\n"
        "set \"BAT_DIR=%~dp0\"\r\n"
        "if \"%BAT_DIR:~-1%\"==\"\\\" set \"BAT_DIR=%BAT_DIR:~0,-1%\"\r\n"
        "REM Walk up from <dist> to find the repo root (looks for nepal-decarb-build or nepal_decarb_pro)\r\n"
        "set \"ROOT=%BAT_DIR%\"\r\n"
        ":findroot\r\n"
        "if exist \"%ROOT%\\pro\\src\\nepal_decarb_pro\\__init__.py\" goto gotroot\r\n"
        "if \"%ROOT%\"==\"%ROOT:~0,3%\" goto failroot\r\n"
        "for %%P in (\"%ROOT%\") do set \"ROOT=%%~dpP\"\r\n"
        "if \"%ROOT:~-1%\"==\"\\\" set \"ROOT=%ROOT:~0,-1%\"\r\n"
        "goto findroot\r\n"
        ":gotroot\r\n"
        f"set \"PY_EXE={py_str}\"\r\n"
        "set \"PYTHONPATH=%ROOT%\\pro\\src;%ROOT%\\tools\\02-kiln-dynamics-simulator\\src;%ROOT%\\tools\\03-cooler-grate-simulator\\src;%PYTHONPATH%\"\r\n"
        "\"%PY_EXE%\" -m nepal_decarb_pro.cli %*\r\n"
        "exit /b %ERRORLEVEL%\r\n"
        ":failroot\r\n"
        "echo [nepal-decarb] ERROR: could not find repo root from %BAT_DIR%\r\n"
        "exit /b 1\r\n"
    )
    # .ps1 launcher: walk up from <PSScriptRoot> to find the repo root
    ps1 = dist / "nepal-decarb.ps1"
    ps1.write_text(
        "# nepal-decarb launcher (Day 11)\n"
        "$here = Split-Path -Parent $MyInvocation.MyCommand.Path\n"
        "$root = $here\n"
        "while ($true) {\n"
        "    if (Test-Path (Join-Path $root 'pro\\src\\nepal_decarb_pro\\__init__.py')) { break }\n"
        "    $parent = Split-Path -Parent $root\n"
        "    if ($parent -eq $root) {\n"
        "        Write-Host '[nepal-decarb] ERROR: could not find repo root from' $here -ForegroundColor Red\n"
        "        exit 1\n"
        "    }\n"
        "    $root = $parent\n"
        "}\n"
        "$env:NEPAL_DECARB_ROOT = $root\n"
        f"$env:PYTHONPATH = \"$root\\pro\\src;\" +\n"
        f"                  \"$root\\tools\\02-kiln-dynamics-simulator\\src;\" +\n"
        f"                  \"$root\\tools\\03-cooler-grate-simulator\\src;\" +\n"
        "                  $env:PYTHONPATH\n"
        f"& '{py_str}' -m nepal_decarb_pro.cli @args\n"
    )
    print(f"Installed: {bat}")
    print(f"Installed: {ps1}")
    print()
    print("Usage (cmd.exe):")
    print(f"  > {bat} version")
    print(f"  > {bat} status")
    print(f"  > {bat} run cooler --plant hetauda")
    print(f"  > {bat} demo --plant hetauda --out .\\demo-output")
    print()
    print("Usage (PowerShell):")
    print(f"  > & '{ps1}' version")
    print(f"  > & '{ps1}' demo --plant hetauda --out .\\demo-output")
    print()
    print("Note: the .bat and .ps1 expect Python at:")
    print(f"  {sys.executable}")
    print("If that path changes, re-run `nepal-decarb install`.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="nepal-decarb",
        description="Nepal Industrial Decarbonization v1.0 unified CLI",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("version", help="Show nepal-decarb + module versions").set_defaults(func=cmd_version)
    sub.add_parser("status", help="Show installed tool stack").set_defaults(func=cmd_status)

    p_run = sub.add_parser("run", help="Run a module (cooler, kiln, or coupled)")
    p_run_sub = p_run.add_subparsers(dest="module")
    pc = p_run_sub.add_parser("cooler", help="Run the cooler")
    pc.add_argument("--plant", required=True, choices=["hetauda", "udayapur", "hongshi-shivam", "ghorahi"])
    pc.add_argument("--out", default=None)
    pc.set_defaults(func=cmd_run_cooler)
    pk = p_run_sub.add_parser("kiln", help="Run the kiln")
    pk.add_argument("--plant", required=True)
    pk.add_argument("--fuel", default=None)
    pk.add_argument("--out", default=None)
    pk.set_defaults(func=cmd_run_kiln)
    pcp = p_run_sub.add_parser("coupled", help="Run the kiln + cooler in sequence")
    pcp.add_argument("--plant", required=True)
    pcp.add_argument("--fuel", default=None)
    pcp.add_argument("--out", default=None)
    pcp.set_defaults(func=cmd_run_coupled)

    p_cal = sub.add_parser("calibrate", help="Calibrate a module to plant data")
    p_cal_sub = p_cal.add_subparsers(dest="module")
    pcc = p_cal_sub.add_parser("cooler", help="Calibrate the cooler")
    pcc.add_argument("--target", default="synthetic", choices=["synthetic", "synthetic-legacy"])
    pcc.add_argument("--csv", default=None, help="Path to plant-data CSV")
    pcc.add_argument("--out", default=None)
    pcc.add_argument("--v04", action="store_true", help="Use v0.4.0 narrow-box instead of v0.5.0 default")
    pcc.set_defaults(func=cmd_calibrate_cooler)

    p_exp = sub.add_parser("export", help="Export artifacts (STEP, etc.)")
    p_exp_sub = p_exp.add_subparsers(dest="artifact")
    pcs = p_exp_sub.add_parser("step-cooler", help="Export v0.5.0 cooler as STEP")
    pcs.add_argument("--output", default=None, help="Output .step path")
    pcs.add_argument("--calibration", default="day-05", help="Calibration posterior to use (default: day-05)")
    pcs.set_defaults(func=cmd_export_step_cooler)
    pks = p_exp_sub.add_parser("step-kiln", help="Export Hetauda rotary kiln as STEP")
    pks.add_argument("--output", default=None, help="Output .step path")
    pks.set_defaults(func=cmd_export_step_kiln)

    p_demo = sub.add_parser("demo", help="Run cooler + kiln + calibration end-to-end")
    p_demo.add_argument("--plant", default="hetauda")
    p_demo.add_argument("--out", default="demo-output")
    p_demo.set_defaults(func=cmd_demo)

    p_install = sub.add_parser("install", help="Install as Windows entry point")
    p_install.add_argument("--dist", default="dist", help="Install directory")
    p_install.set_defaults(func=cmd_install)

    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
