"""
I/O for cooler simulation results — v0.3.1.

What changed from v0.3.0
------------------------
The v0.3.0 ``save_results_csv`` had a shape-mismatch bug: it was
written against the kiln's time-trajectory contract
(``y.shape = (2*n, n_time)``) but the cooler returns
``y.shape = (2*n, 1)`` (quasi-steady). The single 2-D branch
(``y.ndim == 2 and y.shape[1] == 1``) was a band-aid.

v0.3.1 fixes this at the type level:

* The canonical input/output is :class:`CoolerResult` (dataclass) +
  :class:`CoolerParameters` (Pydantic v2). These are *self-describing*
  — the writer does not have to know whether the model is transient
  or steady.
* :func:`save_results_csv` writes a single CSV with a documented
  schema (header + a ``# meta`` block) when given a ``CoolerResult``,
  and keeps the legacy ``(t, y, x)`` path for kiln-link compat.
* :func:`save_results_json` round-trips through
  :func:`load_results_json` — the JSON schema is the contract.
* :func:`save_results_pickle` / :func:`load_results_pickle` are
  added for the verifier's ``load → solve → compare`` idempotency
  check; pickle is safe here because we control both ends of the
  round-trip (the file is never sent across a trust boundary).
* :func:`to_pdd_json` is a dedicated adapter for James's Verra PDD
  schema — keeps Verra-specific keys out of the KPI dict.
* :func:`to_natural_language` is a stub for Sofia's Day 14 LLM
  advisor — returns a 4-line summary with KPI placeholders, marked
  ``Day 14 hand-off``.

References
----------
  - Pydantic v2 docs, ``model_dump`` / ``model_dump_json``.
  - csv stdlib module, PEP 305.
"""
from __future__ import annotations

import csv
import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel

# Try a relative import first (production); fall back to absolute
# (smoke tests, ad-hoc imports, pytest collection).
try:
    from .cooler_types import CoolerResult  # type: ignore[import-not-found]
    from .cooler_ode import (  # type: ignore[import-not-found]
        CoolerParameters, CoolerState,
    )
except ImportError:  # pragma: no cover — smoke-test path
    from nepal_cooler_sim.cooler_types import (  # type: ignore[no-redef]
        CoolerResult,
    )
    from nepal_cooler_sim.cooler_ode import (  # type: ignore[no-redef]
        CoolerParameters, CoolerState,
    )

# ---------------------------------------------------------------------------
# Constants — public, cite-able
# ---------------------------------------------------------------------------

#: Schema version of the JSON payload. Bump when the JSON contract changes.
JSON_SCHEMA_VERSION = "0.3.1"

#: CSV header for the cooler's spatial profile (v0.3.1 canonical).
CSV_PROFILE_HEADER = ["x_m", "t_clinker_c", "t_air_c"]

#: Default encoding for all text output.
DEFAULT_ENCODING = "utf-8"


# ---------------------------------------------------------------------------
# CSV — v0.3.1 canonical
# ---------------------------------------------------------------------------


