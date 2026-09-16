# b20260901-a-generator-writes-the-hosts-path-separator regression — a markdown link target is
#
# spelled with `/` on every operating system, and a generator that formats a `Path` publishes the
# host's answer instead. Two did. `workspace_meta.interface_for` wrote `](auth\gauth.pyi)` into a
# TRACKED CONTEXT.md the moment any routing table was regenerated on Windows, and `render_command`
# rebased command links with `os.path.relpath`, shipping 16 dead links across 5 files since the day
# it was written. Both were fixed with `as_posix()` where they were found; neither was found by a
# check. The class stayed open because nothing asserts that the next generator knows the rule.
#
# THE ASSERTION LIVES IN test_pointer_integrity.check_separators, NOT HERE. That module already
# owns the corpus walk and the definition of a link; a second copy of either is the drift the
# duplication gate exists to refuse. This file is the proof the rule holds, in both directions.
from test_pointer_integrity import check_separators


def _context(tmp_path, body):
    (tmp_path / "CONTEXT.md").write_text(body, encoding="utf-8", newline="\n")
    return check_separators(tmp_path, tmp_path / "no-memory-here")


def test_a_backslash_in_a_link_target_is_a_finding(tmp_path):
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth/gauth.pyi").write_text("stub\n", encoding="utf-8", newline="\n")
    failures = _context(tmp_path, "| [`gauth.py`](auth\\gauth.pyi) | interface |\n")
    assert len(failures) == 1
    assert "auth\\gauth.pyi" in failures[0]
    assert "as_posix" in failures[0], "a gate that blocks names the fix"


def test_the_generated_block_is_read_rather_than_stripped(tmp_path):
    """The routing block is where a generator writes, so a check blind to it is blind to the bug.

    check_pointers deliberately skips this block — staleness inside it is the sync tool's bug, not
    a hand-authored one. Reusing that filter here would have made this check pass on the exact
    file the bug was found in.
    """
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth/gauth.pyi").write_text("stub\n", encoding="utf-8", newline="\n")
    failures = _context(tmp_path, "<!-- routing:start -->\n"
                                  "| [`gauth.py`](auth\\gauth.pyi) |\n"
                                  "<!-- routing:end -->\n")
    assert len(failures) == 1


def test_a_posix_target_is_clean(tmp_path):
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth/gauth.pyi").write_text("stub\n", encoding="utf-8", newline="\n")
    assert _context(tmp_path, "| [`gauth.py`](auth/gauth.pyi) |\n") == []


def test_the_whole_workspace_is_clean():
    """Not a ratchet: the corpus was swept when the two generators were fixed."""
    from conftest import WORKSPACE_ROOT
    from test_pointer_integrity import MEMORY_DIR
    failures = check_separators(WORKSPACE_ROOT, MEMORY_DIR)
    assert not failures, "Host separators published into content:\n" + "\n".join(failures)
