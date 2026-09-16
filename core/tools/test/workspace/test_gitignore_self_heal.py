# T0 self-healing .gitignore allowlist check (core/hooks/SPECS.md): a new domain subdir with a
# CONTEXT.md must get its `!<domain>/<dir>/` allow line added automatically, no human action.
import subprocess
from pathlib import Path

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

SCRIPT = WORKSPACE_ROOT / "core/hooks/git" / "gitignore_heal.py"


def _make_fixture(tmp_path: Path) -> Path:
    (tmp_path / ".gitignore").write_text(
        "core/*\n!core/CONTEXT.md\n!core/tools/\n", encoding="utf-8"
    , newline='\n')
    (tmp_path / "core/hooks").mkdir(parents=True)
    (tmp_path / "core/hooks" / "gitignore-exceptions.txt").write_text(
        "core/excluded\n", encoding="utf-8"
    , newline='\n')
    (tmp_path / "core" / "tools").mkdir(parents=True)
    (tmp_path / "core" / "tools" / "CONTEXT.md").write_text("tools\n", encoding="utf-8", newline='\n')
    (tmp_path / "core" / "newdir").mkdir()
    (tmp_path / "core" / "newdir" / "CONTEXT.md").write_text("newdir\n", encoding="utf-8", newline='\n')
    (tmp_path / "core" / "scratch").mkdir()  # no CONTEXT.md — correctly ignored
    (tmp_path / "core" / "excluded").mkdir()
    (tmp_path / "core" / "excluded" / "CONTEXT.md").write_text("excluded\n", encoding="utf-8", newline='\n')
    (tmp_path / "core" / "ownrepo" / ".git").mkdir(parents=True)
    (tmp_path / "core" / "ownrepo" / "CONTEXT.md").write_text("ownrepo\n", encoding="utf-8", newline='\n')
    return tmp_path


def _run(tmp_path: Path) -> str:
    subprocess.run([interpreter(), str(SCRIPT), str(tmp_path)], check=True)
    return (tmp_path / ".gitignore").read_text(encoding="utf-8")


def _git(fixture: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(fixture), *args], capture_output=True, text=True, check=False
    , encoding='utf-8')


def _make_repo_fixture(tmp_path: Path) -> Path:
    """A fixture that is a real git repo, so the heal can see what staging missed."""
    fixture = _make_fixture(tmp_path)
    _git(fixture, "init", "-q")
    _git(fixture, "add", "-A")
    return fixture


def _heal(fixture: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [interpreter(), str(SCRIPT), str(fixture)], capture_output=True, text=True, check=False
    , encoding='utf-8')


def test_new_context_bearing_subdir_gets_allowlisted(tmp_path):
    gitignore = _run(_make_fixture(tmp_path))
    assert "!core/newdir/" in gitignore


def test_context_free_subdir_is_left_ignored(tmp_path):
    gitignore = _run(_make_fixture(tmp_path))
    assert "!core/scratch/" not in gitignore


def test_exception_listed_subdir_is_never_added(tmp_path):
    gitignore = _run(_make_fixture(tmp_path))
    assert "!core/excluded/" not in gitignore


def test_already_allowed_subdir_is_untouched(tmp_path):
    fixture = _make_fixture(tmp_path)
    before = (fixture / ".gitignore").read_text(encoding="utf-8")
    gitignore = _run(fixture)
    assert gitignore.count("!core/tools/") == before.count("!core/tools/") == 1


def test_running_twice_is_idempotent(tmp_path):
    fixture = _make_fixture(tmp_path)
    _run(fixture)
    gitignore = _run(fixture)
    assert gitignore.count("!core/newdir/") == 1


def test_healing_a_hidden_subdir_stops_the_commit(tmp_path):
    # The bug this closes: staging happens BEFORE this hook runs, so a directory healed here was
    # ignored at `git add` time and is not in the index. Committing anyway ships a CONTEXT.md
    # without the files it describes. Ruled 2026-08-19 (Lucas): heal, then fail loud.
    fixture = _make_repo_fixture(tmp_path)
    (fixture / "core" / "newdir" / "payload.txt").write_text("data\n", encoding="utf-8", newline='\n')
    result = _heal(fixture)
    assert result.returncode != 0, "a heal that hid files must stop the commit"
    assert "core/newdir" in result.stderr, "the message must name the directory"
    assert "!core/newdir/" in (fixture / ".gitignore").read_text(encoding="utf-8")


def test_the_stopped_commit_had_nothing_staged_behind_the_callers_back(tmp_path):
    # The rejected alternative was for the hook to `git add` the missing files itself so one
    # commit always sufficed. A commit hook that stages what the caller did not is worse than
    # the bug, so this asserts the index is untouched apart from .gitignore.
    fixture = _make_repo_fixture(tmp_path)
    (fixture / "core" / "newdir" / "payload.txt").write_text("data\n", encoding="utf-8", newline='\n')
    _heal(fixture)
    staged = _git(fixture, "diff", "--cached", "--name-only").stdout.split()
    assert not [p for p in staged if p.startswith("core/newdir")]


def test_rerunning_after_the_user_stages_lets_the_commit_through(tmp_path):
    fixture = _make_repo_fixture(tmp_path)
    (fixture / "core" / "newdir" / "payload.txt").write_text("data\n", encoding="utf-8", newline='\n')
    _heal(fixture)
    _git(fixture, "add", "core/newdir")
    assert _heal(fixture).returncode == 0


def test_a_heal_that_hides_nothing_does_not_stop_the_commit(tmp_path):
    # The heal and the stop are two decisions, not one: an allow line can be missing while the
    # files are already tracked (added with -f). Adding the line is still right; stopping the
    # commit is not, because nothing was hidden from it. Without this case the suite would pass
    # a version that failed on every heal.
    fixture = _make_repo_fixture(tmp_path)
    _git(fixture, "add", "-f", "core/newdir")  # tracked already, just missing its allow line
    result = _heal(fixture)
    assert result.returncode == 0, result.stderr
    assert "!core/newdir/" in (fixture / ".gitignore").read_text(encoding="utf-8")


def test_own_repo_subdir_is_never_touched(tmp_path):
    # A nested git repo is unreachable from the outer repo: git cannot track files inside it
    # without submodules, killed by the 2026-07-22 nested-gitlink-gate decision. Any allow line
    # tracks nothing and leaves a permanent `?? <dir>` in git status — which is what the first
    # version of this hook did to 13 code/ projects. Routing reads their CONTEXT.md off-disk.
    gitignore = _run(_make_fixture(tmp_path))
    assert "core/ownrepo" not in gitignore
