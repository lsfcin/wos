# drive_sync.py — Google Drive hybrid sync engine with debounce and manifest caching
import datetime
import json
import pathlib
import sys
from typing import Optional

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / "auth"))
sys.path.insert(0, str(_HERE.parent / "slides"))
sys.path.insert(0, str(_HERE.parents[1] / "hooks"))

import drive_core
import gauth
import platform_law

CONFIG_FILENAME = "drive_sync.json"
CACHE_FILENAME = ".drive-manifest-cache.json"
DEFAULT_TTL_SECONDS = 300  # 5 minutes

MIME_GDOC = "application/vnd.google-apps.document"
MIME_GSHEET = "application/vnd.google-apps.spreadsheet"
MIME_GSLIDE = "application/vnd.google-apps.presentation"
MIME_GFORM = "application/vnd.google-apps.form"


def load_config(dir_path: pathlib.Path) -> Optional[dict]:
    """Load the declarative sync config from drive_sync.json in dir_path."""
    cfg_file = dir_path / CONFIG_FILENAME
    if not cfg_file.is_file():
        return None
    try:
        return json.loads(cfg_file.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_config(dir_path: pathlib.Path, config: dict) -> None:
    """Save declarative sync config to drive_sync.json."""
    cfg_file = dir_path / CONFIG_FILENAME
    cfg_file.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline='\n')


def load_cache(dir_path: pathlib.Path) -> dict:
    """Load local sync cache (timestamps, known file hashes) from .drive-manifest-cache.json."""
    cache_file = dir_path / CACHE_FILENAME
    if not cache_file.is_file():
        return {"last_checked": "", "files": {}}
    try:
        return json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        return {"last_checked": "", "files": {}}


def save_cache(dir_path: pathlib.Path, cache: dict) -> None:
    """Save local sync cache to .drive-manifest-cache.json."""
    cache_file = dir_path / CACHE_FILENAME
    cache_file.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline='\n')


def is_debounce_active(cache: dict, ttl_seconds: int = DEFAULT_TTL_SECONDS, now: Optional[datetime.datetime] = None) -> bool:
    """Check if the cache was checked recently within ttl_seconds."""
    last_str = cache.get("last_checked")
    if not last_str:
        return False
    try:
        last_dt = datetime.datetime.fromisoformat(last_str.replace("Z", "+00:00"))
        curr = now or datetime.datetime.now(datetime.timezone.utc)
        if last_dt.tzinfo is None:
            last_dt = last_dt.replace(tzinfo=datetime.timezone.utc)
        elapsed = (curr - last_dt).total_seconds()
        return 0 <= elapsed < ttl_seconds
    except Exception:
        return False


def query_changed_files(alias: str, folder_id: str, since_iso: Optional[str] = None) -> list:
    """Query Drive API for files in folder_id modified since since_iso."""
    svc = drive_core.get_service(alias)
    q = f"'{folder_id}' in parents and trashed=false"
    if since_iso:
        q += f" and modifiedTime > '{since_iso}'"
    res = svc.files().list(
        q=q,
        pageSize=100,
        fields=f"files({drive_core.FILE_FIELDS})",
    ).execute()
    return res.get("files", [])


def sync_file_item(alias: str, file_meta: dict, target_dir: pathlib.Path, generate_previews: bool = True) -> Optional[pathlib.Path]:
    """Sync an individual Drive file according to the 4 pillars:
    - GDoc -> Markdown (.md)
    - GSheet -> Excel (.xlsx, preserving formulas & cells)
    - GSlide -> Download PDF or trigger preview PNGs
    - Other -> direct binary download
    """
    fid = file_meta["id"]
    mime = file_meta.get("mimeType", "")
    name = file_meta.get("name", fid)

    if mime == MIME_GDOC:
        return drive_core.download_file(alias, fid, target_dir, export_as="md")
    elif mime == MIME_GSHEET:
        return drive_core.download_file(alias, fid, target_dir)
    elif mime == MIME_GSLIDE:
        if generate_previews:
            previews_dir = target_dir / "_material" / "previews" / name
            try:
                import slides_core, urllib.request
                deck = slides_core.get_presentation(alias, fid)
                slides = deck.get("slides", [])
                previews_dir.mkdir(parents=True, exist_ok=True)
                for idx, s in enumerate(slides, 1):
                    sid = s["objectId"]
                    url = slides_core.get_thumbnail_url(alias, fid, sid)
                    if url:
                        dest = previews_dir / f"slide_{idx:02d}_{sid}.png"
                        urllib.request.urlretrieve(url, dest)
            except Exception as e:
                sys.stderr.write(f"[drive_sync] Warning generating preview for {name}: {e}\n")
        return None
    elif mime == MIME_GFORM:
        return None
    else:
        return drive_core.download_file(alias, fid, target_dir)


def sync_directory(
    dir_path: pathlib.Path,
    account: Optional[str] = None,
    force: bool = False,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> dict:
    """Orchestrate directory synchronization with debounce and manifest cache.
    Returns a dict with summary metrics: {'checked': bool, 'updated': list, 'skipped_debounce': bool}
    """
    dir_path = pathlib.Path(dir_path).resolve()
    config = load_config(dir_path)
    if not config:
        return {"error": f"No {CONFIG_FILENAME} found in {dir_path}", "checked": False}

    folder_id = config.get("folder_id")
    if not folder_id:
        return {"error": "Missing 'folder_id' in config", "checked": False}

    alias = gauth.resolve_alias(account or config.get("account", "personal"))
    cache = load_cache(dir_path)

    if not force and is_debounce_active(cache, ttl_seconds):
        return {
            "folder_id": folder_id,
            "account": alias,
            "checked": False,
            "skipped_debounce": True,
            "updated": [],
        }

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_iso = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    last_sync = cache.get("last_sync")
    try:
        files = query_changed_files(alias, folder_id, since_iso=last_sync if not force else None)
    except Exception as e:
        return {"error": str(e), "checked": False}

    updated_files = []
    file_cache = cache.get("files", {})

    for f in files:
        fid = f["id"]
        mod = f.get("modifiedTime", "")
        if fid in file_cache and file_cache[fid].get("modifiedTime") == mod and not force:
            continue

        saved_path = sync_file_item(alias, f, dir_path)
        file_cache[fid] = {
            "name": f.get("name"),
            "mimeType": f.get("mimeType"),
            "modifiedTime": mod,
            "local_path": platform_law.rel(saved_path, dir_path) if saved_path else "",
        }
        updated_files.append(f.get("name", fid))

    cache["last_checked"] = now_iso
    cache["last_sync"] = now_iso
    cache["files"] = file_cache
    save_cache(dir_path, cache)

    return {
        "folder_id": folder_id,
        "account": alias,
        "checked": True,
        "skipped_debounce": False,
        "updated": updated_files,
    }
