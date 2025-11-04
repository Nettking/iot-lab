"""Generate simulated sensor data when hardware is unavailable."""

from __future__ import annotations

import random
import time

from iot_lab import configure_logging, load_config

from .message_parser import MessageParser
from .mqtt_client import MQTTClient


def run_simulation() -> None:
    config = load_config()
    configure_logging(config)
    mqtt_cfg = config.get("mqtt", {})
    simulation_cfg = config.get("simulation", {})
    gateway_cfg = config.get("gateway", {})

    parser = MessageParser(device_id=gateway_cfg.get("device_id", "simulator"))
    mqtt_client = MQTTClient(
        host=mqtt_cfg.get("host", "localhost"),
        port=int(mqtt_cfg.get("port", 1883)),
    )
    mqtt_client.connect()

    interval = float(simulation_cfg.get("interval", 1.0))
    sensors = simulation_cfg.get("sensors", [])
    publish_topic = mqtt_cfg.get("publish_topic", "lab/device1/data")

    try:
        while True:
            for sensor in sensors:
                name = sensor.get("name", "sim")
                min_val = float(sensor.get("min", 0))
                max_val = float(sensor.get("max", 100))
                value = round(random.uniform(min_val, max_val), 2)
                payload = parser.parse(f"{name}:{value}")
                if payload:
                    mqtt_client.publish(publish_topic, parser.to_json(payload))
            time.sleep(interval)
    except KeyboardInterrupt:
        mqtt_client.stop()


if __name__ == "__main__":
    run_simulation()
