# test_video_images.py — T1 unit tests for the image-post path (no network, injected runners)
import json
import pytest
import video_images as vi
import video_core

META = {"post_shortcode": "AbC123", "fullname": "Someone", "username": "someone",
        "description": "a caption about normal maps", "count": 3}
DUMP = json.dumps([[3, "https://cdn/1.jpg", META], [3, "https://cdn/2.jpg", META]])


class FakeProc:
    def __init__(self, stdout="", stderr=""):
        self.stdout = stdout
        self.stderr = stderr


class FakeMedia:
    def __init__(self, screen="", caption=""):
        self.screen = screen
        self.caption = caption

    def ocr_image(self, path):
        return self.screen

    def caption_image(self, path):
        return self.caption


def test_metadata_parses_gallery_dl_dump():
    m = vi.metadata("u", runner=lambda a: FakeProc(stdout=DUMP))
    assert m["ok"]
    assert m["uploader"] == "Someone"
    assert m["description"] == "a caption about normal maps"
    assert m["count"] == 3


def test_metadata_empty_output_is_not_ok():
    m = vi.metadata("u", runner=lambda a: FakeProc(stderr="401 Unauthorized"))
    assert not m["ok"]
    assert "401" in m["error"]


def test_metadata_unparseable_output_no_crash():
    m = vi.metadata("u", runner=lambda a: FakeProc(stdout="not json"))
    assert not m["ok"]
    assert "unparseable" in m["error"]


def test_metadata_no_images_found():
    m = vi.metadata("u", runner=lambda a: FakeProc(stdout="[]"))
    assert not m["ok"]


def test_metadata_passes_cookies_when_present(monkeypatch, tmp_path):
    jar = tmp_path / "cookies.txt"
    jar.write_text("x", encoding='utf-8', newline='\n')
    monkeypatch.setattr(vi, "COOKIES", jar)
    seen = []
    vi.metadata("u", runner=lambda a: seen.append(a) or FakeProc(stdout=DUMP))
    assert "--cookies" in seen[0]


def test_download_images_filters_and_caps(tmp_path):
    for i in range(12):
        (tmp_path / f"{i:02d}.jpg").write_bytes(b"x")
    (tmp_path / "meta.json").write_text("{}", encoding='utf-8', newline='\n')
    paths = vi.download_images("u", runner=lambda a: FakeProc(), workdir=tmp_path)
    assert len(paths) == vi.MAX_IMAGES
    assert all(p.suffix == ".jpg" for p in paths)


def test_gather_stops_at_description_on_auto():
    meta, parts, methods = vi.gather(
        "u", _metadata=lambda u: dict(vi.metadata("u", runner=lambda a: FakeProc(stdout=DUMP))),
        _media=FakeMedia(screen="SHOULD NOT RUN"), _paths=[])
    assert methods == ["metadata"]
    assert parts == ["a caption about normal maps"]


def test_gather_ocrs_every_image_when_no_description(tmp_path):
    metadata = lambda u: {"url": u, "ok": True, "description": "", "uploader": "x"}
    meta, parts, methods = vi.gather(
        "u", _metadata=metadata, _media=FakeMedia(screen="on-screen text"),
        _paths=[tmp_path / "a.jpg", tmp_path / "b.jpg"])
    assert methods == ["ocr"]
    assert "[1/2] on-screen text" in parts[0]
    assert "[2/2] on-screen text" in parts[0]


def test_gather_escalates_to_vlm_when_ocr_empty(tmp_path):
    metadata = lambda u: {"url": u, "ok": True, "description": "", "uploader": "x"}
    meta, parts, methods = vi.gather(
        "u", _metadata=metadata, _media=FakeMedia(screen="", caption="a diagram"),
        _paths=[tmp_path / "a.jpg"])
    assert methods == ["visual"]
    assert "[1/1] a diagram" in parts[0]


def test_gather_returns_early_when_metadata_fails():
    metadata = lambda u: {"url": u, "ok": False, "error": "nope"}
    meta, parts, methods = vi.gather("u", _metadata=metadata, _media=FakeMedia())
    assert (parts, methods) == ([], [])


class FakeImages:
    def __init__(self, meta, parts, methods):
        self.args = (meta, parts, methods)

    def gather(self, url, level="auto"):
        return self.args


def test_assemble_falls_back_to_images_when_ytdlp_fails():
    failed = lambda u: {"url": u, "ok": False, "error": "no metadata"}
    imgs = FakeImages({"ok": True, "title": "AbC", "uploader": "Someone",
                       "description": "carousel caption"},
                      ["carousel caption"], ["metadata"])
    b = video_core.assemble("https://www.instagram.com/p/AbC/", _metadata=failed, _images=imgs)
    assert b["ok"]
    assert b["method"] == "metadata"
    assert b["text"] == "carousel caption"


def test_assemble_reports_video_error_when_images_also_fail():
    failed = lambda u: {"url": u, "ok": False, "error": "no metadata"}
    imgs = FakeImages({"ok": False, "error": "no images"}, [], [])
    b = video_core.assemble("https://x/y", _metadata=failed, _images=imgs)
    assert not b["ok"]
    assert b["error"] == "no metadata"
