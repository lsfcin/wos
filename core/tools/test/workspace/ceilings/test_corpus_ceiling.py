# T0 corpus ceilings (core/SCHEMA.md § Placement): the .md corpus may not accumulate more of the three
# defects no link-checker can see. Zero-token, runs in verify-fast.
#
# These sit here rather than beside the checks they call because they assert something
# about the WHOLE TREE, not about one piece of machinery: test_entropy_list.py and
# test_entropy_context.py own whether each check fires correctly, this owns whether the
# backlog is shrinking. Same split as test_pointer_integrity.py beside it.
#
# The OS-port invariants were here too until 2026-08-29 and are now test_port_ceiling.py. Being
# whole-tree is what puts both in this directory; it is not what makes them one file. The shared
# `_git` moved to conftest.py as git_lines() rather than being copied.
#
# Every ceiling only ever goes down. Each is paired with a staleness test, because a ceiling
# nobody lowers is just a baseline, and a baseline is where drift hides.
#
# A ceiling per defect, never one shared ceiling: until 2026-08-15 the placeholder marker was
# counted as finished-work prose, and 70 markers could have masked 70 new ones without the
# number moving. One ceiling per thing the report names.
import entropy_context
import entropy_list
import entropy_naming
from conftest import WORKSPACE_ROOT
from file_law import load_limits

HEAD_WARN = load_limits()['CONTEXT_HEAD_WARN']

# Inherited backlog: finished work and trapped heads (core/SCHEMA.md § Placement) plus generator
# markers. The wos half of both queues is drained; what remains in both is nested-repo
# work, which cannot ride a wos commit — so these two stop falling here.
#
# The marker queue fell 69 → 55 on 2026-08-15 without a single file being described by hand:
# the generator learned to read a multi-line module docstring and the `core/hooks` data files
# (core/hooks/SPECS.md § The `CONTEXT.md` routing block). Markers answered by closing a
# generator gap are the cheapest kind, and they are indistinguishable here from ones answered
# by writing prose — which is the point.
FINISHED_CEILING = 0
UNDESCRIBED_CEILING = 3
MISPLACED_CEILING = 0  # drained 2026-09-06: the dashboard head was the last one

# Routing rows pointing at a file git does not carry — a clone gets the table and not the file.
# Nobody was counting these until 2026-08-31: test_pointer_integrity strips the routing block
# before it looks, and waives a gitignored target on the grounds that the prose cannot be edited
# to fix it. True, and the fix is in .gitignore instead — so it is reported here rather than
# silently allowed. Drained to 0 on 2026-09-01: six targets were allowlisted and four stopped
# being routed to, and workspace_scanner.carried now refuses to write the row at all, so this
# ceiling guards a generator rather than a backlog.
ROUTING_CEILING = 0

# The margin lets one cut land without forcing a test edit; a real drain pass trips it.
FINISHED_SLACK = 10
UNDESCRIBED_SLACK = 10
MISPLACED_SLACK = 5
ROUTING_SLACK = 5


def _files() -> list:
    return entropy_list.tracked_files(WORKSPACE_ROOT)


def _finished() -> int:
    return len(entropy_list.finished_work_hits(
        _files(), entropy_list.enforcement_paths(WORKSPACE_ROOT)))


def _undescribed() -> int:
    return len(entropy_list.unanswered_placeholders(
        _files(), entropy_list.enforcement_paths(WORKSPACE_ROOT)))


def _routing() -> int:
    return len(entropy_naming.untracked_routing_targets(_files(), WORKSPACE_ROOT))


def _misplaced() -> int:
    return sum(1 for path in _files()
               if entropy_context.check_misplaced_answer(path, HEAD_WARN))


def test_prose_describing_finished_work_does_not_grow():
    live = _finished()
    assert live <= FINISHED_CEILING, (
        f'{live} finished-work lines, up from {FINISHED_CEILING}. Cut the prose describing work that '
        f'landed, or rewrite it as present-tense state — ISSUES.md § Prose describing '
        f'finished work')


def test_unanswered_placeholders_do_not_grow():
    live = _undescribed()
    assert live <= UNDESCRIBED_CEILING, (
        f'{live} CONTEXT.md carrying an unanswered placeholder, up from '
        f'{UNDESCRIBED_CEILING}. Answer it at the source — the described file\'s '
        f'first-line comment — never by deleting the marker (core/hooks/SPECS.md)')


def test_routing_tables_pointing_at_untracked_files_do_not_grow():
    live = _routing()
    assert live <= ROUTING_CEILING, (
        f'{live} routing rows name a file this repo does not track, up from '
        f'{ROUTING_CEILING}. A clone gets the table and not the file — track the target, '
        f'or stop routing to it (ISSUES.md § Routing tables pointing at files git does '
        f'not carry)')


def test_constraints_in_context_heads_do_not_grow():
    live = _misplaced()
    assert live <= MISPLACED_CEILING, (
        f'{live} constrained heads, up from {MISPLACED_CEILING}. CONTEXT.md is the only '
        f'enforced-read type — move the contract to a sibling SPECS.md and leave one '
        f'pointer (core/SCHEMA.md § Placement)')


def test_the_ceilings_are_not_stale():
    finished, undescribed, misplaced = _finished(), _undescribed(), _misplaced()
    assert FINISHED_CEILING - finished <= FINISHED_SLACK, (
        f'finished-work is down to {finished} — lower FINISHED_CEILING to match, so the '
        f'ceiling keeps holding the new ground')
    assert UNDESCRIBED_CEILING - undescribed <= UNDESCRIBED_SLACK, (
        f'placeholders are down to {undescribed} — lower UNDESCRIBED_CEILING to match')
    assert MISPLACED_CEILING - misplaced <= MISPLACED_SLACK, (
        f'misplaced is down to {misplaced} — lower MISPLACED_CEILING to match')
    routing = _routing()
    assert ROUTING_CEILING - routing <= ROUTING_SLACK, (
        f'untracked routing targets are down to {routing} — lower ROUTING_CEILING to match')
