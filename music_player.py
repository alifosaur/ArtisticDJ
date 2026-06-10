# music_player.py

import os
import random
import tempfile
import threading
import glob
import queue

import yt_dlp
import pygame

try:
    import imageio_ffmpeg

    _FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
    os.environ["PATH"] = os.path.dirname(_FFMPEG) + os.pathsep + os.environ.get("PATH", "")
except ImportError:
    _FFMPEG = None
    print("[Music] Run: pip install imageio-ffmpeg")

from playlists import PLAYLISTS, MOOD_LABELS

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)

_playing_mood = None
_target_mood = None
_is_loading = False
_current_song_title = "Starting..."
_lock = threading.Lock()
_ready_queue = queue.Queue()
_cache = {}
_downloading_mood = None


def _set_title(title, loading=False):
    global _current_song_title, _is_loading
    with _lock:
        _current_song_title = title
        _is_loading = loading


def _get_playlist_song_urls(playlist_url):
    ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        if not info:
            return []
        entries = info.get("entries") or []
        urls = []
        for e in entries:
            if not e:
                continue
            vid = e.get("id") or e.get("url")
            if vid:
                urls.append(str(vid) if str(vid).startswith("http") else f"https://www.youtube.com/watch?v={vid}")
        if not urls and info.get("id"):
            urls.append(f"https://www.youtube.com/watch?v={info['id']}")
    return urls


def _download_audio_file(video_url):
    if not _FFMPEG:
        raise RuntimeError("pip install imageio-ffmpeg")

    out_base = os.path.join(tempfile.gettempdir(), f"aura_{random.randint(10000, 99999)}")
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "format": "bestaudio/best",
        "outtmpl": out_base + ".%(ext)s",
        "ffmpeg_location": _FFMPEG,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "128"}],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        title = info.get("title", "Unknown Song")
    files = glob.glob(out_base + ".*")
    if not files:
        raise RuntimeError("No audio file")
    return files[0], title


def _fetch_song(mood, playlist_url):
    global _downloading_mood
    label = MOOD_LABELS.get(mood, mood)

    try:
        urls = _get_playlist_song_urls(playlist_url)
        if not urls:
            if _target_mood == mood:
                _set_title(f"No songs for {label}", loading=False)
            return

        random.shuffle(urls)
        for url in urls[:6]:
            if _target_mood != mood:
                return
            try:
                print(f"[Music] Downloading {label}...")
                path, title = _download_audio_file(url)
                _cache[mood] = (path, title)
                _ready_queue.put((mood, path, title))
                print(f"[Music] Ready: {title}")
                return
            except Exception as e:
                print(f"[Music] Retry: {e}")

        if _target_mood == mood:
            _set_title(f"Could not load {label} music", loading=False)
    finally:
        with _lock:
            if _downloading_mood == mood:
                _downloading_mood = None


def _start_playback(path, title, mood):
    global _playing_mood
    pygame.mixer.music.stop()
    if hasattr(pygame.mixer.music, "unload"):
        pygame.mixer.music.unload()
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(0.85)
    pygame.mixer.music.play(-1)
    pygame.event.pump()
    _playing_mood = mood
    _set_title(title, loading=False)
    print(f"[Music] Now playing: {title}")


def tick():
    while True:
        try:
            mood, path, title = _ready_queue.get_nowait()
        except queue.Empty:
            pygame.event.pump()
            return

        if mood == _target_mood:
            try:
                _start_playback(path, title, mood)
            except Exception as e:
                _set_title(f"Play error: {e}", loading=False)


def _play_cached(mood):
    if mood not in _cache:
        return False
    path, title = _cache[mood]
    if not os.path.isfile(path):
        del _cache[mood]
        return False
    try:
        _start_playback(path, title, mood)
        return True
    except Exception as e:
        _set_title(f"Play error: {e}", loading=False)
        return False


def _ensure_download(mood):
    """Start background download if needed."""
    global _target_mood, _downloading_mood

    _target_mood = mood
    if mood in _cache:
        return

    with _lock:
        if _downloading_mood == mood:
            return
        _downloading_mood = mood

    label = MOOD_LABELS.get(mood, mood)
    _set_title(f"Loading {label} music...", loading=True)
    playlist = PLAYLISTS.get(mood, PLAYLISTS["neutral"])
    threading.Thread(target=_fetch_song, args=(mood, playlist), daemon=True).start()


def prepare_mood(mood):
    """Start downloading during the 10s countdown so music is ready on time."""
    _ensure_download(mood)


def play_for_mood(mood):
    """Play song for mood — keeps old song until new one is ready."""
    global _target_mood

    if mood == _playing_mood and is_playing():
        return

    print(f"[Music] Playing {MOOD_LABELS.get(mood, mood)} playlist")
    _target_mood = mood

    if _play_cached(mood):
        return

    _ensure_download(mood)


def preload(mood="neutral"):
    import time

    global _target_mood, _playing_mood
    _target_mood = mood
    _playing_mood = None

    if _play_cached(mood):
        return

    label = MOOD_LABELS.get(mood, mood)
    print(f"[Music] Loading {label} (first time may take 30 sec)...")
    _set_title(f"Loading {label}...", loading=True)

    global _downloading_mood
    with _lock:
        _downloading_mood = mood

    playlist = PLAYLISTS.get(mood, PLAYLISTS["neutral"])
    _fetch_song(mood, playlist)

    for _ in range(180):
        tick()
        if is_playing():
            return
        time.sleep(0.25)

    _set_title("Music failed — check internet", loading=False)


def preload_all_background():
    def worker():
        import time
        time.sleep(5)
        for mood in PLAYLISTS:
            if mood not in _cache:
                try:
                    urls = _get_playlist_song_urls(PLAYLISTS[mood])
                    if urls:
                        path, title = _download_audio_file(random.choice(urls[:5]))
                        _cache[mood] = (path, title)
                        print(f"[Music] Cached {mood}: {title[:50]}")
                except Exception as e:
                    print(f"[Music] Cache {mood}: {e}")

    threading.Thread(target=worker, daemon=True).start()


def get_current_song_title():
    with _lock:
        return _current_song_title


def is_loading():
    with _lock:
        return _is_loading


def is_playing():
    return pygame.mixer.music.get_busy()


def get_playing_mood():
    return _playing_mood


def stop():
    pygame.mixer.music.stop()
