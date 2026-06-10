# playlists.py
# Add your YouTube playlist URLs here for each mood
# Find Bollywood playlists on YouTube, copy the playlist URL and paste below

PLAYLISTS = {
    "happy": "https://youtube.com/playlist?list=PLi7NfXoYSKBf6PC-x2WYiJ2ZMvVC9lcKy&si=ptPfO1P8Q3fsCllj",     # replace with your happy playlist
    "sad": "https://youtube.com/playlist?list=PL9khxBZiiQwoKEqdTrb4ip-S_Tov6FkBQ&si=RqoY2r2anEq8_mpv",       # replace with your sad playlist
    "angry": "https://youtube.com/playlist?list=PLp_LwqrLksxeynGj6LyX9r89NpF9_bNCF&si=Jc8PuOw4QJIez8Q8",     # replace with your angry playlist
    "calm": "https://youtube.com/playlist?list=RDATgqmXfodHlwZV9wbGF5bGlzdA&playnext=1&si=UKnAMs0pGfE6OPI2",      # replace with your calm playlist
    "surprise": "https://youtube.com/playlist?list=RDUZTNacSnivw&playnext=1&si=6HrVP6xoSfq-1I_6",  # replace with your surprise playlist
    "neutral": "https://youtube.com/playlist?list=PLVeCLrtKOITOfvUL1ga_Cl2EUtlx5Z5mV&si=zxHVDx-QNd4Pf1hx",   # replace with your neutral playlist
}

# Mood to glow color mapping (B, G, R) — used by canvas_draw.py
MOOD_COLORS = {
    "happy":    (0, 220, 255),   # golden yellow
    "sad":      (220, 100, 50),  # deep blue
    "angry":    (30,  30, 255),  # red
    "calm":     (200, 200, 50),  # soft teal
    "surprise": (255, 180, 0),   # bright cyan
    "neutral":  (180, 180, 180), # soft white
}

# How long (in seconds) mood must stay the same before music switches
# Prevents music changing every single frame
MOOD_SWITCH_DELAY = 5