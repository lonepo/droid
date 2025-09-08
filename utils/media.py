import os
import cv2
import pygame
from ffpyplayer.player import MediaPlayer

emotion_media_map = {
    'Angry': {'song': 'song1.mp3', 'video': 'notshout.mp4'},
    'Happy': {'song': 'song2.mp3', 'video': 'staycalm.mp4'},
    'Neutral': {'song': 'song3.mp3', 'video': 'sitdown.mp4'},
    'Sad': {'song': 'song4.mp3', 'video': 'staycalm.mp4'},
    'Distinguish': {'song': 'song5.mp3', 'video': 'sitdown.mp4'}
}

def play_video(video_path):
    if not os.path.exists(video_path): return
    video = cv2.VideoCapture(video_path)
    player = MediaPlayer(video_path)
    while True:
        grabbed, frame = video.read()
        audio_frame, val = player.get_frame()
        if not grabbed: break
        cv2.imshow("Video", frame)
        if val != 'eof' and audio_frame is not None: _, _ = audio_frame
        if cv2.waitKey(28) & 0xFF == ord("q"): break
    video.release()
    cv2.destroyAllWindows()

def play_mp3(file_path):
    if not os.path.exists(file_path): return
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy(): pygame.time.wait(100)
    pygame.mixer.quit()
