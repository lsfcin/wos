# T0 the feature registry's honesty half (core/SPECS.md § AD-14): a row claiming a switch must
# really have one, and throwing the switch must move the observable.
#
# WHY THIS IS A FILE OF ITS OWN. test_features.py answers "is the declaration complete and in its
# closed sets" — a question about data. These answer "does the declaration correspond to anything
# that runs" — a question about behaviour, and the one that costs the first ablation run its whole
# signal when it goes unasked. A row claiming to be wired while nothing reads the switch would make
# the ablation report "no effect" for a feature that was never disabled.
import functools
import json
import os
import subprocess
import sys

import feature_law as law
from conftest import WORKSPACE_ROOT
from platform_law import interpreter

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/skills'))
import mirror  # noqa: E402

@functools.cache
def _eligible() -> set:
    """What the floor lets cross, asked of the floor itself rather than restated here.

    REPLACED A SKIP on 2026-09-17. The guard used to be `if not carries(target): continue` — a
    switch in a tree this checkout lacks was called unanswerable, and the one row it covered was
    the Telegram bot, wired into code/aiwbot while `core/public.txt` refused all of code/. That
    made the strongest check in the registry silent for the row that needed it most: a switch the
    public clone cannot reach is a switch the ablation cannot throw, which is the failure
    core/SPECS.md § AD-14 exists to prevent. So it REFUSES now, and no row is exempt by geography.
    """
    sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/publish'))
    import crossing
    return crossing.eligible(crossing.floor())


SKILL_MIRROR = 'core/tools/wos/skills/mirror.py'
NORMS_GENERATOR = 'core/hooks/routing/norms.py'
TOOL_LAW = 'core/tools/tool_law.py'

# A whole group can share one publisher, and then no row can name itself there: the mirror
# cannot spell fourteen skill names and the generator cannot spell ten norm names. Those rows
# are held honest by a BEHAVIOURAL check instead — below for skills, test_norms.py for norms.
# `symmetry` passed the grep by accident, on the word "asymmetry" in a comment, which is the
# whole argument against a grep in one line.
GROUP_PUBLISHERS = {SKILL_MIRROR, NORMS_GENERATOR}


def _published_skills(off: str = '') -> set:
    """What the mirror would publish — the skills group's one observable.

    IMPORTED since the 2026-09-01 port; it used to source a shell fragment through `bash -c` with
    both paths spelled as POSIX text, and it cost 16 s of the suite because every one of the
    fifteen calls spawned bash plus a whole feature_law subprocess underneath it.

    The switch is still read from the ENVIRONMENT, so monkeypatching os.environ is what moves the
    observable — mirror.disabled() asks the law fresh on every call precisely so that works.
    """
    previous = os.environ.get(law.OFF_ENV)
    if off:
        os.environ[law.OFF_ENV] = off
    try:
        return set(mirror.list_skills(WORKSPACE_ROOT / 'core' / 'skills'))
    finally:
        if off:
            if previous is None:
                del os.environ[law.OFF_ENV]
            else:
                os.environ[law.OFF_ENV] = previous


def test_a_row_claiming_to_be_wired_really_is():
    """The honesty check: would turning this off change anything? Answered the strongest way each
    row allows, which is what lets a group share one wiring point. A group with an invocable boundary
    is switched off for real and its observable must move — which a guard on an unreachable branch
    cannot fake. A row owning its call site must name the name there.

    EVERY path is checked, not the first: a feature spanning layers names one file per layer, and
    `latex` is the case that forced it — a gate that calls a tool it has also switched off would
    read the tool's refusal as a violation and block the commit the switch meant to relax.
    """
    broken = []
    for row in law.load_registry():
        for target in law.wired_paths(row):
            path = WORKSPACE_ROOT / target
            if target not in _eligible():
                broken.append(f'{row["name"]}: {target} is outside core/public.txt, so the switch '
                              f'cannot be thrown where the ablation runs')
                continue
            if not path.exists():
                broken.append(f"{row['name']}: {target} does not exist")
            elif target not in GROUP_PUBLISHERS and row['name'] not in path.read_text(encoding='utf-8'):
                broken.append(f"{row['name']}: {target} never mentions the name")
    assert not broken, (
        'these rows claim to be switchable and are not:\n  ' + '\n  '.join(broken))

    group = {r['name'] for r in law.load_registry() if r['wired'] == SKILL_MIRROR}
    live = _published_skills()
    assert group <= live, (
        f'the mirror does not publish {sorted(group - live)}, so switching them off proves '
        f'nothing — the registry and core/skills/ disagree about what exists')
    for name in sorted(group):
        assert name not in _published_skills(off=name), (
            f'{name} is still published with {law.OFF_ENV}={name}: the row names {SKILL_MIRROR} '
            f'but the switch changes nothing there')


def test_an_unknown_name_fails_open():
    """A gate must never stop enforcing because someone mistyped a row."""
    assert law.is_enabled('no-such-feature-anywhere')


def test_the_ablation_switch_turns_one_feature_off(monkeypatch):
    """WOS_FEATURES_OFF is what the ablation drives; without it there is nothing to measure."""
    name = 'line-limit'
    assert law.is_enabled(name)
    monkeypatch.setenv(law.OFF_ENV, f'something-else,{name}')
    assert not law.is_enabled(name)
    assert law.is_enabled('caveman'), 'the switch must remove one feature, not all of them'


