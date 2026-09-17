# T0 pointer-integrity check (Level 0): every relative
# ](path) link across CONTEXT.md / ROADMAP*.md / SCHEMA.md / AGENTS.md (repo) and
# MEMORY.md (auto-memory) must resolve. Zero-token, runs in verify-fast.
#
# [[name]] resolution is intentionally NOT gated here: the memory spec allows a
# dangling [[name]] as a "planned, not yet written" memory, and the corpus mixes
# kebab-case `name:` fields with underscore filenames as the link target, so there
# is no single rule to enforce yet. The entropy dashboard counts them instead.
import re
import subprocess
from pathlib import Path, PurePosixPath

from conftest import WORKSPACE_ROOT, carries  # the depth lives in one file, not nine
from entropy_corpus import LINK_RE  # one definition of what a link is, not two
from platform_law import rel

# The auto-memory store lives IN the workspace as of 2026-08-15; the harness path
# ~/.claude/projects/<name>/memory is a symlink to this directory, so every memory the
# harness writes lands in git and can be trimmed like any other file. This used to reach
# into $HOME and hardcode the project name — a Level 0 gate that read a path outside the
# repo it guards, and that no clone of this workspace could satisfy.
MEMORY_DIR = WORKSPACE_ROOT / "brain/memory"

# Deleted content still on disk is not workspace structure. A file manager moves a
# deleted project into .Trash-<uid>/, whose stale relative links then fail the check
# and block every commit until the trash is emptied — a gate nobody can fix by editing
# the workspace. Trash is excluded by prefix because the uid varies per machine.
EXCLUDE_DIRS = {".git", "node_modules", ".venv", "__pycache__", ".craft"}
EXCLUDE_PREFIXES = (".Trash",)
STRUCTURAL_NAME = re.compile(r"^(CONTEXT|SCHEMA|AGENTS|ROADMAP|ROADMAP-.*)\.md$")

FENCE_RE = re.compile(r"^\s*```")
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
ROUTING_BLOCK_RE = re.compile(
    r"<!-- routing:start -->.*?<!-- routing:end -->", re.DOTALL
)


def _strip_fences(text: str) -> str:
    out, in_fence = [], False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    text = "\n".join(out)
    # Auto-generated routing tables (AGENTS.md: "do not edit manually") hoist a
    # child CONTEXT.md's line-2 description verbatim, links and all; staleness
    # there is a sync-tool bug (dead pointer, or an unrewritten relative path
    # one level up), not a hand-authored one — out of scope for this Level-0 gate.
    text = ROUTING_BLOCK_RE.sub(" ", text)
    # Inline single-backtick spans quote literal syntax for documentation
    # (e.g. `` `[[name]]` `` describing the convention itself) — not real refs.
    return INLINE_CODE_RE.sub(" ", text)


def _structural_files(root: Path, memory_dir: Path):
    for path in root.rglob("*.md"):
        if any(part in EXCLUDE_DIRS or part.startswith(EXCLUDE_PREFIXES)
               for part in path.parts):
            continue
        if STRUCTURAL_NAME.match(path.name):
            yield path
    if memory_dir.is_dir():
        yield from memory_dir.glob("*.md")


def _deliberately_absent(root: Path, targets: list) -> set:
    """Of `targets`, those this repo declines to carry — asked of .gitignore, in one batch.

    A link into a gitignored path resolves on the machine that wrote it and on no clone, so it
    reads as broken everywhere else. That is not the defect this gate is for: it cannot be fixed
    by editing anything, and it made the check pass only for its author. Three links — into
    `academy/lab/`, `branches/casinhas/` and a gitignored `ROADMAP.md` — were red on this clone for
    exactly that reason. `git check-ignore` is the one authority on what the repo declines to carry.

    THE SECOND SOURCE IS THE TREE ITSELF (2026-09-17). This suite runs in two repos, and the public
    one is refused brain/, academy/, branches/ by `core/public.txt` — so `code/aiwbot`, which does
    cross, arrives there carrying four links into trees that were deliberately left behind. Same
    ruling as `conftest.needs()` (Lucas, 2026-09-16): a pointer into a tree this checkout does not
    carry is a question with no subject, not a broken pointer. Judged at the TOP SEGMENT and only
    for a target that names a directory, so a dead `SOMETHING.md` at the root still reports.
    """
    if not targets:
        return set()
    unbuilt = {t for t in targets if '/' in t and not carries(t)}
    # NUL-separated both ways. A newline-separated pipe is rewritten to CRLF by the text layer on
    # some systems, so git received the carriage return as part of each filename, matched nothing,
    # and quoted the odd name back — the answer looked like "none of these are ignored".
    done = subprocess.run(['git', '-C', str(root), 'check-ignore', '-z', '--stdin'],
                          input='\0'.join(targets), capture_output=True, text=True, encoding='utf-8')
    return unbuilt | {name for name in done.stdout.split('\0') if name}


