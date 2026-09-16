#!/usr/bin/env python3
# Level 0 naming and placement, parsed from core/SCHEMA.md. Zero-token, deterministic.
#
# Scope is AUTHORED files only. The 91 tracked paths carrying spaces and accents are all
# received documents (.docx/.pdf/.html from the PPC process) whose names are their
# provenance — renaming them would destroy the link to the official source. The rule is
# about the corpus we write, so it checks the corpus we write.
#
# "Full words, not truncations" is NOT here: it is undecidable in general, so it is
# enforced by declaration instead — core/SCHEMA.md § Retired tokens, checked by
# entropy_list.py. A truncation becomes catchable the moment someone retires it.
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from entropy_corpus import LINK_RE, is_generated_mirror, owning_repo, tracked_paths  # noqa: E402
from entropy_context import ROUTING_END, ROUTING_START  # noqa: E402
from platform_law import posix, rel  # noqa: E402

# A finding is TEXT: it lands in ISSUES.md and is matched against baselines spelled with `/`.
# Spelled by the boundary so the same file produces the same finding on every machine — a `\` here
# silently un-baselined every waiver and reported reviewed exceptions as new violations.
def _head(path) -> str:
    return posix(path)


AUTHORED = {'.md', '.py', '.ts', '.tsx', '.js', '.jsx', '.sh', '.dart',
            '.yaml', '.yml', '.json', '.css', '.scss', '.tex'}

# A leading underscore marks scaffolding (_template.md, _material/), a leading dot marks
# a config file (.agentrc.json); dots and underscores are allowed inside a stem because
# Python modules are snake_case by their own law, and `__init__` is mandated by it.
STEM_OK = re.compile(r'^[_.]?[a-z0-9]+([-_.][a-z0-9]+)*$|^__[a-z0-9]+__$')
# Scaffolding directories hold shapes, not instances: a template README.md is a template,
# not a claim that the directory is a repo.
SCAFFOLD_DIR = re.compile(r'^_')
UPPERCASE_MD = re.compile(r'^[A-Z][A-Z0-9_.-]*\.md$')
# The sanctioned second shape: ROADMAP-<name>.md (AGENTS.md — a plan may live in a
# ROADMAP-<name>.md referenced from the ROADMAP).
TYPE_NAME = re.compile(r'^([A-Z][A-Z0-9_-]*)-([a-z0-9]+(?:-[a-z0-9]+)*)$')
DIR_OK = re.compile(r'^[_.]?[a-z0-9]+([-_.][a-z0-9]+)*$')
# academy/papers/<year>-<VENUE>-<name>: the venue is an acronym and is uppercase in every
# citation of it. A convention that is correct in the outside world outranks ours.
PAPER_DIR = re.compile(r'^\d{4}-[A-Z0-9]+-[a-z0-9][a-z0-9_-]*$')
UNTYPEABLE = re.compile(r'\s|[^\x00-\x7f]')

# The JS/TS ecosystem names components PascalCase and hooks/utils camelCase. That is its
# law the way snake_case is Python's, and a checker that fights it just gets switched off.
JS_LIKE = {'.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'}
JS_STEM = re.compile(r'^[A-Za-z][A-Za-z0-9]*(\.[A-Za-z0-9]+)*$')


def check_shape(path: Path, allowed: set) -> str | None:
    """Filename shape: lowercase instance, allowlisted type, or TYPE-name."""
    if path.suffix not in AUTHORED:
        return None
    name = path.name
    if UNTYPEABLE.search(name):
        return (f'{_head(path)}: filename carries a space or a non-ASCII character.\n'
                f'   Authored files are kebab-case ASCII — they get typed, quoted and\n'
                f'   grepped constantly, and a space breaks all three.')
    if UPPERCASE_MD.match(name):
        return None  # a type name; type-gate.py owns the allowlist question
    stem = name[:-len(path.suffix)]
    if path.suffix in JS_LIKE and JS_STEM.match(stem):
        return None
    typed = TYPE_NAME.match(stem)
    if typed and f'{typed.group(1)}.md' in allowed and path.suffix == '.md':
        return None
    if STEM_OK.match(stem):
        return None
    return (f"{_head(path)}: '{name}' is neither a lowercase instance nor a known type.\n"
            f'   Lowercase instances are kebab-case (snake_case for Python modules);\n'
            f'   a type is UPPERCASE.md, optionally TYPE-<name>.md. The mixed\n'
            f'   <name>.TYPE.md shape is retired (core/SCHEMA.md § The `.md` type system).')


