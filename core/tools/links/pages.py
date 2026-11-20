# pages.py — a course page and its artefacts mirrored into the publish repo and pushed, in one call, for links/cfpages
#
# A course page lives at academy/teaching/classes/<course>/<file>.md and is served from
# outputs/links/<course>/<file>.md. The mapping is the directory name, so there is no table to keep.
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[3]
CLASSES = ROOT / 'academy' / 'teaching' / 'classes'

# A page may carry a block that a generator draws; the generator runs before the copy, so a stale
# drawing never reaches the site. Keyed on the marker the page itself holds: declaring a block IS
# asking for its generator.
GENERATORS = {
    '<!-- painel:dados-': ROOT / 'academy' / 'teaching' / 'structure' / 'painel.py',
    '<!-- habilidades:start -->': ROOT / 'academy' / 'teaching' / 'structure' / 'arvore.py',
}

# Internal files that sit beside the artefacts and must never reach a public repo.
PRIVATE = {'CONTEXT.md'}


class Refused(Exception):
    pass


def resolve_page(page: pathlib.Path, classes: pathlib.Path = CLASSES, root: pathlib.Path = ROOT) -> pathlib.Path:
    """Resolve a course page path from workspace root, classes dir, or cwd."""
    if page.is_absolute():
        return page.resolve()
    if (root / page).exists():
        return (root / page).resolve()
    if (classes / page).exists():
        return (classes / page).resolve()
    if page.exists():
        return page.resolve()
    return (root / page).resolve()


def mirror_of(page: pathlib.Path, publish: pathlib.Path, classes: pathlib.Path = CLASSES) -> pathlib.Path:
    """classes/<course>/<file> -> publish/<course>/<file>; anything else has no public place."""
    page = resolve_page(page, classes=classes)
    try:
        course, name = page.relative_to(classes.resolve()).parts
    except ValueError:
        raise Refused(f"{page} is not a course page — publish takes {classes}/<course>/<file>.md")
    return publish / course / name


def redraw(page: pathlib.Path) -> list[str]:
    """Run every generator the page declares; return the ones that ran."""
    page = resolve_page(page)
    text = page.read_text(encoding='utf-8')
    ran = []
    for marker, script in GENERATORS.items():
        if marker in text:
            subprocess.run([sys.executable, str(script), str(page)], check=True)
            ran.append(script.name)
    return ran


def mirror(page: pathlib.Path, publish: pathlib.Path, classes: pathlib.Path = CLASSES) -> list[pathlib.Path]:
    """Copy the page, and its artefatos/ when it has one, into the publish repo; return the targets."""
    page = resolve_page(page, classes=classes)
    target = mirror_of(page, publish, classes)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(page, target)
    copied = [target]
    # the delivery slots' links and the teacher's pareceres: data the site writes, kept out of the page so it never meets the cap
    for data in (page.parent / 'entregas.tsv', page.parent / 'pareceres.tsv'):
        if data.exists():
            copied.append(pathlib.Path(shutil.copy2(data, target.parent / data.name)))
    artefacts = page.parent / 'artefatos'
    if artefacts.is_dir():
        # rglob: an artefact may keep its model and examples in a folder of its own (artefatos/brw/).
        for f in sorted(artefacts.rglob('*.md')):
            if f.name not in PRIVATE:
                dest = target.parent / 'artefatos' / f.relative_to(artefacts)
                dest.parent.mkdir(parents=True, exist_ok=True)
                copied.append(pathlib.Path(shutil.copy2(f, dest)))
    return copied


