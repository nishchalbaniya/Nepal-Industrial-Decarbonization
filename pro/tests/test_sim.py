"""Tests for the simulator modules."""
import pytest
import numpy as np
from nepal_decarb_pro.sim.kiln_dynamics import (
    KilnParameters, simulate_kiln, run_to_steady_state, compute_outputs,
    arrhenius_rate, convective_htc, radiative_flux,
)
from nepal_decarb_pro.sim.brick_dynamics import (
    BrickKilnParams, simulate_brick_kiln_clamp, simulate_brick_kiln_zigzag,
    simulate_brick_kiln_tunnel,
)
from nepal_decarb_pro.sim.equipment_specs import (
    EQUIPMENT_DATABASE, get_equipment, list_equipment, equipment_by_category,
)
from nepal_decarb_pro.sim.process_flows import (
    generate_pfd_cement, generate_pfd_brick, generate_pid_cement,
)
from nepal_decarb_pro.sim.cad_export import (
    generate_dxf_kiln, generate_dxf_cyclone_preheater,
    generate_freecad_macro, generate_svg_kiln,
)
from nepal_decarb_pro.forecasting.models import (
    ets_forecast, naive_forecast, fit_and_forecast,
)
from nepal_decarb_pro.pinch.analysis import Stream, pinch_analysis, grand_composite_curve
from nepal_decarb_pro.dt.twin import DigitalTwin, kalman_update, detect_anomaly, SensorReading


# =============================================================================
# Kiln dynamics
# =============================================================================

def test_arrhenius():
    k_low = arrhenius_rate(800, 1e6, 110_000)
    k_high = arrhenius_rate(1500, 1e6, 110_000)
    assert k_high > k_low * 100  # rate increases dramatically with T


def test_convective_htc():
    h = convective_htc(Re=10000, Pr=0.7, k=0.05, D=4.6)
    # Nu ~ 19.3, k/D ~ 0.011, h ~ 0.21 W/(m²K) — physically reasonable for gas
    assert 0.1 < h < 50


def test_radiative_flux():
    q = radiative_flux(1500, 800, 0.85)
    assert q > 0


def test_kiln_simulate():
    p = KilnParameters(n_zones=5, t_end_s=600.0)
    t, y, x = simulate_kiln(p, n_time_points=20)
    assert len(t) == 20
    assert y.shape == (6 * p.n_zones, 20)
    assert len(x) == p.n_zones


def test_kiln_steady_state():
    p = KilnParameters(n_zones=5, raw_meal_throughput_t_h=200.0, fuel_rate_t_h=18.0)
    state = run_to_steady_state(p, max_t_s=1200.0)
    # Verify reasonable temperatures
    assert np.max(state.t_solid_k) > 1000     # burning zone
    assert np.max(state.t_gas_k) > 1000


def test_kiln_outputs():
    p = KilnParameters()
    state = run_to_steady_state(p)
    out = compute_outputs(state, p)
    assert "t_clinker_peak_c" in out
    assert "sec_mj_per_t_clinker" in out
    assert out["sec_mj_per_t_clinker"] > 0
    assert out["co2_total_t_h"] > 0
    # 5000 TPD should produce ~0.7-1.2 Mt CO2/yr
    co2_yr = out["co2_total_t_h"] * 24 * 365 / 1e6
    assert 0.5 < co2_yr < 2.0


# =============================================================================
# Brick dynamics
# =============================================================================

def test_clamp_kiln_simulate():
    p = BrickKilnParams()
    state = simulate_brick_kiln_clamp(p, n_bricks=100_000, t_end_h=72.0, n_points=50)
    assert state.t_h[-1] == 72.0
    assert state.T_brick_k[-1] > p.ambient_temp_k


def test_zigzag_kiln_simulate():
    p = BrickKilnParams(thermal_efficiency=0.70)
    state = simulate_brick_kiln_zigzag(p, production_bricks_per_day=20_000, t_end_h=72.0, n_points=50)
    assert state.t_h[-1] == 72.0


def test_tunnel_kiln_simulate():
    p = BrickKilnParams(thermal_efficiency=0.75)
    state = simulate_brick_kiln_tunnel(p, production_bricks_per_day=30_000, t_end_h=72.0, n_points=50)
    assert state.t_h[-1] == 72.0


# =============================================================================
# Equipment
# =============================================================================

def test_equipment_database():
    assert len(EQUIPMENT_DATABASE) >= 30
    assert "rotary_kiln_5000tpd" in EQUIPMENT_DATABASE


def test_get_equipment():
    eq = get_equipment("rotary_kiln_5000tpd")
    assert eq.length_m == 72.0
    assert eq.diameter_m == 4.6


def test_equipment_categories():
    kilns = equipment_by_category("kiln")
    assert len(kilns) >= 2
    bricks = equipment_by_category("brick")
    assert len(bricks) >= 4


def test_list_equipment():
    ids = list_equipment()
    assert "vrm_raw_300tph" in ids
    assert "clamp_kiln_small" in ids


# =============================================================================
# Process flows
# =============================================================================

def test_generate_pfd_cement(tmp_path):
    out = generate_pfd_cement(tmp_path / "pfd_cement.png")
    assert out.exists()
    assert out.stat().st_size > 1000


