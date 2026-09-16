#!/usr/bin/env python3
# The pre-commit stages that WRITE: brain stats, routing tables, interface stubs, skill mirrors.
#
# A generator writes artifacts and stages them into the commit under way; a gate (gates.py,
# gates_project.py) may refuse it. That split is why this file never raises Blocked except where a
# generator's own output could not be trusted.
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402
import file_law  # noqa: E402
from platform_law import rel  # noqa: E402
from pre_commit import Blocked, git, spawn  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'stubgen'))
import stubs  # noqa: E402


def _stage(commit, *paths):
    """git add, tolerant: a generator that could not write is reported by its own arm, not here."""
    for path in paths:
        git('add', str(path), cwd=commit.toplevel)


def prepare(commit):
    """Brain stats and the self-healing .gitignore allowlist. First -- both stage files."""
    # Only on a staged brain/goals/ file, so unrelated commits are not polluted. Resolved against
    # the MACHINERY root: this hook fires in every repo, and a cwd-relative path only happens to
    # work in the one that has brain/GOALS.md.
    if (commit.root / 'brain/GOALS.md').is_file() and \
            any(p.startswith('brain/goals/') for p in commit.staged):
        spawn(commit, 'core/hooks/brain/brain_stats.py')

    import gitignore_heal
    gitignore_heal.heal(commit)


def routing(commit):
    """CONTEXT.md routing blocks, the AGENTS.md norms block, and TeX .texif interfaces."""
    # $STAGED is --diff-filter=ACM, so a DELETED file is invisible to code_files -- and a directory
    # that LOSES a file is exactly the one whose routing table now names something gone, forever,
    # since nothing else re-syncs it. `is_code_file` classifies by name, so the file need not exist.
    dirty = commit.code_files + [p for p in commit.deleted if file_law.is_code_file(Path(p))]
    for leaf in sorted({str(Path(p).parent) for p in dirty}):
        if (commit.toplevel / leaf / 'CONTEXT.md').is_file():
            if spawn(commit, 'core/hooks/routing/context_synchronizer.py', leaf).returncode == 0:
                _stage(commit, Path(leaf) / 'CONTEXT.md')

    # On a staged norm OR a staged registry change: the registry decides both WHICH norms publish
    # and in WHAT ORDER, so a reordered features.txt with no norm edit still moves the
    # always-loaded file. The generator holds the group's feature switch itself.
    if any(p.startswith('core/norms/') or p in ('core/features.txt', 'core/profile.txt')
           for p in commit.staged):
        if spawn(commit, 'core/hooks/routing/norms.py').returncode == 0:
            _stage(commit, commit.root / 'AGENTS.md')

    for source in commit.existing(commit.matching('.tex')):
        if spawn(commit, 'core/hooks/stubgen/tex-interface-gen.py', source).returncode == 0:
            _stage(commit, Path(source).with_suffix('.texif'))
        else:
            print(f'⚠  tex-interface-gen failed for {source} — .texif not staged\n')


def _sweep(commit, staged, pattern, exclude=()):
    """Staged sources, PLUS any stubless sibling in the same directories.

    A source that entered the repo outside Edit/Write -- a bash heredoc, a bulk vendoring, a
    --no-verify commit -- was never stubbed by anything, and nothing ever looked back. Sweeping the
    touched directories catches the common shape without paying a whole-tree scan on every commit.
    """
    found = set(staged)
    for directory in {Path(p).parent for p in staged}:
        for sibling in (commit.toplevel / directory).glob(pattern):
            if sibling.name.endswith(('.d.ts',) + exclude) or '__pycache__' in sibling.parts:
                continue
            interface = stubs.interface_for(sibling)
            if interface and not interface.is_file():
                found.add(rel(sibling, commit.toplevel))
    return sorted(found)


def _typescript(commit, staged):
    """Declarations once per tsconfig project, not once per file. The tsc call itself is stubs.py's,
    which is where every stub-generator invocation lives; this stage owns only what to stage."""
    tsc = stubs.find_tsc()
    if not tsc:
        print('⚠  tsc not found — .d.ts not generated. Install: npm install -g typescript\n')
        return
    roots = {stubs.project_root(Path(p), commit.toplevel) for p in staged} - {None}
    for project in sorted(roots):
        _stage(commit, *stubs.emit_project_dts(project, tsc))
        print(f'✓ .d.ts generated: {project}')


