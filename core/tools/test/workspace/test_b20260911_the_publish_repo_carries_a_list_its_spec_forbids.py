# b20260911 regression — a repo the workspace PUBLISHES to keeps no findings of its own.
#
# core/tools/links/SPECS.md gives the reason the redirect clone is a target and not a project:
# "no ISSUES.md, no pre-commit, and `build` rebuilds it whole from links.txt". The pre-commit is
# global (core.hooksPath), so its list stage fired inside outputs/links anyway and shipped an
# ISSUES.md into a PUBLIC repo on every `cfpages build --push` — a file holding nothing but a
# zeroed entropy block about two generated files.
#
# The question is asked of the .gitignore the project map already reads, so nothing here holds a
# second list of repo names, and a repo becomes a project exactly when it is declared one.
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT, needs
from platform_law import rel

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy'))
from entropy_corpus import declared_projects  # noqa: E402


def test_the_redirect_clone_is_not_a_declared_project():
    """The property the fix leans on. If `outputs/links` ever gains a .gitignore project line, the
    list comes back and this case says so before the next push does."""
    assert 'outputs/links' not in declared_projects(WORKSPACE_ROOT)


def test_every_project_that_keeps_a_list_is_one_git_declares():
    """The other direction: the set is non-empty and names real project paths, so a parse rule that
    silently drifted to matching nothing would switch every nested list OFF unnoticed."""
    needs('PROJECTS.md')
    declared = declared_projects(WORKSPACE_ROOT)
    assert declared, 'no projects declared — the parse rule has drifted'
    assert any(name.startswith('code/') for name in declared), sorted(declared)
    assert not any(name.endswith('/') or '*' in name for name in declared), sorted(declared)


def test_the_parse_rule_has_exactly_one_copy():
    """Two readers held a byte-identical copy of this rule before 2026-09-11 — the close's map
    generator and this suite's own project-declaration case. A third was about to be written into
    the pre-commit, which is what made the duplication worth removing instead of extending."""
    # Spelled in halves so this file is not itself a copy of the rule it is counting.
    rule = 'not line.rstrip()' + ".endswith('/')"
    owners = [path for path in sorted(WORKSPACE_ROOT.glob('core/**/*.py'))
              if rule in path.read_text(encoding='utf-8', errors='replace')]
    assert owners == [WORKSPACE_ROOT / 'core/hooks/entropy/entropy_corpus.py'], \
        [rel(path, WORKSPACE_ROOT) for path in owners]


def test_the_list_stage_asks_before_it_writes():
    """The wiring itself. Read rather than run: the stage needs a real commit in a real repo, and
    what this case owns is that the guard is CALLED, not what it answers."""
    source = (WORKSPACE_ROOT / 'core/hooks/commit/generators.py').read_text(encoding='utf-8')
    body = source.partition('def issues(commit):')[2].partition('\ndef ')[0]
    assert '_keeps_a_list(commit)' in body, 'the list stage writes without asking whose repo'
    assert body.index('_keeps_a_list') < body.index('entropy-dashboard.py'), \
        'the guard runs after the scan, so the cost is paid before it is refused'


def test_the_spec_sentence_and_the_code_still_agree():
    """The issue offered two ways out — delete the file, or delete the sentence. The sentence is
    the half that was right, so it becomes load-bearing and this case is what makes it so."""
    spec = (WORKSPACE_ROOT / 'core/tools/links/SPECS.md').read_text(encoding='utf-8')
    assert 'no `ISSUES.md`' in spec, 'the spec no longer claims what the pre-commit now enforces'


def test_the_published_clone_carries_no_list():
    """The outcome, on this disk, when the clone happens to be here. Skipped rather than failed
    where it is not checked out — a machine without it must not read red for that reason."""
    clone = WORKSPACE_ROOT / 'outputs/links'
    if not (clone / '.git').exists():
        return
    assert not (clone / 'ISSUES.md').exists(), \
        'the redirect clone holds an ISSUES.md again — it is a target, not a project'
