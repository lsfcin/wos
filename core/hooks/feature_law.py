#!/usr/bin/env python3
# What is switched ON: which features are live. The registry is core/features.txt, the answers are
# core/profile.txt, and neither is restated here.
#
# Why it exists (2026-08-16): the ablation bench ran once and produced no signal because no single
# feature could be turned off. Every gate that consults this module becomes measurable; every gate
# that does not is counted as a finding by `core/tools/wos/features --findings`.
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
# GUARDED, BECAUSE A MEASUREMENT MAY NEVER BREAK WHAT IT MEASURES. This module is copied into
# throwaway trees by the suite and reaches half-installed clones, where the recorder beside it may
# simply not be there — and an ImportError here would take down every gate in the workspace to save
# a row of statistics. Same rule core/run states for a clone that is missing pieces.
try:
    import scoreboard  # noqa: E402  — path is set above, which is the house pattern
except ImportError:  # pragma: no cover — only on a tree that carries feature_law without it
    scoreboard = None

CORE = HERE.parent
REGISTRY_FILE = CORE / 'features.txt'
PROFILE_FILE = CORE / 'profile.txt'
# THE ANSWERS ARE PER MACHINE; THE BASE IS NOT (2026-09-04). profile.txt is versioned and its head
# claimed to hold the answers "for THIS machine" — but two clones pull it, on two operating systems
# with genuinely different feature sets, so `features --on` on one landed on the other. This file is
# gitignored and overrides the base row by row, the same shape as .claude/settings.local.json. The
# base stays versioned because that is what keeps the general/Lucas-specific line a reviewable diff.
LOCAL_PROFILE_FILE = CORE / 'profile.local.txt'

# The closed sets the registry's columns may draw from. Kept here rather than in the data file for
# the same reason limits.env holds numbers and file_law.py holds the extension list: the values are
# data, the vocabulary is law.
#
# THE SIX ARE THE TREE'S OWN LAYERS (2026-08-17). The previous five named `capabilities`,
# `context-tree` and `brain`, none of which is a directory — every wired row in the latter two
# pointed into core/hooks/, so the header's claim that the groups "match the tree" died to `ls
# core/`. `norms` is the sixth and the only one without code: rules obeyed rather than enforced,
# the INDUCED half of the line whose ENFORCED half is file_law / schema_law / feature_law.
GROUPS = {'hooks', 'tools', 'skills', 'agents', 'flows', 'norms'}
# WHO STARTS IT, and it is NOT recoverable from ENFORCEMENT (2026-08-18). The registry carried one
# column where it had two facts, and `none` was doing duty for both "fires by itself and applies no
# pressure" and "you call it" — which misled a careful reader of its own data into reporting the
# capability half of this workspace as dead weight. Eleven rows cross: six are automatic and enforce
# nothing (rtk-compaction, subtree-read-tracking, precompact-wipe, brain-attention, opencode-plugin,
# caveman), five are on-demand and do push (the entropy scan's three checks, declared-deps, diagram).
# `automatic` rather than `passive`, `on-demand` rather than `active`: this registry's other job is
# saying which features are switched ON, so "an active feature" would be ambiguous at every site.
RUNS = {'automatic', 'on-demand'}
ENFORCEMENT = {'blocks', 'warns', 'generates', 'advises', 'none'}
SCOPES = {'general', 'lucas'}

# One ablation switch, and it only ever REMOVES. There is no WOS_FEATURES_ON, and the asymmetry is
# deliberate: an ablation run answers "what does this workspace cost without X", so it subtracts.
# A feature that should be on is turned on in the profile, where the choice is versioned and
# reviewable, rather than in an environment variable that vanishes with the shell.
OFF_ENV = 'WOS_FEATURES_OFF'


def _rows(path: Path) -> list:
    """Tab-separated, '#' comments dropped, first surviving line is the header.

    The same shape core/tools/deps.txt uses, parsed the same way, on purpose: three declaration
    files that a reader can open without learning a third format.
    """
    if not path.exists():
        return []
    lines = [ln.rstrip('\n') for ln in path.read_text(encoding='utf-8').splitlines()
             if ln.strip() and not ln.lstrip().startswith('#')]
    if not lines:
        return []
    header = lines[0].split('\t')
    return [dict(zip(header, ln.split('\t'))) for ln in lines[1:]]


def load_registry() -> list:
    """Every declared feature, in file order."""
    return _rows(REGISTRY_FILE)


def names() -> set:
    return {r['name'] for r in load_registry()}


def load_profile() -> dict:
    """The answers, split by kind: {'toggle': {name: 'on'|'off'}, 'setting': {key: value}}.

    The base first, this machine's overrides on top. Reading in that order is the whole merge —
    a local row answers one key and says nothing about the rest, so a machine declares only its
    departures and inherits every question it has no opinion about.
    """
    out: dict = {'toggle': {}, 'setting': {}}
    for row in _rows(PROFILE_FILE) + _rows(LOCAL_PROFILE_FILE):
        kind = row.get('kind', '')
        if kind in out:
            out[kind][row.get('key', '')] = row.get('value', '')
    return out


