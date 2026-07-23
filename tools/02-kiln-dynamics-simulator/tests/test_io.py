"""
Tests for io.py — round-trip CSV / JSON / pickle / MATLAB export.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from nepal_kiln_sim.io import (
    save_results_csv, load_results_csv,
    save_results_json,
    save_state_pickle, load_state_pickle,
    export_matlab_script, export_octave_script,
)
from nepal_kiln_sim.kiln_ode import KilnParameters, run_to_steady_state, compute_outputs, simulate_kiln
from nepal_kiln_sim.plants import PLANT_PRESETS


def test_csv_round_trip(tmp_path):
    p = PLANT_PRESETS["planta"].parameters
    t, y, x = simulate_kiln(p, t_end_s=60.0, n_time_points=5)
    path = save_results_csv(str(tmp_path / "traj.csv"), t, y, x, p)
    assert Path(path).exists()
    df = load_results_csv(path)
    assert "time_s" in df
    assert "x_m" in df
    assert len(df["time_s"]) == p.n_zones * 5


def test_json_contains_outputs(tmp_path):
    p = PLANT_PRESETS["plantb"].parameters
    state = run_to_steady_state(p, max_t_s=180.0)
    outs = compute_outputs(state, p)
    path = save_results_json(str(tmp_path / "out.json"), state, p, outs)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert "parameters" in data
    assert "outputs" in data
    assert data["outputs"]["sec_mj_per_t_clinker"] == outs["sec_mj_per_t_clinker"]


def test_pickle_round_trip(tmp_path):
    p = PLANT_PRESETS["planta"].parameters
    state = run_to_steady_state(p, max_t_s=120.0)
    t, y, x = simulate_kiln(p, t_end_s=120.0)
    path = save_state_pickle(str(tmp_path / "s.pkl"), state, t, y, p)
    loaded = load_state_pickle(path)
    assert loaded["p"].fuel_type == p.fuel_type
    np.testing.assert_allclose(loaded["state"].t_solid_k, state.t_solid_k)


def test_matlab_export(tmp_path):
    p = PLANT_PRESETS["reference_5000tpd"].parameters
    path = export_matlab_script(str(tmp_path / "kiln.m"), p)
    text = Path(path).read_text()
    assert "ode15s" in text
    assert "kiln_rhs" in text


def test_octave_export(tmp_path):
    p = PLANT_PRESETS["plantb"].parameters
    path = export_octave_script(str(tmp_path / "kiln.m"), p)
    text = Path(path).read_text()
    assert "odepkg" in text
    assert "ode15s" in text
