import pyaudio
import wave
import librosa
import numpy as np

def record_audio(filename="mic_input.wav", duration=5, sample_rate=44100):
    chunk = 1024
    format = pyaudio.paInt16
    channels = 1

    p = pyaudio.PyAudio()
    stream = p.open(format=format, channels=channels, rate=sample_rate, input=True, frames_per_buffer=chunk)
    frames = [stream.read(chunk) for _ in range(0, int(sample_rate / chunk * duration))]
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
    jitter = np.std(np.diff(non_zero_pitches)) / np.mean(non_zero_pitches) if len(non_zero_pitches) > 1 else 0
    result["jitter"] = jitter
    return result
