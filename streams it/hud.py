# hud.py
# Draws the on-screen HUD (heads-up display) on the final composited frame.
# Shows: current mood, current song title, and a colored aura indicator dot.
# Kept lightweight — pure OpenCV, no extra libraries.

import cv2
from playlists import MOOD_COLORS

# Font settings
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_LARGE = 0.8
FONT_SCALE_SMALL = 0.55
THICKNESS = 2
THIN = 1


def _draw_text_with_shadow(frame, text, pos, scale, color, thickness):
    """Draws text with a dark shadow underneath for readability on any background."""
    x, y = pos
    # Shadow
    cv2.putText(frame, text, (x + 2, y + 2), FONT, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    # Actual text
    cv2.putText(frame, text, (x, y), FONT, scale, color, thickness, cv2.LINE_AA)


def draw_hud(frame, mood, song_title, is_loading=False):
    """
    Draws the HUD onto the frame in-place.

    Args:
        frame      — the composited frame from canvas_draw.draw()
        mood       — current mood string e.g. "happy"
        song_title — current song name from music_player.get_current_song_title()
        is_loading — True while the song is still being fetched (shows "Loading...")

    Returns the frame with HUD drawn on it.
    """
    h, w = frame.shape[:2]
    color = MOOD_COLORS.get(mood, (180, 180, 180))

    # --- Top-left panel: mood indicator ---
    # Semi-transparent dark background strip for readability
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (320, 70), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    # Aura color dot
    cv2.circle(frame, (28, 28), 14, color, -1)
    cv2.circle(frame, (28, 28), 15, (255, 255, 255), 1)

    # Mood label
    mood_text = f"Mood: {mood.capitalize()}"
    _draw_text_with_shadow(frame, mood_text, (52, 35), FONT_SCALE_LARGE, color, THICKNESS)

    # --- Bottom panel: song name ---
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 50), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay2, 0.45, frame, 0.55, 0, frame)

    if is_loading:
        song_display = "Fetching song..."
        song_color = (150, 150, 150)
    else:
        # Truncate long song titles so they fit on screen
        max_chars = 60
        display_title = song_title if len(song_title) <= max_chars else song_title[:max_chars] + "..."
        song_display = f"Now Playing: {display_title}"
        song_color = (220, 220, 220)

    _draw_text_with_shadow(frame, song_display, (12, h - 18), FONT_SCALE_SMALL, song_color, THIN)

    # --- Top-right: keyboard shortcuts reminder ---
    hints = ["C = clear canvas", "Q = quit"]
    for i, hint in enumerate(hints):
        _draw_text_with_shadow(
            frame, hint,
            (w - 180, 25 + i * 22),
            0.45, (160, 160, 160), 1
        )

    return frame