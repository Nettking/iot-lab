"""Entry-point for the serial to MQTT gateway."""

from __future__ import annotations

import logging
import signal
import time
from typing import Optional, TYPE_CHECKING

from iot_lab import configure_logging, load_config

from .message_parser import MessageParser
from .serial_reader import SerialReader

if TYPE_CHECKING:  # pragma: no cover - type hints only
    from .mqtt_client import MQTTClient

LOGGER = logging.getLogger("gateway")


class GatewayController:
    """Coordinate serial reading, message parsing and MQTT publishing."""

    def __init__(
        self,
        serial_reader: SerialReader,
        mqtt_client: "MQTTClient",
        parser: MessageParser,
        publish_topic: str,
        read_interval: float = 0.1,
    ) -> None:
        self.serial_reader = serial_reader
        self.mqtt_client = mqtt_client
        self.parser = parser
        self.publish_topic = publish_topic
        self.read_interval = read_interval
        self._running = False

    def start(self) -> None:
        LOGGER.info("Starting gateway controller")
        self._running = True
        self.mqtt_client.connect()
        while self._running:
            raw = self.serial_reader.read_line()
            if raw:
                self.handle_line(raw)
            time.sleep(self.read_interval)

    def handle_line(self, raw: str) -> Optional[str]:
        payload_dict = self.parser.parse(raw)
        if not payload_dict:
            LOGGER.debug("Ignoring empty serial payload")
            return None
        payload = self.parser.to_json(payload_dict)
        self.mqtt_client.publish(self.publish_topic, payload)
        return payload

    def stop(self) -> None:
        LOGGER.info("Stopping gateway controller")
        self._running = False
        self.serial_reader.close()
        self.mqtt_client.stop()


def create_controller_from_config(config) -> GatewayController:
    from .mqtt_client import MQTTClient  # Local import to avoid hard dependency in tests

    serial_cfg = config.get("serial", {})
    mqtt_cfg = config.get("mqtt", {})
    gateway_cfg = config.get("gateway", {})

    serial_reader = SerialReader(
        port=serial_cfg.get("port", "/dev/ttyUSB0"),
        baudrate=int(serial_cfg.get("baudrate", 115200)),
        reconnect_interval=float(serial_cfg.get("reconnect_interval", 5)),
    )
    parser = MessageParser(device_id=gateway_cfg.get("device_id", "device"))
    mqtt_client = MQTTClient(
        host=mqtt_cfg.get("host", "localhost"),
        port=int(mqtt_cfg.get("port", 1883)),
        command_topic=mqtt_cfg.get("command_topic"),
    )
    publish_topic = mqtt_cfg.get("publish_topic", "lab/device1/data")
    read_interval = float(gateway_cfg.get("read_interval", 0.1))
    return GatewayController(serial_reader, mqtt_client, parser, publish_topic, read_interval)


def run_gateway() -> None:
    config = load_config()
    configure_logging(config)
    controller = create_controller_from_config(config)

    def _handle_exit(*_args):
        controller.stop()

    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)

    try:
        controller.start()
    finally:
        controller.stop()


if __name__ == "__main__":
    run_gateway()
