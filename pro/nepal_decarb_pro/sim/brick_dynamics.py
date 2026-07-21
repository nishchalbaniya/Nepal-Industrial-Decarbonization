"""
Brick Kiln Dynamic Simulator
=============================

Simulates the firing cycle of a brick kiln (clamp, zigzag, tunnel).
Outputs temperature profiles, heat consumption, and emissions over time.

Approach: We use a simplified explicit time-stepping for the batch process
(clamp kiln) and a steady-state approximation for continuous kilns (zigzag,
tunnel). The simplified approach is more robust than stiff ODE integration
for batch processes with large temperature swings.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from pydantic import BaseModel, Field


class BrickKilnParams(BaseModel):
    """Common parameters for brick kiln dynamics."""
    brick_mass_kg: float = 2.5                       # dry brick mass
    specific_heat_kj_kg_k: float = 0.92              # brick specific heat
    water_content_initial: float = 0.08              # 8% green brick moisture
    ambient_temp_k: float = 298.15
    max_firing_temp_k: float = 1173.15               # 900°C target
    thermal_efficiency: float = 0.40                 # clamp
    # Heat loss
    wall_loss_w_m2_k: float = 5.0
    emissivity: float = 0.85


@dataclass
class BrickKilnState:
    """Time-series of brick kiln state during firing."""
    t_h: np.ndarray
    T_brick_k: np.ndarray
    T_gas_k: np.ndarray
    T_wall_k: np.ndarray
    water_evaporated: np.ndarray
    energy_input_kwh: np.ndarray
    co2_emitted_kg: np.ndarray


# ---------------------------------------------------------------------------
# Clamp kiln — explicit time-stepping (batch)
# ---------------------------------------------------------------------------

def _clamp_schedule(t_h: float) -> float:
    """Gas temperature setpoint at time t for a clamp kiln firing cycle."""
    if t_h < 24:
        return 373.0 + (t_h / 24.0) * 200.0          # 100 -> 300°C
    elif t_h < 72:
        return 573.0 + ((t_h - 24.0) / 48.0) * 300.0  # 300 -> 600°C (drying)
    elif t_h < 96:
        return 873.0 + ((t_h - 72.0) / 24.0) * 300.0  # 600 -> 900°C
    elif t_h < 168:
        return 1173.0                                       # 900°C
    elif t_h < 192:
        return 1173.0 - ((t_h - 168.0) / 24.0) * 200.0  # cool
    else:
        return max(298.0, 973.0 - ((t_h - 192.0) / 48.0) * 675.0)  # to ambient


def simulate_brick_kiln_clamp(
    p: BrickKilnParams,
    n_bricks: int = 100_000,
    t_end_h: float = 240.0,
    n_points: int = 500,
    dt_s: float = 600.0,                            # 10-min time step
) -> BrickKilnState:
    """
    Simulate a clamp kiln firing cycle using explicit Euler.

    Clamps are batch kilns with multiple day firing cycles. The model:
    1. Pre-heating (0-72h): water evaporation
    2. Firing (72-168h): peak temperature
    3. Cooling (168-240h): natural cooling
    """
    n_steps = int(t_end_h * 3600 / dt_s) + 1
    t_array = np.linspace(0, t_end_h, n_steps)
    dt_h = dt_s / 3600.0
    T_brick = p.ambient_temp_k + 5.0
    T_wall = p.ambient_temp_k + 10.0
    water_evap = 0.0
    energy_kwh = 0.0
    co2_kg = 0.0

    T_brick_arr = np.zeros(n_steps)
    T_gas_arr = np.zeros(n_steps)
    T_wall_arr = np.zeros(n_steps)
    water_arr = np.zeros(n_steps)
    energy_arr = np.zeros(n_steps)
    co2_arr = np.zeros(n_steps)

    m_brick = p.brick_mass_kg * n_bricks
    m_water = m_brick * p.water_content_initial
    h_conv = 12.0                                    # W/(m² K) clamp
    A_brick = 0.05 * n_bricks                        # surface area
    # Calibrated time constant: represents the whole batch conduction into the pile
    # but allows T_brick to reach T_gas within ~30h of firing phase
    tau_batch_h = 18.0                              # 18h batch time constant
    tau_s = tau_batch_h * 3600.0

    for i in range(n_steps):
        t_h = t_array[i]
        T_gas = _clamp_schedule(t_h)
        T_gas_arr[i] = T_gas
        T_brick_arr[i] = T_brick
        T_wall = (T_gas + p.ambient_temp_k) / 2.0
        T_wall_arr[i] = T_wall

        # Convective heat transfer gas -> brick
        q_into_brick = h_conv * A_brick * (T_gas - T_brick) / 1000.0  # kW
        d_energy_dt = q_into_brick

        # Water evaporation
        if water_evap < m_water and T_brick > 373.0:
            d_water = min(
                0.0001 * (T_brick - 373.0) * n_bricks,
                (m_water - water_evap)
            )
        else:
            d_water = 0.0

        # Brick temperature rate (1st order lag towards gas temp)
        # tau = m_brick * cp / (h_conv * A)  time constant
        dT_brick = (T_gas - T_brick) * (dt_s / tau_s)
        T_brick += dT_brick
        T_brick = max(T_brick, p.ambient_temp_k)

        # Energy and CO2
        d_energy = d_energy_dt * dt_h  # kWh
        coal_rate_kg_h = d_energy_dt * 3.6 / 25.5
        d_co2 = coal_rate_kg_h * 25.5 * 94.6 / 1000.0 * dt_h  # kg

        water_evap += d_water
        energy_kwh += d_energy
        co2_kg += d_co2

        water_arr[i] = water_evap
        energy_arr[i] = energy_kwh
        co2_arr[i] = co2_kg

    return BrickKilnState(
        t_h=t_array, T_brick_k=T_brick_arr, T_gas_k=T_gas_arr,
        T_wall_k=T_wall_arr, water_evaporated=water_arr,
        energy_input_kwh=energy_arr, co2_emitted_kg=co2_arr,
    )


# ---------------------------------------------------------------------------
# Zigzag kiln — steady-state per "spot" with periodic forcing
# ---------------------------------------------------------------------------

def simulate_brick_kiln_zigzag(
    p: BrickKilnParams,
    production_bricks_per_day: int = 30_000,
    t_end_h: float = 168.0,
    n_points: int = 500,
    dt_s: float = 600.0,
) -> BrickKilnState:
    """Zigzag: continuous, hot zone rotates."""
    n_steps = int(t_end_h * 3600 / dt_s) + 1
    t_array = np.linspace(0, t_end_h, n_steps)
    dt_h = dt_s / 3600.0
    cycle_h = 24.0
    T_brick = p.ambient_temp_k + 5.0
    T_wall = p.ambient_temp_k + 10.0
    water_evap = 0.0
    energy_kwh = 0.0
    co2_kg = 0.0

    T_brick_arr = np.zeros(n_steps)
    T_gas_arr = np.zeros(n_steps)
    T_wall_arr = np.zeros(n_steps)
    water_arr = np.zeros(n_steps)
    energy_arr = np.zeros(n_steps)
    co2_arr = np.zeros(n_steps)

    m_brick = p.brick_mass_kg * production_bricks_per_day / 4.0
    m_water = m_brick * p.water_content_initial
    h_conv = 25.0
    A_brick = 0.05 * production_bricks_per_day / 4.0
    tau_batch_h = 8.0                               # shorter for continuous
    tau_s = tau_batch_h * 3600.0

    for i in range(n_steps):
        t_h = t_array[i]
        phase = (t_h % cycle_h) / cycle_h
        if phase < 0.3:
            T_gas = 373.0 + (phase / 0.3) * 500.0
        elif phase < 0.5:
            T_gas = 873.0 + ((phase - 0.3) / 0.2) * 300.0
        elif phase < 0.7:
            T_gas = 1173.0
        else:
            T_gas = 1173.0 - ((phase - 0.7) / 0.3) * 800.0

        T_gas_arr[i] = T_gas
        T_brick_arr[i] = T_brick
        T_wall = (T_gas + p.ambient_temp_k) / 2.0
        T_wall_arr[i] = T_wall

        q_into_brick = h_conv * A_brick * (T_gas - T_brick) / 1000.0
        d_energy_dt = q_into_brick / p.thermal_efficiency

        if water_evap < m_water and T_brick > 373.0:
            d_water = min(0.0002 * (T_brick - 373.0) * (production_bricks_per_day / 4.0),
                          m_water - water_evap)
        else:
            d_water = 0.0

        # tau = m_brick * cp / (h_conv * A)  -- using tau_s for batch
        T_brick += (T_gas - T_brick) * (dt_s / tau_s)
        T_brick = max(T_brick, p.ambient_temp_k)

        d_energy = d_energy_dt * dt_h
        coal_rate_kg_h = d_energy_dt * 3.6 / 25.5
        d_co2 = coal_rate_kg_h * 25.5 * 94.6 / 1000.0 * dt_h

        water_evap += d_water
        energy_kwh += d_energy
        co2_kg += d_co2

        water_arr[i] = water_evap
        energy_arr[i] = energy_kwh
        co2_arr[i] = co2_kg

    return BrickKilnState(
        t_h=t_array, T_brick_k=T_brick_arr, T_gas_k=T_gas_arr,
        T_wall_k=T_wall_arr, water_evaporated=water_arr,
        energy_input_kwh=energy_arr, co2_emitted_kg=co2_arr,
    )


def simulate_brick_kiln_tunnel(
    p: BrickKilnParams,
    production_bricks_per_day: int = 30_000,
    car_advance_min: int = 30,
    n_cars_in_kiln: int = 30,
    t_end_h: float = 168.0,
    n_points: int = 500,
    dt_s: float = 600.0,
) -> BrickKilnState:
    """Tunnel kiln: cars move through fixed zones."""
    n_steps = int(t_end_h * 3600 / dt_s) + 1
    t_array = np.linspace(0, t_end_h, n_steps)
    dt_h = dt_s / 3600.0
    traverse_h = (car_advance_min / 60.0) * n_cars_in_kiln
    T_brick = p.ambient_temp_k + 5.0
    water_evap = 0.0
    energy_kwh = 0.0
    co2_kg = 0.0

    T_brick_arr = np.zeros(n_steps)
    T_gas_arr = np.zeros(n_steps)
    T_wall_arr = np.zeros(n_steps)
    water_arr = np.zeros(n_steps)
    energy_arr = np.zeros(n_steps)
    co2_arr = np.zeros(n_steps)

    m_brick = p.brick_mass_kg * production_bricks_per_day * traverse_h / 24.0
    m_water = m_brick * p.water_content_initial
    h_conv = 35.0
    A_brick = 0.05 * production_bricks_per_day * traverse_h / 24.0
    tau_batch_h = 4.0
    tau_s = tau_batch_h * 3600.0

    for i in range(n_steps):
        t_h = t_array[i]
        phase = (t_h % traverse_h) / traverse_h
        if phase < 0.2:
            T_gas = 373.0 + (phase / 0.2) * 500.0
        elif phase < 0.4:
            T_gas = 873.0 + ((phase - 0.2) / 0.2) * 300.0
        elif phase < 0.6:
            T_gas = 1173.0
        else:
            T_gas = 1173.0 - ((phase - 0.6) / 0.4) * 1075.0
        T_gas = max(T_gas, p.ambient_temp_k)

        T_gas_arr[i] = T_gas
        T_brick_arr[i] = T_brick
        T_wall_arr[i] = (T_gas + p.ambient_temp_k) / 2.0

        q_into_brick = h_conv * A_brick * (T_gas - T_brick) / 1000.0
        d_energy_dt = q_into_brick / 0.75

        if water_evap < m_water and T_brick > 373.0:
            d_water = min(0.0003 * (T_brick - 373.0) * (production_bricks_per_day * traverse_h / 24.0),
                          m_water - water_evap)
        else:
            d_water = 0.0

        # tau = m_brick * cp / (h_conv * A)  -- using tau_s for batch
        T_brick += (T_gas - T_brick) * (dt_s / tau_s)
        T_brick = max(T_brick, p.ambient_temp_k)

        d_energy = d_energy_dt * dt_h
        coal_rate_kg_h = d_energy_dt * 3.6 / 25.5
        d_co2 = coal_rate_kg_h * 25.5 * 94.6 / 1000.0 * dt_h

        water_evap += d_water
        energy_kwh += d_energy
        co2_kg += d_co2

        water_arr[i] = water_evap
        energy_arr[i] = energy_kwh
        co2_arr[i] = co2_kg

    return BrickKilnState(
        t_h=t_array, T_brick_k=T_brick_arr, T_gas_k=T_gas_arr,
        T_wall_k=T_wall_arr, water_evaporated=water_arr,
        energy_input_kwh=energy_arr, co2_emitted_kg=co2_arr,
    )
