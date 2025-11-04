"""MQTT-backed data buffering for the Streamlit dashboard."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections import deque
from pathlib import Path
from typing import Deque, Dict, List, Optional

import pandas as pd
import paho.mqtt.client as mqtt

LOGGER = logging.getLogger(__name__)


class MQTTDataHandler:
    """Subscribe to an MQTT topic and maintain a rolling buffer of messages."""

    def __init__(
        self,
        host: str,
        port: int,
        data_topic: str,
        history_size: int = 200,
        csv_output: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.data_topic = data_topic
        self.history_size = history_size
        self.csv_output = csv_output
        self.buffer: Deque[Dict[str, object]] = deque(maxlen=history_size)
        self.capture_enabled = True
        self._client = mqtt.Client()
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._thread: Optional[threading.Thread] = None
        self._connected = threading.Event()

    def _on_connect(self, client: mqtt.Client, _userdata, _flags, rc):  # type: ignore[override]
        if rc == 0:
            LOGGER.info("Dashboard connected to MQTT at %s:%s", self.host, self.port)
            client.subscribe(self.data_topic)
            self._connected.set()
        else:
            LOGGER.error("Dashboard MQTT connection failed with code %s", rc)

    def _on_message(self, _client: mqtt.Client, _userdata, msg):  # type: ignore[override]
        if not self.capture_enabled:
            return
        payload = msg.payload.decode("utf-8", errors="ignore")
        try:
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise ValueError("Payload must be a JSON object")
        except (json.JSONDecodeError, ValueError):
            data = {"sensor": "raw", "value": payload}
        data.setdefault("timestamp", time.time())
        data.setdefault("topic", msg.topic)
        self.buffer.append(data)

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        LOGGER.info("Starting MQTT data handler for topic %s", self.data_topic)
        self._client.connect(self.host, self.port, keepalive=60)
        self._thread = threading.Thread(target=self._client.loop_forever, daemon=True)
        self._thread.start()
        self._connected.wait(timeout=5)

    def stop(self) -> None:
        if not self._thread:
            return
        LOGGER.info("Stopping MQTT data handler")
        self._client.loop_stop()
        self._client.disconnect()
        self._thread.join(timeout=1)
        self._thread = None
        self._connected.clear()

    def set_capture(self, enabled: bool) -> None:
        LOGGER.info("Data capture %s", "enabled" if enabled else "paused")
        self.capture_enabled = enabled

    def clear(self) -> None:
        self.buffer.clear()

    def to_dataframe(self) -> pd.DataFrame:
        if not self.buffer:
            return pd.DataFrame(columns=["timestamp", "sensor", "value", "topic", "device"])
        return pd.DataFrame(list(self.buffer))

    def save_to_csv(self) -> Optional[Path]:
        if not self.csv_output:
            return None
        df = self.to_dataframe()
        if df.empty:
            return None
        output_path = Path(self.csv_output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        LOGGER.info("Saved data to %s", output_path)
        return output_path

    def latest_messages(self, limit: int = 20) -> List[Dict[str, object]]:
        return list(self.buffer)[-limit:]
