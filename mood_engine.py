# mood_engine.py — detects happy, sad, angry, surprise, neutral, calm from your face

import threading
import time

import cv2
import numpy as np
from deepface import DeepFace

from playlists import EMOTION_TO_MOOD, MOOD_LABELS

DETECT_INTERVAL_SEC = 0.4
DETECT_SIZE = (224, 224)

_last_mood = "neutral"
_last_emotion = "neutral"
_last_confidence = 0.0
_last_scores = {}
_latest_frame = None
_running = True
_thread = None
_lock = threading.Lock()

_analyze_opts = {
    "actions": ["emotion"],
    "enforce_detection": False,
    "silent": True,
    "detector_backend": "opencv",
    "align": False,
}


def _pick_mood(emotion_scores: dict):
    """Pick mood from DeepFace emotion percentages."""
    if not emotion_scores:
        return "neutral", "neutral", 0.0

    raw = max(emotion_scores, key=emotion_scores.get)
    conf = float(emotion_scores[raw])
    mood = EMOTION_TO_MOOD.get(raw, "neutral")
    return mood, raw, conf


def _analyze_frame(frame):
    small = cv2.resize(frame, DETECT_SIZE)
    result = DeepFace.analyze(small, **_analyze_opts)
    if isinstance(result, list):
        result = result[0]

    scores = result.get("emotion", {})
    if not scores and "dominant_emotion" in result:
        raw = result["dominant_emotion"]
        return EMOTION_TO_MOOD.get(raw, "neutral"), raw, 50.0, {raw: 50.0}

    mood, raw, conf = _pick_mood(scores)
    return mood, raw, conf, scores


def _warmup():
    dummy = np.zeros((DETECT_SIZE[1], DETECT_SIZE[0], 3), dtype=np.uint8)
    try:
        DeepFace.analyze(dummy, **_analyze_opts)
        print("[Mood] Ready — smile=Happy, frown=Sad, wide eyes=Surprise")
    except Exception:
        pass


def _detect_loop():
    global _last_mood, _last_emotion, _last_confidence, _last_scores, _latest_frame, _running

    while _running:
        t0 = time.time()
        with _lock:
            frame = None if _latest_frame is None else _latest_frame.copy()

        if frame is not None:
            try:
                mood, raw, conf, scores = _analyze_frame(frame)
                with _lock:
                    if mood != _last_mood:
                        label = MOOD_LABELS.get(mood, mood)
                        print(f"[Mood] {label} ({raw} {conf:.0f}%)")
                    _last_mood = mood
                    _last_emotion = raw
                    _last_confidence = conf
                    _last_scores = scores
            except Exception as e:
                print(f"[Mood] Skipped: {e}")

        time.sleep(max(0.15, DETECT_INTERVAL_SEC - (time.time() - t0)))


def start():
    global _thread, _running
    if _thread is not None and _thread.is_alive():
        return
    _running = True
    threading.Thread(target=_warmup, daemon=True).start()
    _thread = threading.Thread(target=_detect_loop, daemon=True)
    _thread.start()


def stop():
    global _running
    _running = False


def get_mood_info(frame):
    """Returns mood + emotion details for HUD."""
    global _latest_frame
    with _lock:
        _latest_frame = frame
        return {
            "mood": _last_mood,
            "emotion": _last_emotion,
            "confidence": _last_confidence,
            "scores": dict(_last_scores),
        }


def get_mood(frame):
    return get_mood_info(frame)["mood"]