def _keeps_a_list(commit) -> bool:
    """A PROJECT keeps its own findings; a TARGET keeps none.

    core/tools/links/SPECS.md gives that as the reason the redirect clone is a target. This hook is
    global, so it fired there anyway and shipped a list into a public repo on every build. Asked
    of the same .gitignore the project map reads, so nothing here holds a second list of names.
    """
    if commit.is_workspace:
        return True
    here = rel(commit.toplevel, commit.root)
    if Path(here).is_absolute():   # outside the workspace: it borrows the hook and owns its list
        return True
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'entropy'))
    from entropy_corpus import declared_projects  # noqa: PLC0415
    return here in declared_projects(commit.root)


def issues(commit):
    """This repo's own entropy findings, written into its own ISSUES.md and staged.

    Ruled 2026-09-04 (Lucas): each repo counts only itself, and writes where its reader is. Scanning
    the nested projects from outside committed lists nobody typed and nobody pushed
    (b20260831-scattered-lists-never-push), against a table that described one disk (b20260902).
    WRITES AND WARNS, never refuses: a gate here would refuse commits over a debt they did not make.
    """
    if not feature_law.is_enabled('entropy-dashboard'):
        return
    if not _keeps_a_list(commit):
        return
    if spawn(commit, 'core/hooks/entropy/dashboard/entropy-dashboard.py',
             '--repo', str(commit.toplevel)).returncode == 0:
        _stage(commit, commit.toplevel / 'ISSUES.md')


def interfaces(commit):
    """.pyi, .d.ts and .dart.api, generated and staged into this commit.

    `interface-stubs` names TWO paths in core/features.txt -- this one and postedit/interfaces.sh.
    Not a duplicate trigger: this one stages the stub and sweeps stubless siblings, post-edit keeps
    the stub current inside the session so read/pre-read.py never serves a stale interface.
    """
    if not feature_law.is_enabled('interface-stubs'):
        return

    python = [p for p in commit.matching('.py') if '__pycache__' not in p]
    for source in commit.existing(_sweep(commit, python, '*.py')):
        if stubs.emit_pyi(commit.toplevel / source):
            _stage(commit, Path(source).with_suffix('.pyi'))
        else:
            print(f'⚠  stubgen failed for {source} — .pyi not staged\n')

    skip = ('.min.js', '.config.js')
    javascript = _sweep(commit, commit.matching('.js', exclude=skip), '*.js', exclude=skip)
    if javascript:
        tsc = stubs.find_tsc()
        if not tsc:
            print('⚠  tsc not found — .d.ts not generated for JS. Install: npm i -g typescript\n')
        else:
            for source in commit.existing(javascript):
                if stubs.emit_dts(commit.toplevel / source, tsc):
                    _stage(commit, Path(source).with_suffix('.d.ts'))
                else:
                    print(f'⚠  tsc failed for {source} — .d.ts not staged\n')

    typescript = commit.existing(commit.matching('.ts', '.tsx', exclude=('.d.ts',)))
    if typescript:
        _typescript(commit, typescript)

    for source in commit.existing(commit.matching('.dart')):
        if spawn(commit, 'core/hooks/stubgen/dart-api-extract.py', source).returncode == 0:
            _stage(commit, f'{source}.api')
        else:
            print(f'⚠  dart-api-extract failed for {source} — .dart.api not staged\n')


def skills(commit):
    """Regenerate the skill-library mirrors, then validate their frontmatter.

    Regeneration prunes orphans, the only thing that removes a DELETED skill's copies: `rm` is not
    an Edit, so no post-edit hook sees it. The --check re-run is not belt-and-braces: it catches a
    sync that reported success and left the mirrors disagreeing anyway.

    THIS STAGE NO LONGER STAGES ANYTHING: the copies are gitignored generated content, so the loop
    that staged them added nothing while restating paths sync-skills owns. Correctness lives at the
    moment of the edit (core/hooks/postedit/sync.sh) rather than at commit time.
    """
    if not any(p.startswith('core/skills/') and p.endswith('.md') for p in commit.staged):
        return
    print('→ sync-skills…')
    # Through the launcher, never a spelled interpreter: sync-skills is Python since 2026-09-01 and
    # `bash` would run it as a shell script. The port is also what made the pair of runs cheap
    # enough for the SessionStart heal to exist.
    sync = ['sh', str(commit.root / 'core/run'), 'tools/wos/sync-skills']
    done = subprocess.run(sync, capture_output=True, text=True,
                          cwd=commit.toplevel, encoding='utf-8', errors='replace')
    print(done.stdout + done.stderr)
    if done.returncode != 0:
        raise Blocked('⛔ sync-skills failed — invalid skill frontmatter (see core/SCHEMA.md). '
                      'Fix before committing.')
    if subprocess.run([*sync, '--check'], capture_output=True, text=True,
                      cwd=commit.toplevel, encoding='utf-8').returncode != 0:
        raise Blocked('⛔ skill mirrors out of sync after regeneration.')
    print('✓ skills synced + validated')
