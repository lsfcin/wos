# T0 file law (core/hooks/SPECS.md). Zero-token, runs in verify-fast.
#
# Why this file exists is core/hooks/file_law.py's own head: "a code file" was defined in five
# checkers at once, and what they disagreed about was invisible to the BLOCKING gate.
# test_no_checker_carries_its_own_extension_list is the one that makes that unrepeatable.
import re
import subprocess
import sys
from pathlib import Path

from conftest import WORKSPACE_ROOT, needs  # the depth lives in one file, not nine
# sys.path for the enforcement layer is set once, by conftest.py — a second copy
# here would go stale the next time core/hooks is split.

from file_law import (CODE_EXTS, allowed_extensionless, is_code_file,  # noqa: E402
                      is_tool_entrypoint, is_vendored, load_limits)
from platform_law import posix  # noqa: E402

HOOKS = WORKSPACE_ROOT / 'core/hooks'


def test_an_extensionless_executable_is_code(tmp_path) -> None:
    """The blind spot that let a 385-line pre-commit through, closed."""
    script = tmp_path / 'pre-commit'
    script.write_text('#!/usr/bin/env bash\necho hi\n', encoding='utf-8', newline='\n')
    assert is_code_file(script)


def test_an_extensionless_plain_file_is_not_code(tmp_path) -> None:
    plain = tmp_path / 'LICENSE'
    plain.write_text('MIT\n', encoding='utf-8', newline='\n')
    assert not is_code_file(plain)


def test_shell_scripts_are_code(tmp_path) -> None:
    assert is_code_file(tmp_path / 'deploy.sh')


def test_generated_stubs_are_not_code(tmp_path) -> None:
    """A stub is produced FROM its source; policing it would double-count the source."""
    for name in ('mod.pyi', 'mod.d.ts'):
        assert not is_code_file(tmp_path / name)


def test_prose_is_not_code(tmp_path) -> None:
    """Doc length is a signal, never a cap — .md must never enter the blocking population."""
    for name in ('ROADMAP.md', 'data.yaml', 'pyproject.toml'):
        assert not is_code_file(tmp_path / name)


def test_tex_is_code_because_papers_say_so() -> None:
    """academy/papers/SPECS.md § File size puts section files under the same 200-line rule."""
    assert '.tex' in CODE_EXTS


def test_vendored_templates_are_exempt() -> None:
    """17 of 28 over-cap files are conference templates. Upstream's layout is not ours."""
    template = WORKSPACE_ROOT / 'academy/papers/ai4good/sigconf-i13n.tex'
    ours = WORKSPACE_ROOT / 'core/hooks/file_law.py'
    assert is_vendored(template, WORKSPACE_ROOT)
    assert not is_vendored(ours, WORKSPACE_ROOT)


def test_every_checker_resolves_the_workspace_root_to_the_workspace() -> None:
    """A checker one directory off reads the law correctly and then applies it to nothing.

    `vendored.txt` patterns are workspace-relative, so a checker whose WORKSPACE_ROOT is
    `core/` matches none of them: is_vendored() returns False for every path and the
    exemption silently stops existing. The write gates' own root carried exactly that bug —
    `parents[2]` from `core/hooks/checks/` — so editing a vendored file past the cap was blocked
    by the gate `vendored.txt` was written to waive. Nothing failed; the waiver never applied.

    Asserted against the marker file rather than a hardcoded depth, so moving a checker
    breaks this test instead of silently disabling its exemptions.
    """
    for checker in sorted(HOOKS.rglob('*.py')):
        text = checker.read_text(encoding='utf-8')
        match = re.search(r'WORKSPACE_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]',
                          text)
        if not match:
            continue
        root = checker.resolve().parents[int(match.group(1))]
        assert (root / 'AGENTS.md').exists(), (
            f'{checker.relative_to(WORKSPACE_ROOT)} resolves WORKSPACE_ROOT to {root}, which '
            f'is not the workspace — every workspace-relative law it reads will match nothing')


def test_the_vendored_waiver_reaches_the_edit_gate() -> None:
    """The end-to-end version: a real vendored file, through the size gate's own root.

    It follows the SIZE half of the 2026-09-14 split, because the cap is what the waiver waives —
    `write_payload.py` declares the root and `size-gate.py` is the caller that spends it.
    """
    needs('academy')
    gate = HOOKS / 'checks/write_payload.py'
    depth = int(re.search(r'WORKSPACE_ROOT = Path\(__file__\)\.resolve\(\)\.parents\[(\d+)\]',
                          gate.read_text(encoding='utf-8')).group(1))
    root = gate.resolve().parents[depth]
    # A vendored file this repo TRACKS. The fixture was code/corpora/depth_anything_v2/, which
    # lives in a NESTED repo — so on any clone that has not also cloned it, this failed for a
    # reason the workspace cannot fix, and blamed a fixture that had not moved.
    vendored = WORKSPACE_ROOT / 'academy/administration/pda/template_extracted/word/document.xml'
    assert vendored.exists(), 'fixture moved — pick another path listed in vendored.txt'
    assert is_vendored(vendored, root)


