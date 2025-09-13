@app.route("/api/recognize_emotion", methods=["POST"])
def recognize_emotion_api():
    try:
        face_emotion = recognize_face_emotion()
        audio_emotion = predict_audio_emotion()

        # Choose one emotion (face priority > audio)
        detected = face_emotion if face_emotion != "No face detected" else audio_emotion
        print(f"[DEBUG] Detected emotion: {detected}")  # Debug log

        # Get media mapping
        media = emotion_media_map.get(detected, {"song": None, "video": None})

        # Load custom mapping if it exists
        custom_mapping = load_mapping()
        video_to_play = custom_mapping.get(detected, media["video"])

        response = {
            "result": detected,
            "emotion": detected,
            "song_url": media["song"],
            "video_url": video_to_play
        }
        
        print(f"[DEBUG] Sending response: {response}")  # Debug log
        return jsonify(response)
    except Exception as e:
        print(f"[ERROR] Error in emotion recognition: {str(e)}")
        return jsonify({
            "error": "Failed to recognize emotion",
            "message": str(e)
        }), 500
