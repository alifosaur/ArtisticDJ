# main.py

import sys
import types
import signal
import os

os.environ["OPENCV_VIDEOIO_MSMF_ENABLE_HW_TRANSFORMS"] = "0"


def _stub_mediapipe_tasks():
    if "mediapipe.tasks.python" in sys.modules:
        return
    tasks_pkg = types.ModuleType("mediapipe.tasks")
    tasks_py = types.ModuleType("mediapipe.tasks.python")
    tasks_pkg.python = tasks_py
    sys.modules["mediapipe.tasks"] = tasks_pkg
    sys.modules["mediapipe.tasks.python"] = tasks_py


_stub_mediapipe_tasks()

import cv2
import time

from hand_tracker import get_fingertip, release as release_tracker
from mood_engine import get_mood_info, start as start_mood, stop as stop_mood
from canvas_draw import draw, init_canvas, clear_canvas
from music_player import (
    play_for_mood,
    prepare_mood,
    preload as preload_music,
    preload_all_background,
    get_current_song_title,
    is_loading,
    is_playing,
    get_playing_mood,
    tick as music_tick,
    stop as stop_music,
)
from hud import draw_hud, is_quit_click, is_doodle_click, is_eraser_click, is_clear_click, WINDOW
from playlists import DISPLAY_MOOD_DELAY, MUSIC_SWITCH_DELAY, MOOD_LABELS

_running = True
_doodle_enabled = True
_eraser_enabled = False
_hover_btn = None
_hover_start_time = 0.0
_hover_triggered = False
WINDOW_NAME = WINDOW


def _request_exit(*_args):
    global _running
    _running = False


def _on_mouse(event, x, y, _flags, _param):
    global _running, _doodle_enabled, _eraser_enabled
    if event == cv2.EVENT_LBUTTONDOWN:
        if is_quit_click(x, y):
            _running = False
        elif is_doodle_click(x, y):
            _doodle_enabled = not _doodle_enabled
            print(f"[UI] Doodle toggled: {'ON' if _doodle_enabled else 'OFF'}")
        elif is_eraser_click(x, y):
            _eraser_enabled = not _eraser_enabled
            print(f"[UI] Eraser toggled: {'ON' if _eraser_enabled else 'OFF'}")
        elif is_clear_click(x, y):
            clear_canvas()
            print("[UI] Canvas cleared")


def _window_closed():
    try:
        return cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1
    except cv2.error:
        return True


def _poll_input():
    key = cv2.waitKey(10) & 0xFF
    if key in (ord("q"), ord("Q"), 27):
        return "quit"
    if key in (ord("c"), ord("C")):
        return "clear"
    return None


def main():
    global _running, _doodle_enabled, _eraser_enabled, _hover_btn, _hover_start_time, _hover_triggered

    signal.signal(signal.SIGINT, _request_exit)
    if hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, _request_exit)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not open webcam.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    ret, frame = cap.read()
    if not ret:
        print("[Error] Could not read from webcam.")
        return

    h, w = frame.shape[:2]
    init_canvas(h, w)
    start_mood()

    preload_music("neutral")
    preload_all_background()

    print("=" * 50)
    print("  Aura Canvas")
    print("  Point index finger to draw")
    print(f"  Music changes {int(MUSIC_SWITCH_DELAY)} sec after you change expression")
    print("=" * 50)

    display_mood = "neutral"
    last_detected = "neutral"
    display_hold_start = time.time()

    # Music: wait 10 sec after mood is confirmed on screen
    pending_music_mood = None
    music_switch_at = 0.0

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WINDOW_NAME, 960, 540)
    cv2.setMouseCallback(WINDOW_NAME, _on_mouse)

    while _running:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        mood_info = get_mood_info(frame)
        detected = mood_info["mood"]
        music_tick()

        now = time.time()

        # Fast: stroke color + mood label
        if detected != last_detected:
            last_detected = detected
            display_hold_start = now
        elif now - display_hold_start >= DISPLAY_MOOD_DELAY:
            if detected != display_mood:
                display_mood = detected
                # Schedule music 10 seconds from now
                pending_music_mood = display_mood
                music_switch_at = now + MUSIC_SWITCH_DELAY
                prepare_mood(display_mood)  # download during countdown
                label = MOOD_LABELS.get(display_mood, display_mood)
                print(f"[Music] Will play {label} in {int(MUSIC_SWITCH_DELAY)} sec...")

        # After 10 sec hold: switch music
        if pending_music_mood and now >= music_switch_at:
            if pending_music_mood != get_playing_mood():
                play_for_mood(pending_music_mood)
            pending_music_mood = None

        music_countdown = None
        if pending_music_mood and music_switch_at > now:
            music_countdown = int(music_switch_at - now) + 1

        fingertip, frame, still_drawing = get_fingertip(frame)

        # Check hover buttons
        hovered_now = None
        if fingertip is not None:
            fx, fy = fingertip
            if is_quit_click(fx, fy):
                hovered_now = "quit"
            elif is_doodle_click(fx, fy):
                hovered_now = "doodle"
            elif is_eraser_click(fx, fy):
                hovered_now = "eraser"
            elif is_clear_click(fx, fy):
                hovered_now = "clear"

        hover_progress = 0.0
        if hovered_now is not None:
            if hovered_now != _hover_btn:
                _hover_btn = hovered_now
                _hover_start_time = now
                _hover_triggered = False
            elif not _hover_triggered:
                elapsed = now - _hover_start_time
                hover_progress = min(1.0, elapsed / 0.8)
                if elapsed >= 0.8:
                    _hover_triggered = True
                    if _hover_btn == "quit":
                        _running = False
                    elif _hover_btn == "doodle":
                        _doodle_enabled = not _doodle_enabled
                        print(f"[UI] Doodle toggled via hover: {'ON' if _doodle_enabled else 'OFF'}")
                    elif _hover_btn == "eraser":
                        _eraser_enabled = not _eraser_enabled
                        print(f"[UI] Eraser toggled via hover: {'ON' if _eraser_enabled else 'OFF'}")
                    elif _hover_btn == "clear":
                        clear_canvas()
                        print("[UI] Canvas cleared via hover")
        else:
            _hover_btn = None
            _hover_start_time = 0.0
            _hover_triggered = False

        drawing_active = still_drawing and _doodle_enabled
        if fingertip is not None and fingertip[1] < 92:
            drawing_active = False  # Disable drawing when finger is in HUD area

        frame = draw(frame, fingertip, display_mood, drawing_active=drawing_active, erase=_eraser_enabled)
        frame = draw_hud(
            frame,
            mood_info,
            get_current_song_title(),
            is_loading(),
            is_playing(),
            music_countdown=music_countdown,
            draw_hint=drawing_active,
            doodle_active=_doodle_enabled,
            eraser_active=_eraser_enabled,
            hover_btn=_hover_btn,
            hover_progress=hover_progress,
            fingertip=fingertip,
        )

        cv2.imshow(WINDOW_NAME, frame)

        if _window_closed():
            break
        action = _poll_input()
        if action == "quit":
            break
        if action == "clear":
            clear_canvas()

    cap.release()
    release_tracker()
    stop_mood()
    stop_music()
    cv2.destroyAllWindows()
    print("[Done] Closed.")


if __name__ == "__main__":
    main()
