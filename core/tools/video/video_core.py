# video_core.py — extract navigable text (metadata, captions, transcript) from video/image URLs; whisper/OCR backends are config data
import json, re, shutil, subprocess, pathlib
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))
from attachments_util import safe_name, month_dir, unique_path

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_VENV_YTDLP = _ROOT / ".venv" / "bin" / "yt-dlp"
YTDLP = str(_VENV_YTDLP) if _VENV_YTDLP.exists() else (shutil.which("yt-dlp") or "yt-dlp")
ATTACH = _ROOT / "brain" / "attachments"
COOKIES = pathlib.Path.home() / ".config" / "workspace-video" / "cookies.txt"

_TS = re.compile(r"^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->")
_TAG = re.compile(r"<[^>]+>")


def _cookie_args():
    return ["--cookies", str(COOKIES)] if COOKIES.exists() else []


def _run(args, runner=None):
    runner = runner or (lambda a: subprocess.run(a, capture_output=True, text=True, timeout=180, encoding='utf-8'))
    return runner([YTDLP, *_cookie_args(), *args])


def source_of(url):
    if "instagram.com" in url:
        return "instagram"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    return "web"


def metadata(url, runner=None):
    """L0 — metadata only, no download. Returns {ok, title, uploader, description, subs...}."""
    r = _run(["--dump-json", "--skip-download", url], runner)
    out = (getattr(r, "stdout", "") or "").strip()
    if not out:
        err = (getattr(r, "stderr", "") or "").strip().splitlines()
        return {"url": url, "ok": False,
                "error": err[-1] if err else "no metadata — link may need login/cookies"}
    d = json.loads(out.splitlines()[0])
    return {
        "url": url, "ok": True,
        "title": d.get("title"),
        "uploader": d.get("uploader") or d.get("channel"),
        "description": d.get("description") or "",
        "duration": d.get("duration"),
        "subtitles": sorted((d.get("subtitles") or {}).keys()),
        "auto_captions": sorted((d.get("automatic_captions") or {}).keys()),
    }


def clean_vtt(text):
    """Strip WEBVTT header, timestamps, cue tags, and consecutive duplicate lines."""
    lines = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln or ln == "WEBVTT" or ln.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if _TS.match(ln) or ln.isdigit():
            continue
        ln = _TAG.sub("", ln).strip()
        if ln and (not lines or lines[-1] != ln):
            lines.append(ln)
    return "\n".join(lines)


def get_captions(url, lang="en", runner=None, workdir=None):
    """L1 — download subtitles/auto-captions and return clean text, or None."""
    import tempfile
    tmp = pathlib.Path(workdir or tempfile.mkdtemp(prefix="video-"))
    _run(["--skip-download", "--write-auto-subs", "--write-subs",
          "--sub-langs", lang, "--sub-format", "vtt",
          "-o", str(tmp / "cap"), url], runner)
    vtts = sorted(tmp.glob("*.vtt"))
    if not vtts:
        return None
    return clean_vtt(vtts[0].read_text(encoding="utf-8", errors="replace")) or None


def _render(b):
    lines = [f"# {b.get('title') or b['source']}", "",
             f"- source: {b['source']}", f"- url: {b['url']}"]
    if b.get("uploader"):
        lines.append(f"- uploader: {b['uploader']}")
    lines += [f"- method: {b['method']}", "", "---", "",
              b.get("text") or "(no text extracted)"]
    return "\n".join(lines) + "\n"


def _save(bundle, base=None):
    d = month_dir(pathlib.Path(base) if base else ATTACH)
    stem = safe_name(f"{bundle['source']}-{bundle.get('title') or 'video'}")[:60] or "video"
    path = unique_path(d / f"{stem}.md")
    path.write_text(_render(bundle), encoding="utf-8", newline='\n')
    return str(path)


def _join(parts):
    return "\n\n".join(p for p in parts if p).strip()


def _bundle(url, meta, parts, methods, ok, save, base):
    b = {"url": url, "source": source_of(url), "ok": ok,
         "title": meta.get("title"), "uploader": meta.get("uploader"),
         "description": meta.get("description") or "",
         "text": _join(parts), "method": "+".join(methods) or "none"}
    if not ok:
        b["error"] = meta.get("error")
    if save:
        b["saved_path"] = _save(b, base)
    return b


def assemble(url, level="auto", save=False, base=None,
             _metadata=None, _captions=None, _media=None, _images=None):
    """Escalate L0->L1->L2->L3->L4, stopping once text is found (auto); explicit
    levels force a layer. Returns a text bundle."""
    meta = (_metadata or metadata)(url)
    ok = bool(meta.get("ok"))
    parts, methods = [], []

    # yt-dlp reads video only; an image post reads as a failure.
    # A mixed carousel (video slide 1 + images) reads ok from yt-dlp, but misses later slides.
    # For Instagram or failed video metadata, gather image slides through gallery-dl.
    images = _images or __import__("video_images")
    if not ok:
        imeta, iparts, imethods = images.gather(url, level=level)
        if imeta.get("ok"):
            return _bundle(url, imeta, iparts, imethods, True, save, base)
    elif source_of(url) == "instagram" and level in ("ocr", "visual", "full", "auto"):
        imeta, iparts, imethods = images.gather(url, level=level)
        if imeta.get("ok") and (imeta.get("count", 1) or 1) > 1:
            for p in iparts:
                if p not in parts:
                    parts.append(p)
            for m in imethods:
                if m not in methods:
                    methods.append(m)

    if meta.get("description"):
        parts.append(meta["description"])
        methods.append("metadata")

    def media():
        return _media or __import__("video_media")

    if ok and level in ("auto", "captions", "full") and (
            meta.get("subtitles") or meta.get("auto_captions")):
        caps = (_captions or get_captions)(url)
        if caps:
            parts.append(caps)
            methods.append("captions")

    if ok and (level in ("speech", "full") or (level == "auto" and not _join(parts))):
        audio = media().download_audio(url)
        spoken = media().transcribe(audio) if audio else ""
        if spoken:
            parts.append(spoken)
            methods.append("speech")

    video = None
    if ok and (level in ("ocr", "visual", "full") or (level == "auto" and not _join(parts))):
        video = media().download_video(url)

    if ok and (level in ("ocr", "full") or (level == "auto" and not _join(parts))):
        screen = media().ocr_frames(video) if video else ""
        if screen:
            parts.append(screen)
            methods.append("ocr")

    if ok and (level in ("visual", "full") or (level == "auto" and not _join(parts))):
        caption = media().caption_frames(video) if video else ""
        if caption:
            parts.append(caption)
            methods.append("visual")

    return _bundle(url, meta, parts, methods, ok, save, base)
