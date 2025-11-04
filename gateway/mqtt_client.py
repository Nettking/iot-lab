"""MQTT client helper with reconnection support."""

from __future__ import annotations

import json
import logging
import time
from typing import Callable, Optional

import paho.mqtt.client as mqtt


class MQTTClient:
    """Wrapper around :mod:`paho.mqtt` with sensible defaults."""

    def __init__(
        self,
        host: str,
        port: int,
        command_topic: Optional[str] = None,
        on_command: Optional[Callable[[str], None]] = None,
        reconnect_interval: float = 5.0,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.command_topic = command_topic
        self.on_command = on_command
        self.reconnect_interval = reconnect_interval
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        if on_command and command_topic:
            self.client.on_message = self._on_message
        self._connected = False

    def _on_connect(self, client: mqtt.Client, _userdata, _flags, rc):  # type: ignore[override]
        if rc == 0:
            self.logger.info("Connected to MQTT broker at %s:%s", self.host, self.port)
            self._connected = True
            if self.on_command and self.command_topic:
                client.subscribe(self.command_topic)
                self.logger.info("Subscribed to command topic %s", self.command_topic)
        else:
            self.logger.error("MQTT connection failed with code %s", rc)

    def _on_disconnect(self, _client: mqtt.Client, _userdata, rc):  # type: ignore[override]
        self.logger.warning("MQTT disconnected (code %s)", rc)
        self._connected = False

    def _on_message(self, _client: mqtt.Client, _userdata, msg):  # type: ignore[override]
        payload = msg.payload.decode("utf-8", errors="ignore")
        self.logger.info("Received command on %s: %s", msg.topic, payload)
        if self.on_command:
            self.on_command(payload)

    def connect(self) -> None:
        while not self._connected:
            try:
                self.logger.info("Connecting to MQTT broker at %s:%s", self.host, self.port)
                self.client.connect(self.host, self.port, keepalive=60)
                self.client.loop_start()
                # loop_start triggers connection asynchronously; wait until connected
                for _ in range(20):
                    if self._connected:
                        break
                    time.sleep(0.1)
                if not self._connected:
                    raise ConnectionError("MQTT connection timeout")
            except Exception as exc:  # noqa: BLE001 - broad to keep retrying
                self.logger.warning(
                    "MQTT connection error: %s. Retrying in %ss",
                    exc,
                    self.reconnect_interval,
                )
                time.sleep(self.reconnect_interval)

    def publish(self, topic: str, payload: str | bytes, qos: int = 0, retain: bool = False) -> None:
        if not self._connected:
            self.connect()

        try:
            info = self.client.publish(topic, payload, qos=qos, retain=retain)
            info.wait_for_publish()
            self.logger.info("Published to %s: %s", topic, payload)
        except Exception as exc:  # noqa: BLE001 - maintain gateway uptime
            self.logger.error("Failed to publish MQTT message: %s", exc)
            self._connected = False
            time.sleep(self.reconnect_interval)

    def stop(self) -> None:
        if self._connected:
            self.logger.info("Stopping MQTT client")
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False

    @staticmethod
    def to_payload(data: dict) -> str:
        return json.dumps(data)
