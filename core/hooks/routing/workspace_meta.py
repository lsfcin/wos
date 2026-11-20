# Workspace metadata extraction: file descriptions, public APIs, and interface links.
import re, ast, sys
from pathlib import Path

# One definition, from core/hooks/file_law.py — this module used to carry its own copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from file_law import CODE_EXTS, described  # noqa: E402  (CODE_EXTS re-exported for callers)
from hoist import comment_paragraph, md_blurb  # noqa: E402

# `.env` and `.txt` joined 2026-08-15: the four files core/hooks keeps its law in
# (`limits.env`, `vendored.txt`, `extensionless.txt`, `gitignore-exceptions.txt`) each carry a
# `#` first line and were unreachable by the generator, so core/hooks/CONTEXT.md hand-wrote a
# table to name them — an inventory forced by a gap in this set. Five such files are tracked
# workspace-wide, four of them here; this is a narrow list, not a net for data dumps.
# `.json` joined 2026-09-04, with described.txt as its describing route: it has no comment syntax,
# so the row a harness-dictated config earns cannot come from the file itself.
CONTENT_EXTS = {'.md', '.yaml', '.yml', '.toml', '.env', '.txt', '.json'}
ALL_EXTS     = CODE_EXTS | CONTENT_EXTS
PLACEHOLDER  = '← add first-line comment'

# One entry per extension in ALL_EXTS, asserted by test_every_scanned_extension_can_be
# _described. An extension the scanner picks up but this table has no pattern for is
# undescribable BY CONSTRUCTION: file_description falls through to '' and the generator
# writes the placeholder, so the row asks for a comment the file already has. `.sh` (30
# files) and `.jsx` (29) sat in that gap, which is why `core/hooks/post-edit.sh` carried a
# marker inside the enforcement directory itself — not a lapse of discipline, a missing key.
COMMENT_RE = {
    '.py':  [r'^#\s*(.+)', r'^"""(.+?)"""', r"^'''(.+?)'''"],
    '.js':  [r'^//\s*(.+)'], '.ts':   [r'^//\s*(.+)'], '.tsx':  [r'^//\s*(.+)'],
    '.jsx': [r'^//\s*(.+)'],
    '.css': [r'^/\*\s*(.+?)\s*\*/'],  '.scss': [r'^/\*\s*(.+?)\s*\*/'],
    '.html':[r'^<!--\s*(.+?)\s*-->'], '.dart': [r'^//\s*(.+)'],
    '.md':  [r'^#\s*(.+)', r'^<!--\s*(.+?)\s*-->'], '.yaml': [r'^#\s*(.+)'], '.yml':  [r'^#\s*(.+)'],
    '.tex': [r'^%\s*(.+)'], '.toml': [r'^#\s*(.+)'], '.sh': [r'^#\s*(.+)'],
    '.env': [r'^#\s*(.+)'], '.txt': [r'^#\s*(.+)'],
}

def _exec_description(path: Path) -> str:
    """Extract description from an extensionless executable (shebang file).
    Skips the shebang, finds the first # comment line, returns the part after ' — '."""
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return ''
    for index, line in enumerate(lines[:6]):
        if line.startswith('#!'):
            continue
        if re.match(r'^#\s*(.+)', line):
            text = comment_paragraph(lines, index)
            if ' — ' in text:
                return text.split(' — ', 1)[1].strip()
            return text
    return ''

def _frontmatter_description(path: Path) -> str:
    """Read 'description:' from YAML frontmatter (files that start with ---).
    Handles inline values and block scalars (> and |)."""
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    except OSError:
        return ''
    if not lines or lines[0].strip() != '---':
        return ''
    block_mode = False
    block_lines: list = []
    for line in lines[1:30]:
        if line.strip() in ('---', '...'):
            break
        if block_mode:
            if line.startswith((' ', '\t')):
                block_lines.append(line.strip())
            else:
                break
        else:
            m = re.match(r'^description:\s*(.+?)\s*$', line)
            if m:
                val = m.group(1).strip().strip('"\'')
                if val in ('>', '|', '>-', '|-'):
                    block_mode = True
                else:
                    return val
    if block_lines:
        return ' '.join(block_lines)
    return ''

