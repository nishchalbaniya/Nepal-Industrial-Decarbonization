"""Tests for nepal_cooler_sim I/O and CLI."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from nepal_cooler_sim import (
    CoolerParameters, run_to_steady_state, compute_outputs, simulate_cooler,
    save_results_csv, load_results_csv, save_results_json,
    export_matlab_script, export_octave_script,
)
from nepal_cooler_sim.cli import PRESETS, build_parser


def test_csv_round_trip(tmp_path):
    p = CoolerParameters(n_cells=10, t_end_s=120.0, n_time_points=20)
    t, y, x = simulate_cooler(p)
    path = save_results_csv(str(tmp_path / "traj.csv"), t, y, x, p)
    assert Path(path).exists()
    df = load_results_csv(path)
    assert "time_s" in df and "T_clinker_C" in df
    assert len(df["time_s"]) == p.n_cells * 20


def test_json_outputs(tmp_path):
    p = CoolerParameters(n_cells=15, t_end_s=300.0)
    state = run_to_steady_state(p, max_t_s=300.0)
    outs = compute_outputs(state, p)
    path = save_results_json(str(tmp_path / "out.json"), state, p, outs)
    import json
    data = json.loads(Path(path).read_text())
    assert "outputs" in data and "parameters" in data


def test_matlab_export(tmp_path):
    p = CoolerParameters(n_cells=15)
    path = export_matlab_script(str(tmp_path / "cooler.m"), p)
    text = Path(path).read_text()
    assert "ode15s" in text
    assert "cooler_rhs" in text


def test_octave_export(tmp_path):
    p = CoolerParameters(n_cells=15)
    path = export_octave_script(str(tmp_path / "cooler.m"), p)
    text = Path(path).read_text()
    assert "odepkg" in text


def test_cli_presets_listed():
    from nepal_cooler_sim.cli import cmd_presets
    parser = build_parser()
    args = parser.parse_args(["presets"])
    assert args.func is cmd_presets
    assert "standard_5000tpd" in PRESETS


def test_cli_run_preset():
    parser = build_parser()
    args = parser.parse_args(["run", "--preset", "udayapur"])
    rc = args.func(args)
    assert rc == 0


def test_cli_coupled():
    parser = build_parser()
    args = parser.parse_args(["coupled", "--preset", "hetauda_small"])
    rc = args.func(args)
    assert rc == 0
