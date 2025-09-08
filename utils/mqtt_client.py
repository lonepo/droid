import threading
import paho.mqtt.client as mqtt
from config import MQTT_BROKER, MQTT_PORT, MQTT_TOPIC_ECG, MQTT_TOPIC_SPO2
from utils.sensor import save_sensor_data_to_csv, push_sensor_to_thingspeak

data_buffer = {"ecg": None, "spo2": None}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC_ECG)
        client.subscribe(MQTT_TOPIC_SPO2)

def on_message(client, userdata, msg):
    global data_buffer
    topic = msg.topic
    value = msg.payload.decode()
    if topic == MQTT_TOPIC_ECG: data_buffer["ecg"] = value
    if topic == MQTT_TOPIC_SPO2: data_buffer["spo2"] = value
    if data_buffer["ecg"] and data_buffer["spo2"]:
        save_sensor_data_to_csv(data_buffer["ecg"], data_buffer["spo2"])
        push_sensor_to_thingspeak(data_buffer["ecg"], data_buffer["spo2"])
        data_buffer["ecg"], data_buffer["spo2"] = None, None

def mqtt_client_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
