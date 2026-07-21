"""
MODBUS RTU/TCP Client — read from PLCs, instruments, energy meters.
====================================================================

Supports: Schneider M340/M580, Allen-Bradley CompactLogix, Siemens S7-200/300/400
(with gateway), generic instruments with MODBUS interface.

Required library: pymodbus (pip install pymodbus>=3.5)
Falls back to simulation when not installed.
"""
from __future__ import annotations

import asyncio
import logging
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from pymodbus.client import AsyncModbusTcpClient, AsyncModbusSerialClient
    HAS_MODBUS = True
except ImportError:
    HAS_MODBUS = False
    logger.warning("pymodbus not installed — ModbusClient runs in simulation mode")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class ModbusRegister:
    """A single MODBUS register (16-bit or 32-bit)."""
    address: int                              # 0-based register address
    name: str
    description: str
    unit: str
    scale: float = 1.0                        # engineering unit scaling
    offset: float = 0.0
    data_type: str = "uint16"                 # uint16, int16, uint32, int32, float32
    function_code: int = 3                    # 3 = holding, 4 = input
    category: str = "process"
    min_value: float = 0.0
    max_value: float = 100.0
    last_value: Optional[float] = None
    last_quality: str = "unknown"


@dataclass
class ModbusSnapshot:
    plant_id: str
    timestamp: float
    registers: Dict[str, ModbusRegister] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Default register map for a Nepali cement plant
# ---------------------------------------------------------------------------
DEFAULT_REGISTERS: List[ModbusRegister] = [
    # Energy meter (Schneider PM5560 or similar, slave 1)
    ModbusRegister(0x0000, "EM_VLL_AVG", "Average line-to-line voltage", "V",
                   data_type="float32", scale=1.0, min_value=380, max_value=420, category="electrical"),
    ModbusRegister(0x0002, "EM_CURR_TOT", "Total current",                "A",
                   data_type="float32", scale=1.0, min_value=100, max_value=500, category="electrical"),
    ModbusRegister(0x0004, "EM_KW_TOT",  "Total active power",            "kW",
                   data_type="float32", scale=1.0, min_value=5000, max_value=20000, category="electrical"),
    ModbusRegister(0x0006, "EM_KWH_TOT", "Total energy",                  "kWh",
                   data_type="float32", scale=1.0, min_value=0, max_value=1e8, category="electrical"),
    ModbusRegister(0x0008, "EM_PF",      "Power factor",                  "",
                   data_type="float32", scale=1.0, min_value=0.7, max_value=1.0, category="electrical"),
    ModbusRegister(0x000A, "EM_FREQ",    "Frequency",                     "Hz",
                   data_type="float32", scale=1.0, min_value=49.0, max_value=51.0, category="electrical"),
    # Kiln drive VFD (slave 2)
    ModbusRegister(0x0100, "DRIVE_FREQ", "Kiln drive frequency",          "Hz",
                   data_type="float32", scale=1.0, min_value=0, max_value=50, category="drives"),
    ModbusRegister(0x0102, "DRIVE_RPM",  "Kiln drive speed",              "rpm",
                   data_type="float32", scale=1.0, min_value=2, max_value=5, category="drives"),
    ModbusRegister(0x0104, "DRIVE_TORQ", "Kiln drive torque",             "%",
                   data_type="float32", scale=1.0, min_value=30, max_value=80, category="drives"),
    ModbusRegister(0x0106, "DRIVE_KW",   "Kiln drive power",              "kW",
                   data_type="float32", scale=1.0, min_value=200, max_value=800, category="drives"),
    # Bag filter DP (slave 3, holding registers)
    ModbusRegister(0x0200, "BF_DP",      "Bag filter differential P",    "mbar",
                   data_type="uint16", scale=1.0, min_value=5, max_value=30, category="emissions"),
    ModbusRegister(0x0201, "BF_FAN_HZ",  "Bag filter fan speed",          "Hz",
                   data_type="uint16", scale=0.1, min_value=40, max_value=60, category="emissions"),
    # Coal feeder (slave 4)
    ModbusRegister(0x0300, "COAL_SP",    "Coal feed setpoint",            "t/h",
                   data_type="float32", scale=0.1, min_value=0, max_value=50, category="process"),
    ModbusRegister(0x0302, "COAL_PV",    "Coal feed actual",              "t/h",
                   data_type="float32", scale=0.1, min_value=0, max_value=50, category="process"),
    # Cement mill (slave 5)
    ModbusRegister(0x0400, "MILL_KW",    "Mill motor power",              "kW",
                   data_type="float32", scale=1.0, min_value=2000, max_value=5000, category="process"),
    ModbusRegister(0x0402, "MILL_FLOW",  "Mill throughput",               "t/h",
                   data_type="float32", scale=1.0, min_value=50, max_value=200, category="process"),
    # Pyrometer (slave 6)
    ModbusRegister(0x0500, "PYRO_T",     "Pyrometer temperature",         "°C",
                   data_type="uint16", scale=1.0, min_value=800, max_value=1600, category="temperature"),
]