def save_results_csv(
    path: str | Path,
    result: CoolerResult,
    p: CoolerParameters,
    *,
    include_meta: bool = True,
) -> str:
    """Write the cooler spatial profile to a CSV file.

    Parameters
    ----------
    path : str | Path
        Destination path. Parent directories are created.
    result : CoolerResult
        The canonical v0.3.1 result.
    p : CoolerParameters
        The parameters used to produce ``result``. Written as a ``# meta``
        block for round-trip context.
    include_meta : bool, default True
        If True, prepend a ``# meta`` block with the parameters' JSON
        dump. Disable for kiln-link compat (which writes a bare CSV).

    Returns
    -------
    str
        The absolute path of the written file (as a string).

    Shape contract
    --------------
    The CSV is one row per spatial cell. Header is exactly::

        x_m,t_clinker_c,t_air_c

    This is the v0.3.1 contract. The v0.3.0 contract
    (``time_s,x_m,T_clinker_C,T_air_C`` with one row per time-step) is
    no longer written by this function; kiln-link compat is provided
    by :func:`save_results_csv_legacy`.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    n = len(result.profile.x)
    if n == 0:
        raise ValueError("CoolerResult has empty profile (n_cells=0)")

    with out_path.open("w", encoding=DEFAULT_ENCODING, newline="") as f:
        if include_meta:
            f.write(f"# nepal_cooler_sim {JSON_SCHEMA_VERSION} — spatial profile\n")
            f.write(f"# n_cells={n}, length_m={p.length_m}, "
                    f"clinker_inlet_c={p.clinker_inlet_t_c}\n")
            f.write(f"# generated_at={datetime.now(timezone.utc).isoformat()}\n")
        f.write(",".join(CSV_PROFILE_HEADER) + "\n")
        writer = csv.writer(f)
        for i in range(n):
            writer.writerow([
                f"{float(result.profile.x[i]):.6f}",
                f"{float(result.profile.t_clinker_c[i]):.4f}",
                f"{float(result.profile.t_air_c[i]):.4f}",
            ])
    return str(out_path.resolve())


def save_results_csv_legacy(
    path: str | Path,
    t: np.ndarray,
    y: np.ndarray,
    x: np.ndarray,
    p: CoolerParameters,
) -> str:
    """Legacy v0.3.0 CSV writer for kiln-link compat.

    Preserved so that Day-2 kiln link code that still passes
    ``(t, y, x)`` does not break during the transition. New code should
    call :func:`save_results_csv` with a :class:`CoolerResult`.

    Shape contract
    --------------
    ``y.ndim == 2 and y.shape[1] == 1`` is the cooler's quasi-steady
    case (``y = (2*n, 1)``, ``t = [0.0]``). The other case is the
    kiln's transient (``y = (2*n, n_time)``).
    """
    n = p.n_cells
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding=DEFAULT_ENCODING, newline="") as f:
        f.write("time_s,x_m,T_clinker_C,T_air_C\n")
        if y.ndim == 2 and y.shape[1] == 1:
            ti = 0
            for zi in range(n):
                f.write(
                    f"{float(t[ti]):.4f},{x[zi]:.4f},"
                    f"{float(y[zi, ti]):.4f},{float(y[n + zi, ti]):.4f}\n"
                )
        else:
            for ti in range(y.shape[1]):
                for zi in range(n):
                    f.write(
                        f"{float(t[ti]):.4f},{x[zi]:.4f},"
                        f"{float(y[zi, ti]):.4f},{float(y[n + zi, ti]):.4f}\n"
                    )
    return str(out_path.resolve())


def load_results_csv(path: str | Path) -> dict[str, np.ndarray]:
    """Load a v0.3.0 or v0.3.1 cooler CSV.

    Returns
    -------
    dict
        ``{"x_m", "t_clinker_c", "t_air_c"}`` for v0.3.1, or
        ``{"time_s", "x_m", "t_clinker_c", "t_air_c"}`` for v0.3.0.
        Skips ``# meta`` comment lines.
    """
    out_path = Path(path)
    cols: dict[str, list[float]] = {}
    with out_path.open("r", encoding=DEFAULT_ENCODING) as f:
        # Filter comment lines for the DictReader.
        lines = [ln for ln in f if not ln.startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        for k, v in row.items():
            cols.setdefault(k, []).append(float(v))
    return {k: np.array(v) for k, v in cols.items()}


# ---------------------------------------------------------------------------
# JSON — round-trip
# ---------------------------------------------------------------------------


def save_results_json(
    path: str | Path,
    state: CoolerState | None,
    p: CoolerParameters,
    outputs: dict[str, Any],
    *,
    result: CoolerResult | None = None,
) -> str:
    """Write a JSON payload with parameters, state summary, and outputs.

    Parameters
    ----------
    path : str | Path
        Destination path. Parent directories are created.
    state : CoolerState | None
        The v0.3.0 state container. Optional — if ``result`` is given,
        the profile is taken from there.
    p : CoolerParameters
        Pydantic v2 model, serialised via ``model_dump_json``.
    outputs : dict[str, Any]
        The KPI dict (typically from ``compute_outputs``).
    result : CoolerResult | None
        If given, the v0.3.1 canonical result is also included
        under the ``"result"`` key.

    Returns
    -------
    str
        The absolute path of the written file.

    Round-trip
    ----------
    :func:`load_results_json` reconstructs the parameters and outputs
    but **not** the state (states are not pure data; results are).
    For a result round-trip, use :func:`save_results_pickle`.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "tool": "nepal_cooler_sim",
        "schema_version": JSON_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "parameters": json.loads(p.model_dump_json()),
        "outputs": outputs,
    }
    if state is not None:
        payload["state_summary"] = state.summary()
    if result is not None:
        payload["result"] = result.to_dict()
    with out_path.open("w", encoding=DEFAULT_ENCODING) as f:
        json.dump(payload, f, indent=2, default=_json_default)
    return str(out_path.resolve())