def _git(publish: pathlib.Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(['git', *args], cwd=publish, check=check, capture_output=True, text=True, encoding='utf-8')


def _show(publish: pathlib.Path, rev: str, path: str) -> str | None:
    shown = _git(publish, 'show', f'{rev}:{path}', check=False)
    return shown.stdout if shown.returncode == 0 else None


def pull(publish: pathlib.Path, classes: pathlib.Path = CLASSES) -> list[pathlib.Path]:
    """Bring what the browser committed to the site home to the workspace, then catch the clone up.

    The site is edited in two places — the workspace (published by `mirror`) and the browser (the
    editor and the delivery slots commit straight to the publish repo). Without this, the next
    `mirror` copies the workspace over a browser edit and nobody is told. A three-way merge, with the
    last thing both sides agreed on as the base, keeps both; the same line changed on both sides
    (git counts neighbouring lines as the same) refuses before anything is written, so a refusal never leaves half a pull behind.
    """
    _git(publish, 'fetch', '-q', 'origin')
    if _git(publish, 'rev-parse', '-q', '--verify', '@{u}', check=False).returncode:
        return []  # nothing upstream yet: the first push creates it
    base = _git(publish, 'merge-base', 'HEAD', '@{u}').stdout.strip()
    changed = _git(publish, 'diff', '--name-only', base, '@{u}').stdout.split()
    merged, conflicts = {}, []
    for rel in changed:
        home = classes / rel
        theirs = _show(publish, '@{u}', rel)
        if not rel.endswith(('.md', '.tsv')) or not (classes / rel.split('/')[0]).is_dir() or theirs is None:
            continue  # no workspace home (viewer.js, functions/), or deleted on the site
        ours = home.read_text(encoding='utf-8') if home.exists() else None
        old = _show(publish, base, rel) or ''
        if ours is None or ours == old:
            merged[home] = theirs
            continue
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for name, text in (('ours', ours), ('base', old), ('theirs', theirs)):
                (pathlib.Path(tmp) / name).write_text(text, encoding='utf-8', newline='\n')
                files.append(str(pathlib.Path(tmp) / name))
            result = subprocess.run(['git', 'merge-file', '-p', *files], capture_output=True, text=True, encoding='utf-8')
        if result.returncode:
            conflicts.append(rel)
        else:
            merged[home] = result.stdout
    if conflicts:
        raise Refused(
            "the browser and the workspace changed the same or neighbouring lines in: " + ', '.join(conflicts) +
            f"\n  compare: git -C {publish} diff HEAD @{{u}} -- <file>; settle it in the workspace, then rerun")
    written = []
    for home, text in merged.items():
        if not home.exists() or home.read_text(encoding='utf-8') != text:
            home.parent.mkdir(parents=True, exist_ok=True)
            home.write_text(text, encoding='utf-8', newline='\n')
            written.append(home)
    _git(publish, 'rebase', '-q', '@{u}')
    return written


def production(publish: pathlib.Path) -> None:
    """Cloudflare Pages publishes main alone; any other branch is a preview nobody's short link reaches."""
    branch = subprocess.run(['git', 'branch', '--show-current'], cwd=publish, capture_output=True,
                            text=True, encoding='utf-8', check=True).stdout.strip()
    if branch != 'main':
        raise Refused(f'{publish} is on {branch or "a detached HEAD"}, and only main goes live.\n'
                      f'  git -C {publish} switch main   (pushed commits on {branch} stay there)')


def push(publish: pathlib.Path, paths: list, message: str) -> None:
    """git add exactly these paths, commit when something is staged, push — from main only.

    `add` by path and never `commit -am`: -a skips a file the repo has never seen, which is every
    new artefact. Nothing staged means nothing to COMMIT, never nothing to push — a commit left by a
    run that failed at the push is exactly when the site is still stale.
    """
    production(publish)
    subprocess.run(['git', 'add', '--', *map(str, paths)], cwd=publish, check=True)
    if subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=publish).returncode:
        subprocess.run(['git', 'commit', '-q', '-m', message], cwd=publish, check=True)
    # -u origin HEAD: the same call works on the first push, when there is no upstream yet.
    subprocess.run(['git', 'push', '-q', '-u', 'origin', 'HEAD'], cwd=publish, check=True)
