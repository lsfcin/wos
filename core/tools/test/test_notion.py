# T1 notion: an id survives any form it is pasted in, and a failure hands back a runnable fix.
import os
import pathlib
import subprocess

import pytest

import notion_auth, notion_core, notion_outline
from platform_law import interpreter, is_owner_only

TOOLS_ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = TOOLS_ROOT.parents[1]
PAGE_ID = "1a2b3c4d5e6f7081920a1b2c3d4e5f60"
DASHED = "1a2b3c4d-5e6f-7081-920a-1b2c3d4e5f60"


def block(kind: str, text: str, **extra) -> dict:
    body = dict(extra) or {}
    body.setdefault("rich_text", [{"plain_text": text}])
    return {"id": f"blk-{kind}", "type": kind, kind: body}


def test_a_pasted_page_url_reduces_to_the_id_the_api_wants():
    """Lucas pastes a URL, never a uuid — the name's own dashes must not confuse the parse."""
    url = f"https://www.notion.so/lucas/Aula-3-Computacao-Grafica-{PAGE_ID}?pvs=4"
    assert notion_core.normalize_id(url) == DASHED
    # A copied block link carries a second id in the fragment; the page is still what was asked for.
    assert notion_core.normalize_id(f"https://www.notion.so/x-{PAGE_ID}#deadbeef") == DASHED


def test_an_id_in_either_spelling_lands_on_the_same_uuid():
    assert notion_core.normalize_id(PAGE_ID) == notion_core.normalize_id(DASHED) == DASHED


def test_text_carrying_no_id_is_refused_rather_than_guessed():
    with pytest.raises(ValueError):
        notion_core.normalize_id("the class page")


def test_the_outline_carries_the_block_ids_a_write_would_address():
    """Same contract as gslides read: reading hands back the handles for editing."""
    page = {"object": "page", "id": DASHED, "url": "https://notion.so/x",
            "properties": {"Name": {"type": "title", "title": [{"plain_text": "Aula 3"}]}}}
    text = notion_outline.outline(page, [block("heading_1", "Ementa")])
    assert "# Aula 3" in text
    assert "[blk-heading_1] # Ementa" in text


def test_nested_blocks_indent_under_the_block_that_owns_them():
    parent = block("toggle", "Referências")
    parent["children"] = [block("bulleted_list_item", "Foley & van Dam")]
    lines = notion_outline.outline({}, [parent]).splitlines()
    assert lines[-2].startswith("[blk-toggle] ▸")
    assert lines[-1].startswith("  [blk-bulleted_list_item] -")


def test_a_finished_todo_reads_as_finished():
    assert notion_outline.marker(block("to_do", "x", checked=True)) == "[x]"
    assert notion_outline.marker(block("to_do", "x", checked=False)) == "[ ]"


def test_an_unmapped_block_type_prints_what_it_is_instead_of_vanishing():
    """A silent drop would make the outline lie about the page; the type name is the honest fallback."""
    assert notion_outline.marker(block("breadcrumb", "")) == "breadcrumb"


def test_a_database_row_shows_the_properties_that_carry_its_meaning():
    row = {"object": "page", "id": DASHED, "properties": {
        "Name": {"type": "title", "title": [{"plain_text": "Aula 3"}]},
        "Status": {"type": "status", "status": {"name": "Publicado"}},
        "Data": {"type": "date", "date": {"start": "2026-08-20"}},
        "Empty": {"type": "select", "select": None}}}
    line = notion_outline.row_line(row)
    assert "Aula 3" in line and "Status=Publicado" in line and "Data=2026-08-20" in line
    assert "Empty" not in line, "an empty property is noise, not information"


def test_reading_a_page_does_not_drag_in_every_sub_page(monkeypatch):
    """child_page has children too; following them would fetch a second document unasked."""
    fetched = []

    def fake_paged(alias, method, path, body=None, limit=0):
        fetched.append(path)
        return [{"id": "sub", "type": "child_page", "has_children": True,
                 "child_page": {"title": "Aula 4"}}]

    monkeypatch.setattr(notion_core, "paged", fake_paged)
    notion_core.blocks("personal", PAGE_ID, depth=3)
    assert len(fetched) == 1, f"recursed into a sub-page: {fetched}"


