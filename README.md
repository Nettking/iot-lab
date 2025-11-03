# 🧭 IoT Lab Platform

A complete, modular IoT test environment for **Arduino-based experiments**.

## ⚙️ Components
- **Arduino**: any sensor/actuator sending text via Serial.
- **Python Gateway**: translates Serial ↔ MQTT.
- **MQTT Broker (Docker)**: Eclipse Mosquitto.
- **Streamlit Dashboard**: live web interface.

## 🚀 Usage
1. Start broker and dashboard:
   ```bash
   docker compose up -d
   ```
2. Run the Python gateway on the machine connected to Arduino:
   ```bash
   cd gateway
   pip install paho-mqtt pyserial
   python serial_mqtt_bridge.py
   ```
3. Upload your Arduino sketch:
   ```cpp
   void setup() { Serial.begin(115200); }
   void loop() {
     int sensorValue = analogRead(A0);
     Serial.print("SENSOR:");
     Serial.println(sensorValue);
     delay(2000);
   }
   ```
4. Open [http://localhost:8501](http://localhost:8501) to view data and send commands.
