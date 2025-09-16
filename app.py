# -----------------------------
# Imports
# -----------------------------
from flask import Flask, render_template, jsonify, Response, request, redirect, url_for, session
from flask_cors import CORS
import threading
import cv2
import csv
import os
from datetime import datetime
import json

from utils.motor import motor
from utils.door import operate_door
from utils.camera import gen_frames
from utils.emotion import recognize_face_emotion, predict_audio_emotion
from utils.sensor import initialize_sensor_csv, SENSOR_CSV_FILE
from utils.mqtt_client import mqtt_client_thread
from utils.media import emotion_media_map  #Use static URLs directly

from config import MOTOR_PINS, DOOR_PINS, WRITE_API_KEY, THINGSPEAK_SENSOR_API_KEY, MQTT_BROKER, MQTT_PORT

import json, threading, time
from pathlib import Path

SCHEDULE_FILE = Path("data/schedule.json")
FEATURES = ["Emotion Recognition", "Sound Detection", "Motor Forward", "Door Open"]

def load_schedule():
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {feature: 0 for feature in FEATURES}

def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

# -----------------------------
# Flask Setup
# -----------------------------
app = Flask(__name__)
CORS(app)
app.secret_key = "droid"   # Use a stronger random secret in production

# File for admin video mapping
MAP_FILE = os.path.join("data", "emotion_video_map.json")


