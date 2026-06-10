# hand_tracker.py — draw when index finger is up (pointing gesture, relaxed rules)

import math
import sys
import types

if "mediapipe.tasks.python" not in sys.modules:
    _tasks_pkg = types.ModuleType("mediapipe.tasks")
    _tasks_py = types.ModuleType("mediapipe.tasks.python")
    _tasks_pkg.python = _tasks_py
    sys.modules["mediapipe.tasks"] = _tasks_pkg
    sys.modules["mediapipe.tasks.python"] = _tasks_py

import cv2
import mediapipe as mp

_hands = mp.solutions.hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=0,
)

_SMOOTH = 0.35
_sx = _sy = None
_lost_frames = 0
_was_drawing = False
MAX_LOST_FRAMES = 12


def _dist(a, b):
    return math.hypot(a.x - b.x, a.y - b.y, a.z - b.z)


def _finger_extended(lm, tip_id, pip_id, mcp_id):
    return _dist(lm[tip_id], lm[0]) > _dist(lm[pip_id], lm[0])


def _is_pointing(hand_landmarks):
    """
    Index finger extended, middle finger down.
    Relaxed so pointing at the camera still works.
    """
    lm = hand_landmarks.landmark
    index_out = _finger_extended(lm, 8, 6, 5)
    middle_out = _finger_extended(lm, 12, 10, 9)
    # Index up + middle not fully out = pointing OR single finger up
    if index_out and not middle_out:
        return True
    # Fallback: only index clearly extended (others mostly curled)
    others = sum(
        _finger_extended(lm, t, p, m)
        for t, p, m in [(12, 10, 9), (16, 14, 13), (20, 18, 17)]
    )
    return index_out and others == 0


_was_pinched = False


def _reset():
    global _sx, _sy, _lost_frames, _was_drawing, _was_pinched
    _sx = _sy = None
    _lost_frames = 0
    _was_drawing = False
    _was_pinched = False


_debug_frame_count = 0


def get_fingertip(frame):
    global _sx, _sy, _lost_frames, _was_drawing, _debug_frame_count, _was_pinched

    _debug_frame_count += 1
    h, w, _ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = _hands.process(rgb)

    if not results.multi_hand_landmarks:
        if _debug_frame_count % 30 == 0:
            print("[Hand Tracker] No hand detected in camera feed.")
        if _was_drawing and _lost_frames < MAX_LOST_FRAMES and _sx is not None:
            _lost_frames += 1
            return (int(_sx), int(_sy)), frame, _was_pinched
        _reset()
        return None, frame, False

    hand = results.multi_hand_landmarks[0]
    pointing = _is_pointing(hand)

    # Calculate pinch state: ratio of thumb-tip (4) to index-tip (8) vs hand scale
    lm = hand.landmark
    hand_scale = _dist(lm[9], lm[0])
    pinch_dist = _dist(lm[4], lm[8])
    is_pinched = (pinch_dist / max(1e-5, hand_scale)) < 0.15
    _was_pinched = is_pinched

    if _debug_frame_count % 15 == 0:
        print(f"[Hand Tracker] Hand detected! Pinch ratio: {pinch_dist / max(1e-5, hand_scale):.2f}, Pinched: {is_pinched}, Pointing: {pointing}")

    if not pointing:
        _reset()
        return None, frame, False

    _lost_frames = 0
    _was_drawing = True
    tip = hand.landmark[8]
    rx, ry = tip.x * w, tip.y * h

    if _sx is None:
        _sx, _sy = rx, ry
    else:
        _sx = _SMOOTH * rx + (1 - _SMOOTH) * _sx
        _sy = _SMOOTH * ry + (1 - _SMOOTH) * _sy

    return (int(_sx), int(_sy)), frame, is_pinched


def release():
    _hands.close()
    _reset()