def test_generate_pfd_brick(tmp_path):
    out = generate_pfd_brick(tmp_path / "pfd_brick.png", kiln_type="zigzag")
    assert out.exists()


def test_generate_pid_cement(tmp_path):
    out = generate_pid_cement(tmp_path / "pid.png")
    assert out.exists()


# =============================================================================
# CAD export
# =============================================================================

def test_dxf_kiln(tmp_path):
    out = generate_dxf_kiln(out_path=tmp_path / "kiln.dxf")
    assert out.exists()
    text = out.read_text()
    assert "DXF" in text or "ENTITIES" in text
    assert "LINE" in text or "CIRCLE" in text


def test_dxf_cyclone(tmp_path):
    out = generate_dxf_cyclone_preheater(out_path=tmp_path / "cyclone.dxf")
    assert out.exists()


def test_freecad_macro(tmp_path):
    out = generate_freecad_macro(out_path=tmp_path / "kiln.FCMacro")
    assert out.exists()
    text = out.read_text()
    assert "import FreeCAD" in text
    assert "makeCylinder" in text


def test_svg_kiln(tmp_path):
    out = generate_svg_kiln(out_path=tmp_path / "kiln.svg")
    assert out.exists()
    text = out.read_text()
    assert "<svg" in text
    assert "ellipse" in text  # kiln end circles


# =============================================================================
# Forecasting
# =============================================================================

def test_ets_forecast():
    history = [100 + 10 * np.sin(i / 6) + np.random.normal(0, 2) for i in range(60)]
    result = ets_forecast(history, horizon=12, season_length=12)
    assert len(result.point_forecast) == 12
    assert result.mape >= 0
    assert result.rmse >= 0


def test_naive_forecast():
    history = [100, 102, 98, 101, 99]
    result = naive_forecast(history, horizon=6)
    assert all(v == 99 for v in result.point_forecast)  # last value


# =============================================================================
# Pinch
# =============================================================================

def test_pinch_simple():
    streams = [
        Stream(name="Hot flue gas", supply_temp_c=350, target_temp_c=120, cp_kw_per_k=10),
        Stream(name="Cold air", supply_temp_c=25, target_temp_c=200, cp_kw_per_k=8),
    ]
    r = pinch_analysis(streams, dT_min_c=10.0)
    assert r.q_h_min_kw >= 0
    assert r.q_c_min_kw >= 0
    assert r.mer_kw >= 0


def test_pinch_cement_typical():
    """Typical cement plant: kiln exhaust (hot) heats raw meal + combustion air (cold)."""
    streams = [
        Stream(name="Kiln exhaust", supply_temp_c=350, target_temp_c=180, cp_kw_per_k=20),
        Stream(name="Clinker cooler air out", supply_temp_c=600, target_temp_c=200, cp_kw_per_k=15),
        Stream(name="Raw meal (cold)", supply_temp_c=80, target_temp_c=300, cp_kw_per_k=12),
        Stream(name="Combustion air (cold)", supply_temp_c=30, target_temp_c=250, cp_kw_per_k=8),
    ]
    r = pinch_analysis(streams, dT_min_c=20.0)
    assert r.mer_kw > 0


def test_grand_composite():
    streams = [
        Stream(name="Hot 1", supply_temp_c=300, target_temp_c=100, cp_kw_per_k=5),
        Stream(name="Cold 1", supply_temp_c=50, target_temp_c=200, cp_kw_per_k=4),
    ]
    gcc = grand_composite_curve(streams)
    assert "temperature_c" in gcc
    assert "heat_available_kw" in gcc


# =============================================================================
# Digital Twin
# =============================================================================

def test_kalman_update():
    state = (10.0, 1.0)
    new_state = kalman_update(state, 12.0, quality=1.0)
    # Estimate should move toward measurement
    assert new_state[0] > 10.0
    assert new_state[0] < 12.0


def test_detect_anomaly_normal():
    history = [10, 11, 9, 10, 11, 10, 9, 10, 11] * 3
    assert not detect_anomaly(history, 10.5, threshold=3.0)


def test_detect_anomaly_outlier():
    history = [10, 11, 9, 10, 11, 10, 9, 10, 11] * 3
    assert detect_anomaly(history, 50, threshold=3.0)


def test_digital_twin_update():
    twin = DigitalTwin("test_plant")
    readings = [
        SensorReading(sensor_id="T-001", sensor_type="temperature",
                      value=1450, unit="C"),
        SensorReading(sensor_id="P-001", sensor_type="pressure",
                      value=101325, unit="Pa"),
    ]
    state = twin.update(readings)
    assert "T-001_temperature" in state.estimated
    assert "P-001_pressure" in state.estimated


def test_digital_twin_anomaly_detection():
    twin = DigitalTwin("test_plant")
    # Feed normal readings
    for v in [10, 11, 9, 10, 11, 10, 9, 10, 11, 10, 11, 9] * 3:
        twin.update([SensorReading(sensor_id="T-001", sensor_type="temperature",
                                   value=v, unit="C")])
    # Send outlier
    state = twin.update([SensorReading(sensor_id="T-001", sensor_type="temperature",
                                       value=100, unit="C")])
    assert len(state.anomalies) > 0
