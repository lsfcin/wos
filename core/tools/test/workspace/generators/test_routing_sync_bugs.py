# T0 routing-generator invariants (ROADMAP Batch B item 1): four ways the CONTEXT.md routing
# table used to corrupt itself. Each bug here was found by eye in a live file, never by a check.
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import WORKSPACE_ROOT

ROUTING = WORKSPACE_ROOT / "core/hooks/routing"
sys.path.insert(0, str(ROUTING))

from context_synchronizer import RE, RS, sync  # noqa: E402
from hoist import rebase_links, truncate_outside_links  # noqa: E402
from workspace_scanner import _strip_facade, build_sub_rows  # noqa: E402


# ── (a) a child's description is hoisted into the parent, links and all ────────────────

def test_relative_links_are_rebased_onto_the_child_directory() -> None:
    assert rebase_links("see [REFS.md](REFS.md)", "refs/") == "see [REFS.md](refs/REFS.md)"


@pytest.mark.parametrize("target", ["/abs/x.md", "#anchor", "https://x.dev", "mailto:a@b.c"])
def test_non_relative_targets_are_left_alone(target: str) -> None:
    text = f"see [x]({target})"
    assert rebase_links(text, "sub/") == text


def test_truncation_never_cuts_a_link_in_half() -> None:
    # A limit landing inside the link must drop the whole link, not leave `](RE`.
    text = "aaaa [REFS.md](REFS.md) bbbb"
    assert truncate_outside_links(text, 12) == "aaaa…"
    assert "](" not in truncate_outside_links(text, 12)


def test_truncation_never_cuts_a_word_in_half() -> None:
    """`the Level 0 checks t` read as a typo, not as a cut. Retreat to the last whole word
    and mark the cut, so the reader can tell truncation from a mistake."""
    assert truncate_outside_links("alpha beta gamma delta", 14) == "alpha beta…"


def test_a_cut_on_a_space_keeps_the_whole_last_word() -> None:
    """Retreating a word is for mid-word cuts only; a limit landing on the space between
    words has nothing to retreat from and must not eat a word that fitted."""
    assert truncate_outside_links("alpha beta gamma", 10) == "alpha beta…"


def test_text_within_the_limit_is_never_marked() -> None:
    assert truncate_outside_links("alpha beta", 40) == "alpha beta"


def test_hoisted_row_points_into_the_child(tmp_path: Path) -> None:
    sub = tmp_path / "refs"
    sub.mkdir()
    (sub / "CONTEXT.md").write_text(
        "# refs\n> Captured references — level-1 links in [REFS.md](REFS.md).\n", encoding="utf-8"
    , newline='\n')
    (sub / "REFS.md").write_text("# refs\n", encoding="utf-8", newline='\n')
    row = build_sub_rows([sub], {})
    assert "(refs/REFS.md)" in row
    assert "](REFS.md)" not in row


# ── (b) a directory that LOSES a file must re-sync ────────────────────────────────────

def test_delete_only_commit_still_runs_the_hook() -> None:
    """The dispatcher used to return early on an empty staged list, and a delete-only commit has
    exactly that — so nothing re-synced the table that just went stale."""
    body = (WORKSPACE_ROOT / "core/hooks/commit/pre_commit.py").read_text(encoding="utf-8")
    assert "--diff-filter=D" in body, "deletions are not collected by the dispatcher"
    assert "if not commit.staged and not commit.deleted:" in body, (
        "the early exit ignores deletions again — a delete-only commit skips every stage"
    )


def test_routing_generator_consumes_the_deleted_list() -> None:
    body = (WORKSPACE_ROOT / "core/hooks/commit/generators.py").read_text(encoding="utf-8")
    code = "\n".join(l for l in body.splitlines() if not l.lstrip().startswith("#"))
    assert "commit.deleted" in code


def test_subdir_rows_are_not_reported_as_removed_files(capsys, tmp_path: Path) -> None:
    """A healthy sync printed one "removed stale entry" per subdirectory — subdir rows are
    backticked, so they parsed as files. Noise on that line hides a real removal."""
    sub = tmp_path / "child"
    sub.mkdir()
    (sub / "CONTEXT.md").write_text("# child\n> a child\n", encoding="utf-8", newline='\n')
    (tmp_path / "CONTEXT.md").write_text(f"# d\n> d\n\n{RS}\n## Routing\n\n{RE}\n", encoding="utf-8", newline='\n')
    sync(tmp_path)
    capsys.readouterr()
    sync(tmp_path)
    assert "removed stale entry" not in capsys.readouterr().out


def test_stale_row_is_dropped_when_the_file_is_gone(tmp_path: Path) -> None:
    (tmp_path / "kept.py").write_text("# kept\n", encoding="utf-8", newline='\n')
    (tmp_path / "CONTEXT.md").write_text(
        f"# d\n> d\n\n{RS}\n## Routing\n\n| File | Description |\n|------|-------------|\n"
        f"| [`gone.py`](gone.py) | a file that was deleted |\n"
        f"| [`kept.py`](kept.py) | kept |\n{RE}\n",
        encoding="utf-8", newline='\n'
    )
    sync(tmp_path)
    out = (tmp_path / "CONTEXT.md").read_text(encoding="utf-8")
    assert "gone.py" not in out
    assert "kept.py" in out


