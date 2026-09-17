# video_images.py — image-post path (Instagram carousels etc): gallery-dl metadata + image download, then OCR/VLM per image. yt-dlp reads video only and returns nothing for these.
import json, pathlib, shutil, subprocess, tempfile
from video_core import COOKIES

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_VENV_GDL = _ROOT / ".venv" / "bin" / "gallery-dl"
GALLERYDL = str(_VENV_GDL) if _VENV_GDL.exists() else (shutil.which("gallery-dl") or "gallery-dl")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES = 10


def _run(args, runner=None):
    runner = runner or (lambda a: subprocess.run(a, capture_output=True, text=True, timeout=300, encoding='utf-8'))
    cookies = ["--cookies", str(COOKIES)] if COOKIES.exists() else []
    return runner([GALLERYDL, *cookies, *args])


def _first_meta(data):
    """gallery-dl -j emits [kind, url, meta] rows; find the first row carrying a metadata dict."""
    for row in data if isinstance(data, list) else []:
        if isinstance(row, list) and row and isinstance(row[-1], dict):
            return row[-1]
    return {}


def metadata(url, runner=None):
    """L0 for image posts — description, uploader and image count from gallery-dl."""
    r = _run(["-j", url], runner)
    out = (getattr(r, "stdout", "") or "").strip()
    if not out:
        err = (getattr(r, "stderr", "") or "").strip().splitlines()
        return {"url": url, "ok": False,
                "error": err[-1] if err else "no image metadata — link may need login/cookies"}
    try:
        meta = _first_meta(json.loads(out))
    except ValueError:
        return {"url": url, "ok": False, "error": "gallery-dl returned unparseable metadata"}
    if not meta:
        return {"url": url, "ok": False, "error": "no images found at this link"}
    return {
        "url": url, "ok": True,
        "title": meta.get("post_shortcode") or meta.get("post_id"),
        "uploader": meta.get("fullname") or meta.get("username"),
        "description": meta.get("description") or "",
        "count": meta.get("count"),
    }


def download_images(url, runner=None, workdir=None):
    """Download every image in the post. Returns paths, capped at MAX_IMAGES."""
    tmp = pathlib.Path(workdir or tempfile.mkdtemp(prefix="video-img-"))
    _run(["-D", str(tmp), url], runner)
    paths = sorted(p for p in tmp.glob("*") if p.suffix.lower() in IMG_EXTS)
    return paths[:MAX_IMAGES]


def _join(parts):
    return "\n\n".join(p for p in parts if p).strip()


def _per_image(paths, fn):
    out = []
    for i, p in enumerate(paths, 1):
        text = fn(p)
        if text:
            out.append(f"[{i}/{len(paths)}] {text.strip()}")
    return "\n".join(out)


def gather(url, level="auto", _metadata=None, _media=None, _paths=None):
    """Full image-post extraction. Returns (meta, parts, methods) for video_core.assemble."""
    meta = (_metadata or metadata)(url)
    parts, methods = [], []
    if not meta.get("ok"):
        return meta, parts, methods
    if meta.get("description"):
        parts.append(meta["description"])
        methods.append("metadata")
    # A caption never stops the OCR on an image post: the slides ARE the content, and a caption
    # saying "swipe through to decode" reads as text found and hid ten slides of it for three
    # triages (2026-09-17). OCR is tesseract, local: ~0.6 s per image, zero tokens, so `auto`
    # always pays it. Only the VLM caption below still waits for OCR to come back empty.
    if level == "metadata":
        return meta, parts, methods

    paths = _paths if _paths is not None else download_images(url)
    if not paths:
        return meta, parts, methods
    media = _media or __import__("video_media")

    if level in ("auto", "ocr", "full"):
        screen = _per_image(paths, media.ocr_image)
        if screen:
            parts.append(screen)
            methods.append("ocr")

    if level in ("visual", "full") or (level == "auto" and not _join(parts)):
        caption = _per_image(paths, media.caption_image)
        if caption:
            parts.append(caption)
            methods.append("visual")

    return meta, parts, methods
