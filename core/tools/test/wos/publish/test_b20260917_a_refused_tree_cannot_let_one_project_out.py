# b20260917 regression — the floor's precedence: the longest prefix wins, both ways.
#
# core/public.txt said `absent code` and meant it flatly, so nothing under code/ could ever cross,
# whatever claimed it. That was right until one project under code/ WAS the workspace: `code/aiwbot`
# carries the `bot` feature's switch, and a switch the public clone cannot reach is a switch the
# ablation cannot throw (core/SPECS.md § AD-14). The alternative to precedence was a refusal per
# sibling — a list of everything NOT excepted, which rots the day a sibling is added.
#
# BOTH DIRECTIONS ARE THE SPEC. Loosening `absent` to let a root out is only safe while a deeper
# `absent` still beats a shallower `root`: that is what keeps `core/ROADMAP.md` and
# `core/experiments/` out of the public repo while all of `core/` is a root.
import sys

from conftest import WORKSPACE_ROOT, floor_of

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/tools/wos/publish'))
import crossing  # noqa: E402


def _eligible(tracked, floor, monkeypatch):
    monkeypatch.setattr(crossing, 'tracked', lambda: tracked)
    return crossing.eligible(floor)


def test_a_deeper_root_wins_over_a_shallower_absent(monkeypatch):
    floor = floor_of(roots=('code/aiwbot',), absent={'code': 'his projects'})
    live = _eligible(['code/aiwbot/frontend/bot.py', 'code/dobra/run.py'], floor, monkeypatch)
    assert live == {'code/aiwbot/frontend/bot.py'}, (
        'the named project crosses and its siblings stay refused')


def test_a_deeper_absent_still_wins_over_a_shallower_root(monkeypatch):
    floor = floor_of(roots=('core',), absent={'core/ROADMAP.md': 'his plan',
                                              'core/experiments': 'his measurements'})
    live = _eligible(['core/SCHEMA.md', 'core/ROADMAP.md', 'core/experiments/hook-latency.md'],
                     floor, monkeypatch)
    assert live == {'core/SCHEMA.md'}, 'a refusal inside a root is still a refusal'


def test_the_real_floor_answers_both_the_same_way():
    """The fixtures above are the law; this is the floor as written actually obeying it."""
    live = crossing.eligible(crossing.floor())
    assert 'code/aiwbot/frontend/inbox.py' in live, 'the bot switch has to be reachable publicly'
    assert not any(p.startswith('core/experiments/') or p == 'core/ROADMAP.md' for p in live), (
        'a refusal inside core/ must survive the precedence rule')