def file_description(path: Path) -> str:
    # Asked first, and only ever answers for a path named in core/hooks/described.txt. A format
    # that CAN carry a comment still describes itself at the source, beside what it describes.
    if declared := next((d for p, d in described().items() if str(path).endswith(p)), ''):
        return declared
    if not path.suffix:
        return _exec_description(path)
    if path.suffix == '.md':
        fm = _frontmatter_description(path)
        if fm:
            return fm
        blurb = md_blurb(path)
        if blurb:
            return blurb
    patterns = COMMENT_RE.get(path.suffix, [])
    try:
        lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
        # A shebang is a comment to the regex but not a description — every executable
        # module was advertising its interpreter path in the routing table. Take the
        # real first-line comment, which checks/first-line-gate.py already requires below it.
        if lines and lines[0].startswith('#!'):
            lines = lines[1:]
        first = lines[0]
    except (IndexError, OSError):
        return ''
    for pat in patterns:
        m = re.match(pat, first.strip())
        if m:
            # `#`-commented languages wrap their description across lines exactly as the
            # shebang scripts do, so they get the same paragraph read. The others
            # (`//`, `/* */`, `<!-- -->`) keep the single-line read: their first-line
            # comment is authored as one line and joining `//` lines would swallow the
            # next unrelated comment, which has no blank-line convention to stop at.
            if pat.startswith('^#') and path.suffix != '.md':
                return comment_paragraph(lines, 0) or m.group(1).strip()
            return m.group(1).strip()
    if path.suffix == '.py':
        return _module_docstring(path)
    return ''


def _module_docstring(path: Path) -> str:
    """A module docstring's first line, per PEP 257 — the fallback, never the first choice.

    `COMMENT_RE['.py']` matches `\"\"\"one line\"\"\"` and nothing else, so a module whose
    docstring opens on line 1 and closes three lines down was undescribable: 13 tracked
    modules asked for a comment they had already answered in the way Python itself
    prescribes. Third instance of one gap, after `.sh` and the `.md` blurb — the generator
    holding the text and not reaching for it. The rule that came out of it, and the order
    these sources are tried in: core/hooks/SPECS.md § The `CONTEXT.md` routing block.

    Runs only after the `#` pattern misses, so this workspace's line-1 comment convention
    keeps precedence and no existing row moves.
    """
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding='utf-8', errors='ignore')))
    except (SyntaxError, ValueError, OSError):
        return ''
    return doc.strip().splitlines()[0].strip() if doc and doc.strip() else ''

# A `test_*` name is collected by the runner, never imported by another module, so it is
# not API — listing it in the routing table spends tokens naming something no reader can
# call. Deliberately keyed on the SYMBOL, not on the path: a `tests/` or `test_*.py`
# exemption would be a door an agent could walk production code through to dodge the
# facade and interface-stub gates. Here there is no door — a function only leaves the API
# column by taking a name the test runner will collect, which stops it being usable API.
def _is_api(name: str) -> bool:
    return not name.startswith('_') and not name.startswith('test_')

_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

# Module top level and class bodies, never ast.walk: a walk reaches nested defs, so every
# closure was advertised as importable API. It was masked by the [:5] cap and only showed on
# modules exporting fewer than five names — hoist.py's `fix`, a closure inside rebase_links,
# sitting in the routing table beside four real exports.
# Top-level names fill the list first and methods only take what is left, because the cap makes
# ordering load-bearing: appending each class's methods directly after it pushed real
# module-level functions out of the column, trading one wrong entry for a missing right one.
def python_api(path: Path) -> list:
    try: tree = ast.parse(path.read_text(encoding='utf-8', errors='ignore'))
    except SyntaxError: return []
    top     = [n.name for n in tree.body if isinstance(n, _DEFS) and _is_api(n.name)]
    methods = [m.name for n in tree.body if isinstance(n, ast.ClassDef)
               for m in n.body if isinstance(m, _DEFS[:2]) and _is_api(m.name)]
    return (top + methods)[:5]

def js_api(path: Path) -> list:
    text = path.read_text(encoding='utf-8', errors='ignore')
    pats = [r'export\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)',
            r'export\s+const\s+(\w+)', r'^(?:async\s+)?function\s+(\w+)']
    names, seen = [], set()
    for pat in pats:
        for n in re.findall(pat, text, re.MULTILINE):
            if n not in seen and _is_api(n): seen.add(n); names.append(n)
    return names[:5]

def extract_api(path: Path) -> str:
    if path.suffix == '.py': api = python_api(path)
    elif path.suffix in {'.js', '.ts', '.tsx'}: api = js_api(path)
    else: return '—'
    return ', '.join(f'`{n}`' for n in api) if api else '—'

def interface_for(src: Path, ctx_dir: Path) -> str:
    if src.suffix == '.py':                     c = src.with_suffix('.pyi')
    elif src.suffix in {'.js', '.ts', '.tsx'}:  c = src.with_suffix('.d.ts')
    elif src.suffix == '.dart':                  c = src.parent / (src.stem + '.dart.api')
    elif src.suffix == '.tex':                   c = src.with_suffix('.texif')
    else: return '—'
    # as_posix(), not the Path: a markdown link separator is `/` on every operating system. A bare
    # Path formats with os.sep, so regenerating this table on a Windows clone published
    # `](auth\gauth.pyi)` -- a link that resolves nowhere, in a file test_pointer_integrity checks,
    # written by a generator into a versioned file. Found 2026-09-01 by the table rewriting itself.
    rel = c.relative_to(ctx_dir).as_posix()
    return f'[`{rel}`]({rel})' if c.exists() else '—'