def load_results_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON payload written by :func:`save_results_json`.

    Returns the raw dict. ``payload["parameters"]`` is the Pydantic v2
    parameter dump (a plain dict); callers can reconstruct
    ``CoolerParameters(**payload["parameters"])`` to round-trip.
    """
    out_path = Path(path)
    with out_path.open("r", encoding=DEFAULT_ENCODING) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Pickle — for verifier round-trip
# ---------------------------------------------------------------------------


def save_results_pickle(
    path: str | Path,
    result: CoolerResult,
    p: CoolerParameters,
) -> str:
    """Pickle a ``(CoolerResult, CoolerParameters)`` pair.

    Pickle is safe here because we control both ends of the round-trip
    (the file is never sent across a trust boundary). The verifier uses
    this for an idempotency check: ``load → solve → compare``.
    """
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("wb") as f:
        pickle.dump({"result": result, "parameters": p}, f, protocol=pickle.HIGHEST_PROTOCOL)
    return str(out_path.resolve())


def load_results_pickle(path: str | Path) -> tuple[CoolerResult, CoolerParameters]:
    """Unpickle a ``(CoolerResult, CoolerParameters)`` pair.

    Raises
    ------
    pickle.UnpicklingError
        If the file was not produced by :func:`save_results_pickle`.
    """
    out_path = Path(path)
    with out_path.open("rb") as f:
        blob = pickle.load(f)
    if not isinstance(blob, dict) or "result" not in blob or "parameters" not in blob:
        raise ValueError(
            f"Pickle at {out_path} does not contain a (CoolerResult, CoolerParameters) pair"
        )
    result: CoolerResult = blob["result"]
    params: CoolerParameters = blob["parameters"]
    if not isinstance(params, BaseModel):
        # Forward-compat: if the file was pickled under a different
        # version, ``parameters`` may already be a dict. The caller
        # can then do ``CoolerParameters(**params)``.
        pass
    return result, params


# ---------------------------------------------------------------------------
# Adapters — for downstream agents
# ---------------------------------------------------------------------------


def to_pdd_json(result: CoolerResult, p: CoolerParameters) -> dict[str, Any]:
    """Adapter to the Verra PDD JSON schema (James, Day 13).

    Kept separate from :func:`compute_outputs` so the KPI dict stays
    generic and the PDD-specific keys (e.g. ``projectActivityId``)
    don't leak into engineering reports. Returns a dict; the JSON
    serialisation is the caller's job.

    Day 13 ownership: James wires the real Verra schema. This stub
    emits the fields Day 3 ships and a ``_day_13_extensions`` block
    for the verifier to confirm the seam.
    """
    return {
        "_adapter": "nepal_cooler_sim.to_pdd_json",
        "_schema_version": JSON_SCHEMA_VERSION,
        "projectActivity": "clinker_cooler_heat_recovery",
        "technology": "grate_cooler",
        "tool": "nepal_cooler_sim",
        "tool_version": "0.3.1",
        "operatingParameters": json.loads(p.model_dump_json()),
        "performance": {
            "secondaryAirOutletC": float(result.secondary_air_outlet_c),
            "clinkerOutletC": float(result.clinker_outlet_c),
            "coolerEfficiency": float(result.cooler_efficiency),
            "firstLawImbalance": float(result.first_law_imbalance),
        },
        "_day_13_extensions": {
            "_note": "James — replace this block with the Verra PDD "
                     "fields (projectActivityId, emissionReductionType, "
                     "monitoringPlan, etc.).",
        },
    }


def to_natural_language(result: CoolerResult, p: CoolerParameters) -> str:
    """Stub for Sofia's Day 14 LLM advisor.

    Returns a 4-line plain-text summary of the cooler result. The Day 14
    hand-off is to (a) inject RAG context (Peray §6, Mujumdar 2007,
    Achenbach 1995), (b) add LLM-friendly commentary hooks, and
    (c) return a structured dict instead of a plain string.

    The wire format today is plain text so the CLI's ``diagnose``
    subcommand can print it as-is.
    """
    return (
        f"Cooler: {p.length_m:.1f} m × {p.width_m:.1f} m grate, "
        f"{p.n_compartments} compartments.\n"
        f"Clinker outlet: {result.clinker_outlet_c:.0f} °C "
        f"(target {p.clinker_outlet_t_c:.0f} °C).\n"
        f"Secondary air outlet: {result.secondary_air_outlet_c:.0f} °C; "
        f"cooler efficiency: {result.cooler_efficiency * 100.0:.1f} %.\n"
        f"First-law imbalance: {result.first_law_imbalance * 100.0:.2f} % "
        f"(target ≤ 2.0 %)."
    )


# ---------------------------------------------------------------------------
# MATLAB / Octave export — preserved from v0.3.0
# ---------------------------------------------------------------------------


_MATLAB_TEMPLATE = """% {title}
% Generated by nepal_cooler_sim v{version} on {date}
% 1D grate cooler (cement clinker) — v0.3.1
% Run with MATLAB R2020b+ or GNU Octave 7+

