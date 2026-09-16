# b20260911 regression — the close re-renders the permission config the session drifted.
#
# The harness appends an allow-entry to the gitignored .claude/settings.local.json for each newly
# approved command, so ANY session that approves something new leaves that rendered file
# disagreeing with core/profile.txt. The SessionStart heal then warns about it in every later
# session, and the warning reddened a mirror case that asserted the hook's line COUNT rather than
# the line it cared about. Per-session accretion into a rendered file wants a re-render, and the
# close is when the session's approvals are finally all in.
#
# What the renderer DOES is ../test_permissions.py's question. What this file owns is the wiring:
# the close asks before it writes, it reads the level rather than choosing one, and it reports.
# Ruled 2026-09-11 (Lucas). Reading the level from core/profile.txt — tracked, this clone's own
# answer — is what keeps this different from applying a level that ARRIVED over the network, the
# thing core/hooks/session/mirror-heal.py must never do.
import importlib.machinery as machinery
import importlib.util as importutil
import sys

from conftest import WORKSPACE_ROOT

CLOSE = WORKSPACE_ROOT / 'core/tools/wos/roundup'


def _close():
    """The close, loaded as a module. Extensionless, so it needs an explicit loader — the house
    pattern, and the same one ../test_permissions.py uses on the CLI beside it."""
    for folder in ('core/tools/wos/close', 'core/hooks', 'core/hooks/entropy', 'core/tools/verify'):
        path = str(WORKSPACE_ROOT / folder)
        if path not in sys.path:
            sys.path.insert(0, path)
    loader = machinery.SourceFileLoader('closetool', str(CLOSE))
    module = importutil.module_from_spec(importutil.spec_from_loader('closetool', loader))
    loader.exec_module(module)
    return module


def _body() -> str:
    source = CLOSE.read_text(encoding='utf-8')
    return source.partition('def permissions(root: Path) -> str:')[2].partition('\ndef ')[0]


def test_the_close_asks_whether_anything_drifted_before_it_writes():
    """Silent unless it acted — the property that separates a cure from a nag, and the one the
    mirror heal next door is built on. A close that speaks every session spends context every
    session on a line with no news in it."""
    body = _body()
    assert '--check' in body and '--set' in body, 'the close no longer drives the renderer'
    assert body.index('--check') < body.index('--set'), 'it writes before asking'
    assert "return ''" in body, 'nothing returns the silence a clean config earns'


def test_the_level_is_read_from_the_profile_and_never_chosen():
    """core/profile.txt is this clone's own tracked answer. The close restates it and decides
    nothing, which is why re-rendering here is not the same act as applying a level that arrived."""
    assert "feature_law.setting('permissions')" in _body(), 'the close picks a level of its own'


def test_a_missing_declaration_is_reported_and_not_guessed():
    """A profile with no answer must not fall back to a level. Offering `open` to a machine that
    never chose it is the failure the whole split exists to prevent."""
    body = _body()
    assert 'declared level missing' in body, 'an absent answer is silently substituted'


def test_the_cure_reaches_the_state_block():
    """WHICH lines the close prints is that file's business alone (core/SPECS.md § AD-09), so a
    cure nothing prints is one nobody can see stop working."""
    close = _close()
    assert 'permissions' in close.STATE


def test_it_runs_before_the_suite_does():
    """Ordering is the whole point: two cases assert what the SessionStart heal says, and a drifted
    config makes both red over nothing. Curing it after verify would fix next session's run only."""
    source = CLOSE.read_text(encoding='utf-8')
    main = source.partition('def main(argv: list) -> int:')[2]
    assert main.index('permissions(root)') < main.index('verify(root)'), \
        'the close verifies against the drift it is about to cure'