# ── (c) a hand-written `## Routing` must be replaced, not doubled ─────────────────────

def test_unsentineled_routing_section_is_replaced_not_appended(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("# mod\n", encoding="utf-8", newline='\n')
    (tmp_path / "CONTEXT.md").write_text(
        "# d\n> d\n\n## Routing\n\n| File | Description |\n|------|-------------|\n"
        "| `hand.py` | hand-maintained, going stale |\n\n## Notes\n\nkeep me\n",
        encoding="utf-8", newline='\n'
    )
    sync(tmp_path)
    out = (tmp_path / "CONTEXT.md").read_text(encoding="utf-8")
    assert out.count("## Routing") == 1, "two Routing sections — which one is true?"
    assert "hand.py" not in out
    assert "keep me" in out, "content after the hand-written section was eaten"
    assert "mod.py" in out


# ── (d) the facade prefix is decoration, re-derived every run ─────────────────────────

def test_facade_prefix_never_accumulates() -> None:
    assert _strip_facade("**facade** — " * 22 + "x") == "x"
    assert _strip_facade("x") == "x"


def test_repeated_sync_is_idempotent_for_a_commentless_facade(tmp_path: Path) -> None:
    """`__init__.py` with no first-line comment: file_description() is empty, so the row
    falls back to the previous table cell — which already carried the prefix."""
    (tmp_path / "__init__.py").write_text("from x import y\n", encoding="utf-8", newline='\n')
    (tmp_path / "CONTEXT.md").write_text(f"# d\n> d\n\n{RS}\n## Routing\n\n{RE}\n", encoding="utf-8", newline='\n')
    for _ in range(5):
        sync(tmp_path)
    out = (tmp_path / "CONTEXT.md").read_text(encoding="utf-8")
    assert out.count("**facade** —") == 1, f"prefix accumulated:\n{out}"


def test_no_tracked_context_has_a_doubled_facade_prefix() -> None:
    files = subprocess.run(
        ["git", "ls-files", "-z", "*CONTEXT.md"],
        cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, encoding='utf-8'
    ).stdout
    offenders = [
        p for p in files.split("\0")
        if p and "**facade** — **facade** —" in (WORKSPACE_ROOT / p).read_text(encoding="utf-8")
    ]
    assert not offenders, f"facade prefix accumulated in: {offenders}"


def _routed(tool: str) -> bool:
    """Is this tool named in the nearest table above it? A family with its own CONTEXT.md spells
    the row by bare name; one that folded into its parent spells it by the path from there."""
    for directory in (WORKSPACE_ROOT / tool).parents:
        table = directory / "CONTEXT.md"
        if table.exists():
            row = Path(tool).relative_to(directory.relative_to(WORKSPACE_ROOT)).as_posix()
            return f"[`{row}`](" in table.read_text(encoding="utf-8")
    return False


def test_every_extensionless_tool_keeps_its_routing_row() -> None:
    """A tool that lost its shebang must not lose its row — the port's silent regression.

    `is_scanned` carried its own `_is_exec_script`: extensionless AND starts with `#!`. That
    is a second copy of a question `file_law.is_code_file` already answers, and when S5 taught
    the law module the shape rule (`is_tool_entrypoint`) because the port stripped the
    shebangs, this copy never heard. All 33 `core/tools` CLIs dropped out of their own routing
    tables, and the generator rewrote each table without them — so the loss left no diff to
    notice and no error to read. Found 2026-08-29 only because a merge added a *new* tool and
    its row vanished on save while a human was watching.

    Whole-tree, not a fixture: the fixture version passes against a scanner that reads the
    right law for the wrong reason. This asks the live tables.

    THE TABLE IS NOT ALWAYS THE TOOL'S OWN DIRECTORY (2026-09-15). This opened
    `<tool dir>/CONTEXT.md` alone, restating the opposite of core/tools/SPECS.md § Adding a tool:
    a one-tool family gets NO CONTEXT.md and folds into its parent's table. The first such family
    failed here with a FileNotFoundError on a tree the generator had laid out as specified.
    """
    tools = [
        p for p in subprocess.run(
            ["git", "ls-files", "-z", "core/tools/*"],
            cwd=WORKSPACE_ROOT, capture_output=True, text=True, check=True, encoding='utf-8'
        ).stdout.split("\0")
        if p and "." not in Path(p).name and "/test/" not in p
    ]
    assert tools, "found no extensionless core/tools CLI — the query is wrong, not the tree"
    missing = [p for p in tools if not _routed(p)]
    assert not missing, (
        f"these tools have no routing row: {missing}. `is_scanned` must ask "
        "file_law.is_code_file about an extensionless file, never re-derive it from a shebang")
