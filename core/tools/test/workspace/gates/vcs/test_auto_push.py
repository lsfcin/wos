# T0 the auto-push hook's diagnosis. core/hooks/post-commit is the only place most sessions ever
# learn that pushing failed, so what it names as the cause is the whole of what the operator knows.
#
# WHAT THIS PROVES AND WHAT IT DOES NOT. It reads the script, so it proves the three causes are
# written as three branches -- it does not prove each fires on the right condition, which needs a
# temp repo per cause and a credential state you cannot fake. Said plainly because a check that a
# name is present is the weaker kind, and this file is one. It exists because the defect it guards
# was invisible to every stronger check: the message was well-formed, confident, and wrong.
#
# The bug, 2026-08-28: an unauthenticated push does not fail fast, it blocks on a device-code prompt
# until `timeout 25` kills it, and every failure -- that one included -- printed "offline, or history
# diverged (force-push needed)". Two causes named, and on a fresh clone neither was the one.
from platform_law import AUTHORING_ROOT
from conftest import WORKSPACE_ROOT

HOOK = WORKSPACE_ROOT / 'core/hooks/commit/post_commit.py'


def _body() -> str:
    return HOOK.read_text(encoding='utf-8')


def test_the_failure_names_authentication_as_its_own_cause():
    body = _body()
    assert "'gh', 'auth', 'status'" in body, (
        'post-commit cannot tell an unauthenticated machine from an offline one, so the first '
        'push on a fresh clone is diagnosed as a network problem')
    assert 'not authenticated' in body


def test_the_three_causes_stay_three_branches():
    """Collapsing them is the original defect, so the shape itself is the assertion."""
    body = _body()
    assert body.count('auto-push failed') >= 2, 'the failure branch was collapsed back into one'
    assert 'diverged' in body, 'the diverged-history cause was dropped'


def test_the_operator_is_shown_what_git_actually_said():
    """The old hook sent stderr to /dev/null, so the one authoritative message was discarded
    before anybody could read it -- which is what left the hook guessing in the first place."""
    body = _body()
    assert 'capture_output=True' in body and '(done.stderr or done.stdout)' in body, \
        'the push output is being discarded again'


def test_the_hook_does_not_spawn_a_python_windows_does_not_have():
    """`python3` reaches a Store alias on Windows: it prints an advert, exits 9009, and the feature
    switch this hook reads is silently answered by the advert instead of by feature_law."""
    body = _body()
    assert 'python3 ' not in body, 'post-commit spawns bare python3 again; go through core/hooks/run'
    assert AUTHORING_ROOT.lstrip('/') not in body, 'post-commit hardcodes one machine path again'
