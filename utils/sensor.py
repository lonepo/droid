import csv
import requests
from datetime import datetime
from config import SENSOR_CSV_FILE, THINGSPEAK_SENSOR_API_KEY, API_URL

def initialize_sensor_csv():
    with open(SENSOR_CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "ECG Signal", "SpO2"])

def save_sensor_data_to_csv(ecg, spo2):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SENSOR_CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, ecg, spo2])
    print(f"Saved: ECG={ecg}, SpO2={spo2}")

def push_sensor_to_thingspeak(ecg, spo2):
    payload = {"api_key": THINGSPEAK_SENSOR_API_KEY, "field4": ecg, "field5": spo2}
    try:
        response = requests.get(API_URL, params=payload)
        print("Sensor pushed") if response.status_code==200 else print("Failed", response.status_code)
    except Exception as e:
        print(f"Error: {e}")
