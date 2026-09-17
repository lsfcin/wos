# b20260917 regression — the sync copied bytes and stopped: three ways the DESTINATION was left
# unfinished, each of which reported clean.
#
# `repo --check` said `0 difference(s)` for weeks while 34 pointers inside the target's generated
# blocks aimed at files the floor refuses — `core/CONTEXT.md` there routed to `core/experiments/`,
# a REFUSED tree. Not one verdict named any of it, because all three failures live in the half of
# the job that happens AFTER the copy, and nothing ran there: push() used --no-verify, so the
# target's own pipeline — generators, gates and its suite — never fired.
#
# The three are separable and each is checked on its own below.
import subprocess
import sys

from conftest import WORKSPACE_ROOT, floor_of

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/publish'))
import crossing  # noqa: E402


def test_a_tree_grants_eligibility(monkeypatch):
    """`eligible()` built its allow-list from roots and files and forgot `trees`.

    Invisible until 2026-09-17 because the only `tree` row sat inside `root core` and was made
    eligible by that. The first one written under an `absent` root — `tree code/_templates`, the
    project skeletons `core/flows/craft/architect.md` tells an agent to copy — granted nothing, and
    its contents simply never appeared in the target. No orphan, no ESCAPES, no verdict: a kind the
    floor documents as crossing has to reach that tuple or it is a row that does nothing.
    """
    floor = floor_of(trees=('code/_templates',), absent={'code': 'his projects'})
    monkeypatch.setattr(crossing, 'tracked',
                        lambda: ['code/_templates/SPECS.md', 'code/dobra/run.py'])
    assert crossing.eligible(floor) == {'code/_templates/SPECS.md'}, (
        'a `tree` under an `absent` root must let its contents through')


def test_the_real_floor_ships_the_templates_the_craft_flow_points_at():
    """The fixture above is the law; this is the floor as written obeying it."""
    crossed = crossing.report().crossing
    assert any(p.startswith('code/_templates/') for p in crossed), (
        'core/flows/craft/architect.md crosses and sends the reader to code/_templates/SPECS.md')


def test_every_escaping_kind_gets_a_gitignore_exception():
    """The target's .gitignore re-included `roots` under a refusal and nothing else.

    A refusal is written as `/<path>/*` plus one `!` per thing let back out, because git will not
    re-include a file whose parent is excluded. That exception list read `floor.roots` alone, so the
    first `file` let out of an absent tree — `code/CONTEXT.md` — stayed ignored IN THE TARGET.
    `_present()` asks the target's git what it holds, git did not mention it, and every single run
    recopied it as MISSING: an oscillation that no verdict called one, because MISSING is what a
    first copy looks like too. The check is on the generated text, which is the artifact that broke.
    """
    floor = crossing.floor()
    if not floor.target.is_dir():
        return   # a clone reads the same floor and has no target of its own checked out
    ignore = (floor.target / '.gitignore').read_text(encoding='utf-8')
    for path in floor.files + floor.trees:
        if not any(path.startswith(a + '/') for a in floor.absent):
            continue   # not under a refusal, so nothing has to re-include it
        escape = f'!/{path}/' if path in floor.trees else f'!/{path}'
        assert escape in ignore.splitlines(), (
            f'{path} escapes a refusal but the target ignores it, so the sync cannot see it land')


def test_the_target_regenerates_its_own_routing_rather_than_inheriting_ours():
    """The observable that says the destination finished: its tables describe ITS tree.

    Asserted on the two files that actually drifted. AGENTS.md is the sharp one — it is always
    loaded, so a stale block there is paid by every session in the clone — and `core/CONTEXT.md` is
    the one that pointed at a refused tree. Deliberately NOT a byte comparison against this side:
    the correct block differs between the two repos, which is exactly why repo's `_same()` ignores
    generated blocks, and why ignoring them is only honest while rebuild.py runs.
    """
    floor = crossing.floor()
    if not floor.target.is_dir():
        return   # nothing checked out to ask; the floor says so itself and `show` prints it
    agents = (floor.target / 'AGENTS.md').read_text(encoding='utf-8')
    assert '](code/CONTEXT.md)' in agents, (
        'the clone carries a project under code/ and must route to it')
    core_ctx = (floor.target / 'core/CONTEXT.md').read_text(encoding='utf-8')
    for refused in ('experiments/CONTEXT.md', 'prompts/CONTEXT.md'):
        assert refused not in core_ctx, f'the target routes to {refused}, which the floor refuses'


def test_the_target_commits_under_the_branch_gate_like_every_other_repo():
    """--no-verify is what made all three invisible, so its absence is the regression.

    gitflow_gate covers any repo under code/ and the target sits on a shared branch, so the bypass
    was bought to get past that one refusal — and took the whole pipeline with it. push() now
    branches instead. Read as text rather than run: the alternative is a test that pushes.

    COMMENTS ARE STRIPPED FIRST, and that is the point rather than tidiness: the prose right there
    explains the bypass it is forbidding, so a witness over raw text passes on the explanation and
    fails on the fix. ISSUES.md carries the same defect in test_features_wiring.py's name witness.
    """
    source = (WORKSPACE_ROOT / 'core/tools/wos/publish/repo').read_text(encoding='utf-8')
    body = source.split('def push(')[1]
    code = '\n'.join(ln for ln in body.splitlines() if not ln.lstrip().startswith('#'))
    assert '--no-verify' not in code, (
        'the sync must not bypass the target pipeline that is its only outside reader')
    assert 'feature/sync-' in code, 'it has to branch, which is what makes the gate passable'


def test_a_rebuilt_target_settles_in_one_pass():
    """Idempotence is the property the oscillation broke, and the cheapest one to state.

    Two syncs in a row: the second must find nothing. Runs the real tool against the real target
    because the bug was in the interaction between the copy, the generators and the target's git —
    three things no fixture reproduces. Skipped when the target is not checked out.
    """
    floor = crossing.floor()
    if not floor.target.is_dir():
        return
    tool = ['sh', str(WORKSPACE_ROOT / 'core/run'), 'tools/wos/publish/repo', '--sync']
    run = dict(cwd=WORKSPACE_ROOT, capture_output=True, text=True, encoding='utf-8', check=True)
    subprocess.run(tool, **run)
    second = subprocess.run(tool, **run)
    assert 'synced: 0 difference(s)' in second.stdout, (
        f'the sync does not settle:\n{second.stdout}')
