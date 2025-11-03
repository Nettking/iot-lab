import serial
import paho.mqtt.client as mqtt
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200
MQTT_BROKER = "localhost"
TOPIC_PUB = "iot/device1/data"
TOPIC_SUB = "iot/device1/cmd"

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker.")
    client.subscribe(TOPIC_SUB)

def on_message(client, userdata, msg):
    print(f"[MQTT → Arduino] {msg.payload.decode()}")
    ser.write((msg.payload.decode() + "\n").encode())

client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, 1883, 60)
client.loop_start()

try:
    while True:
        line = ser.readline().decode().strip()
        if line:
            print(f"[Arduino → MQTT] {line}")
            client.publish(TOPIC_PUB, line)
        time.sleep(0.1)
except KeyboardInterrupt:
    client.loop_stop()
    ser.close()
    print("Bridge stopped.")
