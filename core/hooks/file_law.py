#!/usr/bin/env python3
# What a file IS, and which rules apply to it. The numeric-law sibling of schema_law.py:
# that module parses core/SCHEMA.md, this one owns the file-shape law every size, crowding
# and line-count check reads.
#
# Why it exists (2026-07-31): "a code file" was defined in four checkers, no two agreeing, so the
# BLOCKING gate could not see `.sh` or an extensionless executable. One definition, one home.
import fnmatch
import re
from pathlib import Path
from platform_law import rel as _rel

HERE = Path(__file__).resolve().parent
LIMITS_FILE = HERE / 'limits.env'
VENDORED_FILE = HERE / 'vendored.txt'
GENERATED_FILE = HERE / 'generated.txt'
EXTENSIONLESS_FILE = HERE / 'extensionless.txt'
DESCRIBED_FILE = HERE / 'described.txt'

# Things the line cap and the crowding signal apply to. `.md` is not here: is_authored_prose below
# answers for it. `.tex` is code on purpose — a paper section file is authored under the same line
# rule (academy/papers/SPECS.md § File size).
CODE_EXTS = {'.js', '.jsx', '.ts', '.tsx', '.py', '.dart', '.sh',
             '.html', '.css', '.scss', '.tex'}

# A stub is generated FROM its source and rides in the routing table's Interface column.
GENERATED = ('.pyi', '.d.ts', '.dart.api', '.texif')

# Files that ARE their own interface, so nothing generates one beside them and the read gate never
# fires on one. It was spelled out in four places — stubgen, both facade hooks and the routing
# scanner — which had already drifted in what they CALLED it.
FACADES = {'index.ts', 'index.tsx', 'index.js', 'index.jsx', '__init__.py', 'index.dart'}

# How a file of each kind declares what it is. One home, because it used to have three, and only
# the shell one ran at commit time — as a warning, over code extensions alone.
EXAMPLE_COMMENT = {
    '.py': '# Short description',      '.js': '// Short description',
    '.ts': '// Short description',     '.tsx': '// Short description',
    '.jsx': '// Short description',    '.dart': '// Short description',
    '.sh': '# Short description',      '.css': '/* Short description */',
    '.scss': '/* Short description */', '.html': '<!-- Short description -->',
    '.yaml': '# Short description',    '.yml': '# Short description',
    '.toml': '# Short description',    '.env': '# Short description',
    '.txt': '# Short description',     '.tex': '% Short description of this section',
    '.md': '# Title of this document',
}


def is_tool_entrypoint(path: Path) -> bool:
    """An extensionless CLI under core/tools/, by SHAPE — not by the shebang that named one
    machine's venv and made all 33 unrunnable elsewhere."""
    return not path.suffix and '/core/tools/' in f'/{path.as_posix()}'


def is_code_file(path: Path) -> bool:
    """One definition. An extension, a core/tools CLI, or a shebang — the last two arms closing the
    blind spot that hid pre-commit and every core/tools CLI from the cap (31 files)."""
    if path.name.endswith(GENERATED):
        return False
    if path.suffix in CODE_EXTS:
        return True
    if path.suffix:
        return False
    try:
        return is_tool_entrypoint(path) or path.open('rb').read(2) == b'#!'
    except OSError:
        return False


def load_limits() -> dict:
    """Every numeric limit, from the one file that holds them."""
    limits = {}
    for line in LIMITS_FILE.read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if '=' in line:
            key, value = line.split('=', 1)
            limits[key.strip()] = int(value.strip())
    return limits


def _lines(path: Path) -> list:
    text = path.read_text(encoding='utf-8') if path.exists() else ''
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith('#')]


def allowed_extensionless() -> set:
    """Basenames an external tool dictates, so they cannot carry an extension."""
    return set(_lines(EXTENSIONLESS_FILE))


def _listed(path: Path, root: Path, declaration: Path) -> bool:
    """True when this path matches a glob in one of the sibling declaration files.

    Two questions of one shape — is this path in a named, reviewed list — so one reader. Why each
    list exists is stated in its own head, where a rule about a data file belongs."""
    try:
        rel = _rel(path.resolve(), root)
    except ValueError:
        return False
    return any(fnmatch.fnmatch(rel, p) for p in _lines(declaration))


def is_vendored(path: Path, root: Path) -> bool:
    """Third-party files we did not author and must not police — core/hooks/vendored.txt."""
    return _listed(path, root, VENDORED_FILE)


def is_generated_artifact(path: Path, root: Path) -> bool:
    """A file one of OUR tools writes — core/hooks/generated.txt. Separate from is_vendored: that
    list is provenance we do not own, this one is provenance we do."""
    return _listed(path, root, GENERATED_FILE)


def described() -> dict:
    """{path: description} for a file whose format has no comment syntax to carry one — JSON is the
    class. core/hooks/described.txt says which, and why it is not a net."""
    rows = (ln.split('\t', 1) for ln in _lines(DESCRIBED_FILE) if '\t' in ln)
    return {name.strip(): text.strip() for name, text in rows}


def is_authored(path: Path, root: Path) -> bool:
    """True when our authoring rules apply: code, ours, and written by a person. The one question
    every size and shape gate actually asks, so they ask it in one place."""
    return (is_code_file(path) and not is_vendored(path, root)
            and not is_generated_artifact(path, root))


BLOCK_OPEN = re.compile(r'^\s*<!--\s*[\w-]+:start\s*-->')
BLOCK_CLOSE = re.compile(r'^\s*<!--\s*[\w-]+:end\s*-->')


def generated_spans(text: str) -> list:
    """(start, end) line numbers of the blocks a generator owns inside an authored file.

    `is_generated_artifact` answers for WHOLE files; this is the other half, which three readers
    needed separately before 2026-09-11. Inside a block there is no legal fix — core/SCHEMA.md
    forbids hand-editing one — so a finding there is one nobody can act on. Never the whole file:
    an authored file's own half stays held to every rule.
    """
    spans, opened = [], None
    for number, line in enumerate(text.splitlines(), 1):
        if BLOCK_OPEN.match(line):
            opened = number
        elif BLOCK_CLOSE.match(line) and opened:
            spans.append((opened, number))
            opened = None
    return spans


def is_generated_line(text: str, number: int) -> bool:
    """Whether one 1-indexed line of an authored file sits inside a generated block."""
    return any(start <= number <= end for start, end in generated_spans(text))


def is_authored_prose(path: Path, root: Path) -> bool:
    """The prose twin, for the gates that hold .md to the same line cap (2026-08-18).

    A separate predicate rather than a wider is_authored, because entropy_crowding counts MODULES in
    a directory — a flat collection of documents is a legitimate shape, and brain/goals/ is 57
    files. It lives here rather than in the gates that ask it, for the reason the whole module
    exists: the same question answered in two files drifts.
    """
    return (path.suffix == '.md' and not is_vendored(path, root)
            and not is_generated_artifact(path, root))


