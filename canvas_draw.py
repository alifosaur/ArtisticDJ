# canvas_draw.py
# Permanent neon strokes — no fade, full-screen continuous drawing

import math

import cv2
import numpy as np

from playlists import MOOD_COLORS

_mask = None
_glow_cache = None
_h = _w = 0
_smooth = None
_draw_prev = None
_glow_dirty = True
_last_glow_mood = None
LINE_THICK = 10
MAX_SEGMENT = 12


def init_canvas(height, width):
    global _mask, _glow_cache, _h, _w, _smooth, _draw_prev, _glow_dirty, _last_glow_mood
    _h, _w = height, width
    _mask = np.zeros((height, width), dtype=np.uint8)
    _glow_cache = np.zeros((height, width, 3), dtype=np.uint8)
    _smooth = None
    _draw_prev = None
    _glow_dirty = True
    _last_glow_mood = None


def _reset_stroke():
    global _smooth, _draw_prev
    _smooth = None
    _draw_prev = None


def _interp_segment(p1, p2):
    x1, y1 = p1
    x2, y2 = p2
    dist = math.hypot(x2 - x1, y2 - y1)
    steps = max(1, int(dist / MAX_SEGMENT))
    pts = [p1]
    for i in range(1, steps + 1):
        t = i / steps
        pts.append((int(x1 + (x2 - x1) * t), int(y1 + (y2 - y1) * t)))
    return pts


def _draw_segment(p1, p2, erase=False):
    global _mask, _glow_dirty
    pts = _interp_segment(p1, p2)
    val = 0 if erase else 255
    thick = LINE_THICK * 4 if erase else LINE_THICK
    for i in range(1, len(pts)):
        cv2.line(_mask, pts[i - 1], pts[i], val, thick, cv2.LINE_AA)
    _glow_dirty = True


def _build_glow(color_bgr):
    b, g, r = color_bgr
    inner = cv2.GaussianBlur(_mask, (0, 0), sigmaX=5, sigmaY=5)
    outer = cv2.GaussianBlur(_mask, (0, 0), sigmaX=18, sigmaY=18)

    glow = np.zeros((_h, _w, 3), dtype=np.float32)
    glow[:, :, 0] = outer * (b / 255.0) * 0.8 + inner * (b / 255.0) * 0.5
    glow[:, :, 1] = outer * (g / 255.0) * 0.8 + inner * (g / 255.0) * 0.5
    glow[:, :, 2] = outer * (r / 255.0) * 0.8 + inner * (r / 255.0) * 0.5

    core = cv2.GaussianBlur(_mask, (0, 0), sigmaX=1.2, sigmaY=1.2)
    glow[:, :, 0] = np.clip(glow[:, :, 0] + core * 1.8, 0, 255)
    glow[:, :, 1] = np.clip(glow[:, :, 1] + core * 1.8, 0, 255)
    glow[:, :, 2] = np.clip(glow[:, :, 2] + core * 1.6, 0, 255)
    return glow.astype(np.uint8)


def draw(frame, fingertip, mood, drawing_active=True, erase=False):
    global _glow_cache, _smooth, _draw_prev, _glow_dirty, _last_glow_mood

    if _mask is None:
        init_canvas(frame.shape[0], frame.shape[1])

    color = MOOD_COLORS.get(mood, (200, 255, 255))

    if fingertip is not None and drawing_active:
        x, y = fingertip
        if _smooth is None:
            _smooth = [float(x), float(y)]
        else:
            _smooth[0] = 0.38 * x + 0.62 * _smooth[0]
            _smooth[1] = 0.38 * y + 0.62 * _smooth[1]

        cx, cy = int(_smooth[0]), int(_smooth[1])
        if _draw_prev is not None:
            _draw_segment(_draw_prev, (cx, cy), erase=erase)
        _draw_prev = (cx, cy)
    elif not drawing_active:
        _reset_stroke()

    # Rebuild glow when strokes added or mood color changes
    need_glow = _glow_dirty or mood != _last_glow_mood
    if _mask is not None and _mask.max() > 0 and (_glow_cache is None or _glow_cache.max() == 0):
        need_glow = True
    if need_glow:
        _glow_cache = _build_glow(color)
        _glow_dirty = False
        _last_glow_mood = mood


    dimmed = cv2.addWeighted(frame, 0.5, np.zeros_like(frame), 0.5, 0)
    bf = dimmed.astype(np.float32)
    gf = _glow_cache.astype(np.float32) * 0.95
    return np.clip(bf + gf - (bf * gf / 255.0), 0, 255).astype(np.uint8)


def clear_canvas():
    global _mask, _glow_cache, _glow_dirty, _last_glow_mood
    if _mask is not None:
        _mask[:] = 0
    if _glow_cache is not None:
        _glow_cache[:] = 0
    _glow_dirty = True
    _last_glow_mood = None
    _reset_stroke()