def test_a_missing_token_names_the_one_command_that_stores_one(monkeypatch, tmp_path):
    monkeypatch.setattr(notion_auth, "config_dir", lambda: tmp_path)
    with pytest.raises(notion_auth.AuthMissing) as failure:
        notion_auth.load_token("personal")
    text = str(failure.value)
    assert "core/tools/notes/notion auth personal" in text
    assert notion_auth.INTEGRATIONS in text


def test_the_recovery_text_names_a_tool_that_exists(monkeypatch, tmp_path):
    """The instruction is only runnable while its path is real. Renames rot it silently."""
    monkeypatch.setattr(notion_auth, "config_dir", lambda: tmp_path)
    for text in (notion_auth.setup_text("personal"), notion_auth.revoked_text("personal"),
                 notion_auth.not_shared_text("personal", "the class page")):
        named = [word for line in text.splitlines() for word in line.split()
                 if word.startswith("core/tools/")]
        assert named, f"a recovery text with no command to run:\n{text}"
        for path in named:
            assert (WORKSPACE_ROOT / path).is_file(), f"recovery points at a missing tool: {path}"


def test_lucas_is_only_ever_asked_for_what_happens_inside_notion(monkeypatch, tmp_path):
    """His correction, 2026-08-14: a command the agent could run is not a chore to hand over.

    Minting a secret and connecting a page are Notion-side clicks nobody else can make. Storing
    the result is not — so no CLI path may appear above the AGENT line.
    """
    monkeypatch.setattr(notion_auth, "config_dir", lambda: tmp_path)
    for text in (notion_auth.setup_text("personal"), notion_auth.revoked_text("personal")):
        his_half, _, agents_half = text.partition("AGENT:")
        assert "core/tools/" not in his_half, f"handed Lucas a command to type:\n{his_half}"
        assert "core/tools/notes/notion auth personal" in agents_half


def test_the_secret_is_never_stored_through_a_command_argument(monkeypatch, tmp_path):
    """argv is readable by any process of this user, and survives in shell history."""
    monkeypatch.setattr(notion_auth, "config_dir", lambda: tmp_path)
    text = notion_auth.setup_text("personal")
    assert "printf" in text and "| core/tools/notes/notion auth" in text


def test_a_404_blames_the_connection_before_it_blames_the_id():
    """The usual cause by far — a message that starts at 'wrong id' sends Lucas the wrong way."""
    text = notion_auth.not_shared_text("personal", "the class page")
    assert "Connections" in text
    assert text.index("Connections") < text.index("the id is the problem")


def test_the_stored_secret_is_not_readable_by_anyone_else(monkeypatch, tmp_path):
    monkeypatch.setattr(notion_auth, "config_dir", lambda: tmp_path)
    path = notion_auth.save_token("personal", "ntn_secret")
    assert is_owner_only(path), "token file is readable by someone other than its owner"
    assert notion_auth.load_token("personal") == "ntn_secret"


def test_the_cli_routes_its_entrypoint_through_run(tmp_path):
    """Run the CLI and watch the wrapper actually get called.

    This replaced `"notion_core.run(main)" in cli.read_text()` on 2026-08-24. Bypassing
    run() would print a traceback and lose the instruction it carries, and a substring
    could not tell the call apart from the same characters in a comment. The recorder
    raises SystemExit(0) inside the wrapper, so no request is ever made.
    """
    shim = tmp_path / "shim"
    shim.mkdir()
    check = tmp_path / "check.txt"
    (shim / "sitecustomize.py").write_text(
        "import os, pathlib, sys\n"
        f"sys.path.insert(0, {str(TOOLS_ROOT / 'notes')!r})\n"
        "import notion_core\n"
        "def _rec(main_fn, *also):\n"
        "    pathlib.Path(os.environ['RUN_CHECK']).write_text('called')\n"
        "    raise SystemExit(0)\n"
        "notion_core.run = _rec\n", encoding="utf-8", newline='\n')
    subprocess.run([interpreter(), str(TOOLS_ROOT / "notes" / "notion")],
                   capture_output=True, text=True, timeout=60,
                   env={**os.environ, "PYTHONPATH": str(shim), "RUN_CHECK": str(check)}, encoding='utf-8')
    assert check.exists(), "the notion CLI never reaches notion_core.run"