# -----------------------------
# Emotion Video Mapping Helpers
# -----------------------------
def load_mapping():
    """Load admin-defined mapping (emotion video)."""
    if os.path.exists(MAP_FILE):
        try:
            with open(MAP_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[WARNING] Failed to read mapping file: {e}")
            return {}
    return {}

def save_mapping(mapping):
    """Save admin-defined mapping (emotion → video)."""
    os.makedirs(os.path.dirname(MAP_FILE), exist_ok=True)
    try:
        with open(MAP_FILE, "w") as f:
            json.dump(mapping, f, indent=4)
    except Exception as e:
        print(f"[ERROR] Could not save mapping: {e}")

# -----------------------------
# User Authentication
# -----------------------------
USERS = {
    "admin": {"password": "password123", "role": "admin"},
    "user1": {"password": "user123", "role": "user"}
}


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username]["password"] == password:
            session["user"] = username
            session["role"] = USERS[username]["role"]

            #  Role-based redirect
            if session["role"] == "admin":
                return redirect(url_for("settings"))
            else:
                return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=session.get("user"), role=session.get("role"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("role", None)
    return redirect(url_for("login"))


# -----------------------------
# Camera Feed
# -----------------------------
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# -----------------------------
# Motor / Door APIs
# -----------------------------
@app.route('/api/motor_forward', methods=['POST'])
def motor_forward():
    motor.forward()
    return jsonify({"message": "Motor moving forward"})


@app.route('/api/motor_backward', methods=['POST'])
def motor_backward():
    motor.backward()
    return jsonify({"message": "Motor moving backward"})


@app.route('/api/motor_stop', methods=['POST'])
def motor_stop():
    motor.stop()
    return jsonify({"message": "Motor stopped"})


@app.route('/api/open_door', methods=['POST'])
def open_door():
    operate_door("open")
    return jsonify({"message": "Door opened"})


@app.route('/api/close_door', methods=['POST'])
def close_door():
    operate_door("close")
    return jsonify({"message": "Door closed"})


# -----------------------------
# Emotion Recognition API
# -----------------------------
@app.route("/api/recognize_emotion", methods=["POST"])
def recognize_emotion_api():
    face_emotion = recognize_face_emotion()
    audio_emotion = predict_audio_emotion()

    # Choose one emotion (face priority > audio)
    detected = face_emotion if face_emotion != "No face detected" else audio_emotion

    # Get the media mappings
    mapping = load_mapping()
    video_file = mapping.get(detected)
    if not video_file:
        video_file = emotion_media_map.get(detected, {}).get("video")

    return jsonify({
        "emotion": detected,
        "video_url": video_file,
        "song_url": emotion_media_map.get(detected, {}).get("song")
    })


# -----------------------------
# Decibel Detection API
# -----------------------------
@app.route('/api/detect_decibels', methods=['POST'])
def detect_decibels():
    try:
        voice_emotion = predict_audio_emotion()

        # Load mapping file (admin-defined)
        mapping = {}
        if os.path.exists(MAP_FILE):
            try:
                with open(MAP_FILE, "r") as f:
                    content = f.read().strip()
                    if content:
                        mapping = json.loads(content)
            except Exception as e:
                print(f"[WARNING] Could not read mapping file: {e}")

        # Default to static mapping if admin hasn’t overridden
        video_file = mapping.get(voice_emotion)
        if not video_file:
            video_file = emotion_media_map.get(voice_emotion, {}).get("video")

        audio_file = emotion_media_map.get(voice_emotion, {}).get("song")

        print(f"[DEBUG] Detected Voice Emotion: {voice_emotion}, Video: {video_file}, Audio: {audio_file}")

        return jsonify({
            "result": voice_emotion,
            "video_url": video_file,
            "song_url": audio_file,
            "message": "Voice emotion detected"
        })
    except Exception as e:
        return jsonify({"result": "Error", "message": str(e)}), 500


# -----------------------------
# CSV / ThingSpeak APIs
# -----------------------------
@app.route('/api/get_current_time', methods=['POST'])
def get_current_time():
    return jsonify({"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})


@app.route('/api/save_to_csv', methods=['POST'])
def save_to_csv():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid data"}), 400

        file_exists = os.path.isfile(SENSOR_CSV_FILE)
        with open(SENSOR_CSV_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(["Timestamp", "Face_Emotion", "Voice_Emotion"])
            writer.writerow([data["current_time"], data["emotion_face"], data["emotion_voice"]])

        return jsonify({"message": f"Data saved to {SENSOR_CSV_FILE}"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/api/upload_to_thingspeak', methods=['POST'])
def upload_to_thingspeak():
    try:
        import requests
        data = request.get_json()
        if not data:
            return jsonify({"message": "Invalid data"}), 400

        payload = {
            "api_key": WRITE_API_KEY,
            "field1": data.get("emotion_face", ""),
            "field2": data.get("emotion_voice", "")
        }
        response = requests.post("https://api.thingspeak.com/update.json", data=payload)
        if response.status_code == 200:
            return jsonify({"message": "Data uploaded to ThingSpeak"})
        else:
            return jsonify({"message": "ThingSpeak upload failed"}), 500
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# -----------------------------
# Medical Data API
# -----------------------------
@app.route('/api/get_medical_data', methods=['GET'])
def get_medical_data():
    try:
        if not os.path.exists(SENSOR_CSV_FILE):
            return jsonify([])
        data_list = []
        with open(SENSOR_CSV_FILE, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data_list.append({
                    "Timestamp": row.get("Timestamp", ""),
                    "ECG": row.get("Face_Emotion", ""),   # Placeholder
                    "SpO2": row.get("Voice_Emotion", "")  # Placeholder
                })
        return jsonify(data_list)
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# -----------------------------
# Settings Page (Admin Only)
# -----------------------------
@app.route("/settings", methods=["GET", "POST"])
def settings():
    mapping = load_mapping()   # existing function for emotion video
    emotions = ["Happy", "Sad", "Angry", "Neutral"]  # adjust if needed
    video_files = os.listdir("static/videos")

    schedule = load_schedule()

    if request.method == "POST" and "delay_Emotion Recognition" not in request.form:
        # existing mapping save logic
        new_mapping = {}
        for emotion in emotions:
            selected = request.form.get(emotion, "")
            if selected:
                new_mapping[emotion] = selected
        save_mapping(new_mapping)
        return render_template("settings.html", emotions=emotions,
                               video_files=video_files, mapping=new_mapping,
                               features=FEATURES, schedule=schedule,
                               success="Mapping saved!")

    return render_template("settings.html", emotions=emotions,
                           video_files=video_files, mapping=mapping,
                           features=FEATURES, schedule=schedule)

# -----------------------------
# Schedule Helpers
# -----------------------------
def load_schedule():
    if SCHEDULE_FILE.exists():
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return {feature: 0 for feature in FEATURES}

def save_schedule_to_file(schedule):   # >>> CHANGE (rename helper)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=4)

@app.route("/save_schedule", methods=["POST"])
def save_schedule_route():   # >>> CHANGE (keep route separate)
    schedule = {}
    for feature in FEATURES:
        delay = int(request.form.get(f"delay_{feature}", 0))
        schedule[feature] = delay
    save_schedule_to_file(schedule)   # >>> CHANGE (call renamed helper)
    return render_template(
        "settings.html",
        emotions=["Happy", "Sad", "Angry", "Neutral"],
        video_files=os.listdir("static/videos"),
        mapping=load_mapping(),
        features=FEATURES,
        schedule=schedule,
        schedule_success="Schedule saved successfully!"
    )
# -----------------------------
# Feature → Action Map
# -----------------------------
# app.py

FEATURE_ACTIONS = {
    "Emotion Recognition": recognize_face_emotion,
    "Sound Detection": predict_audio_emotion,
    "Motor Forward": lambda: motor.forward(duration=5, speed=80),  # run 5s then stop
    "Door Open": lambda: operate_door("open")
}



def run_scheduled_tasks():
    schedule = load_schedule()

    def worker():
        for feature, delay in schedule.items():
            if delay > 0 and feature in FEATURE_ACTIONS:   # >>> CHANGE
                time.sleep(delay)
            print(f"[SCHEDULE] Triggering: {feature}")
            FEATURE_ACTIONS[feature]()   # >>> CHANGE



    threading.Thread(target=worker, daemon=True).start()

@app.route("/api/start_schedule", methods=["POST"])
def api_start_schedule():
    run_scheduled_tasks()
    return jsonify({"message": "Schedule started successfully!"})


# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    initialize_sensor_csv()
    threading.Thread(target=mqtt_client_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=5006, debug=True, threaded=True, use_reloader=False)