def untracked_routing_targets(files: list, root: Path) -> list:
    """A routing table pointing at a file git does not carry.

    The general form of the TYPE_NAME question above, and it sits here for that reason: the shape
    law says a `TYPE-<name>.md` is a real part of its type, and this says the tree really has one.
    A name that passes `check_shape` and a file a clone never receives are the same defect read
    from two ends.

    NOBODY WAS WATCHING THIS, and two gates each had a reason not to.
    `test_pointer_integrity.check_pointers` strips the routing block before it looks, because a
    stale generated table is a generator bug rather than an authoring one; and what it does see it
    waives through `_deliberately_absent`, because a link into a gitignored path cannot be fixed by
    editing the file that carries it. Both are right about blocking and wrong about silence: the
    fix is real, it is just in `.gitignore` rather than in the prose. So this reports and never
    blocks, which is what the dashboard is for.

    Generated mirrors are not findings. `.opencode/` and `.zcode/` rebuild their skill trees from
    `core/skills/` on every sync and git is meant to ignore them — 27 of the 40 links found the day
    this was written. `is_generated_mirror` already knows them; a second list here is the drift
    these checks exist to catch.
    """
    tracked = tracked_paths(root, nested=True)
    findings = []
    for path in files:
        if path.name != 'CONTEXT.md' or is_generated_mirror(path):
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeDecodeError):
            continue
        if ROUTING_START not in text or ROUTING_END not in text:
            continue
        block = text.split(ROUTING_START, 1)[1].split(ROUTING_END, 1)[0]
        for link in sorted(set(LINK_RE.findall(block))):
            if link.startswith(('http://', 'https://', 'mailto:')) or '<' in link:
                continue
            target = (path.parent / link.split('#', 1)[0]).resolve()
            if is_generated_mirror(target) or target.resolve() in tracked:
                continue
            if not target.is_file() or owning_repo(target, root) != root.resolve():
                # A broken link, another repo's file, or a bare directory. The first is
                # test_pointer_integrity's, the second is that repo's own list's, and git has
                # no object for the third — none of them is a routing table carrying a lie.
                continue
            findings.append(
                f'{_head(path)}: routes to {rel(target, root)}, which this repo does not\n'
                f'   track. A clone gets the table and not the file, so the row points at\n'
                f'   nothing. Track the target, or stop routing to it.')
    return sorted(set(findings))


def check_dirs(path: Path, root: Path) -> str | None:
    """Every directory holding authored files is lowercase — case-only differences are
    invisible on macOS and fatal on Linux, and a path is typed far more often than read."""
    if path.suffix not in AUTHORED:
        return None
    try:
        parts = path.resolve().relative_to(root).parts[:-1]
    except ValueError:
        parts = path.parts[:-1]
    bad = next(((i, p) for i, p in enumerate(parts)
                if not DIR_OK.match(p) and not PAPER_DIR.match(p)), None)
    if bad is None:
        return None
    index, name = bad
    # Anchor the finding on the DIRECTORY, not the file: one bad directory holding 82
    # files is one violation with one fix, and reporting it 82 times buries the other 81
    # findings on the dashboard.
    return (f"{'/'.join(parts[:index + 1])}: directory {name!r} is not lowercase "
            f'kebab-case.\n'
            f'   Directories are lowercase; only .md types are uppercase.')


def check_placement(path: Path, scopes: dict, root: Path) -> str | None:
    """A type that declares a scope in core/SCHEMA.md must live inside it."""
    scope = scopes.get(path.name)
    if scope is None or any(SCAFFOLD_DIR.match(p) for p in path.parts):
        return None
    parent = path.resolve().parent
    if scope == 'root':
        if parent != root.resolve():
            return (f'{_head(path)}: {path.name} is declared root-only in core/SCHEMA.md.\n'
                    f'   A second one competes with the first for the same authority.')
    elif scope == 'repo-root' and not (parent / '.git').exists():
        return (f'{_head(path)}: {path.name} is declared repo-root-only in core/SCHEMA.md.\n'
                f'   It answers "I just cloned this" — a directory nobody clones does\n'
                f'   not get one; describe it in CONTEXT.md instead.')
    return None
