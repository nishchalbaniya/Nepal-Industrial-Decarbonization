"""Industrial integration — OPC-UA, MODBUS, historian, Aspen, MATLAB."""
from .opcua_client import OpcuaClient, OpcuaTag, OpcuaSnapshot, DEFAULT_TAGS
from .modbus_client import ModbusClient, ModbusRegister, ModbusSnapshot, DEFAULT_REGISTERS
from .historian import Historian, InMemoryHistorian, TimescaleDBHistorian
from .aspen_export import AspenExporter
from .matlab_export import MatlabExporter

__all__ = [
    "OpcuaClient", "OpcuaTag", "OpcuaSnapshot", "DEFAULT_TAGS",
    "ModbusClient", "ModbusRegister", "ModbusSnapshot", "DEFAULT_REGISTERS",
    "Historian", "InMemoryHistorian", "TimescaleDBHistorian",
    "AspenExporter", "MatlabExporter",
]
