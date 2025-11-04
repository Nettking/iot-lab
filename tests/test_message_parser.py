import json
from unittest import mock

from gateway.message_parser import MessageParser


def test_parse_key_value_line():
    parser = MessageParser(device_id="device")
    with mock.patch("gateway.message_parser.time.time", return_value=1700000000):
        payload = parser.parse("A0:123")
    assert payload == {
        "device": "device",
        "sensor": "A0",
        "value": 123,
        "timestamp": 1700000000,
    }


def test_parse_json_line_preserves_fields():
    parser = MessageParser(device_id="device")
    data = {"sensor": "temp", "value": "24.5"}
    with mock.patch("gateway.message_parser.time.time", return_value=1700000000):
        payload = parser.parse(json.dumps(data))
    assert payload["device"] == "device"
    assert payload["sensor"] == "temp"
    assert payload["value"] == 24.5
    assert payload["timestamp"] == 1700000000


def test_parse_empty_line_returns_none():
    parser = MessageParser(device_id="device")
    assert parser.parse("") is None
