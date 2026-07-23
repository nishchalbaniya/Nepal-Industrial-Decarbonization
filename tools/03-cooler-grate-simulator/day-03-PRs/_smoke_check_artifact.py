"""Smoke test for Maya's v0.3.1 PR.

Run with:  py -3 smoke_check.py
Located in the PR directory; not part of the shipped PR.
"""
import importlib.util
import sys
import tempfile

PR = r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\tools\03-cooler-grate-simulator\day-03-PRs\cs-architect"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# Register the PR modules under the upstream namespace so their
# relative-then-absolute fallbacks resolve cleanly during the
# smoke test. (In production, the PR lives inside
# `src/nepal_cooler_sim/`, so the relative import wins.)
def register_under_upstream(name: str, path: str) -> None:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)


def main() -> int:
    from nepal_cooler_sim.cooler_ode import (
        CoolerParameters, run_to_steady_state, compute_outputs,
    )
    print("upstream cooler_ode OK")

    t = load("cs_v031_types", PR + r"\cooler_types.py")
    register_under_upstream("nepal_cooler_sim.cooler_types", PR + r"\cooler_types.py")
    i = load("cs_v031_io", PR + r"\io.py")
    register_under_upstream("nepal_cooler_sim.io", PR + r"\io.py")
    # The PR's __init__ expects to be loaded as a package; smoke test
    # can skip it (its exports are visible via cooler_types + io + cli).
    c = load("cs_v031_cli", PR + r"\cli.py")

    for name in (
        "CoolerProfile", "CoolerResult", "CoolerOutputs",
        "ShapeContractError", "solve_steady_state",
    ):
        assert hasattr(t, name), name
        print(f"  types.{name} OK")
    for name in (
        "save_results_csv", "save_results_csv_legacy", "load_results_csv",
        "save_results_json", "load_results_json",
        "save_results_pickle", "load_results_pickle",
        "to_pdd_json", "to_natural_language",
        "export_matlab_script", "export_octave_script",
    ):
        assert hasattr(i, name), name
        print(f"  io.{name} OK")
    for name in (
        "build_parser", "main", "cmd_run", "cmd_coupled",
        "cmd_sensitivity", "cmd_export", "cmd_diagnose", "cmd_presets",
        "PRESETS",
    ):
        assert hasattr(c, name), name
        print(f"  cli.{name} OK")

    p = CoolerParameters(n_cells=10, t_end_s=900.0)
    result = t.solve_steady_state(p)
    print(
        f"solve_steady_state -> CoolerResult; "
        f"profile.x.shape={result.profile.x.shape}, "
        f"clinker_outlet_c={result.clinker_outlet_c:.1f}, "
        f"secondary_air_outlet_c={result.secondary_air_outlet_c:.1f}, "
        f"first_law_imbalance={result.first_law_imbalance:.3f}"
    )

    with tempfile.TemporaryDirectory() as td:
        csv_path = i.save_results_csv(td + r"\profile.csv", result, p)
        loaded = i.load_results_csv(csv_path)
        print(
            f"CSV round-trip OK: keys={list(loaded.keys())}, "
            f"rows={len(loaded['x_m'])}"
        )

        state = run_to_steady_state(p, max_t_s=p.t_end_s)
        outs = compute_outputs(state, p)
        j_path = i.save_results_json(
            td + r"\outputs.json", state, p, outs, result=result
        )
        j_loaded = i.load_results_json(j_path)
        print(f"JSON round-trip OK: schema_version={j_loaded['schema_version']}")

        p_path = i.save_results_pickle(td + r"\r.pkl", result, p)
        r2, p2 = i.load_results_pickle(p_path)
        print(
            f"pickle round-trip OK: "
            f"secondary_air_outlet_c={r2.secondary_air_outlet_c:.1f}"
        )

        pdd = i.to_pdd_json(result, p)
        print(
            f"PDD adapter OK: adapter={pdd['_adapter']}, "
            f"projectActivity={pdd['projectActivity']}"
        )

        nl = i.to_natural_language(result, p)
        print(f"natural-language OK ({len(nl.splitlines())} lines)")

    rc = c.main(["presets"])
    print(f"CLI presets -> rc={rc}")
    rc = c.main(["diagnose", "--preset", "planta", "--human"])
    print(f"CLI diagnose --human -> rc={rc}")

    print("ALL PR SMOKE TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
