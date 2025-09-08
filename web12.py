from flask import Flask, request, jsonify, render_template
from flask import Response
from flask_cors import CORS
import os
import cv2
import pandas as pd
import numpy as np
import time
import sounddevice as sd
from datetime import datetime
import pygame
from ffpyplayer.player import MediaPlayer
from tensorflow.keras.models import load_model
import csv
import requests
import pyaudio
import wave
import librosa
import ast
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import joblib
from sklearn.preprocessing import StandardScaler
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import threading

# ThingSpeak API configurations
API_URL = "https://api.thingspeak.com/update"
WRITE_API_KEY = "REDACTED_THINGSPEAK_WRITE_KEY"  # Emotion data channel
THINGSPEAK_SENSOR_API_KEY = "REDACTED_THINGSPEAK_SENSOR_KEY"  # Sensor data channel

# MQTT configurations
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_ECG = "health/ecg"
MQTT_TOPIC_SPO2 = "health/spo2"
SENSOR_CSV_FILE = "sensor_data.csv"

# GPIO Setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Motor GPIO Pins
IN1, IN2, IN3, IN4 = 4, 17, 27, 22
GPIO.setup([IN1, IN2, IN3, IN4], GPIO.OUT)
GPIO.output([IN1, IN2, IN3, IN4], False)

# Door GPIO Pins
IN5, IN6 = 19, 26
GPIO.setup([IN5, IN6], GPIO.OUT)
GPIO.output([IN5, IN6], False)

# Motor Control Class
class MotorController:
    def __init__(self):
        self.stop()

    def forward(self):
        self._set_motor_pins(False, True, False, True)

    def backward(self):
        self._set_motor_pins(True, False, True, False)

    def stop(self):
        self._set_motor_pins(False, False, False, False)

    def _set_motor_pins(self, in1, in2, in3, in4):
        GPIO.output([IN1, IN2, IN3, IN4], [in1, in2, in3, in4])
        print(f"Motor Pins - IN1: {in1}, IN2: {in2}, IN3: {in3}, IN4: {in4}")

motor = MotorController()

# Door Control
def operate_door(open_door=True):
    print('Operating Door...')
    if open_door:
        GPIO.output(IN5, True)
        GPIO.output(IN6, False)
        time.sleep(3)
        GPIO.output(IN5, False)
        time.sleep(6)
        GPIO.output(IN5, False)
        GPIO.output(IN6, True)
        time.sleep(3)
    else:
        GPIO.output(IN5, False)
        GPIO.output(IN6, False)
cap = cv2.VideoCapture(0)
face_detect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
emotion_model = load_model("face_emotion_rec_v2.h5")
with open('label.names', 'r') as f:
    classNames = f.read().rstrip('\n').split('\n')

# Generate MJPEG frames for live streaming
# Generate MJPEG frames for live streaming
def gen_frames():
    while True:
        success, frame = cap.read()
        if not success:
            continue
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# Play MP4 Videos
def play_video(video_path):
    if not os.path.exists(video_path):
        print(f"Error: {video_path} not found!")
        return

    video = cv2.VideoCapture(video_path)
    player = MediaPlayer(video_path)

    print(f"Playing video: {video_path}")
    while True:
        grabbed, frame = video.read()
        audio_frame, val = player.get_frame()

        if not grabbed:
            print("End of video.")
            break
        if cv2.waitKey(28) & 0xFF == ord("q"):
            break

        cv2.imshow("Video", frame)
        if val != 'eof' and audio_frame is not None:
            _, _ = audio_frame

    video.release()
    cv2.destroyAllWindows()

# Play MP3 Files
def play_mp3(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return

    print(f"Playing MP3: {file_path}")
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)  # Wait until playback is complete
    pygame.mixer.quit()

