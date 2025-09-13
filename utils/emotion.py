import cv2
import numpy as np
import sounddevice as sd
import librosa
from tensorflow.keras.models import load_model
from config import FACE_MODEL, LABEL_NAMES, VIDEO_MAP
from utils.media import play_video, play_mp3, emotion_media_map

# -----------------------------
# Face Emotion Recognition
# -----------------------------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def recognize_face_emotion():
    """
    Captures a single frame from the camera and predicts face emotion.
    """
    from utils.camera import cap  # use shared camera
    ret, frame = cap.read()
    if not ret:
        return "No face detected"

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 0:
        return "No face detected"

    for (x, y, w, h) in faces:
        roi_color = frame[y:y + h, x:x + w]
        roi_resized = cv2.resize(roi_color, (224, 224))
        roi_normalized = roi_resized / 255.0
        roi_input = np.expand_dims(roi_normalized, axis=0)

        predictions = FACE_MODEL.predict(roi_input, verbose=0)
        emotion_idx = np.argmax(predictions)
        emotion = LABEL_NAMES[emotion_idx]

        print(f"[Face] Detected emotion: {emotion}")

        # 🔥 Trigger video playback
        if emotion in VIDEO_MAP:
            play_video(VIDEO_MAP[emotion])

        return emotion


# -----------------------------
# Audio Emotion Recognition
# -----------------------------
def predict_audio_emotion(duration=3, fs=44100):
    """
    Records audio from microphone and predicts emotion from the sound.
    """
    try:
        print("[Audio] Recording... Please speak")
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()
        print("[Audio] Recording complete")

        audio_data = recording.flatten()

        # Feature extraction
        mfccs = librosa.feature.mfcc(y=audio_data, sr=fs, n_mfcc=13)
        mfccs_mean = np.mean(mfccs.T, axis=0)

        # Placeholder logic
        import random
        emotions = ["Happy", "Sad", "Angry", "Neutral"]
        emotion = random.choice(emotions)

        print(f"[Audio] Detected emotion: {emotion}")

        # 🔥 Trigger video playback
        if emotion in VIDEO_MAP:
            play_video(VIDEO_MAP[emotion])

        return emotion
    except Exception as e:
        return f"Error: {str(e)}"
