"""Utilities for parsing serial messages into structured payloads."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional


def _coerce_value(value: str) -> Any:
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


class MessageParser:
    """Parse serial strings into JSON-serialisable dictionaries."""

    def __init__(self, device_id: str, default_sensor: str = "sensor", logger=None) -> None:
        self.device_id = device_id
        self.default_sensor = default_sensor
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def parse(self, raw: str) -> Optional[Dict[str, Any]]:
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            return None

        timestamp = int(time.time())
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError("JSON payload must be an object")
            payload.setdefault("device", self.device_id)
            payload.setdefault("timestamp", timestamp)
            if "value" in payload and isinstance(payload["value"], str):
                payload["value"] = _coerce_value(payload["value"])
            return payload
        except (json.JSONDecodeError, ValueError):
            pass

        sensor: str
        value: Any
        if ":" in raw:
            sensor, value_str = [item.strip() for item in raw.split(":", 1)]
            sensor = sensor or self.default_sensor
            value = _coerce_value(value_str)
        elif "=" in raw:
            sensor, value_str = [item.strip() for item in raw.split("=", 1)]
            sensor = sensor or self.default_sensor
            value = _coerce_value(value_str)
        else:
            sensor = self.default_sensor
            value = _coerce_value(raw)

        payload = {
            "device": self.device_id,
            "sensor": sensor,
            "value": value,
            "timestamp": timestamp,
        }
        self.logger.debug("Parsed payload: %s", payload)
        return payload

    @staticmethod
    def to_json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload)
