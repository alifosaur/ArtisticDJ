# hud.py

import cv2
from playlists import MOOD_COLORS, MOOD_LABELS

FONT = cv2.FONT_HERSHEY_SIMPLEX
WINDOW = "Aura Canvas"
QUIT_BTN = {"x1": -1, "y1": -1, "x2": -1, "y2": -1}
DOODLE_BTN = {"x1": -1, "y1": -1, "x2": -1, "y2": -1}
ERASER_BTN = {"x1": -1, "y1": -1, "x2": -1, "y2": -1}
CLEAR_BTN = {"x1": -1, "y1": -1, "x2": -1, "y2": -1}


def _draw_text(frame, text, pos, scale, color, thickness):
    x, y = pos
    cv2.putText(frame, text, (x + 2, y + 2), FONT, scale, (0, 0, 0), thickness + 1, cv2.LINE_AA)
    cv2.putText(frame, text, (x, y), FONT, scale, color, thickness, cv2.LINE_AA)


def draw_hud(
    frame,
    mood_info,
    song_title,
    is_loading=False,
    music_playing=False,
    music_countdown=None,
    draw_hint=False,
    doodle_active=True,
    eraser_active=False,
    hover_btn=None,
    hover_progress=0.0,
    fingertip=None,
):
    global QUIT_BTN, DOODLE_BTN, ERASER_BTN, CLEAR_BTN

    mood = mood_info.get("mood", "neutral")
    emotion = mood_info.get("emotion", "neutral")
    conf = mood_info.get("confidence", 0)

    h, w = frame.shape[:2]
    color = MOOD_COLORS.get(mood, (180, 180, 180))
    label = MOOD_LABELS.get(mood, mood.capitalize())

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 92), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    cv2.circle(frame, (22, 28), 11, color, -1)
    _draw_text(frame, f"Mood: {label}", (42, 28), 0.7, color, 2)
    _draw_text(frame, f"Face: {emotion.capitalize()} ({conf:.0f}%)", (42, 52), 0.45, (200, 200, 200), 1)

    if draw_hint:
        if eraser_active:
            _draw_text(frame, "Erasing ON — point index finger", (42, 72), 0.45, (100, 200, 255), 1)
        else:
            _draw_text(frame, "Drawing ON — point index finger", (42, 72), 0.45, (150, 255, 150), 1)
    else:
        if not doodle_active:
            _draw_text(frame, "Doodle mode is OFF — click DOODLE to enable", (42, 72), 0.45, (160, 160, 160), 1)
        elif eraser_active:
            _draw_text(frame, "Point index finger up to erase", (42, 72), 0.45, (100, 200, 255), 1)
        else:
            _draw_text(frame, "Point index finger up to draw", (42, 72), 0.45, (160, 160, 160), 1)

    # QUIT Button
    bx1, by1, bx2, by2 = w - 90, 8, w - 10, 42
    QUIT_BTN = {"x1": bx1, "y1": by1, "x2": bx2, "y2": by2}
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (40, 40, 180), -1)
    _draw_text(frame, "QUIT", (bx1 + 18, by2 - 10), 0.55, (255, 255, 255), 2)
    if hover_btn == "quit":
        cv2.rectangle(frame, (bx1, by2 - 4), (bx1 + int((bx2 - bx1) * hover_progress), by2), (255, 255, 255), -1)

    # DOODLE Toggle Button
    dbx1, dby1, dbx2, dby2 = w - 215, 8, w - 100, 42
    DOODLE_BTN = {"x1": dbx1, "y1": dby1, "x2": dbx2, "y2": dby2}
    doodle_color = (60, 180, 60) if doodle_active else (100, 100, 100)
    doodle_text = "DOODLE: ON" if doodle_active else "DOODLE: OFF"
    cv2.rectangle(frame, (dbx1, dby1), (dbx2, dby2), doodle_color, -1)
    _draw_text(frame, doodle_text, (dbx1 + 10, dby2 - 12), 0.42, (255, 255, 255), 2 if doodle_active else 1)
    if hover_btn == "doodle":
        cv2.rectangle(frame, (dbx1, dby2 - 4), (dbx1 + int((dbx2 - dbx1) * hover_progress), dby2), (255, 255, 255), -1)

    # ERASER Toggle Button
    ebx1, eby1, ebx2, eby2 = w - 340, 8, w - 225, 42
    ERASER_BTN = {"x1": ebx1, "y1": eby1, "x2": ebx2, "y2": eby2}
    eraser_color = (0, 140, 255) if eraser_active else (100, 100, 100)
    eraser_text = "ERASER: ON" if eraser_active else "ERASER: OFF"
    cv2.rectangle(frame, (ebx1, eby1), (ebx2, eby2), eraser_color, -1)
    _draw_text(frame, eraser_text, (ebx1 + 10, eby2 - 12), 0.42, (255, 255, 255), 2 if eraser_active else 1)
    if hover_btn == "eraser":
        cv2.rectangle(frame, (ebx1, eby2 - 4), (ebx1 + int((ebx2 - ebx1) * hover_progress), eby2), (255, 255, 255), -1)

    # CLEAR Button
    cbx1, cby1, cbx2, cby2 = w - 440, 8, w - 350, 42
    CLEAR_BTN = {"x1": cbx1, "y1": cby1, "x2": cbx2, "y2": cby2}
    cv2.rectangle(frame, (cbx1, cby1), (cbx2, cby2), (180, 60, 60), -1)
    _draw_text(frame, "CLEAR", (cbx1 + 18, cby2 - 10), 0.48, (255, 255, 255), 2)
    if hover_btn == "clear":
        cv2.rectangle(frame, (cbx1, cby2 - 4), (cbx1 + int((cbx2 - cbx1) * hover_progress), cby2), (255, 255, 255), -1)

    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 44), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay2, 0.55, frame, 0.45, 0, frame)

    if music_countdown is not None:
        song_text = f"Music in {music_countdown}s ({MOOD_LABELS.get(mood, mood)})..."
        song_color = (180, 220, 255)
    elif is_loading:
        song_text = song_title or "Loading music..."
        song_color = (180, 200, 255)
    elif music_playing:
        t = song_title if len(song_title) <= 55 else song_title[:55] + "..."
        song_text = f"Now Playing: {t}"
        song_color = (150, 255, 150)
    else:
        t = song_title if len(song_title) <= 55 else song_title[:55] + "..."
        song_text = f"Music: {t}"
        song_color = (200, 200, 200)

    _draw_text(frame, song_text, (10, h - 14), 0.48, song_color, 1)

    if fingertip is not None:
        if draw_hint:
            # Pinching (Active Drawing): Solid mood-colored cursor with white border
            cv2.circle(frame, fingertip, 8, color, -1)
            cv2.circle(frame, fingertip, 8, (255, 255, 255), 2)
        else:
            # Hovering (Inactive Drawing): Open cursor with white center
            cv2.circle(frame, fingertip, 5, (255, 255, 255), -1)
            cv2.circle(frame, fingertip, 10, color, 2)

    return frame


def is_quit_click(x, y):
    b = QUIT_BTN
    return b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]


def is_doodle_click(x, y):
    b = DOODLE_BTN
    return b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]


def is_eraser_click(x, y):
    b = ERASER_BTN
    return b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]


def is_clear_click(x, y):
    b = CLEAR_BTN
    return b["x1"] <= x <= b["x2"] and b["y1"] <= y <= b["y2"]
