# playlists.py — mood playlists + labels shown on screen

PLAYLISTS = {
    "happy": "https://youtube.com/playlist?list=PLi7NfXoYSKBf6PC-x2WYiJ2ZMvVC9lcKy",
    "sad": "https://youtube.com/playlist?list=PL9khxBZiiQwoKEqdTrb4ip-S_Tov6FkBQ",
    "angry": "https://youtube.com/playlist?list=PLp_LwqrLksxeynGj6LyX9r89NpF9_bNCF",
    "calm": "https://youtube.com/playlist?list=PLVeCLrtKOITOfvUL1ga_Cl2EUtlx5Z5mV",
    "surprise": "https://youtube.com/playlist?list=PLi7NfXoYSKBf6PC-x2WYiJ2ZMvVC9lcKy",
    "neutral": "https://youtube.com/playlist?list=PLVeCLrtKOITOfvUL1ga_Cl2EUtlx5Z5mV",
}

MOOD_COLORS = {
    "happy": (0, 200, 255),
    "sad": (255, 120, 80),
    "angry": (40, 40, 255),
    "calm": (255, 180, 60),
    "surprise": (255, 255, 100),
    "neutral": (200, 255, 255),
}

# What the user sees on screen for each mood
MOOD_LABELS = {
    "happy": "Happy",
    "sad": "Sad",
    "angry": "Angry",
    "calm": "Calm",
    "surprise": "Surprised",
    "neutral": "Neutral",
}

# DeepFace emotion name -> our mood
EMOTION_TO_MOOD = {
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "surprise": "surprise",
    "neutral": "neutral",
    "fear": "calm",
    "disgust": "angry",
}

DISPLAY_MOOD_DELAY = 0.8
# Wait this long after face mood is stable, then switch music
MUSIC_SWITCH_DELAY = 10.0
