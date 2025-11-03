import streamlit as st
import paho.mqtt.client as mqtt
import threading
from queue import Queue
import time
import os
import plotly.express as px
import pandas as pd

BROKER = os.getenv("MQTT_BROKER", "localhost")
TOPIC_DATA = "iot/device1/data"
TOPIC_CMD = "iot/device1/cmd"

msg_queue = Queue()
data_log = []

def on_message(client, userdata, msg):
    msg_queue.put((msg.topic, msg.payload.decode()))

def mqtt_thread():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(BROKER, 1883, 60)
    client.subscribe(TOPIC_DATA)
    client.loop_forever()

t = threading.Thread(target=mqtt_thread, daemon=True)
t.start()

st.set_page_config(page_title="IoT Test Interface", layout="wide")
st.title("🧭 IoT Test Dashboard")

col1, col2 = st.columns([2, 1])

with col2:
    st.subheader("Send Command")
    cmd = st.text_input("Enter command (e.g. LED_ON):")
    if st.button("Send"):
        client = mqtt.Client()
        client.connect(BROKER, 1883)
        client.publish(TOPIC_CMD, cmd)
        client.disconnect()
        st.success(f"Sent: {cmd}")

with col1:
    st.subheader("Live Data")
    log_placeholder = st.empty()
    graph_placeholder = st.empty()

while True:
    while not msg_queue.empty():
        topic, payload = msg_queue.get()
        timestamp = time.strftime("%H:%M:%S")
        data_log.append({"time": timestamp, "payload": payload})
        if len(data_log) > 100:
            data_log.pop(0)
        log_text = "\n".join([f"{d['time']} → {d['payload']}" for d in reversed(data_log[-20:])])
        log_placeholder.text(log_text)

        try:
            val = float(payload)
            df = pd.DataFrame(data_log[-50:])
            df["value"] = pd.to_numeric(df["payload"], errors="coerce")
            fig = px.line(df, x="time", y="value", title="Live Sensor Data")
            graph_placeholder.plotly_chart(fig, use_container_width=True)
        except ValueError:
            pass

    time.sleep(0.3)
