"""Configuration helpers for the IoT lab platform."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Tuple

try:  # pragma: no cover - optional dependency
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - fallback
    yaml = None

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "config.yaml"

_ENV_MAP = {
    ("serial", "port"): "IOT_LAB_SERIAL_PORT",
    ("serial", "baudrate"): "IOT_LAB_SERIAL_BAUD",
    ("mqtt", "host"): "IOT_LAB_MQTT_HOST",
    ("mqtt", "port"): "IOT_LAB_MQTT_PORT",
    ("mqtt", "publish_topic"): "IOT_LAB_MQTT_PUB",
    ("mqtt", "command_topic"): "IOT_LAB_MQTT_CMD",
    ("logging", "level"): "IOT_LAB_LOG_LEVEL",
    ("gateway", "device_id"): "IOT_LAB_DEVICE_ID",
}


def _convert_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none"}:
        return None
    try:
        if value.startswith("0") and value != "0" and not "." in value:
            # avoid octal interpretation
            return value
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def _split_key_value(text: str) -> Tuple[str, str | None]:
    if ":" not in text:
        raise ValueError(f"Invalid line: {text}")
    key, raw = text.split(":", 1)
    key = key.strip()
    raw = raw.strip()
    return key, raw if raw else None


def _parse_lines(lines: list[str], index: int, indent: int) -> Tuple[Any, int]:
    mapping: Dict[str, Any] = {}
    sequence: list[Any] = []
    is_sequence = False

    while index < len(lines):
        raw_line = lines[index]
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        current_indent = len(raw_line) - len(raw_line.lstrip(" "))
        if current_indent < indent:
            break

        if stripped.startswith("- "):
            is_sequence = True
            content = stripped[2:].strip()
            index += 1
            item, index = _parse_list_item(lines, index, current_indent + 2, content)
            sequence.append(item)
            continue

        key, value = _split_key_value(stripped)
        index += 1
        if value is None:
            child, index = _parse_lines(lines, index, current_indent + 2)
            mapping[key] = child
        else:
            mapping[key] = _convert_scalar(value)

    return (sequence if is_sequence else mapping), index


def _parse_list_item(
    lines: list[str], index: int, indent: int, content: str
) -> Tuple[Any, int]:
    if not content:
        child, index = _parse_lines(lines, index, indent)
        return child, index

    if ":" in content:
        key, value = _split_key_value(content)
        item: Dict[str, Any] = {}
        if value is None:
            child, index = _parse_lines(lines, index, indent)
            item[key] = child
        else:
            item[key] = _convert_scalar(value)

        while index < len(lines):
            peek = lines[index]
            stripped = peek.strip()
            if not stripped or stripped.startswith("#"):
                index += 1
                continue
            current_indent = len(peek) - len(peek.lstrip(" "))
            if current_indent < indent:
                break
            if stripped.startswith("- "):
                break
            key2, value2 = _split_key_value(stripped)
            index += 1
            if value2 is None:
                child, index = _parse_lines(lines, index, current_indent + 2)
                item[key2] = child
            else:
                item[key2] = _convert_scalar(value2)
        return item, index

    return _convert_scalar(content), index


def _fallback_load(text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    parsed, _ = _parse_lines(lines, 0, 0)
    if not isinstance(parsed, dict):
        raise ValueError("Configuration root must be a mapping")
    return parsed


def _read_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:  # pragma: no cover - real dependency
        return yaml.safe_load(text) or {}
    return _fallback_load(text)


@lru_cache(maxsize=1)
def load_config(path: str | os.PathLike[str] | None = None) -> Dict[str, Any]:
    """Load the YAML configuration, applying any environment overrides."""

    config_path = Path(path or os.getenv("IOT_LAB_CONFIG", DEFAULT_CONFIG_PATH))
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = _read_yaml(config_path)
    for (section, key), env_var in _ENV_MAP.items():
        value = os.getenv(env_var)
        if value is None:
            continue
        if section not in config:
            config[section] = {}
        if key == "port" and section == "mqtt":
            try:
                config[section][key] = int(value)
            except ValueError as exc:
                raise ValueError(
                    f"Environment variable {env_var} must be an integer"
                ) from exc
        elif key == "baudrate" and section == "serial":
            try:
                config[section][key] = int(value)
            except ValueError as exc:
                raise ValueError(
                    f"Environment variable {env_var} must be an integer"
                ) from exc
        else:
            config[section][key] = value
    return config


def configure_logging(config: Dict[str, Any]) -> int:
    """Configure root logging from the provided config."""

    level_name = (
        config.get("logging", {}).get("level", "INFO").upper()
    )
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("paho").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    return level


__all__ = ["load_config", "configure_logging"]
