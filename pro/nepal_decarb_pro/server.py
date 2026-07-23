"""
nepal-decarb FastAPI server (Day 10) -- a tiny HTTP frontend over the
unified CLI. Wraps the cooler + kiln + calibration + STEP / P&ID export
modules so the user can drive everything from a browser.

Endpoints
---------
GET  /                          -- minimal HTML dashboard
GET  /api/version               -- module versions
GET  /api/status                -- tool stack status
GET  /api/plants                -- available plant presets (cooler)
POST /api/cooler/run            -- run the cooler (body: {plant, overrides?})
POST /api/kiln/run              -- run the kiln (body: {plant, fuel?})
POST /api/cooler/calibrate      -- calibrate cooler (body: {target, v04?})
POST /api/cooler/export-step    -- export cooler STEP
POST /api/kiln/export-step      -- export kiln STEP
POST /api/cooler/export-pid     -- export cooler P&ID (STEP+SVG+JSON)
GET  /api/artifacts             -- list generated files in <out_dir>
GET  /api/artifacts/{name}      -- download a generated file
GET  /api/pid-svg               -- return the cooler P&ID SVG inline

Run:
  > python -m nepal_decarb_pro.server --port 8000
Then open http://127.0.0.1:8000/ in any browser.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# FastAPI + pydantic
try:
    from fastapi import FastAPI, HTTPException, Body
    from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"[server] FastAPI not installed: {e}")
    print("[server] install with: python -m pip install fastapi uvicorn[standard] python-multipart")
    raise

# Make sure the cooler + kiln + pro packages are importable
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent.parent  # pro/src/nepal_decarb_pro -> pro/src -> pro -> repo
_KILN_SRC = _REPO_ROOT / "tools" / "02-kiln-dynamics-simulator" / "src"
_COOLER_SRC = _REPO_ROOT / "tools" / "03-cooler-grate-simulator" / "src"
for p in (str(_HERE), str(_KILN_SRC), str(_COOLER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

# Where generated artifacts land by default
DEFAULT_OUT_DIR = _REPO_ROOT / "pro" / "demo-output"
DEFAULT_OUT_DIR.mkdir(parents=True, exist_ok=True)

FREECAD = r"C:\Users\TG\AppData\Local\Programs\FreeCAD 1.1\bin\FreeCADCmd.exe"


# ----------------------------------------------------------------------------
# Pydantic request/response models
# ----------------------------------------------------------------------------

class CoolerOverride(BaseModel):
    grate_speed_m_min: Optional[float] = None
    under_grate_air_velocity_m_s: Optional[float] = None
    recuperator_preheat_c: Optional[float] = None
    coal_rate_kg_s: Optional[float] = None
    secondary_air_excess_factor: Optional[float] = None
    emissivity: Optional[float] = None
    void_fraction: Optional[float] = None
    grate_length_m: Optional[float] = None
    bed_depth_m: Optional[float] = None
    n_compartments: Optional[int] = None


class CoolerRunRequest(BaseModel):
    plant: str = Field("planta")
    out: Optional[str] = None
    overrides: Optional[CoolerOverride] = None


class KilnRunRequest(BaseModel):
    plant: str = Field("planta")
    fuel: Optional[str] = None
    out: Optional[str] = None


class CoolerCalibrateRequest(BaseModel):
    target: str = Field("synthetic")  # synthetic | synthetic-legacy
    csv: Optional[str] = None
    v04: bool = False
    out: Optional[str] = None


class ExportStepCoolerRequest(BaseModel):
    output: Optional[str] = None
    calibration: str = "day-05"


class ExportStepKilnRequest(BaseModel):
    output: Optional[str] = None


class ExportPidRequest(BaseModel):
    output: Optional[str] = None


# ----------------------------------------------------------------------------
# Lazy import of sim modules (so the server can start even if the sim fails)
# ----------------------------------------------------------------------------

def _import_cooler():
    import nepal_cooler_sim
    return nepal_cooler_sim


def _import_kiln():
    import nepal_kiln_sim
    return nepal_kiln_sim


def _run_cooler(req: CoolerRunRequest) -> Dict[str, Any]:
    sim = _import_cooler()
    presets = {
        "planta": sim.planta,
        "plantb": sim.plantb,
        "plantc": sim.plantc,
        "plantd": sim.plantd,
    }
    if req.plant not in presets:
        raise HTTPException(400, f"unknown plant {req.plant!r}; available={list(presets)}")
    p = presets[req.plant]()
    if req.overrides:
        for f, v in req.overrides.model_dump(exclude_none=True).items():
            if hasattr(p, f):
                setattr(p, f, v)
    state = sim.solve_steady_state(p)
    out = sim.compute_outputs(state, p)
    out_path = None
    if req.out:
        out_path = Path(req.out)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "cooler_outputs.json").write_text(json.dumps(out, indent=2, default=str))
    return {"ok": True, "outputs": {k: float(v) if isinstance(v, (int, float)) else v
                                    for k, v in out.items()},
            "written_to": str(out_path / "cooler_outputs.json") if out_path else None,
            "plant": req.plant,
            "parameters_applied": req.overrides.model_dump(exclude_none=True) if req.overrides else {}}


def _run_kiln(req: KilnRunRequest) -> Dict[str, Any]:
    sim = _import_kiln()
    if req.plant not in sim.PLANT_PRESETS:
        raise HTTPException(400, f"unknown plant {req.plant!r}; available={list(sim.PLANT_PRESETS)}")
    preset = sim.get_plant_preset(req.plant)
    p = preset.parameters
    if req.fuel:
        p.fuel_key = req.fuel
    state = sim.run_to_steady_state(p)
    out = sim.compute_outputs(state, p)
    out_path = None
    if req.out:
        out_path = Path(req.out)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "kiln_outputs.json").write_text(json.dumps(out, indent=2, default=str))
    return {"ok": True, "outputs": {k: float(v) if isinstance(v, (int, float)) else v
                                    for k, v in out.items()},
            "written_to": str(out_path / "kiln_outputs.json") if out_path else None,
            "plant": req.plant, "fuel": getattr(p, "fuel_key", None)}


def _run_calibration(req: CoolerCalibrateRequest) -> Dict[str, Any]:
    sim = _import_cooler()
    import nepal_cooler_sim.calibration  # ensure submodule is loaded
    if req.target == "synthetic":
        target_path = _COOLER_SRC.parent / "day-04-PRs" / "data" / "synthetic_planta_v050_shift_4h.csv"
    elif req.target == "synthetic-legacy":
        target_path = _COOLER_SRC.parent / "day-04-PRs" / "data" / "synthetic_planta_shift_4h.csv"
    else:
        target_path = Path(req.csv) if req.csv else None
    if target_path is None:
        raise HTTPException(400, "specify target=synthetic|synthetic-legacy or csv=<path>")
    if not target_path.exists():
        raise HTTPException(404, f"target file not found: {target_path}")
    target = sim.calibration.load_plant_data(target_path)
    if req.v04:
        res = sim.calibration.calibrate_to_plant_data(target, n_restarts=4, seed=20260722)
    else:
        # Use the inlined v0.5.0 from cli.py
        from nepal_decarb_pro.cli import _calibrate_v050
        res = _calibrate_v050(target, n_outer=4, n_restarts=8, seed=20260722)
    out_path = None
    payload = {
        "loss_prior": res.loss_at_prior,
        "loss_posterior": res.loss_at_posterior,
        "rmse_sec_air_K": res.rmse_sec_air_K,
        "rmse_clinker_K": res.rmse_clinker_K,
        "rmse_exhaust_K": res.rmse_exhaust_K,
        "posterior": res.posterior,
        "posterior_kpis": {k: float(v) for k, v in (res.posterior_kpis or {}).items()
                           if isinstance(v, (int, float))},
        "ship_gate_pass": res.ship_gate_pass,
    }
    n_pass = sum(1 for v in res.ship_gate_pass.values() if v)
    payload["n_bands_pass"] = n_pass
    payload["n_bands_total"] = 6
    if req.out:
        out_path = Path(req.out)
        out_path.mkdir(parents=True, exist_ok=True)
        (out_path / "calibration_result.json").write_text(json.dumps(payload, indent=2, default=str))
        payload["written_to"] = str(out_path / "calibration_result.json")
    return payload


def _freecad_export(script_path: Path, out_dir: Path, timeout: int = 120) -> Dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if not Path(FREECAD).exists():
        raise HTTPException(500, f"FreeCAD not found at {FREECAD}")
    cmd = [FREECAD, "-c", f"exec(open(r'{script_path}').read())"]
    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, f"FreeCAD export timed out after {timeout}s")
    dt = time.time() - t0
    if r.returncode != 0:
        raise HTTPException(500, f"FreeCAD export failed: {r.stderr[-500:]}")
    return {"returncode": r.returncode, "elapsed_s": round(dt, 2), "out_dir": str(out_dir)}


def _export_step_cooler(req: ExportStepCoolerRequest) -> Dict[str, Any]:
    script = _COOLER_SRC.parent / "day-06-PRs" / "export_v050_cooler_step.py"
    if not script.exists():
        raise HTTPException(404, f"STEP export script not found at {script}")
    out = Path(req.output or (DEFAULT_OUT_DIR / "v050_cooler_assembly.step"))
    out.parent.mkdir(parents=True, exist_ok=True)
    info = _freecad_export(script, script.parent / "cad")
    src = script.parent / "cad" / "v050_cooler_assembly.step"
    if src.exists():
        out.write_bytes(src.read_bytes())
    return {"ok": True, "path": str(out), "size_bytes": out.stat().st_size if out.exists() else 0, **info}


def _export_step_kiln(req: ExportStepKilnRequest) -> Dict[str, Any]:
    script = _KILN_SRC.parent / "day-08-PRs" / "export_planta_kiln_step.py"
    if not script.exists():
        raise HTTPException(404, f"kiln STEP export script not found at {script}")
    out = Path(req.output or (DEFAULT_OUT_DIR / "planta_kiln_assembly.step"))
    out.parent.mkdir(parents=True, exist_ok=True)
    info = _freecad_export(script, script.parent / "cad")
    src = script.parent / "cad" / "planta_kiln_assembly.step"
    if src.exists():
        out.write_bytes(src.read_bytes())
    return {"ok": True, "path": str(out), "size_bytes": out.stat().st_size if out.exists() else 0, **info}


def _export_pid(req: ExportPidRequest) -> Dict[str, Any]:
    script = _COOLER_SRC.parent / "day-09-PRs" / "export_pid_cooler.py"
    if not script.exists():
        raise HTTPException(404, f"P&ID export script not found at {script}")
    out_dir = Path(req.output or DEFAULT_OUT_DIR)
    info = _freecad_export(script, script.parent / "cad")
    written = []
    for name in ("planta_cooler_pid.svg", "planta_cooler_pid.json", "planta_cooler_pid.step"):
        src = script.parent / "cad" / name
        if src.exists():
            dst = out_dir / name
            dst.write_bytes(src.read_bytes())
            written.append({"name": name, "size": dst.stat().st_size, "path": str(dst)})
    return {"ok": True, "written": written, **info}


# ----------------------------------------------------------------------------
# App + routes
# ----------------------------------------------------------------------------

app = FastAPI(
    title="nepal-decarb API",
    description="Nepal Industrial Decarbonization v1.0 unified HTTP API (Day 10)",
    version="0.7.0",
)


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return _INDEX_HTML


@app.get("/api/version")
def api_version() -> Dict[str, Any]:
    out = {"nepal_decarb_pro": "0.7.0"}
    try:
        sim = _import_cooler()
        out["nepal_cooler_sim"] = sim.__version__
    except Exception as e:
        out["nepal_cooler_sim_error"] = str(e)
    try:
        sim = _import_kiln()
        out["nepal_kiln_sim"] = sim.__version__
    except Exception as e:
        out["nepal_kiln_sim_error"] = str(e)
    return out


@app.get("/api/status")
def api_status() -> Dict[str, Any]:
    out: Dict[str, Any] = {"python": sys.version.split()[0]}
    try:
        import platform
        out["os"] = f"{platform.system()} {platform.release()}"
    except Exception:
        pass
    try:
        import FreeCAD
        out["freecad"] = ".".join(str(x) for x in FreeCAD.Version()[:3])
    except Exception:
        out["freecad"] = None
    for mod in ("numpy", "scipy", "pydantic", "fastapi", "uvicorn"):
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "?")
        except Exception:
            out[mod] = None
    return out


@app.get("/api/plants")
def api_plants() -> Dict[str, Any]:
    out = {"cooler": ["planta", "plantb", "plantc", "plantd"]}
    try:
        sim = _import_kiln()
        out["kiln"] = list(sim.PLANT_PRESETS)
    except Exception as e:
        out["kiln_error"] = str(e)
    return out


@app.post("/api/cooler/run")
def api_cooler_run(req: CoolerRunRequest) -> Dict[str, Any]:
    return _run_cooler(req)


@app.post("/api/kiln/run")
def api_kiln_run(req: KilnRunRequest) -> Dict[str, Any]:
    return _run_kiln(req)


@app.post("/api/cooler/calibrate")
def api_cooler_calibrate(req: CoolerCalibrateRequest) -> Dict[str, Any]:
    return _run_calibration(req)


@app.post("/api/cooler/export-step")
def api_cooler_export_step(req: ExportStepCoolerRequest) -> Dict[str, Any]:
    return _export_step_cooler(req)


@app.post("/api/kiln/export-step")
def api_kiln_export_step(req: ExportStepKilnRequest) -> Dict[str, Any]:
    return _export_step_kiln(req)


@app.post("/api/cooler/export-pid")
def api_cooler_export_pid(req: ExportPidRequest) -> Dict[str, Any]:
    return _export_pid(req)


@app.get("/api/artifacts")
def api_artifacts() -> Dict[str, Any]:
    files: List[Dict[str, Any]] = []
    if DEFAULT_OUT_DIR.exists():
        for p in sorted(DEFAULT_OUT_DIR.iterdir()):
            if p.is_file():
                files.append({"name": p.name, "size": p.stat().st_size, "path": str(p)})
    return {"out_dir": str(DEFAULT_OUT_DIR), "files": files}


@app.get("/api/artifacts/{name}")
def api_artifact_download(name: str):
    p = DEFAULT_OUT_DIR / name
    if not p.exists() or not p.is_file():
        raise HTTPException(404, f"not found: {p}")
    media = "application/octet-stream"
    if name.endswith(".svg"):
        media = "image/svg+xml"
    elif name.endswith(".json"):
        media = "application/json"
    elif name.endswith(".step") or name.endswith(".stp"):
        media = "application/step"
    return FileResponse(str(p), media_type=media, filename=name)


@app.get("/api/pid-svg")
def api_pid_svg() -> Response:
    p = DEFAULT_OUT_DIR / "planta_cooler_pid.svg"
    if not p.exists():
        raise HTTPException(404, f"not found: {p}. POST /api/cooler/export-pid first.")
    return Response(content=p.read_bytes(), media_type="image/svg+xml")


# ----------------------------------------------------------------------------
# Minimal in-browser HTML dashboard (no JS frameworks -- one file, works offline)
# ----------------------------------------------------------------------------

_INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>nepal-decarb -- v1.0 dashboard</title>
<style>
  :root { --bg:#0b0f14; --panel:#11171f; --ink:#e6edf3; --muted:#7d8590;
          --accent:#3fb950; --warn:#d29922; --err:#f85149; --line:#30363d; }
  * { box-sizing: border-box; }
  body { margin:0; font: 14px/1.5 -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
         background: var(--bg); color: var(--ink); }
  header { padding: 18px 24px; border-bottom: 1px solid var(--line);
           display: flex; align-items: center; gap: 16px; }
  header h1 { margin: 0; font-size: 18px; }
  header .ver { color: var(--muted); font-size: 12px; }
  main { max-width: 1180px; margin: 0 auto; padding: 24px;
         display: grid; grid-template-columns: 320px 1fr; gap: 24px; }
  aside { display: flex; flex-direction: column; gap: 12px; }
  section.card { background: var(--panel); border: 1px solid var(--line);
                 border-radius: 8px; padding: 14px; }
  section.card h2 { margin: 0 0 8px; font-size: 13px; color: var(--muted);
                    text-transform: uppercase; letter-spacing: .04em; }
  button { background: #21262d; color: var(--ink); border: 1px solid var(--line);
           border-radius: 6px; padding: 8px 12px; cursor: pointer; font-size: 13px; }
  button:hover { background: #30363d; }
  button.primary { background: #238636; border-color: #2ea043; }
  button.primary:hover { background: #2ea043; }
  select, input[type=text] { background: #0d1117; color: var(--ink);
                             border: 1px solid var(--line); border-radius: 6px;
                             padding: 6px 8px; font-size: 13px; width: 100%; }
  label { display: block; font-size: 12px; color: var(--muted);
          margin-bottom: 4px; }
  pre { background: #0d1117; border: 1px solid var(--line); border-radius: 6px;
        padding: 12px; overflow: auto; max-height: 420px; font-size: 12px; }
  .kpi-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .kpi { background: #0d1117; border: 1px solid var(--line); border-radius: 6px;
         padding: 8px; }
  .kpi .k { color: var(--muted); font-size: 11px; }
  .kpi .v { font-size: 16px; font-weight: 600; }
  .kpi.pass .v { color: var(--accent); }
  .kpi.fail .v { color: var(--err); }
  .kpi.warn .v { color: var(--warn); }
  .row { display: flex; gap: 8px; }
  .row > * { flex: 1; }
  #pid-svg-host { background: #fff; border-radius: 6px; padding: 8px;
                  max-height: 480px; overflow: auto; }
  #pid-svg-host svg { max-width: 100%; height: auto; }
  .footer { color: var(--muted); font-size: 12px; padding: 16px 24px;
            border-top: 1px solid var(--line); margin-top: 24px; }
  a { color: #58a6ff; }
  .status-dot { width: 8px; height: 8px; border-radius: 50%;
                background: var(--muted); display: inline-block; margin-right: 6px; }
  .status-dot.ok { background: var(--accent); }
  .status-dot.err { background: var(--err); }
</style>
</head>
<body>
<header>
  <h1>nepal-decarb</h1>
  <span class="ver" id="ver">v0.7.0</span>
  <span style="flex:1"></span>
  <span id="health"><span class="status-dot"></span> <span id="health-text">checking...</span></span>
</header>

<main>
  <aside>
    <section class="card">
      <h2>Status</h2>
      <div id="status-block">loading...</div>
    </section>

    <section class="card">
      <h2>Run cooler</h2>
      <label>Plant preset</label>
      <select id="cooler-plant">
        <option value="planta">planta</option>
        <option value="plantb">plantb</option>
        <option value="plantc">plantc</option>
        <option value="plantd">plantd</option>
      </select>
      <div style="margin-top:8px"><button class="primary" onclick="runCooler()">Run cooler</button></div>
    </section>

    <section class="card">
      <h2>Run kiln</h2>
      <label>Plant preset</label>
      <select id="kiln-plant">
        <option value="planta">planta</option>
      </select>
      <label style="margin-top:8px">Fuel key (optional)</label>
      <input id="kiln-fuel" type="text" placeholder="leave blank for default">
      <div style="margin-top:8px"><button class="primary" onclick="runKiln()">Run kiln</button></div>
    </section>

    <section class="card">
      <h2>Calibrate cooler</h2>
      <label>Target</label>
      <select id="cal-target">
        <option value="synthetic">synthetic (v0.5.0)</option>
        <option value="synthetic-legacy">synthetic-legacy (v0.4.0)</option>
      </select>
      <label style="margin-top:8px"><input id="cal-v04" type="checkbox"> Use v0.4.0 narrow-box</label>
      <div style="margin-top:8px"><button class="primary" onclick="calibrate()">Calibrate</button></div>
    </section>

    <section class="card">
      <h2>Export</h2>
      <div class="row">
        <button onclick="exportStepCooler()">Cooler STEP</button>
        <button onclick="exportStepKiln()">Kiln STEP</button>
      </div>
      <div style="margin-top:8px"><button class="primary" onclick="exportPid()">P&amp;ID (STEP+SVG)</button></div>
    </section>
  </aside>

  <section>
    <section class="card">
      <h2>KPIs (cooler)</h2>
      <div class="kpi-grid" id="cooler-kpis">-- run the cooler to populate --</div>
    </section>

    <section class="card" style="margin-top:16px">
      <h2>Calibration result</h2>
      <pre id="cal-result">-- run calibration to populate --</pre>
    </section>

    <section class="card" style="margin-top:16px">
      <h2>P&amp;ID (PlantA cooler, ISA-5.1)</h2>
      <div id="pid-svg-host">-- click "P&amp;ID" then refresh --</div>
    </section>

    <section class="card" style="margin-top:16px">
      <h2>Raw response</h2>
      <pre id="raw">-- responses will appear here --</pre>
    </section>
  </section>
</main>

<div class="footer">
  nepal-decarb v1.0 (Day 10) -- local FastAPI server.
  All math is open-source (SciPy, NumPy). No data leaves this machine.
</div>

<script>
const $ = (id) => document.getElementById(id);
const raw = $("raw");
function show(obj) { raw.textContent = JSON.stringify(obj, null, 2); }
async function api(path, body) {
  const r = await fetch(path, body ? {method:"POST", headers:{"Content-Type":"application/json"},
                                     body: JSON.stringify(body)} : {});
  const t = await r.text();
  let obj; try { obj = JSON.parse(t); } catch { obj = t; }
  if (!r.ok) { show({error: r.status, body: obj}); throw new Error(`HTTP ${r.status}`); }
  return obj;
}
function bandClass(name, v) {
  const B = {
    secondary_air_outlet_c: [600, 1000],
    tertiary_air_outlet_c:  [400, 700],
    exhaust_air_outlet_c:   [150, 300],
    clinker_outlet_c:       [120, 200],
    cooler_efficiency:      [0.65, 0.85],
    first_law_imbalance:    [0, 0.02],
  };
  const w = B[name]; if (!w) return "";
  if (name === "first_law_imbalance") return v <= w[1] ? "pass" : "fail";
  return (v >= w[0] && v <= w[1]) ? "pass" : "fail";
}
function renderCoolerKpis(out) {
  const names = [
    "secondary_air_outlet_c","tertiary_air_outlet_c","exhaust_air_outlet_c",
    "clinker_outlet_c","cooler_efficiency","first_law_imbalance",
  ];
  const grid = $("cooler-kpis"); grid.innerHTML = "";
  names.forEach(n => {
    const v = out[n];
    if (v === undefined) return;
    const cls = bandClass(n, v);
    const div = document.createElement("div");
    div.className = "kpi " + cls;
    div.innerHTML = `<div class="k">${n}</div><div class="v">${Number(v).toFixed(1)}</div>`;
    grid.appendChild(div);
  });
}
async function refreshStatus() {
  try {
    const s = await api("/api/status");
    const v = await api("/api/version");
    $("ver").textContent = "v" + (v.nepal_decarb_pro || "?");
    const html = Object.entries(s).map(([k,v]) =>
      `<div><span style="color:var(--muted)">${k}:</span> ${v ?? "<span style=color:var(--err)>not installed</span>"}</div>`).join("");
    $("status-block").innerHTML = html;
    $("health").innerHTML = '<span class="status-dot ok"></span><span>ready</span>';
  } catch (e) {
    $("health").innerHTML = '<span class="status-dot err"></span><span>error: '+e.message+'</span>';
  }
}
async function runCooler() {
  const plant = $("cooler-plant").value;
  const r = await api("/api/cooler/run", {plant, out: "pro/demo-output"});
  show(r); renderCoolerKpis(r.outputs);
}
async function runKiln() {
  const plant = $("kiln-plant").value;
  const fuel = $("kiln-fuel").value || null;
  const r = await api("/api/kiln/run", {plant, fuel, out: "pro/demo-output"});
  show(r);
}
async function calibrate() {
  const target = $("cal-target").value;
  const v04 = $("cal-v04").checked;
  const r = await api("/api/cooler/calibrate", {target, v04, out: "pro/demo-output"});
  $("cal-result").textContent = JSON.stringify(r, null, 2);
  if (r.posterior_kpis) renderCoolerKpis(r.posterior_kpis);
  show(r);
}
async function exportStepCooler() {
  const r = await api("/api/cooler/export-step", {});
  show(r); alert("wrote " + r.path + " (" + r.size_bytes + " bytes)");
}
async function exportStepKiln() {
  const r = await api("/api/kiln/export-step", {});
  show(r); alert("wrote " + r.path + " (" + r.size_bytes + " bytes)");
}
async function exportPid() {
  const r = await api("/api/cooler/export-pid", {});
  show(r);
  // Pull the SVG
  const svg = await fetch("/api/pid-svg");
  if (svg.ok) {
    const text = await svg.text();
    $("pid-svg-host").innerHTML = text;
  }
  alert("P&ID written: " + r.written.map(w => w.name + " (" + w.size + "B)").join(", "));
}
refreshStatus();
</script>
</body></html>
"""


# ----------------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------------

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="nepal-decarb-server",
                                description="nepal-decarb FastAPI server (Day 10)")
    p.add_argument("--host", default="127.0.0.1", help="bind host (default 127.0.0.1 = localhost only)")
    p.add_argument("--port", type=int, default=8000, help="bind port (default 8000)")
    p.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev only)")
    args = p.parse_args(argv)
    try:
        import uvicorn
    except ImportError:
        print("[server] uvicorn not installed: python -m pip install uvicorn[standard]")
        return 1
    print(f"[nepal-decarb server] http://{args.host}:{args.port}/")
    print(f"[nepal-decarb server] API docs: http://{args.host}:{args.port}/docs")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
