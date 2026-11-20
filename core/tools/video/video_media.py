# video_media.py — heavy layers for the video tool: audio download + local transcription (L2), frame OCR (L3), frame description (L4). Whisper model + tesseract langs are config data, not names.
import pathlib, subprocess, tempfile
import describe
from video_core import _run

_MODELS = {}


def _load_model(name):
    from faster_whisper import WhisperModel
    if name not in _MODELS:
        _MODELS[name] = WhisperModel(name, device="cpu", compute_type="int8")
    return _MODELS[name]


def _download(url, fmt, prefix, runner=None):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix=prefix))
    _run(["-f", fmt, "-o", str(tmp / "m.%(ext)s"), url], runner)
    files = sorted((p for p in tmp.iterdir() if p.is_file() and p.stat().st_size > 0),
                   key=lambda p: p.stat().st_size, reverse=True)
    return files[0] if files else None


def download_audio(url, runner=None):
    return _download(url, "bestaudio/best", "video-a-", runner)


def download_video(url, runner=None):
    return _download(url, "mp4/best", "video-v-", runner)


def transcribe(audio_path, model="base", lang=None, _model=None):
    """L2 — local speech-to-text; returns joined transcript."""
    m = _model or _load_model(model)
    try:
        segments, _info = m.transcribe(str(audio_path), language=lang)
        return " ".join(s.text.strip() for s in segments).strip()
    except Exception:
        return ""


def ocr_image(img_path, lang="por+eng"):
    """L3 primitive — OCR one image; returns raw text. One OCR for every tool: core/tools/describe.py."""
    return describe.ocr(img_path, lang)


_FRAME_CACHE = {}


def _video_duration(video_path):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
                           capture_output=True, text=True, encoding='utf-8', timeout=30)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


def sample_frames(video_path, n=10, workdir=None):
    key = (str(video_path), n)
    if key in _FRAME_CACHE and workdir is None:
        frames = _FRAME_CACHE[key]
        if all(p.exists() for p in frames):
            return frames
    tmp = pathlib.Path(workdir or tempfile.mkdtemp(prefix="video-f-"))
    dur = _video_duration(video_path)
    if dur > 0:
        rate = n / dur
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video_path),
                        "-vf", f"fps={rate}", "-frames:v", str(n), str(tmp / "f-%03d.png")],
                       capture_output=True, timeout=180)
    else:
        subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video_path),
                        "-vf", "thumbnail", "-frames:v", str(n), str(tmp / "f-%03d.png")],
                       capture_output=True, timeout=180)
    frames = sorted(tmp.glob("f-*.png"))
    if workdir is None:
        _FRAME_CACHE[key] = frames
    return frames


def ocr_frames(video_path, n=10, lang="por+eng", workdir=None):
    """L3 — sample frames and OCR burned-in text, deduped across frames."""
    seen, lines = set(), []
    for fr in sample_frames(video_path, n, workdir):
        for ln in ocr_image(fr, lang).splitlines():
            ln = ln.strip()
            if ln and ln not in seen:
                seen.add(ln)
                lines.append(ln)
    return "\n".join(lines)


def caption_image(img_path, describer="agy"):
    """L4 primitive — describe one image (pure-visual content) through the shared describer, agy first.

    The local Qwen3-VL-2B this used to load scored 159/189 facts and invented a floor-plan legend in
    the 2026-09-25 bake-off (core/experiments/vlm-describe.md); Lucas moved video onto agy with pdf.
    """
    return describe.describe(img_path, describer, prompt=describe.FRAME_PROMPT).text


def caption_frames(video_path, n=10, describer="agy", workdir=None):
    """L4 — sample frames and describe pure-visual content (no speech/on-screen text), deduped across frames."""
    seen, lines = set(), []
    for fr in sample_frames(video_path, n, workdir):
        cap = caption_image(fr, describer)
        if cap and cap not in seen:
            seen.add(cap)
            lines.append(cap)
    return "\n".join(lines)
