# Workspace scanner: directory discovery and CONTEXT.md routing-table assembly.
import re
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HOOKS))
sys.path.insert(0, str(_HOOKS / 'entropy'))
from entropy_corpus import ignored_here, is_generated_mirror  # noqa: E402
from file_law import FACADES, is_code_file, load_limits  # noqa: E402
from hoist import hoist, md_blurb  # noqa: E402
from part_table import EMPTY_CELL, render_table  # noqa: E402
from workspace_meta import (  # noqa: E402
    ALL_EXTS, PLACEHOLDER, extract_api, file_description, interface_for,
)

# The number lives in limits.env, never here — this file held the only copy for months
# while three other checkers each invented their own (see file_law.py). FOLD_FILES since
# 2026-09-06: this asks whether a directory is substantial enough to route TO, which is not
# the question WARN_FILES asks, and sharing one constant meant raising the crowding signal
# would have folded every 7-9-file directory into its parent as a side effect.
SPLIT_THRESHOLD = load_limits()['FOLD_FILES']
_ROOT        = _HOOKS.parents[1]
_SKIP_DIRS   = {'node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'venv'}

def is_scanned(path: Path) -> bool:
    """True if this file gets a row in its directory's routing table.

    The commit-time description gate asks this before demanding a first-line comment, so
    the gate and the generator can never disagree about who owes one — that disagreement
    is what put a placeholder inside the enforcement directory itself.

    THE EXTENSIONLESS ARM IS ASKED, NEVER RE-DERIVED. This file carried its own
    `_is_exec_script` — "extensionless AND starts with a shebang" — a second copy of a
    question `file_law.is_code_file` already answers. S5 taught that module the shape rule
    (`is_tool_entrypoint`) when the port stripped the shebangs; this copy never heard, so
    all 33 core/tools CLIs silently lost their routing row, and the loss was invisible
    because the generator simply rewrote each table without them. Caught 2026-08-29 when
    the merge added `core/tools/chat/wazip` and watched its row disappear on save.
    """
    return (path.is_file()
            and path.name not in ('CONTEXT.md', 'WORKSPACE.md', 'AGENTS.md')
            and not path.name.endswith(('.d.ts', '.pyi'))
            and (path.suffix in ALL_EXTS or is_code_file(path)))

def carried(paths: list) -> list:
    """Those of `paths` a clone actually receives, order kept.

    The table is generated from disk but SHIPS in git, so a row for an ignored path describes a
    tree the reader does not have. Ten had accumulated by 2026-09-01, and one of them
    (`academy/reviews/…/outputs/CONTEXT.md`) was a placeholder this generator wrote itself, inside a
    directory git is told to ignore — the row and the file it pointed at were both its own work.

    Asked of the paths about to become rows, never inside `is_scanned`: that question is shared
    with the commit-time description gate, and one `git check-ignore` per file would put a
    subprocess in the recursion `has_code_content` runs on every save.

    A generated mirror is carried by its generator instead of by git — `.opencode/skills/` and the
    three trees beside it are rebuilt from `core/skills/` on every sync, so a clone that installs
    has them and the rows are true. `is_generated_mirror` already knows which those are, and
    `untracked_routing_targets` waives the same set; a second list here is the drift both exist
    to catch.
    """
    if not paths:
        return []
    ignored = ignored_here(paths, _ROOT)
    return [p for p in paths if p.resolve() not in ignored or is_generated_mirror(p)]

def code_files(directory: Path) -> list:
    return sorted(p for p in directory.iterdir() if is_scanned(p))

def has_code_content(directory: Path) -> bool:
    if code_files(directory): return True
    return any(has_code_content(p) for p in directory.iterdir()
               if p.is_dir() and not p.name.startswith('.') and p.name not in _SKIP_DIRS)

def subdir_scan(directory: Path, rs: str, re_end: str) -> tuple:
    fold_list, link_list = [], []
    for sub in carried(sorted(p for p in directory.iterdir()
                              if p.is_dir() and not p.name.startswith('.')
                              and p.name not in _SKIP_DIRS)):
        has_ctx = (sub / 'CONTEXT.md').exists()
        if not has_code_content(sub) and not has_ctx: continue
        files = code_files(sub)
        is_branch = any(has_code_content(p) for p in sub.iterdir()
                        if p.is_dir() and not p.name.startswith('.'))
        if has_ctx or len(files) >= SPLIT_THRESHOLD or is_branch:
            if not has_ctx:
                placeholder = sub / 'CONTEXT.md'
                placeholder.write_text(
                    f'# {sub.name}\n> ← add description\n\n{rs}\n## Routing\n\n{re_end}\n',
                    encoding='utf-8', newline='\n')
                print(f'  created placeholder: {placeholder}')
            link_list.append(sub)
        else:
            for f in files: fold_list.append((f, f'{sub.name}/{f.name}'))
    # A folded file is a grandchild, so an ignored one survives its parent's filter: the row
    # `2026-07/instagram-video-by-bodam.sketch.md` in brain/attachments reached a clone that way.
    kept = set(carried([f for f, _ in fold_list]))
    return [pair for pair in fold_list if pair[0] in kept], link_list

def parse_preserved_files(inner: str) -> dict:
    """Descriptions already in the table, kept across a re-sync.

    Column-count agnostic on purpose: build_file_rows drops generated columns that are
    empty for every row, so a table may have 2, 3 or 4 columns. The filename is always
    first and the description always last — anchor on those, never on a fixed arity.
    """
    rows = {}
    for line in inner.splitlines():
        if not line.startswith('|'): continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 2: continue
        m = re.match(r'\[?`([^`]+)`\]?', cells[0])
        if not m: continue
        fname, desc = m.group(1), cells[-1]
        # Subdirectory rows are backticked too, so they matched here and were then
        # reported as "removed stale entry" on every healthy sync — 13 alarming lines
        # for core/hooks alone, which is how a real removal notice gets missed. Their
        # descriptions come from parse_preserved_subs; here they are noise.
        if fname.endswith('/'): continue
        if desc not in ('Description', '—', '', PLACEHOLDER): rows[fname] = desc
    return rows

def parse_preserved_subs(inner: str) -> dict:
    rows = {}
    for line in inner.splitlines():
        m = re.match(r'\|\s*\[`([^/`]+)/`\][^|]*\|\s*([^|]+?)\s*\|', line)
        if m:
            name, desc = m.group(1), m.group(2).strip()
            if desc not in ('Description', '—', '', '← add description'): rows[name] = desc
    return rows

def build_sub_rows(link_list: list, preserved_subs: dict) -> str:
    rows = ['| Subdirectory | Description |', '|--------------|-------------|']
    for sub in link_list:
        ctx_sub = sub / 'CONTEXT.md'
        desc = preserved_subs.get(sub.name, '—')
        if ctx_sub.exists() and (blurb := md_blurb(ctx_sub)):
            desc = hoist(blurb, f'{sub.name}/')
        link = f'{sub.name}/CONTEXT.md' if ctx_sub.exists() else f'{sub.name}/'
        rows.append(f'| [`{sub.name}/`]({link}) | {desc} |')
    return '\n'.join(rows)

HEADERS   = ('File', 'Interface', 'API', 'Description')
ALWAYS    = (0, 3)          # File and Description are the table; the rest earn their place
FACADE_PREFIX = '**facade** — '


def _strip_facade(desc: str) -> str:
    """Drop every facade prefix already on a preserved description.

    The prefix is *decoration re-derived each run*, but it was being prepended to a
    description that had been read back out of the table with last run's prefix still on
    it. A facade whose own first-line comment is missing therefore grew one copy per sync —
    `core/skills/caveman/scripts/CONTEXT.md` reached 22 before this was noticed.
    """
    while desc.startswith(FACADE_PREFIX):
        desc = desc[len(FACADE_PREFIX):]
    return desc

def build_file_rows(files_with_rel: list, preserved: dict, ctx_dir: Path) -> str:
    """The routing table, minus any generated column that is empty on every row.

    Measured 2026-07-30: 773 of 1242 rows workspace-wide carried an em-dash Interface,
    paying table width in every read to say "nothing here". A column that says nothing
    for every file in a directory is not information about that directory.
    """
    rows = []
    for f, rel in sorted(files_with_rel, key=lambda x: (x[0].name not in FACADES, x[1])):
        pre  = FACADE_PREFIX if f.name in FACADES else ''
        kept = _strip_facade(preserved.get(rel, preserved.get(f.name, PLACEHOLDER)))
        found = file_description(f)
        # Every description here is hoisted text and takes the same bound. A `.md`'s is its own
        # file's blurb, written under its own H1 in its own directory, so it is rebased too. A
        # code file's has nothing to rebase — but it is not the one-liner this used to assume:
        # `comment_paragraph` reads a whole PARAGRAPH for every `#`-commented language, so an
        # author explaining themselves at length published the explanation into a table one
        # directory up. The row that taught this was 1,300 characters of two bugs' history
        # (2026-09-11), in a CONTEXT.md the context gate makes mandatory.
        if found:
            folded = Path(rel).parent
            rebase = f.suffix == '.md' and str(folded) != '.'
            found = hoist(found, f'{folded}/' if rebase else '')
        desc = pre + (found or kept)
        rows.append((f'[`{rel}`]({rel})', interface_for(f, ctx_dir), extract_api(f), desc))
    return render_table(HEADERS, rows, ALWAYS)

def build_routing_block(sub_content: str, file_content: str, rs: str, re_end: str) -> str:
    parts = [rs, '## Routing', '']
    if sub_content:
        parts.append(sub_content)
        if file_content: parts.append('')
    if file_content: parts.append(file_content)
    parts.append(re_end)
    return '\n'.join(parts) + '\n'