def check_separators(root: Path, memory_dir: Path) -> list:
    """Link targets spelled with a backslash — the host's separator, published as content.

    A markdown separator is `/` on every operating system, and nothing checked that a generator
    knows it. Two did not: `workspace_meta.interface_for` formatted a `Path`, so regenerating any
    routing table on Windows wrote `](auth\\gauth.pyi)` into a TRACKED CONTEXT.md, and
    `render_command` rebased every command link with `os.path.relpath`, publishing 16 dead links
    across 5 files. Both were found by accident, because the machine that authored them spells the
    separator the way markdown wants and reads its own output as correct.

    THIS ONE READS RAW TEXT, unlike check_pointers. `_strip_fences` drops the routing block, and
    the routing block is exactly where a generator writes — stripping first would make the check
    blind to the case that motivated it.
    """
    failures = []
    for path in _structural_files(root, memory_dir):
        for link in LINK_RE.findall(path.read_text(encoding="utf-8")):
            if "\\" in link:
                failures.append(
                    f"{path}: link target spells the host's separator -> {link}\n"
                    f"   A markdown separator is `/` everywhere. If a generator wrote this,\n"
                    f"   fix it there with `as_posix()` — never by editing the table.")
    return failures


def check_pointers(root: Path, memory_dir: Path) -> list:
    """Return a list of human-readable broken-pointer messages (empty = clean)."""
    failures, missing = [], []
    for path in _structural_files(root, memory_dir):
        text = _strip_fences(path.read_text(encoding="utf-8"))
        for link in LINK_RE.findall(text):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            if "<" in link:  # template placeholder, e.g. brain/goals/<name>.md
                continue
            target = link.split("#", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                missing.append((path, link, resolved))
    ignored = _deliberately_absent(root, [rel(r, root) for _p, _l, r in missing])
    for path, link, resolved in missing:
        if rel(resolved, root) not in ignored:
            failures.append(f"{path}: broken link -> {link}")
    return failures


def test_pointer_integrity():
    failures = check_pointers(WORKSPACE_ROOT, MEMORY_DIR)
    assert not failures, "Pointer integrity broken:\n" + "\n".join(failures)


def test_dangling_relative_link_is_detected(tmp_path):
    # Regression fixture for the `../.vendor` dangling-link class of bug
    # (core/skills/caveman/scripts/CONTEXT.md, fixed f3d837f-era).
    sub = tmp_path / "scripts"
    sub.mkdir()
    (sub / "CONTEXT.md").write_text(
        "attribution in [`../.vendor`](../.vendor).\n", encoding="utf-8"
    , newline='\n')
    failures = check_pointers(tmp_path, tmp_path / "no-memory-here")
    assert len(failures) == 1
    assert "../.vendor" in failures[0]


def test_a_pointer_into_a_tree_this_checkout_lacks_is_not_broken(tmp_path):
    """b20260917 — the public clone carries code/aiwbot and not brain/, and the links between them.

    The second half is the point: an unbuilt TREE is silenced, a dead file at the root is not, or
    the gate would go quiet on exactly the typo it exists to catch."""
    (tmp_path / "CONTEXT.md").write_text(
        "goal [x](naoexiste-em-lugar-nenhum/goals/x.md) and [y](NAOEXISTE.md)\n",
        encoding="utf-8", newline='\n')
    failures = check_pointers(tmp_path, tmp_path / "no-memory-here")
    assert len(failures) == 1, failures
    assert "NAOEXISTE.md" in failures[0]


def test_clean_fixture_has_no_failures(tmp_path):
    (tmp_path / "target.md").write_text("target\n", encoding="utf-8", newline='\n')
    (tmp_path / "CONTEXT.md").write_text("see [target](target.md).\n", encoding="utf-8", newline='\n')
    assert check_pointers(tmp_path, tmp_path / "no-memory-here") == []


def test_no_committed_symlink_carries_an_absolute_path():
    """A symlink is committed by its TEXT, so an absolute one names this machine and no other.

    Found 2026-08-25: all 42 skill mirrors under .claude/, .opencode/ and .zcode/ read
    an absolute `core/skills/<name>.md`, so a student cloning anywhere else got 42 dangling
    links and no skills in any harness — while criterion 4, clonable by a student, read as met.
    Same class as a dangling `](path)`: a pointer that resolves only where it was written.

    READ FROM THE OBJECT, NEVER FROM THE CHECKOUT. This called `.readlink()` on the working tree,
    which answers a different question — what git materialised here — and on a clone with
    `core.symlinks=false` it does not answer at all: the entries are ordinary files and readlink
    raises (ISSUES.md B8). What is committed is the blob, and the blob IS the target text, so
    `cat-file` gives the same answer on every machine.
    """
    listing = subprocess.run(
        ["git", "-C", str(WORKSPACE_ROOT), "ls-files", "-s"],
        capture_output=True, text=True, check=True, encoding='utf-8').stdout
    absolute = []
    for line in listing.splitlines():
        mode, blob, _, path = line.split(maxsplit=3)
        if mode != "120000":
            continue
        target = subprocess.run(["git", "-C", str(WORKSPACE_ROOT), "cat-file", "blob", blob],
                                capture_output=True, text=True, check=True, encoding='utf-8').stdout.strip()
        if PurePosixPath(target).is_absolute():
            absolute.append(f"{path} -> {target}")
    assert not absolute, "Committed symlinks with an absolute target:\n" + "\n".join(absolute)