# Emotion Recognition (Face)
def recognize_emotion():
    model = load_model("face_emotion_rec_v2.h5")
    face_detect = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    with open('label.names', 'r') as f:
        classNames = f.read().rstrip('\n').split('\n')

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise IOError("Can't open webcam")

    detected_emotions = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detect.detectMultiScale(gray_img, 1.1, 4)

        for x, y, w, h in faces:
            roi_color = frame[y:y + h, x:x + w]
            final_img = cv2.resize(roi_color, (224, 224))
            final_img = np.expand_dims(final_img, axis=0) / 255.0

            prediction = model.predict(final_img)
            pred = np.argmax(prediction[0])
            detected_emotions.append(classNames[pred])

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(frame, classNames[pred], (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow("Emotion Recognition", frame)

        if cv2.waitKey(100) & 0xFF == ord("q"):
            break
        if len(detected_emotions) > 5:  # Stop after 5 detected emotions
            break

    cap.release()
    cv2.destroyAllWindows()

    most_common_emotion = max(set(detected_emotions), key=detected_emotions.count)
    return most_common_emotion
    

# ML code for Emotion Prediction from Audio
def record_audio(filename="mic_input.wav", duration=5, sample_rate=44100):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1
    record_time = duration

    p = pyaudio.PyAudio()
    print("Recording...")

    stream = p.open(format=format,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=chunk)

    frames = []
    for _ in range(0, int(sample_rate / chunk * record_time)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))

def extract_features(audio_file):
    y, sr = librosa.load(audio_file, sr=None)
    features = {}

    features["duration"] = librosa.get_duration(y=y, sr=sr)

    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
    features["pitch"] = np.mean(pitches[pitches > 0]) if np.any(pitches > 0) else 0

    zcr = librosa.feature.zero_crossing_rate(y)
    features["speech_rate"] = np.sum(zcr) / features["duration"]

    mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features["mfccs"] = np.mean(mfccs, axis=1)

    features.update(calculate_jitter_shimmer(y, sr))

    return features

def calculate_jitter_shimmer(y, sr):
    result = {}

    frame_size = int(0.01 * sr)
    hop_size = int(0.005 * sr)
    frames = librosa.util.frame(y, frame_length=frame_size, hop_length=hop_size)

    amplitudes = [np.mean(np.abs(frame)) for frame in frames.T]
    shimmer = np.std(np.diff(amplitudes)) / np.mean(amplitudes) if len(amplitudes) > 1 else 0
    result["shimmer"] = shimmer

    pitches, _ = librosa.piptrack(y=y, sr=sr)
    non_zero_pitches = pitches[pitches > 0]
    if len(non_zero_pitches) > 1:
        jitter = np.std(np.diff(non_zero_pitches)) / np.mean(non_zero_pitches)
    else:
        jitter = 0
    result["jitter"] = jitter

    return result

def process_mfccs(df):
    df['MFCCs'] = df['MFCCs'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    df['MFCCs_mean'] = df['MFCCs'].apply(lambda x: np.mean(x) if isinstance(x, list) else np.nan)
    df['MFCCs_std'] = df['MFCCs'].apply(lambda x: np.std(x) if isinstance(x, list) else np.nan)
    df['MFCCs_max'] = df['MFCCs'].apply(lambda x: np.max(x) if isinstance(x, list) else np.nan)
    df['MFCCs_min'] = df['MFCCs'].apply(lambda x: np.min(x) if isinstance(x, list) else np.nan)
    df.drop('MFCCs', axis=1, inplace=True)
    df.fillna(0, inplace=True)
    return df

data = pd.read_csv('Speech.csv')
data = process_mfccs(data)
X = data.drop('Mood', axis=1)
y = data['Mood']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

cv_scores = cross_val_score(rf, X_scaled, y, cv=5)
print(f"Cross-Validation Accuracy: {cv_scores.mean()}")

y_pred = rf.predict(X_test)
print("Test Accuracy:", accuracy_score(y_test, y_pred))

joblib.dump(rf, 'Emotion_Predictor.pkl')

rf = joblib.load('Emotion_Predictor.pkl')

def predict_emotion():
    audio_filename = "mic_input.wav"
    record_audio(filename=audio_filename, duration=5)

    features = extract_features(audio_filename)

    input_data = pd.DataFrame({
        'Speech Duration': [features["duration"]],
        'Pitch': [features["pitch"]],
        'Speech Rate': [features["speech_rate"]],
        'Jitter': [features["jitter"]],
        'Shimmer': [features["shimmer"]],
        'MFCCs_mean': [np.mean(features["mfccs"])],
        'MFCCs_std': [np.std(features["mfccs"])],
        'MFCCs_max': [np.max(features["mfccs"])],
        'MFCCs_min': [np.min(features["mfccs"])],
    })

    input_data_scaled = scaler.transform(input_data)

    prediction = rf.predict(input_data_scaled)
    print(f"Predicted Emotion: {prediction[0]}")

emotion_media_map = {
    'Angry': {'song': 'song1.mp3', 'video': 'notshout.mp4'},
    'Happy': {'song': 'song2.mp3', 'video': 'staycalm.mp4'},
    'Neutral': {'song': 'song3.mp3', 'video': 'sitdown.mp4'},
    'Sad': {'song': 'song4.mp3', 'video': 'staycalm.mp4'},
    'Distinguish': {'song': 'song5.mp3', 'video': 'sitdown.mp4'}
}

def save_to_csv(current_time, face_emotion, sound_emotion):
    file_exists = os.path.exists("emotion_data.csv")

    with open("emotion_data.csv", mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Time", "Facial Emotion", "Sound Emotion"])

        writer.writerow([current_time, face_emotion, sound_emotion])
        print(f"Data saved to CSV: Time: {current_time}, Facial Emotion: {face_emotion}, Sound Emotion: {sound_emotion}")

def upload_to_thingspeak(time, face_emotion, sound_emotion):
    payload = {
        'api_key': WRITE_API_KEY,
        'field1': time,
        'field2': face_emotion,
        'field3': sound_emotion,
    }
    response = requests.post(API_URL, data=payload)
    if response.status_code == 200:
        print(f"Data uploaded successfully: {time}, {face_emotion}, {sound_emotion}")
    else:
        print(f"Failed to upload data. Status code: {response.status_code}")

# Initialize sensor CSV
def initialize_sensor_csv():
    with open(SENSOR_CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "ECG Signal", "SpO2"])  # Must match exactly
# MQTT callbacks and functions
data_buffer = {"ecg": None, "spo2": None}

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT broker")
        client.subscribe(MQTT_TOPIC_ECG)
        client.subscribe(MQTT_TOPIC_SPO2)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global data_buffer
    topic = msg.topic
    value = msg.payload.decode()

    if topic == MQTT_TOPIC_ECG:
        data_buffer["ecg"] = value
    elif topic == MQTT_TOPIC_SPO2:
        data_buffer["spo2"] = value

    if data_buffer["ecg"] is not None and data_buffer["spo2"] is not None:
        save_sensor_data_to_csv(data_buffer["ecg"], data_buffer["spo2"])
        push_sensor_to_thingspeak(data_buffer["ecg"], data_buffer["spo2"])
        data_buffer = {"ecg": None, "spo2": None}

def save_sensor_data_to_csv(ecg, spo2):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SENSOR_CSV_FILE, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, ecg, spo2])
    print(f"Sensor data saved to CSV: ECG={ecg}, SpO2={spo2}")

