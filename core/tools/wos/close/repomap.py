#!/usr/bin/env python3
# The map of where every project lives, redrawn at session close into PROJECTS.md.
#
# Only what is the same on every clone. The ROW SET comes from .gitignore, which is tracked, and
# never from the disk: a table describing what happens to be checked out here is a fact about one
# machine, which is what ISSUES.md ruled against on 2026-09-04 after the same commit read green on
# one disk and red on the other. The disk fills CELLS and blanks none — two machines share this
# workspace and neither has every project cloned, so a generator that wrote only what it can see
# would delete the other machine's answer at every close.
import json
from pathlib import Path

import artifacts
from artifacts import git, out

MAP = 'PROJECTS.md'
HEAD = ('| Path | Remote | Drive |', '|------|--------|-------|')


def declared(root: Path) -> set:
    """Project paths as .gitignore declares them — the key column's independent source.

    The parse rule itself is entropy_corpus.declared_projects, which the pre-commit's list stage
    asks the same question of. A second copy here is where the two would start disagreeing about
    what a project is.
    """
    from entropy_corpus import declared_projects
    return declared_projects(root)


def link(url: str) -> str:
    """A remote as a link named by its host, which is the only thing about it worth reading."""
    clean = url.removesuffix('.git').replace('https://git@', 'https://')
    return f'[{"Overleaf" if "overleaf" in clean else "github"}]({clean})'


def home(folder: Path) -> str:
    """What a folder's drive_sync.json declares, or nothing. Never guessed from a folder name."""
    try:
        found = json.loads((folder / 'drive_sync.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return ''
    return (f'[sync `{found.get("account", "")}`]'
            f'(https://drive.google.com/drive/folders/{found["folder_id"]})'
            if found.get('folder_id') else '')


def known(text: str) -> dict:
    """Path → [remote, drive], read back out of the block already written, so a cell survives.

    PROJECTS.md says an address written from memory is worse than an empty cell, because the
    empty one asks. An address ERASED because one machine lacks the clone is worse than either.
    """
    start, end = artifacts.markers('projects')
    rows = {}
    for line in text.partition(start)[2].partition(end)[0].splitlines():
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(cells) == 3 and cells[0].startswith('`'):
            rows[cells[0].strip('`')] = [cells[1], cells[2]]
    return rows


def row_set_is_this_close_s_own_change(root: Path, rows: dict, seen: dict) -> bool:
    """Whether the redraw is describing a project set that has already been committed.

    `settle` rolls a write back whenever the tree is dirty, which is right against another
    session's work and wrong for the one close that CHANGES the project set: there the dirt is
    the change the map exists to describe, and until 2026-09-12 the only way past it was to
    disable settle for one call — reaching around a generator's own safety.

    The row set comes from `.gitignore`, which is tracked, so the two cases separate cleanly. A
    row set that moved while `.gitignore` is clean means the change is already committed and the
    map is merely behind; the write is this close's own and must survive. A row set that moved
    while `.gitignore` is itself dirty means the change is not committed yet, so the map would be
    drawn from a source nobody has agreed to, and the rollback is correct.
    """
    if set(rows) == set(seen):
        return False
    return git(root, 'diff', '--quiet', 'HEAD', '--', '.gitignore').returncode == 0


def redraw(root: Path, leave_dirty: bool) -> str:
    """Rewrite the map and settle it. Silent when nothing moved, which is the common case."""
    from platform_law import posix
    from entropy_corpus import nested_repos
    target = root / MAP
    if not target.is_file():   # a repo declaring no map is not a repo that wants one invented
        return ''
    was_clean = git(root, 'diff', '--quiet', MAP).returncode == 0
    seen = known(target.read_text(encoding='utf-8'))
    rows = {name: seen.get(name, ['—', '—']) for name in declared(root)}
    for repo in nested_repos(root):
        name = posix(repo.relative_to(root))
        if name in rows and out(repo, 'remote', 'get-url', 'origin'):
            rows[name][0] = link(out(repo, 'remote', 'get-url', 'origin'))
    for folder in sorted(root.glob('*/*/drive_sync.json')) + sorted(
            root.glob('*/*/*/drive_sync.json')):
        name = posix(folder.parent.relative_to(root))
        if name in rows and home(folder.parent):
            rows[name][1] = home(folder.parent)
    artifacts.write_block(target, 'projects', '\n'.join(
        (*HEAD, *(f'| `{name}` | {cells[0]} | {cells[1]} |' for name, cells in sorted(rows.items())))))
    if git(root, 'diff', '--quiet', MAP).returncode == 0:
        return ''
    own = row_set_is_this_close_s_own_change(root, rows, seen)
    return f'{MAP} redrawn' + artifacts.settle(
        root, MAP, was_clean, 'chore(projects): redraw the map at session close',
        leave_dirty and not own)
