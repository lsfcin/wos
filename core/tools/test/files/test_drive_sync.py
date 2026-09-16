# T1 drive_sync: manifest config, cache with debounce, query diffing, and 4 pillars handling
import datetime
import json
import pathlib
import pytest

from conftest import WORKSPACE_ROOT
import drive_sync


def test_load_and_save_config(tmp_path):
    assert drive_sync.load_config(tmp_path) is None
    cfg = {"folder_id": "folder123", "account": "personal"}
    drive_sync.save_config(tmp_path, cfg)
    loaded = drive_sync.load_config(tmp_path)
    assert loaded == cfg


def test_load_and_save_cache(tmp_path):
    empty = drive_sync.load_cache(tmp_path)
    assert empty == {"last_checked": "", "files": {}}
    cache_data = {
        "last_checked": "2026-08-31T00:00:00Z",
        "last_sync": "2026-08-31T00:00:00Z",
        "files": {"file1": {"name": "doc1", "modifiedTime": "2026-08-30T10:00:00Z"}},
    }
    drive_sync.save_cache(tmp_path, cache_data)
    loaded = drive_sync.load_cache(tmp_path)
    assert loaded == cache_data


def test_debounce_is_active_within_ttl():
    now = datetime.datetime(2026, 8, 31, 12, 0, 0, tzinfo=datetime.timezone.utc)
    recent = (now - datetime.timedelta(seconds=120)).isoformat()
    old = (now - datetime.timedelta(seconds=350)).isoformat()

    assert drive_sync.is_debounce_active({"last_checked": recent}, ttl_seconds=300, now=now) is True
    assert drive_sync.is_debounce_active({"last_checked": old}, ttl_seconds=300, now=now) is False
    assert drive_sync.is_debounce_active({}, ttl_seconds=300, now=now) is False


def test_sync_directory_returns_error_without_config(tmp_path):
    res = drive_sync.sync_directory(tmp_path)
    assert "error" in res
    assert res["checked"] is False


def test_sync_directory_skips_when_debounce_active(tmp_path, monkeypatch):
    drive_sync.save_config(tmp_path, {"folder_id": "f123", "account": "personal"})
    recent = datetime.datetime.now(datetime.timezone.utc).isoformat()
    drive_sync.save_cache(tmp_path, {"last_checked": recent, "files": {}})

    res = drive_sync.sync_directory(tmp_path, force=False)
    assert res.get("skipped_debounce") is True
    assert res.get("checked") is False


def test_sync_directory_downloads_changed_items_and_updates_cache(tmp_path, monkeypatch):
    drive_sync.save_config(tmp_path, {"folder_id": "f123", "account": "personal"})

    fake_files = [
        {"id": "doc1", "name": "Ementa", "mimeType": drive_sync.MIME_GDOC, "modifiedTime": "2026-08-31T01:00:00Z"},
        {"id": "sheet1", "name": "Notas", "mimeType": drive_sync.MIME_GSHEET, "modifiedTime": "2026-08-31T01:05:00Z"},
    ]

    monkeypatch.setattr(drive_sync, "query_changed_files", lambda alias, folder_id, since_iso=None: fake_files)

    downloaded = []
    def fake_download(alias, file_id, dest_dir, export_as=None):
        out = dest_dir / (f"{file_id}.md" if export_as == "md" else f"{file_id}.xlsx")
        out.write_text("mock content", encoding="utf-8", newline='\n')
        downloaded.append((file_id, export_as))
        return out

    monkeypatch.setattr(drive_sync.drive_core, "download_file", fake_download)

    res = drive_sync.sync_directory(tmp_path, force=True)
    assert res.get("checked") is True
    assert set(res.get("updated")) == {"Ementa", "Notas"}
    assert len(downloaded) == 2

    # Check cache saved
    cache = drive_sync.load_cache(tmp_path)
    assert "doc1" in cache["files"]
    assert "sheet1" in cache["files"]
    assert cache["files"]["doc1"]["name"] == "Ementa"


def test_sync_file_item_routes_slide_previews(tmp_path, monkeypatch):
    slide_item = {"id": "deck1", "name": "Aula1", "mimeType": drive_sync.MIME_GSLIDE}

    preview_calls = []
    class FakeSlidesCore:
        @staticmethod
        def get_presentation(alias, fid):
            preview_calls.append(("get_presentation", alias, fid))
            return {"slides": [{"objectId": "s1"}, {"objectId": "s2"}]}

        @staticmethod
        def get_thumbnail_url(alias, fid, sid):
            preview_calls.append(("get_thumbnail", fid, sid))
            return f"https://thumb.test/{fid}/{sid}"

    import sys
    monkeypatch.setitem(sys.modules, "slides_core", FakeSlidesCore)

    url_retrieved = []
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlretrieve", lambda url, dest: url_retrieved.append((url, str(dest))))

    ret = drive_sync.sync_file_item("personal", slide_item, tmp_path, generate_previews=True)
    assert ret is None
    assert len(url_retrieved) == 2
    assert (tmp_path / "_material/previews/Aula1").is_dir()
