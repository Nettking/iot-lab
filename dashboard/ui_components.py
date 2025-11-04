"""Reusable UI elements for the Streamlit dashboard."""

from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st


def render_header() -> None:
    st.set_page_config(page_title="IoT Lab Dashboard", layout="wide")
    st.title("🧭 IoT Lab Dashboard")
    st.caption(
        "Monitor Arduino sensors, publish MQTT commands, and export lab data."
    )


def render_control_panel(capture_enabled: bool) -> Dict[str, bool]:
    col1, col2, col3 = st.columns(3)
    actions = {"toggle": False, "clear": False, "export": False}

    with col1:
        label = "Pause capture" if capture_enabled else "Resume capture"
        actions["toggle"] = st.button(label, use_container_width=True)
    with col2:
        actions["clear"] = st.button("Clear data", use_container_width=True)
    with col3:
        actions["export"] = st.button("Save CSV", use_container_width=True)

    return actions


def render_command_sender(command_topic: str, broker: str, port: int) -> None:
    with st.expander("Send command", expanded=False):
        st.write(
            "Send manual commands to the device via MQTT (e.g. `LED_ON`)."
        )
        command = st.text_input("Command", key="command_input")
        if st.button("Publish", key="command_button") and command:
            import paho.mqtt.client as mqtt

            client = mqtt.Client()
            client.connect(broker, port)
            client.publish(command_topic, command)
            client.disconnect()
            st.success(f"Sent `{command}` to `{command_topic}`")


def render_live_chart(df: pd.DataFrame) -> None:
    st.subheader("Live sensor chart")
    if df.empty:
        st.info("Waiting for sensor data …")
        return
    chart_df = df.copy()
    chart_df["time"] = pd.to_datetime(chart_df["timestamp"], unit="s")
    pivot = chart_df.pivot_table(
        index="time", columns="sensor", values="value", aggfunc="last"
    )
    pivot = pivot.sort_index()
    st.line_chart(pivot)


def render_message_log(messages: List[Dict[str, object]]) -> None:
    st.subheader("Recent messages")
    if not messages:
        st.info("No messages received yet.")
        return
    rows = [
        f"{pd.to_datetime(msg.get('timestamp', 0), unit='s').strftime('%H:%M:%S')} | "
        f"{msg.get('sensor', 'unknown')}: {msg.get('value')}"
        for msg in messages[::-1]
    ]
    st.code("\n".join(rows))


def render_metrics(latest: List[Dict[str, object]]) -> None:
    if not latest:
        return
    cols = st.columns(min(3, len(latest)))
    for col, msg in zip(cols, latest[::-1]):
        with col:
            st.metric(
                label=f"{msg.get('sensor', 'sensor')} ({msg.get('device', 'device')})",
                value=msg.get("value"),
            )
