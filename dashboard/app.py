"""Streamlit application for the IoT lab dashboard."""

from __future__ import annotations

import streamlit as st

from iot_lab import configure_logging, load_config

from .data_handler import MQTTDataHandler
from . import ui_components


def _initialise_handler(config) -> MQTTDataHandler:
    mqtt_cfg = config.get("mqtt", {})
    dashboard_cfg = config.get("dashboard", {})
    handler = MQTTDataHandler(
        host=mqtt_cfg.get("host", "localhost"),
        port=int(mqtt_cfg.get("port", 1883)),
        data_topic=mqtt_cfg.get("publish_topic", "lab/device1/data"),
        history_size=int(dashboard_cfg.get("history_size", 200)),
        csv_output=dashboard_cfg.get("csv_output"),
    )
    handler.start()
    return handler


def main() -> None:
    config = load_config()
    configure_logging(config)
    ui_components.render_header()

    if "data_handler" not in st.session_state:
        st.session_state.data_handler = _initialise_handler(config)
        st.session_state.capture_enabled = True

    handler: MQTTDataHandler = st.session_state.data_handler
    capture_enabled: bool = st.session_state.get("capture_enabled", True)

    actions = ui_components.render_control_panel(capture_enabled)
    if actions["toggle"]:
        capture_enabled = not capture_enabled
        handler.set_capture(capture_enabled)
        st.session_state.capture_enabled = capture_enabled
    if actions["clear"]:
        handler.clear()
        st.success("Cleared buffered data")
    if actions["export"]:
        saved_path = handler.save_to_csv()
        if saved_path:
            st.success(f"Saved data to {saved_path}")
        else:
            st.warning("No data to export yet.")

    mqtt_cfg = config.get("mqtt", {})
    ui_components.render_command_sender(
        command_topic=mqtt_cfg.get("command_topic", "lab/device1/cmd"),
        broker=mqtt_cfg.get("host", "localhost"),
        port=int(mqtt_cfg.get("port", 1883)),
    )

    df = handler.to_dataframe()
    latest = handler.latest_messages(3)
    ui_components.render_metrics(latest)
    ui_components.render_live_chart(df)
    ui_components.render_message_log(handler.latest_messages())


if __name__ == "__main__":
    main()
