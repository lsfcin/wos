# T0 the encoding law: no text read or write in this workspace inherits the operating system's
# answer. Zero-token, runs in verify-fast.
#
# THIS FILE IS THE LAW, not a restatement of one kept elsewhere. Four files cited "core/SCHEMA.md
# AD-9" for it and that pointer never resolved: SCHEMA.md holds no AD at all, and the AD-09 that
# does exist (core/SPECS.md) is about session close. The rule was real and its home was not, which
# is the B7 shape exactly -- so it is written here, beside the check that holds it, and cited by
# name rather than by a number that can drift.
#
# THE LAW. A text file is opened, read and written with `encoding='utf-8'`, and a text file is
# WRITTEN with `newline='\n'`. A subprocess whose output is decoded names the same encoding. Not a
# concession to any one system: LF and UTF-8 are the workspace's own answers -- .gitattributes says
# so for every clone -- and a default is whatever the machine happened to be.
#
# WHAT INHERITING COST, measured 2026-09-01 on the Windows clone rather than argued:
#   * `permissions --set` rewrote the tracked core/profile.txt as CRLF. Git normalises on commit, so
#     the repo stayed right and the working tree did not: ` M` in `git status` with an EMPTY diff.
#     That is the unreadable state, and it is what refuses to start a merge (ISSUES.md B9).
#   * Two gate specs failed with `UnicodeDecodeError: 'charmap'` -- the child printed a glyph, the
#     parent decoded cp1252, the reader thread raised, and `result.stdout` came back None. The gate
#     under test was fine. Nothing in the failure said "encoding".
#   * 304 call sites in 113 files were inheriting. The port's own ratchet had recorded this law as
#     owed and guessed "the corpus is clean"; it was not, and no check could see it.
#
# A CEILING OF ZERO IS AN ASSERT, and this one may not creep by one: a single inherited write is a
# tracked file that reads as modified on the next clone that touches it.
#
# NOT COVERED HERE, and deliberately: a program's OWN stdout. `core/run` exports PYTHONIOENCODING
# for everything it spawns, which is every hook and every tool in production, and
# platform_law.speak_utf8() is the answer for a program spawned any other way. A ratchet over that
# would be counting the programs core/run already covers.
import ast
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks'))
sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/entropy'))
from entropy_corpus import tracked_files  # noqa: E402
from file_law import is_tool_entrypoint  # noqa: E402

BOUNDARY = 'core/hooks/platform_law.py'
MODE_CHARS = set('rwxab+t')
SUBPROCESS_CALLS = {'run', 'Popen', 'check_output', 'call', 'check_call'}


def _python_files() -> list:
    """Tracked python: the .py files, plus the extensionless CLIs under core/tools/.

    NOT by shebang, and that miss is why this note exists. The tools dropped their shebangs when
    `core/run` took over starting them (file_law.is_tool_entrypoint says so in as many words), so a
    check that asks for one skips every tool in the workspace — including the writer that first
    caught this whole law rewriting a tracked file with the machine's line ending. Asked through
    file_law, which already owns "what a file IS", instead of a second definition here.

    The shell tools are the exception the predicate cannot see, and they DO carry a shebang: a
    first line naming an interpreter that is not python is not ours to parse.
    """
    found = []
    for path in tracked_files(WORKSPACE_ROOT):
        if path.suffix == '.py':
            found.append(path)
        elif is_tool_entrypoint(path) and path.is_file():
            with path.open('rb') as handle:
                first = handle.readline()
            if not first.startswith(b'#!') or b'python' in first:
                found.append(path)
    return found


def _mode(node) -> str:
    """The mode string of an open() call, or '?' when it is not a literal we can read.

    Two callables share the name and disagree about where the mode sits: the builtin takes the path
    first, `Path.open` takes the mode first. Reading the wrong slot reports a binary open as text --
    and the fix for one of those raises at the call, so a guess here is worse than a miss.
    """
    for keyword in node.keywords:
        if keyword.arg == 'mode':
            return keyword.value.value if isinstance(keyword.value, ast.Constant) else '?'
    slot = 1 if isinstance(node.func, ast.Name) else 0
    if len(node.args) > slot:
        arg = node.args[slot]
        if not isinstance(arg, ast.Constant) or not isinstance(arg.value, str):
            return '?'
        # `zipfile.open('member.txt')` lands here too; a name is not a mode.
        return arg.value if arg.value and set(arg.value) <= MODE_CHARS else '?'
    return 'r'


def _inherits(node) -> list:
    """Which answers this call is taking from the machine instead of naming."""
    if not isinstance(node, ast.Call):
        return []
    have = {k.arg for k in node.keywords if k.arg}
    name = getattr(node.func, 'attr', None) or getattr(node.func, 'id', '')

    if name == 'write_text':
        return [k for k in ('encoding', 'newline') if k not in have]
    if name == 'read_text':
        return [] if 'encoding' in have else ['encoding']
    if name == 'open':
        mode = _mode(node)
        if mode == '?' or 'b' in mode:
            return []
        missing = [] if 'encoding' in have else ['encoding']
        if any(c in mode for c in 'wax+') and 'newline' not in have:
            missing.append('newline')
        return missing
    if (isinstance(node.func, ast.Attribute) and node.func.attr in SUBPROCESS_CALLS
            and isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess'):
        decoding = [k for k in node.keywords if k.arg in ('text', 'universal_newlines')
                    and isinstance(k.value, ast.Constant) and k.value.value is True]
        return ['encoding'] if decoding and 'encoding' not in have else []
    return []


def _findings() -> list:
    hits = []
    for path in _python_files():
        source = path.read_text(encoding='utf-8')
        try:
            tree = ast.parse(source)
        except SyntaxError as broken:
            # NOT `continue`. A file this check cannot parse is a file it cannot clear, and passing
            # it in silence is the failure shape ROADMAP.md § Silent failure names: on the day this
            # check was written, four files were left unparseable by the very edit meant to satisfy
            # it, and the run went green because the skip hid exactly the files that had changed.
            hits.append(f'{path.relative_to(WORKSPACE_ROOT).as_posix()}:{broken.lineno} '
                        f'(unparseable: {broken.msg})')
            continue
        for node in ast.walk(tree):
            for answer in _inherits(node):
                hits.append(f'{path.relative_to(WORKSPACE_ROOT).as_posix()}:{node.lineno} '
                            f'({answer})')
    return sorted(hits)


def test_no_text_read_or_write_inherits_the_os_answer():
    live = _findings()
    assert not live, (
        f'{len(live)} call(s) take the encoding or the line ending from the machine: '
        f'{live[:12]}. Name them — `encoding="utf-8"` on every text read and write, '
        f'`newline="\\n"` on every write, and the same encoding on a subprocess you decode. '
        f'A default is what the machine happened to be, and this workspace has two kinds')


def test_the_declared_line_ending_is_the_one_this_asserts():
    """The law is only worth holding while .gitattributes still says LF for every clone.

    A ratchet that outlives its own premise is the drift these checks exist to catch, so the
    premise is read rather than remembered.
    """
    declared = (WORKSPACE_ROOT / '.gitattributes').read_text(encoding='utf-8')
    assert 'eol=lf' in declared, (
        '.gitattributes no longer declares LF, so the newline half of this check is asserting '
        f'something the workspace stopped saying. Settle it there first, then here and in {BOUNDARY}')
