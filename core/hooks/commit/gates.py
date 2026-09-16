#!/usr/bin/env python3
# The pre-commit stages that may REFUSE: line counts, duplication, facade boundaries, terms, lint.
#
# A gate rejects by raising Blocked, never by exiting: the dispatcher owns the one path out, so a
# refusal cannot leave without naming its fix (ISSUES.md B4). What a code/ project must DECLARE is
# the other half, in gates_project.py -- split because that one gate is six, and one file holding
# both reached the size cap the gate itself enforces.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
from pre_commit import Blocked, spawn  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'checks'))
import line_counts  # noqa: E402

SOURCE = ('.js', '.jsx', '.ts', '.tsx', '.py', '.dart')


def source_quality(commit):
    """Line counts over everything this commit staged.

    The missing first-line description comment used to be checked here too. It moved into the Level
    0 gate (checks/type-gate.py, reached from gates_project.py), which already runs over exactly
    this commit's added files. What was here was a shell case-list that only warned, only over code
    extensions, and was a third copy of a table now living once in file_law.py.

    The whole staged set, not `code_files`: which of them the cap applies to is line_counts.report's
    own question, asked of file_law, and a pre-filter here was this gate answering it a second time
    -- which is how prose stayed outside the warn while limits.env held one number for both.
    """
    if not commit.staged or not feature_law.is_enabled('line-limit'):
        return
    lines, blocked = line_counts.report(commit.staged, root=commit.toplevel, staged=True)
    if blocked:
        raise Blocked('\n'.join(lines))
    print('\n'.join(lines))


def duplication_and_terms(commit):
    """Copy-paste clones, facade boundary crossings, and paper term consistency."""
    duplicated = commit.matching(*SOURCE, exclude=('.d.ts', '.pyi', '.min.js'))
    if duplicated:
        done = spawn(commit, 'core/hooks/checks/check-duplication.py',
                     stdin='\n'.join(duplicated))
        if done.returncode != 0:
            raise Blocked(done.stdout + done.stderr)

    facade = commit.matching(*SOURCE, exclude=('.d.ts',))
    if facade:
        done = spawn(commit, 'core/hooks/facade/check-facade-imports.py',
                     stdin='\n'.join(facade))
        if done.returncode != 0:
            raise Blocked(done.stdout + done.stderr)

    _terms(commit)


def _terms(commit):
    """Terminology consistency for papers carrying a terms.yaml.

    THE SWITCH IS CONSULTED BEFORE THE TOOL, NOT AFTER, and that is not bookkeeping. The tool
    carries the same `latex` switch and exits 69 when it is off, which a plain `if it failed` reads
    as a terminology violation -- blocking the very commit the switch was thrown to relax. A feature
    spanning two layers is only honest when both layers consult the law (core/SPECS.md § AD-14).
    """
    tex = commit.matching('.tex')
    if not tex or not feature_law.is_enabled('latex'):
        return
    tool = commit.root / 'core/tools/paper/terms'
    if not tool.is_file():
        return
    roots = set()
    for source in tex:
        directory = (commit.toplevel / source).parent
        while directory != directory.parent:
            if (directory / 'terms.yaml').is_file():
                roots.add(directory)
                break
            directory = directory.parent
    for paper in sorted(roots):
        done = spawn(commit, 'core/tools/paper/terms', str(paper))
        print(done.stdout + done.stderr)
        if done.returncode != 0:
            raise Blocked('⛔ Fix terminology inconsistencies before committing.\n'
                          '   Edit the .tex file, or update terms.yaml if the term was '
                          'intentionally revised.\n'
                          '   Override: git commit --no-verify\n')


def lint(commit):
    """ESLint over staged TypeScript under code/. LAST -- it needs the .d.ts the generators wrote.

    `lint-typescript` names TWO paths in core/features.txt: this one blocks the commit,
    postedit/lint.sh prettier-writes and warns while editing. Different jobs, one switch.
    """
    if not feature_law.is_enabled('lint-typescript'):
        return
    staged = [p for p in commit.matching('.ts', '.tsx', exclude=('.d.ts',))
              if p.startswith('code/') and p.count('/') >= 2]
    seen = set()
    for path in commit.existing(staged):
        project = path.split('/')[1]
        if project in seen:
            continue
        seen.add(project)
        directory = commit.root / 'code' / project
        if not (directory / 'eslint.config.js').is_file():
            continue
        # A local binary, not a global one: the project's own eslint is the one its config was
        # written against, and the .bin shim is `eslint.cmd` on Windows.
        binary = next((directory / 'node_modules/.bin' / name
                       for name in ('eslint.cmd', 'eslint')
                       if (directory / 'node_modules/.bin' / name).is_file()), None)
        if not binary:
            print(f'⚠  eslint not found in {project} — run: npm install\n')
            continue
        files = [p[len(f'code/{project}/'):] for p in staged if p.startswith(f'code/{project}/')]
        print(f'→ ESLint ({project})…')
        done = subprocess.run([str(binary), *files], cwd=directory, capture_output=True,
                              text=True, encoding='utf-8', errors='replace')
        if done.returncode != 0:
            raise Blocked(f'{done.stdout}{done.stderr}\n'
                          f'❌ ESLint violations in {project} block commit. '
                          f'Fix before committing.\n')
