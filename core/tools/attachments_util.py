# attachments_util.py — shared filename/dir helpers for Core/tools attachment downloaders (gmail, telegram)
import pathlib, re
from datetime import datetime


def safe_name(filename: str) -> str:
    return re.sub(r"[^\w\-.]", "-", filename).lower()


def month_dir(base: pathlib.Path) -> pathlib.Path:
    d = base / datetime.now().strftime("%Y-%m")
    d.mkdir(parents=True, exist_ok=True)
    return d


def unique_path(base: pathlib.Path) -> pathlib.Path:
    if not base.exists():
        return base
    i = 1
    while True:
        candidate = base.parent / f"{base.stem}-{i}{base.suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def prune_old_attachments(base: pathlib.Path, max_days: int = 7) -> list[pathlib.Path]:
    """Remove raw media attachments older than max_days and clean empty subdirectories."""
    import time
    if not base.exists():
        return []
    cutoff = time.time() - (max_days * 86400)
    removed = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".ogg", ".jpg", ".jpeg", ".png", ".mp3", ".mp4", ".wav"}:
            if path.stat().st_mtime < cutoff:
                path.unlink()
                removed.append(path)
    for folder in sorted(base.glob("*/"), reverse=True):
        if folder.is_dir() and not any(folder.iterdir()):
            folder.rmdir()
    return removed
