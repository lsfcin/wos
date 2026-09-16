#!/usr/bin/env python3
# WHEN it fires. The fourth law module: file_law.py says what a file IS, schema_law.py what a name
# MAY BE, feature_law.py which features are LIVE — this one says at which moment a live feature
# runs. Like the other three it reads its answer out of declared files rather than holding one.
#
# Why it exists (2026-08-18): the picture of this workspace had no machine-readable answer and used
# a 13-entry dict keyed on DIRECTORY CONVENTION instead, which every consumer had to label
# `inferred` — and which was wrong for the norms, filed under a generator directory and so reported
# as firing "on save" when a norm is loaded with AGENTS.md at every moment there is.
#
# The answer was already declared in three places, none of them written for this:
#   a harness settings file   registers a command against an event      -> registrations()
#   the git dispatcher        sources its stages in execution order      -> hook_reach.chain()
#   SETUP.md's install step   registers what must live outside the repo  -> _setup_moments()
# A feature none of the three can place is REPORTED, never guessed: moments_of returns source
# 'none', which the picture counts as a finding with a target of zero.
import json
import re
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]
for _dir in (HOOKS, HOOKS / 'entropy'):
    sys.path.insert(0, str(_dir))

import dispatch  # noqa: E402
import feature_law  # noqa: E402
import hook_reach  # noqa: E402
from entropy_corpus import tracked_files  # noqa: E402
from platform_law import rel as _rel  # noqa: E402
from schema_law import WORKSPACE_ROOT  # noqa: E402

# The canonical vocabulary, in the order a session runs it. OURS, not any harness's: each provider's
# event names are the translation table below, so the provider stays data and never becomes a name
# in the logic. `always in context` is not a step in the sequence — it is the band spanning all of
# them, which is what a norm's cost actually is.
MOMENTS = ['always in context', 'session start', 'every prompt', 'before read', 'after read',
           'before edit', 'after edit', 'before bash', 'subagent start', 'on compact',
           'pre-commit', 'post-commit']

EVENTS = {'SessionStart': ['session start'], 'UserPromptSubmit': ['every prompt'],
          'PreCompact': ['on compact'], 'SubagentStart': ['subagent start']}
TOOLS = {'Read': 'read', 'Grep': 'read', 'Edit': 'edit', 'Write': 'edit', 'NotebookEdit': 'edit',
         'Bash': 'bash'}
# Asked of the payload rather than of a tool name — gates.txt's first two columns. A gate's moment
# is its own (moment, capability), never the whole matcher its dispatcher was hung on. The `post`
# half arrived 2026-09-05 with the PostToolUse collapse (b20260905): before then the trackers were
# their own registrations and this module read their moment off a matcher naming Read.
CAPABILITY_MOMENTS = {('pre', 'shell'): 'before bash', ('pre', 'read'): 'before read',
                      ('pre', 'write'): 'before edit', ('post', 'read'): 'after read',
                      ('post', 'write'): 'after edit'}

# git dictates these two names (core.hooksPath — see CONTEXT.md), so they are entrypoints that no
# settings file registers and none ever will.
GIT_ENTRYPOINTS = {'core/hooks/pre-commit': ['pre-commit'],
                   'core/hooks/post-commit': ['post-commit']}
_WALKED: dict = {}   # one walk of the tree per root, not one per feature asked about


def _moments(event: str, matcher: str) -> list:
    """The canonical moments one registration lands on. ONE REGISTRATION MAY LAND ON SEVERAL: the
    context chain's matcher names Read and Edit, so it fires at two of them.

    A WILDCARD MATCHER LANDS ON ALL OF THEM, and reading it as none is what made this module go
    quiet. The matchers became `.*` on 2026-09-04 (b20260901, so a second shell tool could not walk
    past the read gates); `[A-Za-z]+` finds no tool name in `.*`, so every PreToolUse registration
    resolved to no moment at all and the `when` half of the feature registry blanked for 25 of the
    37 hook features — with nothing red, because an unplaced feature is only ever counted.
    """
    if event in EVENTS:
        return list(EVENTS[event])
    prefix = {'PreToolUse': 'before', 'PostToolUse': 'after'}.get(event)
    if not prefix:
        return []
    if 'Agent' in matcher:
        return ['subagent start']
    named = {TOOLS[t] for t in re.findall(r'[A-Za-z]+', matcher) if t in TOOLS}
    return sorted(f'{prefix} {tool}' for tool in (named or set(TOOLS.values())))


def ordered(moments) -> list:
    return [moment for moment in MOMENTS if moment in set(moments)]