def push_sensor_to_thingspeak(ecg, spo2):
    payload = {
        "api_key": THINGSPEAK_SENSOR_API_KEY,
        "field4": ecg,
        "field5": spo2
    }
    try:
        response = requests.get(API_URL, params=payload)
        if response.status_code == 200:
            print("Sensor data pushed to ThingSpeak successfully")
        else:
            print(f"Failed to push sensor data. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error pushing sensor data: {e}")

def mqtt_client_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print("Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT Error: {e}")

# Flask API Setup
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index9.html')

@app.route('/api/motor_forward', methods=['POST'])
def motor_forward():
    motor.forward()
    return jsonify({"message": "Motor moving forward."})

@app.route('/api/motor_backward', methods=['POST'])
def motor_backward():
    motor.backward()
    return jsonify({"message": "Motor moving backward."})

@app.route('/api/motor_stop', methods=['POST'])
def motor_stop():
    motor.stop()
    return jsonify({"message": "Motor stopped."})

@app.route('/api/open_door', methods=['POST'])
def door_open():
    operate_door(open_door=True)
    return jsonify({"message": "Door opened."})

@app.route('/api/close_door', methods=['POST'])
def door_close():
    operate_door(open_door=False)
    return jsonify({"message": "Door closed."})

# Route for live camera feed
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Updated emotion recognition to predict from current frame only
@app.route('/api/recognize_emotion', methods=['POST'])
def emotion_recognition():
    try:
        success, frame = cap.read()
        if not success:
            return jsonify({"message": "Failed to capture frame"}), 500

        gray_img = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detect.detectMultiScale(gray_img, 1.1, 4)

        detected_emotions = []
        for x, y, w, h in faces:
            roi_color = frame[y:y+h, x:x+w]
            final_img = cv2.resize(roi_color, (224, 224))
            final_img = np.expand_dims(final_img, axis=0)/255.0
            prediction = emotion_model.predict(final_img)
            pred = np.argmax(prediction[0])
            detected_emotions.append(classNames[pred])

        if detected_emotions:
            most_common_emotion = max(set(detected_emotions), key=detected_emotions.count)
        else:
            most_common_emotion = "Neutral"

        return jsonify({"result": most_common_emotion})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/api/detect_decibels', methods=['POST'])
