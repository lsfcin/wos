#!/usr/bin/env python3
# The entropy dashboard. Runs every Level 0 check over ONE repo — this one, or the `--repo` named —
# and writes one generated report, so agents and Lucas read a pre-computed file instead of
# re-scanning the tree. Zero-token, no LLM.
#
# Division of labour with core/hooks/checks/type-gate.py: the gate is a ratchet and only blocks what
# a commit ADDS, which is why a repo that inherited violations is not blocked on every
# commit. Everything it lets through historically shows up here, once, with a count.
#
# Nothing here blocks. The cap that does lives in checks/size-gate.py; this file reports what the
# tree already carries, including the files a ratchet let through before the cap reached them.
# Crossing a threshold asks for a CUT, never for a summary — forced brevity is the trap, and
# core/SCHEMA.md § A type that outgrows the cap is cut says what a cut may
# not throw away.
import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# The checks are one level up in entropy/; the law (file_law, schema_law) is two, at the root of
# the enforcement layer; git/ holds the one check that reads git state instead of file content.
_ENTROPY = Path(__file__).resolve().parents[1]
for _dir in (_ENTROPY, _ENTROPY.parent, _ENTROPY.parent / 'git',
             _ENTROPY.parent / 'routing'):
    sys.path.insert(0, str(_dir))

import feature_law  # noqa: E402
from blocks import replace_block  # noqa: E402
from branch_debt import (merged_local_branches, merged_remote_branches,  # noqa: E402
                         unmerged_branches, unpushed_work)
from entropy_context import (check_goal_link,  # noqa: E402
                             check_misplaced_answer, check_truncation)
from entropy_corpus import (enforcement_paths, tracked_files,  # noqa: E402
                            wiki_exempt_paths)
from entropy_crowding import crowding_signals  # noqa: E402
from entropy_fields import field_hits  # noqa: E402
from entropy_list import (duplicate_ids, finished_work_hits,  # noqa: E402
                            goal_vocabulary, retired_hits,
                            unanswered_placeholders, wiki_link_hits)
from entropy_naming import (check_dirs, check_placement,  # noqa: E402
                            check_shape, untracked_routing_targets)
from entropy_size import size_signals, stub_signals  # noqa: E402
from entropy_report import END, SECTIONS, SEED, START, local_seed, render  # noqa: E402
from entropy_trend import baseline, format_trend  # noqa: E402
from entropy_stores import experiment_hits, ref_level_hits  # noqa: E402
from entropy_vendor import vendor_directive_hits  # noqa: E402
from file_law import load_limits  # noqa: E402
from platform_law import rel  # noqa: E402
from schema_law import (SCHEMA, WORKSPACE_ROOT, load_law,  # noqa: E402
                        load_retired, load_scopes)

# NAMED, NEVER INHERITED — the law is core/tools/test/workspace/test_encoding_ratchet.py. The status
# line here carries `→`. core/run exports PYTHONIOENCODING for what it spawns, which is every
# production caller and not the suite: this was red under pytest and green through its own hook.
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# The measurements sit under the hand-written issues, in their own block: an entropy finding and a
# known bug answer the same question, and core/SCHEMA.md gives that question one file. This tool
# owns the block, never the file.
REPORT = WORKSPACE_ROOT / 'ISSUES.md'

LISTS = {
    # Every part of the wos list is ONE namespace: criterion 2 forbids the same item in two
    # lists, and cutting a list does not make its own parts rivals.
    'wos-roadmap': [WORKSPACE_ROOT / 'ROADMAP.md',
                    *sorted(WORKSPACE_ROOT.glob('ROADMAP-*.md'))],
    'core-roadmap': [WORKSPACE_ROOT / 'core/ROADMAP.md'],
    'goals': sorted((WORKSPACE_ROOT / 'brain/goals').glob('*.md')),
}


