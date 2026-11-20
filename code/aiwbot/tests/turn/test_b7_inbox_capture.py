# test_b7_inbox_capture.py — b7: a capture the bot confirmed must still be in the file.
import pathlib
import threading

import pytest

from frontend import inbox

HEAD = f"# inbox\n\n{inbox.INBOX_MARKER}\n"


@pytest.fixture
def capture_file(tmp_path, monkeypatch):
    """The real INBOX_FILE is a module constant pointing at the live workspace file."""
    path = tmp_path / "INBOX.md"
    path.write_text(HEAD, encoding="utf-8", newline="\n")
    monkeypatch.setattr(inbox, "INBOX_FILE", path)
    return path


def test_append_entry_refuses_when_another_writer_clobbers_it(capture_file, monkeypatch):
    """The b7 symptom itself: the bot answered "guardado em brain/INBOX.md" to eight messages on
    2026-09-20 and none of the eight was in the file 36 minutes later. append_entry returned
    because write_text returned — it never looked to see whether the entry was still there, so a
    process holding an older read of the same file won in silence. Returning normally here IS the
    bug: bot.py sends the confirmation on the next line.

    The file reads back without the entry — which is what a clobber looks like from here, and the
    only thing append_entry can actually observe about one."""
    monkeypatch.setattr(pathlib.Path, "read_text", lambda self, **kwargs: HEAD)
    with pytest.raises(inbox.CaptureLost):
        inbox.append_entry("uma captura que nunca aterrissou")


def test_every_concurrent_capture_lands(capture_file):
    """Eight queued updates drain at once when the bot reconnects, each in its own task, and
    append_entry rewrites the whole file. Each writer opens the file itself, so the lock has to be
    on the file rather than in the process — an asyncio lock would not have covered this."""
    bodies = [f"captura {i}" for i in range(8)]
    errors = []

    def capture(body):
        try:
            inbox.append_entry(body)
        except Exception as e:  # noqa: BLE001 — the assertion below names the failure
            errors.append(e)

    threads = [threading.Thread(target=capture, args=(b,)) for b in bodies]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []
    text = capture_file.read_text(encoding="utf-8")
    assert [b for b in bodies if b not in text] == []