def decibel_detection():
    try:
        audio_filename = "mic_input.wav"
        record_audio(filename=audio_filename, duration=5)

        features = extract_features(audio_filename)

        input_data = pd.DataFrame({
            'Speech Duration': [features["duration"]],
            'Pitch': [features["pitch"]],
            'Speech Rate': [features["speech_rate"]],
            'Jitter': [features["jitter"]],
            'Shimmer': [features["shimmer"]],
            'MFCCs_mean': [np.mean(features["mfccs"])],
            'MFCCs_std': [np.std(features["mfccs"])],
            'MFCCs_max': [np.max(features["mfccs"])],
            'MFCCs_min': [np.min(features["mfccs"])],
        })

        input_data_scaled = scaler.transform(input_data)
        prediction = rf.predict(input_data_scaled)

        return jsonify({
            "message": "Sound emotion detected successfully.",
            "result": prediction[0]
        })
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/play_video', methods=['POST'])
def play_video_endpoint():
    data = request.get_json()
    video_path = data.get('param', '')
    try:
        play_video(video_path)
        return jsonify({"message": f"Playing video: {video_path}"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/play_mp3', methods=['POST'])
def play_mp3_endpoint():
    data = request.get_json()
    mp3_path = data.get('param', '')
    try:
        play_mp3(mp3_path)
        return jsonify({"message": f"Playing MP3: {mp3_path}"})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/get_current_time', methods=['POST'])
def get_current_time():
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({"current_time": current_time})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/save_to_csv', methods=['POST'])
def save_to_csv_route():
    try:
        data = request.json
        save_to_csv(data["current_time"], data["emotion_face"], data["emotion_voice"])
        return jsonify({"message": "Data saved to CSV."})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500

@app.route('/api/upload_to_thingspeak', methods=['POST'])
def upload_to_thingspeak_route():
    try:
        data = request.json
        # Check for required fields
        if not data or 'current_time' not in data or 'emotion_face' not in data or 'emotion_voice' not in data:
            return jsonify({"message": "Missing required data fields: current_time, emotion_face, emotion_voice."}), 400
        
        upload_to_thingspeak(data["current_time"], data["emotion_face"], data["emotion_voice"])
        return jsonify({"message": "Data uploaded to ThingSpeak."})
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    
@app.route('/api/get_medical_data', methods=['GET'])
def get_medical_data():
    try:
        # Read sensor data from CSV
        medical_data = []
        with open(SENSOR_CSV_FILE, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                medical_data.append({
                    "Timestamp": row["Timestamp"],
                    "ECG": row["ECG Signal"],
                    "SpO2": row["SpO2"]
                })
        return jsonify(medical_data)
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
    
# Route to check MQTT client status
@app.route('/api/mqtt_status', methods=['GET'])
def mqtt_status():
    return jsonify({"status": "MQTT client is running"})

if __name__ == '__main__':
    initialize_sensor_csv()
    mqtt_thread = threading.Thread(target=mqtt_client_thread)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    app.run(debug=True, host="0.0.0.0", port=5005, threaded=True, use_reloader=False)