def test_every_extensionless_tracked_file_is_explained() -> None:
    """Extensionless is allowed but never accidental: an outside name, a tool, or a shebang.

    Git names its own hooks, make names its own file, and core/tools names a tool for the
    provider it wraps. Each exemption is a NAMED category, which is what stops extensionless
    files being a blind spot again. The shebang arm used to cover the 33 tools and covered
    them wrongly — the line they carried named one machine's venv, so it was evidence of the
    port defect rather than of anything being runnable. is_entrypoint is the honest answer.
    """
    mandated = allowed_extensionless()
    out = subprocess.run(['git', 'ls-files'], cwd=WORKSPACE_ROOT,
                         capture_output=True, text=True, encoding='utf-8').stdout
    unexplained = []
    for rel in out.splitlines():
        path = WORKSPACE_ROOT / rel
        if Path(rel).suffix or not path.is_file() or path.name in mandated:
            continue
        if is_vendored(path, WORKSPACE_ROOT) or is_tool_entrypoint(path):
            continue
        try:
            if path.open('rb').read(2) != b'#!':
                unexplained.append(rel)
        except OSError:
            continue
    assert not unexplained, (
        f'extensionless files that are neither a core/tools entrypoint, vendored, executable, '
        f'nor listed in core/hooks/extensionless.txt: {unexplained}')


# Extension sets in the hook tree that are deliberately NOT "a code file". Each names a
# different population, so importing is_code_file would be wrong, not right. Named and
# reviewed — the same shape as vendored.txt, and for the same reason: the alternative is a
# heuristic that quietly decides for us.
NOT_THE_CODE_LAW = {
    'file_law.py':                    'THE LAW ITSELF — it holds the one list every other checker '
                                      'imports. It passed unlisted only while a usage string '
                                      'happened to spell its own name (2026-09-12)',
    'entropy/entropy_corpus.py':      'SCANNED — text files worth walking, includes .md/.json',
    'entropy/entropy_naming.py':      'AUTHORED — the files our naming rules apply to',
    'facade/check-facade-imports.py': 'per-language import syntax, not file-ness',
    'facade/facade-scan.py':          'extension -> facade filename',
    'commit/gates_project.py':        'TESTED — languages a code/ project runs a suite for, which '
                                      'is narrower than "code": staging a .tex or .css does not '
                                      'oblige a project to declare verify:fast',
    'stubgen/stubs.py':               'STUBBED — types that have a generated interface, narrower '
                                      'than "code": .sh and .css are code files nothing stubs, '
                                      'and .dart is stubbed by dart-api-extract, not from here',
}


def test_no_checker_carries_its_own_extension_list() -> None:
    """The defect this whole module exists to prevent: a second definition of "code".

    Walks the hook tree rather than naming checkers. The hand-list this replaced covered 14
    of 62 files and had no way to notice the other 48 — a blind spot that survived the
    core/hooks split precisely because nothing measured it.
    """
    offenders = []
    for path in sorted(HOOKS.rglob('*')):
        relative = path.relative_to(HOOKS)
        if any(part.startswith(('.', '_')) for part in relative.parts):
            continue
        # posix(), not str(): the keys below are spelled with `/`, and on a clone where a path
        # stringifies with `\` not one exemption matched — so four reviewed populations were
        # reported as offenders and the real ones were invisible in the noise.
        name = posix(relative)
        if not path.is_file() or not is_code_file(path) or name in NOT_THE_CODE_LAW:
            continue
        source = path.read_text(encoding='utf-8', errors='ignore')
        restates = ("'.py'" in source and "'.ts'" in source) or 'js|ts|tsx|py' in source
        if restates and 'file_law' not in source:
            offenders.append(name)
    assert not offenders, (
        f'these restate the code-file law instead of importing file_law: {offenders}. '
        f'If the set is a different population, add it to NOT_THE_CODE_LAW with the reason.')


def test_the_exemption_list_has_no_corpses() -> None:
    """An exemption that no longer names a real file stops exempting and starts hiding."""
    missing = sorted(name for name in NOT_THE_CODE_LAW if not (HOOKS / name).exists())
    assert not missing, f'NOT_THE_CODE_LAW names files that do not exist: {missing}'


def test_every_limit_has_one_home() -> None:
    """Every number, one file. A checker hard-coding one of them is drift.

    Asserted as a subset, not an equality: pinning the exact set made adding a limit
    fail here for a reason that has nothing to do with the file law (it happened when
    the context meter landed CTX_WARN/CTX_LOUD). What must hold is that each pair is
    present and ordered warn-before-block, not that the population never grows.
    """
    limits = load_limits()
    assert {'WARN_LINES', 'BLOCK_LINES', 'WARN_FILES', 'BLOCK_FILES'} <= set(limits)
    assert limits['WARN_LINES'] < limits['BLOCK_LINES']
    assert limits['WARN_FILES'] < limits['BLOCK_FILES']
    scanner = (HOOKS / 'routing/workspace_scanner.py').read_text(encoding='utf-8')
    assert 'SPLIT_THRESHOLD = 7' not in scanner
