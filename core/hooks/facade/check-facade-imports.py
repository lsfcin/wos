#!/usr/bin/env python3
# Blocks cross-module imports that bypass facade files (index.ts / __init__.py).
import sys, re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feature_law  # noqa: E402

# Test files, facade files themselves, and generated dirs are exempt.
EXEMPT_RE = re.compile(
    r'(?:^|/)[^/]*\.(?:test|spec)\.[tj]sx?$'           # TS/JS: *.test.ts, *.spec.ts
    r'|(?:^|/)(?:test_[^/]*|[^/]*_test)\.(?:py|dart)$'  # Python/Dart: test_*.py, *_test.dart
    r'|(?:^|/)(?:__init__\.py|index\.(?:[tj]sx?|dart))$' # facade files themselves
    r'|(?:^|/)(?:generated|vendor|node_modules)/'
    r'|(?:^|/)[^/]*\.config\.[tj]sx?$',                 # config files (eslint.config.js etc.)
    re.IGNORECASE,
)

# Matches: from '...', export ... from '...', require('...')  — relative paths only.
TS_FROM_RE   = re.compile(r'''(?:from|require\s*\()\s*['"](\.[^'"]+)['"]''')
# Matches: from ..pkg.submod import  — relative Python imports descending into a submodule.
# The module part must START WITH A NAME. Without that bound `\S+` ate the second dot of
# `from .. import x` — the form that goes THROUGH the parent facade — and every one of those
# was reported as a violation, with a message naming no module (2026-09-12, 16 files in
# code/aiwbot on the way in). A dotless `from . import x` was never matched at all, so the
# bug only ever fired on the import the rule is meant to bless.
PY_REL_RE    = re.compile(r'^from\s+(\.+)([A-Za-z_]\S*)\s+import', re.MULTILINE)
# Matches: import '../folder/file.dart' or export '../folder/file.dart'
DART_FROM_RE = re.compile(r'''(?:import|export)\s+['"](\.[^'"]+\.dart)['"]''')


def ts_violations(path: Path, src: str) -> list[str]:
    out = []
    for m in TS_FROM_RE.finditer(src):
        imp = m.group(1).rstrip('/')
        target = (path.parent / imp).resolve()
        if target.parent == path.parent.resolve():
            continue  # same folder — intra-module, always OK
        if target.is_dir() or target.stem == 'index':
            continue  # resolves to folder (index.ts) or explicit 'index' — OK
        out.append(f"  {path}: '{imp}' bypasses facade → import from '{target.parent.name}/' instead")
    return out


def py_violations(path: Path, src: str) -> list[str]:
    out = []
    for m in PY_REL_RE.finditer(src):
        dots, mod = m.group(1), m.group(2)
        if '.' in mod:  # from ..pkg.submod import — descends past __init__
            pkg = mod.split('.')[0]
            out.append(
                f"  {path}: 'from {dots}{mod}' bypasses facade → use 'from {dots}{pkg}' instead"
            )
    return out


def dart_violations(path: Path, src: str) -> list[str]:
    out = []
    for m in DART_FROM_RE.finditer(src):
        imp = m.group(1)
        target = (path.parent / imp).resolve()
        if target.parent == path.parent.resolve():
            continue  # same folder — intra-module, OK
        if target.name == 'index.dart':
            continue  # explicit facade import — OK
        out.append(f"  {path}: '{imp}' bypasses facade → import 'index.dart' from '{target.parent.name}/' instead")
    return out


def check(f: str) -> list[str]:
    path = Path(f).resolve()
    if not path.is_file() or EXEMPT_RE.search(f.replace('\\', '/')):
        return []
    try:
        src = path.read_text(encoding='utf-8', errors='ignore')
    except OSError:
        return []
    if path.suffix in {'.ts', '.tsx', '.js', '.jsx'}:
        return ts_violations(path, src)
    if path.suffix == '.py':
        return py_violations(path, src)
    if path.suffix == '.dart':
        return dart_violations(path, src)
    return []


if __name__ == '__main__':
    # facade-discipline, one of the four features the ablation names. It spans two files —
    # this import block and facade/facade-gate.py's read gate — and the registry's `wired`
    # column holds one path, so both are guarded and this one is named. Guarding only one
    # would leave the feature half-off and make the ablation price a cost nobody removed.
    if not feature_law.is_enabled('facade-discipline'):
        sys.exit(0)
    files = sys.argv[1:] or [ln.strip() for ln in sys.stdin if ln.strip()]
    violations = [v for f in files for v in check(f)]
    if violations:
        print('⛔ Facade boundary violations — cross-module imports must go through index / __init__:\n')
        for v in violations:
            print(v)
        print('\n  Fix: add index.ts / __init__.py / index.dart to the target folder, then import from it.')
        print('  Exempt: test files, index.ts, __init__.py, generated/ and vendor/ dirs.')
        print('  Override (temporary): git commit --no-verify\n')
        sys.exit(1)