def _asks_the_law(hook: str, tmp_path) -> set:
    """Slugs the hook really asks about — recorded from a run, not read off the source.

    A sitecustomize wraps `feature_law.is_enabled` before the hook's own code loads, so the
    hook's law consultation lands in the log. The payload has to carry a command AND a
    file_path: several gates return early on an empty one and never reach their own switch,
    which reads identically to a gate that has no switch at all.
    """
    shim, log = tmp_path / 'shim', tmp_path / 'law.txt'
    shim.mkdir(parents=True)
    log.touch()
    (shim / 'sitecustomize.py').write_text(
        '# check: record every name a hook asks the law about, at runtime.\n'
        'import os, pathlib, sys\n'
        f'sys.path.insert(0, {str(WORKSPACE_ROOT / "core/hooks")!r})\n'
        'import feature_law\n'
        '_log, _orig = pathlib.Path(os.environ["LAW_CHECK"]), feature_law.is_enabled\n'
        'def _rec(name, *a, **k):\n'
        '    _log.open("a").write(name + "\\n")\n'
        '    return _orig(name, *a, **k)\n'
        'feature_law.is_enabled = _rec\n', encoding='utf-8', newline='\n')
    payload = json.dumps({'tool_name': 'Bash', 'session_id': 'law-check',
                          'cwd': str(WORKSPACE_ROOT),
                          'tool_input': {'command': 'ls', 'file_path': '/tmp/check.py',
                                         'content': '# check\n'}})
    subprocess.run([interpreter(), str(WORKSPACE_ROOT / hook)], input=payload, text=True,
                   capture_output=True, timeout=60,
                   env={**os.environ, 'PYTHONPATH': str(shim), 'LAW_CHECK': str(log)}, encoding='utf-8')
    return set(log.read_text(encoding='utf-8').split())


def _strip_comments(body: str, target: str) -> str:
    """Source with comment lines removed — `symmetry` passed on the word *asymmetry* in one."""
    marker = '//' if target.endswith('.js') else '#'
    return '\n'.join(line for line in body.splitlines()
                     if not line.lstrip().startswith(marker))


def test_the_wired_gates_actually_consult_the_law(tmp_path):
    """Both boundaries, end to end: a shell gate and a node hook reach the same law module.

    They are in different languages on purpose — the `--enabled` CLI arm is what lets a third
    harness wire a gate without a second implementation of the registry. A `core/tools`
    tool reaches the law through `tool_law`, which carries the sys.path hop; that hop is
    asserted itself, or the indirection becomes a place for the chain to go quietly dead.

    Rewritten 2026-08-24. It used to be `'feature_law' in body or 'tool_law' in body` — an OR
    of two common tokens matched anywhere, comments included, which is a weaker witness than
    the one that already passed on *asymmetry*. A standalone hook is now RUN and its law
    consultation observed; the rest (libraries, sourced shell fragments, node plugins) cannot
    be driven from a bare payload, so their source is read with comments stripped.
    """
    assert 'feature_law' in _strip_comments(
        (WORKSPACE_ROOT / TOOL_LAW).read_text(encoding='utf-8'), TOOL_LAW), (
        f'{TOOL_LAW} is the tools-layer hop and must reach feature_law itself')
    silent, ran = [], 0
    for row in law.load_registry():
        for target in law.wired_paths(row):
            if target not in _eligible():
                continue   # refused by the floor, and named as such by the case above
            body = (WORKSPACE_ROOT / target).read_text(encoding='utf-8')
            # A standalone hook ends by running main() on stdin; those we can observe.
            if target.endswith('.py') and 'sys.exit(main())' in body:
                ran += 1
                if row['name'] not in _asks_the_law(target, tmp_path / row['name'] / target):
                    silent.append(f"{row['name']}: {target} ran without asking the law")
            elif not ({'feature_law', 'tool_law'} & set(_strip_comments(body, target).split())
                      or 'feature_law' in _strip_comments(body, target)):
                silent.append(f"{row['name']}: {target} never reaches feature_law")
    assert not silent, 'these rows claim a switch nothing consults:\n  ' + '\n  '.join(silent)
    assert ran, 'no wired hook was observable — the classifier stopped matching anything'


def test_a_switched_off_tool_refuses_to_run():
    """A tool stops at invocation, with its own exit code.

    AD-14 files skills and tools together as the rows with nowhere to put a call. True of
    a skill — markdown, switched off only by the mirror declining to publish it. A tool is
    a CLI this workspace owns, so it has a moment of its own, and this check answers per row
    where a shared publisher answers once for the group. `OFF_EXIT` is asserted rather than
    "non-zero": every tool exits 1 on a real failure, so any-non-zero would pass on a broken one.
    """
    import tool_law
    checked = []
    for row in law.load_registry():
        for target in law.wired_paths(row):
            # Scoped by wiring point, not by group. `rtk-compaction` is wired to a hook, whose
            # observable is what it rewrites; the skills mirror is a sourced fragment checked
            # above. AD-14 exactly — the wiring point decides how a row is checked.
            if target == SKILL_MIRROR or not target.startswith('core/tools/'):
                continue
            out = subprocess.run([interpreter(), str(WORKSPACE_ROOT / target)], capture_output=True, text=True,
                                 cwd=WORKSPACE_ROOT,
                                 env={**os.environ, law.OFF_ENV: row['name']}, encoding='utf-8')
            assert out.returncode == tool_law.OFF_EXIT, (
                f"{row['name']}: exits {out.returncode} under {law.OFF_ENV}, so the switch does "
                f"not stop {target}")
            assert row['name'] in out.stderr, f'{row["name"]} stops without naming itself'
            checked.append(row['name'])
    assert checked, 'no tool is wired to an entrypoint yet — this check proves nothing'
