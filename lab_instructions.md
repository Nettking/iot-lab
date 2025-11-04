# IoT Lab Exercise Guide

## Overview
This lab walks students through connecting an Arduino sensor board to the IoT Lab stack, observing telemetry, and extending the system with custom visualisations. The activities are designed for a 2–3 hour practical session.

## Step 1 – Prepare the hardware
1. Connect the Arduino board to your computer via USB
2. Wire the primary sensor to pin `A0` (analog input) and provide power/ground
3. Upload the starter sketch:
   ```cpp
   const int sensorPin = A0;
   void setup() { Serial.begin(115200); }
   void loop() {
     Serial.print("A0:");
     Serial.println(analogRead(sensorPin));
     delay(1000);
   }
   ```
4. Verify serial output using the Arduino Serial Monitor

## Step 2 – Run the software stack
1. Update `config/config.yaml` with the correct serial port (e.g. `/dev/ttyACM0` or `COM5`)
2. Start the Docker environment:
   ```bash
   docker compose up
   ```
3. Open the Streamlit dashboard at [http://localhost:8501](http://localhost:8501)
4. Observe live sensor readings and the rolling log panel

## Step 3 – Extend the Arduino payload
1. Add a second sensor or derived metric, e.g.:
   ```cpp
   Serial.print("temperature:");
   Serial.println(readTemperatureC());
   Serial.print("humidity:");
   Serial.println(readHumidityPercent());
   ```
2. Confirm that new MQTT messages include the extra sensors
3. Watch how the dashboard automatically plots additional series

## Step 4 – Customise the dashboard
1. Modify `dashboard/ui_components.py` to add a new widget (e.g., threshold slider)
2. Use Streamlit state to trigger MQTT commands (LED toggles, calibration requests)
3. Export the captured data to CSV and inspect it in Python or Excel

## Challenge tasks
- **Multi-device support**: Configure two gateways with different `gateway.device_id` values and display both in the chart
- **Fault detection**: Implement a simple moving average and flag abnormal sensor deviations in the dashboard
- **Data persistence**: Replace the CSV export with a SQLite database and add a “Replay session” button that plots historical runs

## Deliverables
- Screenshot of the dashboard with your customised widget
- Short reflection on how MQTT topics can organise multiple devices
- Optional: GitHub fork or patch showcasing your dashboard enhancements
