# test_inbox.py — free unit test: build_entry tags forwarded (non-Lucas) captures.
from frontend import inbox


def test_build_entry_typed_has_no_src_tag():
    entry = inbox.build_entry("oi", None)
    assert "[src:" not in entry
    assert entry.startswith("oi\n")


def test_build_entry_forwarded_is_tagged_telegram_fwd():
    entry = inbox.build_entry("oi", None, forwarded=True)
    lines = entry.splitlines()
    assert lines[0] == "[src: telegram-fwd]"
    assert lines[1] == "oi"


def test_build_entry_forwarded_tag_precedes_attachment():
    # Built from the root the code itself resolves, so this case says the same thing on a clone
    # that lives anywhere else — build_entry reports the attachment relative to that root.
    path = inbox.WORKSPACE_ROOT / "brain" / "attachments" / "2026-07" / "foo.jpg"
    entry = inbox.build_entry("photo caption", path, forwarded=True)
    lines = entry.splitlines()
    assert lines[0] == "[src: telegram-fwd]"
    assert lines[1] == "photo caption"
    assert lines[2] == "[attachment: brain/attachments/2026-07/foo.jpg]"
