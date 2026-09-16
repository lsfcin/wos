#!/usr/bin/env python3
# What a code/ project must declare before it can commit: verify contract, goal link, spec,
# branch shape, .md type, citations, gitlink.
#
# THREE FEATURES LIVE IN THIS ONE FILE -- verify-contract, verify-suite, project-contract -- so the
# name-names-the-file rule cannot apply here and three registry rows name this path. Each switch is
# read ONCE at the top and treated as a flag, never acted on by returning early from the whole
# stage: a disabled feature must skip its own section, or it silently takes the sections after it
# down with it. That was a live bug in the sourced-bash version's shape.
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# The verification contract lives with the verify docs, not with the hooks — one definition, two
# consumers. Bound to a distinct name so it cannot be confused with a project's own `contract.py`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools/verify'))
import contract as contract_law  # noqa: E402
import feature_law  # noqa: E402
from pre_commit import Blocked, git, spawn  # noqa: E402

# NARROWER THAN file_law.is_code_file ON PURPOSE, and named as its own population in
# test_file_law.NOT_THE_CODE_LAW: this asks which languages a project runs a SUITE for, not what
# the workspace calls code. Staging a .tex, .css or .sh does not oblige a project to declare
# verify:fast. Importing the file law here would widen the gate without anyone deciding to.
CODE_SUFFIX = ('.js', '.jsx', '.ts', '.tsx', '.py', '.dart')
GOAL_LINE = r'^>\s*goal:\s*(\[[^]]+\]\([^)]+\)|none)\s*$'


def _under_code(commit) -> bool:
    """Whether the repo committing is a project under code/ -- asked of the MACHINERY root.

    The bash matched an absolute `code/*` path on one machine, which is the whole reason this pipeline
    could not run on any other clone. `toplevel` is the repo being committed; `root` is where the
    workspace lives; the question is whether the first sits inside `code/` of the second.
    """
    try:
        return commit.toplevel.relative_to(commit.root).parts[:1] == ('code',)
    except ValueError:
        return False


def _contract(commit) -> list:
    """Which verify:fast contract this project declares, if any.

    Asked of core/tools/verify/contract.py, which is the one definition of what counts as declared —
    shared with core/tools/wos/roundup, which asks the same question one level up. Two copies of an
    ordered discovery list is exactly how the gate and the close would come to disagree about
    whether a project has a contract at all.
    """
    return contract_law.discover(commit.toplevel, 'fast')


def project_contract(commit):
    verify_contract = feature_law.is_enabled('verify-contract')
    verify_suite = feature_law.is_enabled('verify-suite')
    project = feature_law.is_enabled('project-contract')

    staged_code = commit.matching(*CODE_SUFFIX, exclude=('.d.ts',))
    if staged_code:
        contract = _contract(commit)
        if verify_contract and not contract and _under_code(commit):
            raise Blocked(
                '⛔ No verify:fast contract found — every code/ project needs one.\n'
                '   Declare package.json "verify:fast" (npm) or a Makefile "verify-fast:" '
                'target (any stack).\n'
                '   No real tests yet? A passing stub is enough — see code/ROADMAP-verify.md G5.')
        if verify_suite and contract:
            _run_suite(commit, contract)

    if project and _under_code(commit):
        _goal_link(commit)
        _spec_declaration(commit)

    # Delegated gates carry their own guards, so they are not wrapped in a switch here.
    import gitflow_gate
    import gitlink_gate
    gitflow_gate.check(commit)

    if project:
        for gate in ('checks/type-gate.py', 'checks/citation-gate.py'):
            done = spawn(commit, f'core/hooks/{gate}')
            if done.returncode != 0:
                raise Blocked(done.stdout + done.stderr)

    gitlink_gate.check(commit)

    # Branch drift: warn, never block. A deliberate mid-session switch is legitimate.
    import branch_marker
    branch_marker.check(commit)


def _run_suite(commit, contract):
    """The project's own verify:fast. Red blocks the commit, and the output says which command.

    A RUNNER THAT IS NOT INSTALLED IS NOT A RED SUITE. `make` is absent on a stock Windows clone, and
    reporting that as "verify:fast is red — fix before committing" tells the operator their tests
    failed when nothing ran. That is precisely the shape this pipeline was ported to remove, so the
    missing runner warns and names its install instead of blocking on a result nobody produced.

    RESOLVED, AND NEVER THROUGH A SHELL. `which` honours PATHEXT, so `npm` is found however this
    machine spells it; a bare name handed to subprocess is resolved only against .exe, and
    `shell=True` on a string made the quoting of an interpreter path the caller's problem.
    """
    label = contract[0]
    print('→ verify:fast…')
    code, log = contract_law.run(commit.toplevel, contract)
    if code is None:
        print(f'⚠  {contract[1]} not found — verify:fast not run for {commit.toplevel.name}.')
        print(f'   Install it, or declare a contract this machine can run. SETUP.md § {label}.\n')
        return
    if code != 0:
        tail = '\n'.join(log.splitlines()[-30:])
        raise Blocked(f'{tail}\n⛔ verify:fast is red — fix before committing. '
                      f'Full output: {label}')
    print('✓ verify:fast green')


def _goal_link(commit):
    """code/<proj>/CONTEXT.md line 3 declares which goal this project serves, or `none`."""
    import re
    if 'CONTEXT.md' not in commit.staged:
        return
    context = commit.toplevel / 'CONTEXT.md'
    lines = context.read_text(encoding='utf-8', errors='replace').splitlines()
    third = lines[2] if len(lines) > 2 else ''
    if not re.match(GOAL_LINE, third):
        raise Blocked(f"⛔ {commit.toplevel.name}/CONTEXT.md missing '> goal:' link on line 3.\n"
                      "   Add '> goal: [name](../../brain/goals/<name>.md)' or '> goal: none'.")


def _spec_declaration(commit):
    """A NEW module CONTEXT.md under code/ must declare '> spec: <file>' or '> spec: none'.

    Ratchet / boy-scout: only files this commit ADDS, so existing modules are grandfathered and a
    repo that inherited violations is not blocked on every commit. Mirrors the goal-link convention.
    """
    import re
    added = [p for p in git('diff', '--cached', '--name-only', '--diff-filter=A',
                            cwd=commit.toplevel).splitlines()
             if p == 'CONTEXT.md' or p.endswith('/CONTEXT.md')]
    for path in commit.existing(added):
        text = (commit.toplevel / path).read_text(encoding='utf-8', errors='replace')
        found = re.search(r'^>\s*spec:\s*(\S.*)$', text, re.MULTILINE)
        declared = found.group(1).strip() if found else ''
        if not declared:
            raise Blocked(f"⛔ {path} missing '> spec:' declaration (new module under code/).\n"
                          "   Add '> spec: SPECS.md' (author it from code/_templates/"
                          "SPECS-module.md),\n"
                          "   or '> spec: none' to opt out. See code/ROADMAP-spec-drive.md.")
        if declared != 'none' and not (commit.toplevel / Path(path).parent / declared).is_file():
            raise Blocked(f"⛔ {path} declares '> spec: {declared}' but "
                          f'{Path(path).parent}/{declared} is missing.\n'
                          '   Create it from code/_templates/SPECS-module.md, '
                          "or use '> spec: none'.")
