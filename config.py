from tensorflow.keras.models import load_model

# -----------------------------
# Face Emotion Recognition Model
# -----------------------------
FACE_MODEL = load_model("models/face_emotion_rec_v2.h5")

with open("models/label.names", "r") as f:
    LABEL_NAMES = [line.strip() for line in f]

# -----------------------------
# GPIO Pins
# -----------------------------
MOTOR_PINS = {"IN1": 4, "IN2": 17, "IN3": 27, "IN4": 22}
DOOR_PINS = {"IN5": 19, "IN6": 26}

# -----------------------------
# ThingSpeak / MQTT
# -----------------------------
WRITE_API_KEY = "REDACTED_THINGSPEAK_WRITE_KEY"
THINGSPEAK_SENSOR_API_KEY = "REDACTED_THINGSPEAK_SENSOR_KEY"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

# -----------------------------
# Sensor / CSV / ThingSpeak
# -----------------------------
SENSOR_CSV_FILE = "data/sensor_data.csv"
API_URL = "https://api.thingspeak.com/update"

# -----------------------------
# MQTT Topics
# -----------------------------
MQTT_TOPIC_ECG = "health/ecg"
MQTT_TOPIC_SPO2 = "health/spo2"
