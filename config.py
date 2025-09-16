import os
import json
from tensorflow.keras.models import load_model

# -----------------------------
# Motor / Door pins
# -----------------------------
MOTOR_PINS = {
    "driver1": {
        "C1A": 17,   # IN1
        "C1B": 27,   # IN2
        "EN1": 18,   # PWM (Motor 1 enable)

        "C2A": 22,   # IN3
        "C2B": 23,   # IN4
        "EN2": 13    # PWM (Motor 2 enable)
    }
}

DOOR_PINS = {"IN5": 19, "IN6": 26}

# -----------------------------
# ThingSpeak / MQTT
# -----------------------------
WRITE_API_KEY = "REDACTED_THINGSPEAK_WRITE_KEY"
THINGSPEAK_SENSOR_API_KEY = "REDACTED_THINGSPEAK_SENSOR_KEY"
MQTT_BROKER = "localhost"
MQTT_PORT = 1883

SENSOR_CSV_FILE = "data/sensor_data.csv"
API_URL = "https://api.thingspeak.com/update"

MQTT_TOPIC_ECG = "health/ecg"
MQTT_TOPIC_SPO2 = "health/spo2"

# -----------------------------
# Emotion Model & Video Map
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "face_emotion_rec_v2.h5")
LABELS_PATH = os.path.join(BASE_DIR, "models", "label.names")
VIDEO_MAP_PATH = os.path.join(BASE_DIR, "data", "emotion_video_map.json")

# Load model once, share globally
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "face_emotion_rec_v2.h5")

FACE_MODEL = load_model(MODEL_PATH)


# Load label names
with open(LABELS_PATH, "r") as f:
    LABEL_NAMES = [line.strip() for line in f]

# Load emotion-to-video mapping
if os.path.exists(VIDEO_MAP_PATH):
    with open(VIDEO_MAP_PATH, "r") as f:
        VIDEO_MAP = json.load(f)
else:
    VIDEO_MAP = {
        "Angry": "static/videos/notshout.mp4",
        "Happy": "static/videos/staycalm.mp4",
        "Neutral": "static/videos/sitdown.mp4",
        "Sad": "static/videos/staycalm.mp4",
        "Surprise": "static/videos/video1.mp4",
    }
