import json
import os
from tensorflow.keras.models import load_model

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_emotion_rec_v2.h5")
LABELS_PATH = os.path.join(BASE_DIR, "models", "label.names")
VIDEO_MAP_PATH = os.path.join(BASE_DIR, "data", "emotion_video_map.json")

# Load face emotion recognition model
FACE_MODEL = load_model(MODEL_PATH)

# Load label names
with open(LABELS_PATH, "r") as f:
    LABEL_NAMES = [line.strip() for line in f]

# Load emotion-to-video mapping
if os.path.exists(VIDEO_MAP_PATH):
    with open(VIDEO_MAP_PATH, "r") as f:
        VIDEO_MAP = json.load(f)
else:
    VIDEO_MAP = {}  # fallback if file missing

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