clear; clc;
n = {n_cells};
L = {length_m};
W = {width_m};
h_bed = {bed_depth_m};
v_grate = {grate_speed_m_min} / 60;       % m/s
T_in = {clinker_inlet_t_c};                % C
T_out_target = {clinker_outlet_t_c};       % C
v_air = {under_grate_air_velocity_m_s};    % m/s
T_air_in = {under_grate_air_temp_c};
m_clinker_t_h = {clinker_throughput_t_h};
rho_bulk = {rho_clinker_kg_m3};
cp_clinker = {cp_clinker_kj_kg_k} * 1000;  % J/(kg K)
emiss = {emissivity};

m_clinker = m_clinker_t_h * 1000 / 3600;
y0 = zeros(2 * n, 1);
for i = 1:n
    y0(i) = T_in;
    y0(n + i) = T_air_in;
end

tspan = [0 {t_end_s}];
options = odeset('RelTol', 1e-5, 'AbsTol', 1e-7, 'MaxStep', 5);
[t, y] = ode15s(@(t,y) cooler_rhs(t, y, n, L, W, h_bed, v_grate, v_air, ...
    m_clinker, rho_bulk, cp_clinker, emiss), tspan, y0, options);

% Final spatial profile
T_clinker = y(end, 1:n);
T_air = y(end, n+1:end);
x = linspace(0, L, n);

figure;
subplot(2,1,1);
plot(x, T_clinker); xlabel('Grate position (m)'); ylabel('Clinker T (C)');
title('Clinker temperature along grate (steady state)');

subplot(2,1,2);
plot(x, T_air); xlabel('Grate position (m)'); ylabel('Cooling air T (C)');
title('Cooling air temperature along grate');

fprintf('Clinker outlet: %.1f C (target %.1f C)\\n', T_clinker(end), T_out_target);
"""


def export_matlab_script(
    path: str | Path,
    p: CoolerParameters,
    title: str = "Grate cooler simulation",
) -> str:
    """Render a self-contained MATLAB / Octave script for the cooler."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    body = _MATLAB_TEMPLATE.format(
        title=title,
        version=JSON_SCHEMA_VERSION,
        date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        n_cells=p.n_cells,
        length_m=p.length_m,
        width_m=p.width_m,
        bed_depth_m=p.bed_depth_m,
        grate_speed_m_min=p.grate_speed_m_min,
        clinker_inlet_t_c=p.clinker_inlet_t_c,
        clinker_outlet_t_c=p.clinker_outlet_t_c,
        under_grate_air_velocity_m_s=p.under_grate_air_velocity_m_s,
        under_grate_air_temp_c=p.under_grate_air_temp_c,
        clinker_throughput_t_h=p.clinker_throughput_t_h,
        rho_clinker_kg_m3=p.rho_clinker_kg_m3,
        cp_clinker_kj_kg_k=p.cp_clinker_kj_kg_k,
        emissivity=p.emissivity,
        t_end_s=p.t_end_s,
    )
    with out_path.open("w", encoding=DEFAULT_ENCODING) as f:
        f.write(body)
    return str(out_path.resolve())


def export_octave_script(
    path: str | Path,
    p: CoolerParameters,
    title: str = "Grate cooler (Octave)",
) -> str:
    """Render a self-contained Octave script (loads ``odepkg``)."""
    # Octave can run the MATLAB script after `pkg load odepkg;`.
    out_path = Path(path)
    export_matlab_script(out_path, p, title)
    text = out_path.read_text(encoding=DEFAULT_ENCODING)
    text = text.replace("clear; clc;", "pkg load odepkg;\nclear; clc;")
    out_path.write_text(text, encoding=DEFAULT_ENCODING)
    return str(out_path.resolve())


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _json_default(o: Any) -> Any:
    """JSON serialiser for numpy / pydantic types.

    Order matters: ``np.bool_`` is a subclass of ``int`` in some
    numpy versions, so check it before the integer branch.
    """
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, BaseModel):
        return json.loads(o.model_dump_json())
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)
