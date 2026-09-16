# video_media.py — heavy layers for the video tool: audio download + local transcription (L2), frame OCR (L3). Whisper model + tesseract langs are config data, not names.
import pathlib, subprocess, tempfile
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
    segments, _info = m.transcribe(str(audio_path), language=lang)
    return " ".join(s.text.strip() for s in segments).strip()


def ocr_image(img_path, lang="por+eng"):
    """L3 primitive — OCR one image; returns raw text."""
    import pytesseract
    from PIL import Image
    return pytesseract.image_to_string(Image.open(img_path), lang=lang).strip()


def sample_frames(video_path, n=5, workdir=None):
    tmp = pathlib.Path(workdir or tempfile.mkdtemp(prefix="video-f-"))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(video_path),
                    "-vf", "thumbnail", "-frames:v", str(n), str(tmp / "f-%03d.png")],
                   capture_output=True, timeout=180)
    return sorted(tmp.glob("f-*.png"))


def ocr_frames(video_path, n=5, lang="por+eng", workdir=None):
    """L3 — sample frames and OCR burned-in text, deduped across frames."""
    seen, lines = set(), []
    for fr in sample_frames(video_path, n, workdir):
        for ln in ocr_image(fr, lang).splitlines():
            ln = ln.strip()
            if ln and ln not in seen:
                seen.add(ln)
                lines.append(ln)
    return "\n".join(lines)


_VLM = {}


def _load_vlm(model_id):
    import torch
    from transformers import Qwen3VLForConditionalGeneration, AutoProcessor
    if model_id not in _VLM:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_id, dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map=device)
        proc = AutoProcessor.from_pretrained(model_id)
        _VLM[model_id] = (model, proc)
    return _VLM[model_id]


def caption_image(img_path, model_id="Qwen/Qwen3-VL-2B-Instruct", _vlm=None):
    """L4 primitive — caption one image with a local VLM (pure-visual content); returns one sentence."""
    from PIL import Image
    model, proc = _vlm or _load_vlm(model_id)
    messages = [{"role": "user", "content": [
        {"type": "image", "image": Image.open(img_path)},
        {"type": "text", "text": "Describe this image in one short sentence."},
    ]}]
    inputs = proc.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                       return_dict=True, return_tensors="pt").to(model.device)
    out = model.generate(**inputs, max_new_tokens=60)
    return proc.batch_decode(out[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True)[0].strip()


def caption_frames(video_path, n=5, model_id="Qwen/Qwen3-VL-2B-Instruct", workdir=None):
    """L4 — sample frames and caption pure-visual content (no speech/on-screen text), deduped across frames."""
    seen, lines = set(), []
    vlm = _load_vlm(model_id)
    for fr in sample_frames(video_path, n, workdir):
        cap = caption_image(fr, _vlm=vlm)
        if cap and cap not in seen:
            seen.add(cap)
            lines.append(cap)
    return "\n".join(lines)
