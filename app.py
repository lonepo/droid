# -----------------------------
# Routes for HTML pages
# -----------------------------
from flask import Flask, render_template, jsonify, Response, request, redirect, url_for, session
from flask_cors import CORS
import threading
import cv2
import csv
import os
from datetime import datetime
from utils.motor import motor
from utils.door import operate_door
from utils.camera import gen_frames, cap
from utils.emotion import recognize_face_emotion, predict_audio_emotion
from utils.sensor import initialize_sensor_csv, SENSOR_CSV_FILE
from utils.mqtt_client import mqtt_client_thread
from config import MOTOR_PINS, DOOR_PINS, WRITE_API_KEY, THINGSPEAK_SENSOR_API_KEY, MQTT_BROKER, MQTT_PORT

app = Flask(__name__)
CORS(app)

# Secret key for sessions
app.secret_key = "droid"   # 🔑 put a strong random key here

# -----------------------------
# Login System
# -----------------------------
USERS = {"admin": "password123"}  # ✅ You can later replace with DB or CSV

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")   # renamed your old index.html

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# -----------------------------
# Motor / Door API
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
# Emotion / Decibel API
# -----------------------------
@app.route('/api/recognize_emotion', methods=['POST'])
def recognize_emotion():
    try:
        face_emotion = recognize_face_emotion()
        return jsonify({"result": face_emotion, "message": "Face emotion detected"})
    except Exception as e:
        return jsonify({"result": "Error", "message": str(e)}), 500

@app.route('/api/detect_decibels', methods=['POST'])
def detect_decibels():
    try:
        voice_emotion = predict_audio_emotion()
        return jsonify({"result": voice_emotion, "message": "Voice emotion detected"})
    except Exception as e:
        return jsonify({"result": "Error", "message": str(e)}), 500

# -----------------------------
# CSV / ThingSpeak API
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
                    "ECG": row.get("Face_Emotion", ""),  # Replace with ECG if available
                    "SpO2": row.get("Voice_Emotion", "")  # Replace with SpO2 if available
                })
        return jsonify(data_list)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

# -----------------------------
# Main
# -----------------------------
if __name__ == "__main__":
    initialize_sensor_csv()
    threading.Thread(target=mqtt_client_thread, daemon=True).start()
    app.run(host="0.0.0.0", port=5005, debug=True, threaded=True, use_reloader=False)
