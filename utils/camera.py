import cv2
import threading

# Global camera object
cap = None

def find_available_camera(max_index=5):
    """
    Try to find the first available camera index.
    """
    for i in range(max_index):
        test_cap = cv2.VideoCapture(i)
        if test_cap.isOpened():
            print(f"[INFO] Camera found at index {i}")
            return test_cap
        test_cap.release()
    print("[WARN] No camera detected!")
    return None

# Initialize camera once
cap = find_available_camera()

# MJPEG stream generator
def gen_frames():
    global cap
    if cap is None:
        # If no camera, yield a blank frame
        import numpy as np
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        while True:
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    else:
        while True:
            ret, frame = cap.read()
            if not ret:
                # Yield blank frame instead of crashing
                import numpy as np
                frame = np.zeros((480, 640, 3), dtype=np.uint8)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