def _decode_value(registers: List[int], data_type: str) -> float:
    """Decode a MODBUS register value (uint16, int16, uint32, int32, float32)."""
    if not registers:
        return 0.0
    if data_type == "uint16":
        return float(registers[0])
    if data_type == "int16":
        v = registers[0]
        return float(v - 65536) if v & 0x8000 else float(v)
    if data_type in ("uint32", "int32", "float32"):
        # Word order: big-endian (standard MODBUS)
        # Slave order: high word first
        if len(registers) < 2:
            return 0.0
        b = struct.pack(">HH", registers[0], registers[1])
        if data_type == "uint32":
            return float(struct.unpack(">I", b)[0])
        if data_type == "int32":
            return float(struct.unpack(">i", b)[0])
        if data_type == "float32":
            return struct.unpack(">f", b)[0]
    return 0.0


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class ModbusClient:
    """Read-only MODBUS TCP/RTU client for cement plant instrumentation.

    Usage:
        client = ModbusClient(host="10.1.2.100", port=502)
        await client.connect()
        snap = await client.snapshot()
        await client.disconnect()
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 502,
                 plant_id: str = "default", unit_id: int = 1,
                 registers: Optional[List[ModbusRegister]] = None,
                 serial: bool = False, serial_port: str = "/dev/ttyUSB0"):
        self.host = host
        self.port = port
        self.plant_id = plant_id
        self.unit_id = unit_id
        self.serial = serial
        self.serial_port = serial_port
        self.registers = {r.name: r for r in (registers or DEFAULT_REGISTERS)}
        self._client: Optional[Any] = None
        self._connected = False
        self._sim_t0 = time.time()

    async def connect(self) -> None:
        if not HAS_MODBUS:
            logger.info("ModbusClient in simulation mode")
            self._connected = True
            return
        if self.serial:
            self._client = AsyncModbusSerialClient(self.serial_port, baudrate=9600, timeout=3)
        else:
            self._client = AsyncModbusTcpClient(self.host, port=self.port, timeout=3)
        await self._client.connect()
        self._connected = True
        logger.info("MODBUS connected: %s:%s", self.host, self.port)

    async def disconnect(self) -> None:
        if self._client and self._connected:
            self._client.close()
        self._connected = False

    async def read_register(self, name: str) -> float:
        if not self._connected:
            raise RuntimeError("Not connected")
        reg = self.registers.get(name)
        if not reg:
            raise KeyError(name)
        if not HAS_MODBUS or self._client is None:
            return self._simulate_register(name)
        if reg.data_type == "float32" or reg.data_type in ("uint32", "int32"):
            count = 2
        else:
            count = 1
        if reg.function_code == 4:
            rr = await self._client.read_input_registers(address=reg.address,
                                                          count=count,
                                                          slave=self.unit_id)
        else:
            rr = await self._client.read_holding_registers(address=reg.address,
                                                            count=count,
                                                            slave=self.unit_id)
        if rr.isError():
            raise IOError(f"MODBUS error: {rr}")
        val = _decode_value(rr.registers, reg.data_type)
        return val * reg.scale + reg.offset

    async def snapshot(self) -> ModbusSnapshot:
        if not self._connected:
            raise RuntimeError("Not connected")
        snap = ModbusSnapshot(plant_id=self.plant_id, timestamp=time.time())
        for name, reg in self.registers.items():
            try:
                reg.last_value = await self.read_register(name)
                reg.last_quality = "Good" if HAS_MODBUS else "Good-Simulated"
                snap.registers[name] = reg
            except Exception as e:
                snap.errors.append(f"{name}: {e}")
                reg.last_quality = "Bad"
        return snap

    def _simulate_register(self, name: str) -> float:
        import math
        t_h = (time.time() - self._sim_t0) / 3600.0
        reg = self.registers.get(name)
        if not reg:
            return 0.0
        rng = reg.max_value - reg.min_value
        center = (reg.max_value + reg.min_value) / 2
        osc = 0.20 * rng * math.sin(t_h * 0.4 + hash(name) % 100)
        noise = 0.04 * rng * math.sin(t_h * 9.0 + hash(name) % 50)
        return round(center + osc + noise, 2)