def _off_by_env() -> set:
    return {s.strip() for s in os.environ.get(OFF_ENV, '').split(',') if s.strip()}


def needs(row: dict) -> list:
    """The features this one cannot work without — the `needs` column, `-` meaning none."""
    return [n for n in row.get('needs', '-').split(',') if n and n != '-']


def _live(name: str, toggles: dict, off: set, rows: dict, seen: set) -> bool:
    """Switched on, and so is everything it needs. A cycle is not followed twice: `seen` answers on.

    A feature whose need is off is off itself (2026-09-26): pdf-twin-reads kept refusing PDFs on a
    clone with no `pdf` to make the twin, and blocked forever with nothing tracking the unlocking read.
    """
    if name in seen:
        return True
    if name in off or toggles.get(name, 'on') == 'off':
        return False
    return all(_live(n, toggles, off, rows, seen | {name}) for n in needs(rows.get(name, {})))


def is_enabled(name: str) -> bool:
    """Is this feature live right now?

    Fail-open on an unknown name, and that is the load-bearing choice: a gate must never stop
    enforcing because someone mistyped a row. A feature nobody declared behaves exactly as it did
    before this module existed, so wiring a gate can only ever be safe.
    """
    rows = {r['name']: r for r in load_registry()}
    live = _live(name, load_profile()['toggle'], _off_by_env(), rows, set())
    # THE ONE PLACE A FEATURE OF ANY GROUP CAN BE COUNTED. Every switched feature — hook, tool,
    # skill, flow, norm — passes through here, which is why the scoreboard hangs off this line
    # rather than off thirty call sites. Recorded only when live: a feature that is off did not
    # fire, it was skipped, and counting the skip would make an ablation run look busy.
    if live and scoreboard is not None:
        scoreboard.record(name, 'fired')
    return live


def setting(key: str, default: str = '') -> str:
    """A profile answer that is not a switch — the interaction language, and its kind."""
    return load_profile()['setting'].get(key, default)


def groups(row: dict) -> list:
    """The layers this feature is built from — one, or several joined by `+`.

    A feature is a layer or a COMBINATION of them: `caveman` is a skill plus a hook, `latex` is a
    pre-commit gate plus a tool family. Every part still names a directory, which is the property
    the group column exists to give and the old five-group set could not keep.
    """
    return [g for g in row.get('group', '').split('+') if g]


def is_wired(row: dict) -> bool:
    """Does this row have an in-process switch?

    `n/a` says one cannot exist — the .venv every hook runs on cannot disable itself and still
    leave a gate running to answer. Those rows are NOT findings and are NOT checked: they are
    ablated by building a clone variant without them, which is the harness's job and not this
    module's (core/SPECS.md § AD-14). Everything else either names a file or is a finding.
    """
    return row.get('wired', '-').split()[:1] not in ([], ['-'], ['n/a'])


def wired_paths(row: dict) -> list:
    """Every file that switches this feature off, in declaration order.

    Several when the feature spans layers, and the plural is load-bearing rather than tidy:
    `latex` is a pre-commit gate AND the tool family that gate calls, so a switch that stopped only
    the tool would leave the gate treating the tool's refusal as a violation and BLOCK the commit
    it was meant to relax. A row is honest only when every point that enforces it consults the law.
    """
    if not is_wired(row):
        return []
    return [p for p in (s.strip() for s in row['wired'].split(',')) if p]


def findings() -> list:
    """Rows with no switch and no reason: features that cannot be turned off at all.

    This is the audit, not a warning list. A feature entangled with this repo rather than
    sitting on it is invisible to an ablation, so the count is the number the ablation study has
    to drive down before it can measure anything (core/SPECS.md § AD-14). Its target is zero,
    which is only honest because `n/a` carries the rows where a switch cannot exist.
    """
    return [r for r in load_registry()
            if not is_wired(r) and r.get('wired', '-').split()[:1] != ['n/a']]


def disabled() -> list:
    """Every declared name that is currently off, in file order.

    The set form exists so a group dispatcher pays ONE subprocess instead of one per row: the
    skills mirror filters fourteen rows through a single call. Asking `--enabled` in a loop is the
    same answer at fourteen times the cost, and a loop over a hot path is how a switch acquires a
    reputation for being slow to consult.
    """
    return [r['name'] for r in load_registry() if not is_enabled(r['name'])]


def main() -> int:
    """`--enabled <name>` exits 0 when live, 1 when off — so a shell gate or a node hook shares
    this law instead of reimplementing it.
    `--disabled` prints the off names for a caller that filters a whole group at once."""
    if len(sys.argv) == 3 and sys.argv[1] == '--enabled':
        return 0 if is_enabled(sys.argv[2]) else 1
    if len(sys.argv) == 2 and sys.argv[1] == '--disabled':
        print('\n'.join(disabled()))
        return 0
    print('usage: feature_law.py --enabled <name> | --disabled', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