def _gate(name: str):
    """Load a kebab-named gate from checks/ — the dashboard reports what the gates block."""
    spec = spec_from_file_location(
        name.replace('-', '_'), WORKSPACE_ROOT / f'core/hooks/checks/{name}.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _rel(path) -> str:
    return rel(path, WORKSPACE_ROOT)


def collect(files: list, repo: Path = WORKSPACE_ROOT, promoting: str = '') -> dict:
    """Every check, over one repo's files. `repo` is the repo being counted; the LAW is always the
    workspace's, because a nested project obeys the same SCHEMA. Only the questions that ask git
    something — what is tracked, what a branch is ahead of — are repo-relative.

    `promoting` is the branch the caller is about to merge, and only a session close knows one.
    branch_debt.unmerged_branches carries the reason; it is threaded rather than re-derived here
    because this tool cannot see the verify verdict that decides whether the merge happens."""
    gate = _gate("type-gate")
    allowed, exempt = load_law(SCHEMA)
    scopes = load_scopes(SCHEMA)
    head_warn = load_limits()['CONTEXT_HEAD_WARN']
    findings = {'types': [], 'inventories': [], 'naming': [], 'goals': [],
                'misplaced': [], 'truncated': []}
    for path in files:
        if failure := gate.check_name(path, allowed, exempt):
            findings['types'].append(failure)
        if path.name == 'CONTEXT.md' and (failure := gate.check_inventory(path)):
            findings['inventories'].append(failure)
        if failure := check_misplaced_answer(path, head_warn):
            findings['misplaced'].append(failure)
        if failure := check_goal_link(path):
            findings['goals'].append(failure)
        if failure := check_truncation(path):
            findings['truncated'].append(failure)
        for failure in (check_shape(path, allowed), check_dirs(path, WORKSPACE_ROOT),
                        check_placement(path, scopes, WORKSPACE_ROOT)):
            if failure:
                findings['naming'].append(failure)
    exempt = enforcement_paths(WORKSPACE_ROOT)
    findings['retired'] = retired_hits(files, load_retired(SCHEMA), exempt)
    citations = _gate('citation-gate')
    findings['citations'] = citations.citation_hits(
        files, citations.citation_exempt_paths(WORKSPACE_ROOT))
    findings['wiki'] = wiki_link_hits(
        files, goal_vocabulary(WORKSPACE_ROOT / 'brain/goals'),
        wiki_exempt_paths(WORKSPACE_ROOT))
    # The workspace's own lists. A nested project has its own and does not answer for these.
    findings['duplicates'] = [f'`[{item_id}]` claimed by {", ".join(sorted(claims))}'
                              for item_id, claims in duplicate_ids(
                                  LISTS if repo == WORKSPACE_ROOT else {}).items()]
    findings['routing'] = untracked_routing_targets(files, repo)
    findings['size'] = size_signals(files)
    findings['stubs'] = stub_signals(files)
    findings['crowding'] = crowding_signals(files, WORKSPACE_ROOT)
    findings['branches'] = unmerged_branches(repo, promoting)
    findings['unpushed'] = unpushed_work(repo)
    findings['locals'] = merged_local_branches(repo)
    findings['remotes'] = merged_remote_branches(repo)
    findings['finished'] = finished_work_hits(files, exempt)
    findings['undescribed'] = unanswered_placeholders(files, exempt)
    findings['stores'] = experiment_hits(files) + ref_level_hits(files)
    findings['vendor'] = vendor_directive_hits(files, exempt)
    findings['fields'] = field_hits(files)
    # One directory-level finding is reported by every file under it; dedupe so a count
    # means "things to fix", not "files touched by a thing to fix".
    findings['naming'] = sorted(set(findings['naming']))
    return findings


def main(argv: list | None = None) -> int:
    if not feature_law.is_enabled('entropy-dashboard'):
        return 0  # switched off: no report is written, so the number stops existing rather than lying
    args = argv if argv is not None else sys.argv[1:]
    dry_run = '--dry-run' in args or bool(os.environ.get('LAW_CHECK')) or bool(os.environ.get('WOS_DRY_RUN'))
    # EVERY REPO COUNTS ONLY ITSELF (ruled 2026-09-04, Lucas). The root used to scan all 27 nested
    # repos and carry a table of them — repos its own git IGNORES, so the committed block described
    # THIS DISK and the clone without them read the same commit as red for work it had not done.
    # A project's findings are written where its reader is: by its own pre-commit, into its own
    # ISSUES.md. Which projects exist, and where they live outside, is PROJECTS.md.
    repo = Path(args[args.index('--repo') + 1]).resolve() if '--repo' in args else WORKSPACE_ROOT
    # The branch the CALLER is about to merge, excused from the branch-debt count because it is
    # about to stop being true. Only a session close can answer this, so the default is no branch
    # and a bare run reports every branch that is ahead — see branch_debt.unmerged_branches.
    promoting = args[args.index('--promoting') + 1] if '--promoting' in args else ''
    issues = repo / 'ISSUES.md'
    files = tracked_files(repo, nested=False)
    findings = collect(files, repo, promoting)
    here = sum(len(findings[k]) for k, _, _ in SECTIONS)
    name = '' if repo == WORKSPACE_ROOT else _rel(repo)
    # A bare count is how "flat" got written every session while the real number climbed —
    # re-derive the baseline from git history every run rather than trusting yesterday's memory.
    trend = format_trend(here, baseline(repo)) if repo == WORKSPACE_ROOT else ''
    block = render(findings, len(files), repo, name=name, trend=trend)
    seed = SEED if repo == WORKSPACE_ROOT else local_seed(name)
    if not dry_run:
        text = issues.read_text(encoding='utf-8') if issues.exists() else seed
        issues.write_text(replace_block(text, block, START, END, at_end=not issues.exists()),
                          encoding="utf-8", newline='\n')
    status = '[dry-run] ' if dry_run else ''
    print(f'entropy {status}→ {_rel(issues)} ({here} findings, {len(files)} files scanned)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
