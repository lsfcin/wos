# b20260905 regression — a declared subtree is carried by git, and a model named in a filename is
# attribution rather than a directive.
#
# ASYMMETRY ONE. brain/drafts/ had no CONTEXT.md, so it was absent from brain/CONTEXT.md's routing,
# so it never entered .gitignore's `brain/*` exception list. Six drafts existed on one disk and
# nowhere else, and nothing anywhere said so: `git status` cannot report a file it is ignoring, and
# the routing table cannot route to a directory it has never heard of. The two silences compound,
# which is why this went a month without being noticed by a workspace that checks almost everything.
# Ruled 2026-09-05 (Lucas): drafts becomes a real subtree.
#
# The class check below is the point rather than the one directory. `test_gitignore_self_heal.py`
# already proves the healer ADDS an allow line for a new CONTEXT.md-bearing subdir; what nothing
# checked is whether the tree it healed is actually the tree on disk. A healer that works and a
# subtree that was created before it ran are perfectly compatible, and that pair is this bug.
#
# A DRAFT LEAVES RATHER THAN ACCUMULATES. What survives is promoted to whatever owns it — a goal
# file, academy/teaching/SPECS-aulas.md, core/refs/REFS.md — and the draft is deleted, git being
# the history. A directory of drafts nobody promotes is a second list wearing a folder. This rule
# lives here rather than in the CONTEXT.md head because CONTEXT.md is the one enforced-read type
# and a contract in its head is a finding (core/SCHEMA.md § Placement); the head points here.
#
# ASYMMETRY TWO closes with a ruling and no code. The drafts carry `-sonnet`, `-opus`, `-gemini`
# in their filenames, and the question was whether the provider-agnostic norm needed a written
# exception for a comparative experiment. It does not, because the norm never banned the word:
# entropy_vendor.py's own head says the check "READS POSITION, NOT PRESENCE... A bare model name is
# legitimate as DATA and illegitimate as a DIRECTIVE." Comparing harnesses is something this
# workspace wants to support, and recording which one produced a document is what makes the
# comparison checkable. The last case pins that reading down, so a later session cannot quietly
# reinterpret the norm into a token ban and delete the experiment's own labels.
import subprocess

import pytest
from conftest import WORKSPACE_ROOT, needs
from platform_law import rel

BRAIN = WORKSPACE_ROOT / 'brain'
DRAFTS = BRAIN / 'drafts'


def tracked() -> set:
    done = subprocess.run(['git', 'ls-files'], cwd=WORKSPACE_ROOT,
                          capture_output=True, text=True, encoding='utf-8')
    return set(done.stdout.split('\n'))


def declared_subtrees() -> list:
    """Every directory under brain/ that declares itself with a CONTEXT.md."""
    return sorted(p.parent for p in BRAIN.glob('*/CONTEXT.md'))


def test_brain_declares_subtrees_at_all() -> None:
    """The floor. A glob that matched nothing would make every case below vacuously true."""
    needs('brain')
    assert len(declared_subtrees()) >= 3, [str(p) for p in declared_subtrees()]


@pytest.mark.parametrize('subtree', [p.name for p in declared_subtrees()])
def test_a_declared_brain_subtree_is_carried_by_git(subtree) -> None:
    """A CONTEXT.md is a claim that a directory is part of the workspace. If git does not carry it,
    the claim is false on every machine but this one, and no other check can see the difference."""
    carried = tracked()
    on_disk = sorted(p for p in (BRAIN / subtree).glob('*.md'))
    assert on_disk, f'brain/{subtree}/ declares itself and holds no .md at all'
    missing = [p.name for p in on_disk if rel(p) not in carried]
    assert not missing, (
        f'brain/{subtree}/ has a CONTEXT.md but git does not carry {missing}. The only copy is '
        f'this disk. Run core/run hooks/git/gitignore_heal.py, then git add the directory.')


def test_the_drafts_that_started_this_are_the_ones_now_carried() -> None:
    """Named rather than left to the class check: these six files were the exposure, and a class
    check that passed because the directory had been deleted would be the wrong kind of green."""
    needs('brain/drafts')
    carried = tracked()
    names = {p.name for p in DRAFTS.glob('*.md')}
    assert 'CONTEXT.md' in names, 'brain/drafts/ lost the declaration that tracks it'
    assert any(n.startswith('metodologia-aulas-') for n in names), 'the compared drafts are gone'
    assert 'brain/drafts/CONTEXT.md' in carried


def test_a_model_named_in_a_filename_is_not_what_the_vendor_check_forbids() -> None:
    """The ruling, made checkable. The norm bans a list assigning a MODEL where it should assign
    a level — a bolded `**model: …**` directive — not the word appearing as data. If this ever fails,
    someone has widened the check into a token ban, and the three-way comparison in brain/drafts/
    loses the labels that are its whole point."""
    import entropy_vendor
    assert entropy_vendor.DIRECTIVE.search('→ **model: opus** for the contract'), (
        'the vendor check no longer recognises the directive it exists to forbid')
    for legitimate in ('metodologia-aulas-sonnet.md',
                       'measured on `claude-opus-5` and on minimax-m3',
                       'the stale model id quoted in a bug was claude-opus-4-8'):
        assert not entropy_vendor.DIRECTIVE.search(legitimate), (
            f'the vendor check now fires on a model name used as DATA: {legitimate!r}')
