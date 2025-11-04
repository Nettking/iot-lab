import json
from unittest import mock

from gateway.main import GatewayController
from gateway.message_parser import MessageParser


def build_controller():
    parser = MessageParser(device_id="arduino1")
    serial_reader = mock.Mock()
    mqtt_client = mock.Mock()
    controller = GatewayController(
        serial_reader=serial_reader,
        mqtt_client=mqtt_client,
        parser=parser,
        publish_topic="lab/device1/data",
    )
    return controller, mqtt_client


def test_handle_line_publishes_json_payload():
    controller, mqtt_client = build_controller()
    with mock.patch("gateway.message_parser.time.time", return_value=1700000000):
        payload = controller.handle_line("temp:26.5")
    mqtt_client.publish.assert_called_once()
    topic, sent_payload = mqtt_client.publish.call_args[0][:2]
    assert topic == "lab/device1/data"
    body = json.loads(sent_payload)
    assert body["device"] == "arduino1"
    assert body["sensor"] == "temp"
    assert body["value"] == 26.5
    assert body["timestamp"] == 1700000000
    assert payload == sent_payload


def test_handle_line_ignores_empty_messages():
    controller, mqtt_client = build_controller()
    result = controller.handle_line("")
    assert result is None
    mqtt_client.publish.assert_not_called()