def registrations(root: Path = WORKSPACE_ROOT) -> list:
    """[{command, matcher, moments, source}] — every hook registration DECLARED inside this repo.

    Which files those are is a RULE and not a list of `.claude` / `.opencode`: AGENTS.md's first
    structural claim is that a dotted top-level directory belongs to a harness, so its settings.json
    is where that harness declares what it runs. A list would go stale the day a provider is added.
    An unparseable one contributes nothing silently, which is safe only because the consequence
    surfaces per feature — anything left unplaced becomes source 'none' and is counted.
    """
    out = []
    files = sorted(p for p in tracked_files(root)
                   if p.name == 'settings.json' and p.relative_to(root).parts[0].startswith('.'))
    for path in files:
        try:
            hooks = json.loads(path.read_text(encoding='utf-8')).get('hooks', {})
        except (ValueError, OSError):
            continue
        for event, entries in sorted(hooks.items()):
            for entry in entries:
                matcher = entry.get('matcher', '')
                out += [{'command': hook.get('command', ''), 'matcher': matcher,
                         'moments': _moments(event, matcher),
                         'source': _rel(path, root)} for hook in entry.get('hooks', [])]
    return out


def _spread(rel: str, moments: list, seeds: dict, root: Path) -> dict:
    """A dispatcher's moments belong to the gates it dispatches, and gates.txt is where they are.

    core/hooks/dispatch.py names no gate in its own source — it reads them out of a data file — so
    the walk below cannot see the edge and would leave nine gates unplaced. This is the one edge
    declared in data rather than in code, which is why it is spelled here and not in hook_reach.

    EACH GATE TAKES ITS CAPABILITY'S MOMENT, not the dispatcher's whole matcher. The registration
    is `.*`, so inheriting it verbatim would say the heredoc gate fires before a read — true of the
    process, false of the gate, and the finer answer is sitting in the same row. Intersected with
    the dispatcher's own moments, so a harness that registers it on reads alone is believed.
    """
    if not rel.endswith('hooks/dispatch.py'):
        return seeds
    # PARSED BY THE DISPATCHER'S OWN READER, never re-split here. This function hand-split the table
    # until 2026-09-14, when a sixth column broke it and two other copies of the same loop at once.
    for (gate_moment, cap), gates in dispatch.load_table(root / 'core/hooks/gates.txt').items():
        moment = CAPABILITY_MOMENTS.get((gate_moment, cap))
        if moment not in moments:
            continue
        for path, _kind, _feature in gates:
            seeds.setdefault(f'core/hooks/{path}', []).append(moment)
    return seeds


def sites(root: Path = WORKSPACE_ROOT) -> dict:
    """{repo-relative path: [moments]} — every file a declared entrypoint reaches, and when."""
    if str(root) in _WALKED:
        return _WALKED[str(root)]
    seeds = {rel: list(moments) for rel, moments in GIT_ENTRYPOINTS.items()}
    for reg in registrations(root):
        for token in reg['command'].split():
            rel = hook_reach.target(token, root)
            if rel:
                seeds.setdefault(rel, []).extend(reg['moments'])
                seeds = _spread(rel, reg['moments'], seeds, root)
    # A DIRECT REGISTRATION OUTRANKS BEING NAMED BY SOMEBODY ELSE. Both are declarations, but one
    # says "run this here" and the other only says "this file knows that file exists", so a seed is
    # authoritative about itself and inherits nothing.
    reached = hook_reach.reaches(sorted(seeds), root)
    _WALKED[str(root)] = {rel: ordered(seeds[rel] if rel in seeds
                                       else [m for seed in owners for m in seeds[seed]])
                          for rel, owners in reached.items()}
    return _WALKED[str(root)]


def _setup_moments(name: str, root: Path) -> list:
    """The moment of a feature whose registration lives OUTSIDE this repo, by design.

    Not a fallback and not a defect: rtk-compaction is registered globally on purpose — Claude Code
    merges hook scopes and runs every match, so a project entry would run beside the global one
    instead of replacing it, and the global one also covers sessions opened inside a nested code/
    repo. SETUP.md carries that registration, so SETUP.md is where its moment is declared.
    """
    text = (root / 'SETUP.md').read_text(encoding='utf-8', errors='replace')
    moments: list = []
    for block in re.split(r'^> feature: ', text, flags=re.M)[1:]:
        if not block.startswith(f'`{name}`'):
            continue
        body = block.split('\n## ')[0]
        matcher = ' '.join(re.findall(r"'matcher':\s*'([^']+)'", body))
        for event in list(EVENTS) + ['PreToolUse', 'PostToolUse']:
            moments += _moments(event, matcher) if event in body else []
    return ordered(moments)


def moments_of(row: dict, root: Path = WORKSPACE_ROOT) -> tuple:
    """([moments], source) for one feature row. `source` names WHERE the moment is declared —
    registered | norms | setup | on-demand | none — and 'none' is a finding rather than a normal
    state, which is the whole difference between this module and the convention it replaced."""
    if 'norms' in feature_law.groups(row):
        return ['always in context'], 'norms'
    if row.get('runs') == 'on-demand':
        return [], 'on-demand'
    reached = sites(root)
    moments = ordered([m for path in feature_law.wired_paths(row) for m in reached.get(path, [])])
    if moments:
        return moments, 'registered'
    declared = _setup_moments(row['name'], root)
    return (declared, 'setup') if declared else ([], 'none')
