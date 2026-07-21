"""
OPC-UA Client — read from real industrial DCS systems.
========================================================

Supports: Siemens S7-1500, ABB 800xA, Beckhoff CX, Honeywell Experion,
Yokogawa CENTUM, Emerson DeltaV — all use OPC-UA as the standard.

Required library: asyncua (pip install asyncua)
Fallback: if library not installed, the client runs in simulation mode
with synthetic but realistic values, so the rest of the platform works
for demo / development.

This is a read-only client. We never write to a plant DCS.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try the real library; fall back gracefully.
# ---------------------------------------------------------------------------
try:
    from asyncua import Client as AsyncClient
    from asyncua.ua import DataValue, Variant
    HAS_OPCUA = True
except ImportError:
    HAS_OPCUA = False
    logger.warning("asyncua not installed — OPCUAClient runs in simulation mode")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class OpcuaTag:
    """A single OPC-UA tag mapping."""
    node_id: str                              # OPC-UA NodeId string, e.g. "ns=2;s=KilnTemp"
    description: str
    unit: str
    category: str                             # temperature, pressure, flow, etc.
    min_value: float
    max_value: float
    last_value: Optional[float] = None
    last_quality: str = "unknown"
    last_read_time: float = 0.0


@dataclass
class OpcuaSnapshot:
    """A snapshot of all tag readings at a point in time."""
    plant_id: str
    timestamp: float
    tags: Dict[str, OpcuaTag] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "plant_id": self.plant_id,
            "timestamp": self.timestamp,
            "tags": {k: {"value": v.last_value, "unit": v.unit, "quality": v.last_quality}
                     for k, v in self.tags.items()},
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Standard tag set for a Nepali cement plant
# ---------------------------------------------------------------------------
DEFAULT_TAGS: List[OpcuaTag] = [
    # Kiln
    OpcuaTag("ns=2;s=KILN_T1_BURNING",    "Kiln burning-zone temperature (TC1)",  "°C",  "temperature",  1300, 1600),
    OpcuaTag("ns=2;s=KILN_T2_TRANSITION", "Kiln transition-zone temperature",     "°C",  "temperature",  1000, 1300),
    OpcuaTag("ns=2;s=KILN_T3_CALCIN",     "Kiln calcining-zone temperature",      "°C",  "temperature",   800, 1100),
    OpcuaTag("ns=2;s=KILN_SPEED",        "Kiln rotational speed",                "rpm", "rotational",      2,    5),
    OpcuaTag("ns=2;s=KILN_TORQUE",       "Kiln drive torque",                    "%",   "load",           30,   80),
    OpcuaTag("ns=2;s=KILN_O2",           "Kiln inlet O2",                        "%",   "composition",    0,    8),
    OpcuaTag("ns=2;s=KILN_CO",           "Kiln inlet CO",                        "ppm", "composition",    0,  500),
    OpcuaTag("ns=2;s=KILN_NOX",          "Kiln stack NOx",                       "mg/Nm3","emissions",   200, 1200),
    OpcuaTag("ns=2;s=KILN_SO2",          "Kiln stack SO2",                       "mg/Nm3","emissions",     0,  400),
    OpcuaTag("ns=2;s=KILN_DUST",         "Kiln stack dust",                      "mg/Nm3","emissions",    10,   80),
    OpcuaTag("ns=2;s=KILN_PRESS",        "Kiln inlet pressure",                  "mbar",  "pressure",     -5,    5),
    # Preheater
    OpcuaTag("ns=2;s=PREH_T1",           "Preheater stage 1 temperature",        "°C",  "temperature",  300,  500),
    OpcuaTag("ns=2;s=PREH_T2",           "Preheater stage 2 temperature",        "°C",  "temperature",  400,  600),
    OpcuaTag("ns=2;s=PREH_T3",           "Preheater stage 3 temperature",        "°C",  "temperature",  500,  700),
    OpcuaTag("ns=2;s=PREH_T4",           "Preheater stage 4 temperature",        "°C",  "temperature",  600,  800),
    OpcuaTag("ns=2;s=PREH_T5",           "Preheater stage 5 temperature",        "°C",  "temperature",  700,  900),
    # Mill
    OpcuaTag("ns=2;s=MILL_CEM_FLOW",     "Cement mill throughput",               "t/h", "flow",          50,  180),
    OpcuaTag("ns=2;s=MILL_CEM_POW",     "Cement mill power draw",               "kW",  "power",       2000, 5000),
    OpcuaTag("ns=2;s=MILL_RAW_FLOW",    "Raw mill throughput",                  "t/h", "flow",          80,  250),
    OpcuaTag("ns=2;s=MILL_COAL_FLOW",   "Coal mill throughput",                 "t/h", "flow",          10,   40),
    # Cooler
    OpcuaTag("ns=2;s=COOL_CLINK_T",     "Clinker cooler discharge temperature", "°C",  "temperature",  100,  250),
    OpcuaTag("ns=2;s=COOL_AIR_FLOW",    "Cooler air flow",                      "Nm3/h","flow",      50000,150000),
    # Power
    OpcuaTag("ns=2;s=PLANT_KWH",         "Plant power import",                   "kW",  "power",       5000, 20000),
    OpcuaTag("ns=2;s=PLANT_KWH_DAILY",   "Daily energy consumption",             "kWh", "energy",   100000,500000),
    # Coal feed
    OpcuaTag("ns=2;s=COAL_FEED",         "Coal feed to kiln",                    "t/h", "flow",          10,   35),
    OpcuaTag("ns=2;s=COAL_HV",           "Coal heating value (current)",          "kcal/kg","fuel",  5000, 7000),
    # Emissions (CEMS)
    OpcuaTag("ns=2;s=CEMS_CO2",          "CEMS CO2 (stack)",                     "%",   "emissions",      0,   30),
    OpcuaTag("ns=2;s=CEMS_FLOW",         "CEMS stack flow",                      "Nm3/h","flow",     50000,200000),
    OpcuaTag("ns=2;s=CEMS_TEMP",         "CEMS stack temperature",               "°C",  "temperature",  80,  200),
    # Production
    OpcuaTag("ns=2;s=PROD_CLINK_DAY",    "Daily clinker production",             "t",   "production",   800,  5500),
    OpcuaTag("ns=2;s=PROD_CEM_DAY",     "Daily cement production",              "t",   "production",  1000,  6000),
]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------
class OpcuaClient:
    """Read-only OPC-UA client for cement plant DCS.

    Usage:
        client = OpcuaClient("opc.tcp://plant-dcs.local:4840")
        await client.connect()
        snap = await client.snapshot()
        # snap.tags["KILN_T1_BURNING"].last_value  -> 1450.3
        await client.disconnect()
    """
    def __init__(self, endpoint: str, plant_id: str = "default", tags: Optional[List[OpcuaTag]] = None):
        self.endpoint = endpoint
        self.plant_id = plant_id
        self.tags = {t.node_id: t for t in (tags or DEFAULT_TAGS)}
        self._client: Optional["AsyncClient"] = None
        self._connected = False
        # Simulation state for fallback
        self._sim_t0 = time.time()

    async def connect(self) -> None:
        if not HAS_OPCUA:
            logger.info("OPCUAClient in simulation mode")
            self._connected = True
            return
        self._client = AsyncClient(url=self.endpoint, timeout=10)
        await self._client.connect()
        self._connected = True
        logger.info("OPC-UA connected: %s", self.endpoint)

    async def disconnect(self) -> None:
        if self._client and self._connected:
            await self._client.disconnect()
        self._connected = False

    async def read_tag(self, node_id: str) -> float:
        if not self._connected:
            raise RuntimeError("Not connected")
        if not HAS_OPCUA or self._client is None:
            return self._simulate_tag(node_id)
        dv = await self._client.read_attributes([node_id])
        return dv[0].Value.Value

    async def snapshot(self) -> OpcuaSnapshot:
        if not self._connected:
            raise RuntimeError("Not connected — call connect() first")
        snap = OpcuaSnapshot(plant_id=self.plant_id, timestamp=time.time())
        if HAS_OPCUA and self._client is not None:
            try:
                for nid, tag in self.tags.items():
                    try:
                        dv: DataValue = await self._client.read_attributes([nid])  # type: ignore
                        val = dv[0].Value.Value if dv[0].Value else None
                        tag.last_value = float(val) if val is not None else None
                        tag.last_quality = "Good" if tag.last_value is not None else "Bad"
                        tag.last_read_time = snap.timestamp
                        snap.tags[nid] = tag
                    except Exception as e:
                        snap.errors.append(f"{nid}: {e}")
            except Exception as e:
                snap.errors.append(f"Snapshot error: {e}")
        else:
            # Simulation
            for nid, tag in self.tags.items():
                tag.last_value = self._simulate_tag(nid)
                tag.last_quality = "Good-Simulated"
                tag.last_read_time = snap.timestamp
                snap.tags[nid] = tag
        return snap

    def _simulate_tag(self, node_id: str) -> float:
        """Generate a realistic synthetic value for demo / development."""
        import math
        # Use the node name to pick a sensible baseline + slow oscillation
        t_h = (time.time() - self._sim_t0) / 3600.0
        tag = self.tags.get(node_id)
        if not tag:
            return 0.0
        rng = tag.max_value - tag.min_value
        # Center of range with slow sinusoidal drift
        center = (tag.max_value + tag.min_value) / 2
        osc = 0.15 * rng * math.sin(t_h * 0.5 + hash(node_id) % 100)
        noise = 0.03 * rng * math.sin(t_h * 7.0 + hash(node_id) % 50)
        return round(center + osc + noise, 2)


# ---------------------------------------------------------------------------
# CLI helper: stream tags to stdout (for debugging at the plant)
# ---------------------------------------------------------------------------
async def stream_tags(endpoint: str, plant_id: str, interval_s: float = 5.0, max_iter: Optional[int] = None) -> None:
    client = OpcuaClient(endpoint, plant_id)
    await client.connect()
    print(f"Streaming OPC-UA tags from {endpoint} every {interval_s}s (Ctrl+C to stop)")
    print("-" * 80)
    i = 0
    try:
        while max_iter is None or i < max_iter:
            snap = await client.snapshot()
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(snap.timestamp))
            print(f"\n[{ts}] {snap.plant_id} — {len(snap.tags)} tags")
            for nid, tag in list(snap.tags.items())[:8]:
                print(f"  {tag.description:50s}  {tag.last_value:>10.2f} {tag.unit}")
            i += 1
            await asyncio.sleep(interval_s)
    except KeyboardInterrupt:
        pass
    finally:
        await client.disconnect()


if __name__ == "__main__":  # pragma: no cover
    import sys
    endpoint = sys.argv[1] if len(sys.argv) > 1 else "opc.tcp://demo.local:4840"
    asyncio.run(stream_tags(endpoint, "demo", interval_s=2.0))
