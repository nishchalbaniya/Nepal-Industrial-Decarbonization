"""
MQTT bridge for IoT sensor data ingestion.

Connects to a broker (Mosquitto, HiveMQ, AWS IoT, etc.), receives
sensor data from ESP32/Arduino devices in cement plants and brick kilns,
and routes to the emissions calculation engine.
"""
from __future__ import annotations

import json
import asyncio
from typing import Dict, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MQTTSensor(BaseModel):
    """A registered IoT sensor."""
    sensor_id: str
    sensor_type: str                            # temperature | flow | co2 | dust | energy
    location: str                               # Plant location
    unit: str
    topic: str
    last_value: Optional[float] = None
    last_updated: Optional[str] = None


class MQTTBridge:
    """
    MQTT bridge for IoT sensor data.

    Usage:
        bridge = MQTTBridge(broker="mqtt://localhost:1883")
        bridge.add_sensor("kiln-temp-01", "temperature", "PlantA", "C", "factory/kiln/temp")
        bridge.on_message(lambda sensor, value, ts: print(sensor, value))
        bridge.run()
    """

    def __init__(
        self,
        broker: str = "mqtt://localhost:1883",
        port: int = 1883,
        client_id: str = "nepal-decarb-bridge",
    ) -> None:
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.sensors: Dict[str, MQTTSensor] = {}
        self.callback: Optional[Callable] = None
        self.connected = False

    def add_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        location: str,
        unit: str,
        topic: str,
    ) -> MQTTSensor:
        sensor = MQTTSensor(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            location=location,
            unit=unit,
            topic=topic,
        )
        self.sensors[sensor_id] = sensor
        return sensor

    def on_message(self, callback: Callable) -> None:
        """Set the message callback: callback(sensor, value, timestamp)."""
        self.callback = callback

    def _on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker {self.broker}")
            for sensor in self.sensors.values():
                client.subscribe(sensor.topic)
                logger.info(f"Subscribed to {sensor.topic}")
        else:
            logger.error(f"Failed to connect, code {rc}")

    def _on_message(self, client, userdata, msg) -> None:
        try:
            payload = json.loads(msg.payload.decode())
            # Find sensor by topic
            for sensor in self.sensors.values():
                if sensor.topic == msg.topic:
                    sensor.last_value = float(payload.get("value", 0))
                    sensor.last_updated = datetime.now().isoformat()
                    if self.callback:
                        self.callback(sensor, sensor.last_value, sensor.last_updated)
                    break
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def run(self) -> None:
        """Start the MQTT bridge (blocking)."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            raise ImportError("Install paho-mqtt: pip install paho-mqtt")
        client = mqtt.Client(self.client_id)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.connect(self.broker, self.port, 60)
        client.loop_forever()

    async def run_async(self) -> None:
        """Async version of run()."""
        # Note: paho-mqtt is sync; in production, use aiomqtt or paho's loop_start
        self.run()


def run() -> None:
    """CLI entry point: python -m nepal_decarb_pro.io.mqtt_bridge"""
    bridge = MQTTBridge()
    bridge.add_sensor(
        "kiln-temp-01",
        "temperature",
        "PlantA",
        "C",
        "nepal/planta/kiln/temperature",
    )
    bridge.add_sensor(
        "co2-stack-01",
        "co2",
        "PlantA",
        "ppm",
        "nepal/planta/stack/co2",
    )
    bridge.on_message(
        lambda s, v, t: print(f"[{t}] {s.sensor_id} ({s.location}): {v} {s.unit}")
    )
    bridge.run()
