# T0 one door: in core/, a PDF is opened raw only by pdf_meta.py (poppler) and pdf_engine.py (the engines). Every other file asks core/run tools/pdf/<leaf>. Zero-token, no network.
#
# Before 2026-09-26 pdftoppm was spawned in four places (pdf_meta, pdf_cli, and twice in slides),
# each with its own flags and its own idea of how poppler numbers the pages. The list of what counts
# as a raw reader lives in pdf_meta.RAW_COMMANDS / RAW_MODULES — the same list the read gate refuses
# an agent — and is not restated here.
import re

import pdf_meta
from conftest import WORKSPACE_ROOT, git_lines

DOORS = {'core/tools/pdf/pdf_meta.py', 'core/tools/pdf/pdf_engine.py'}
COMMAND = re.compile(r"""['"](%s)['"]""" % '|'.join(map(re.escape, pdf_meta.RAW_COMMANDS)))
MODULE = re.compile(r'^\s*(?:import|from)\s+(%s)\b' % '|'.join(map(re.escape, pdf_meta.RAW_MODULES)), re.M)


def _code_files():
    for rel in git_lines('ls-files', 'core'):
        name = rel.rsplit('/', 1)[-1]
        if rel.endswith('.py') or '.' not in name:
            path = WORKSPACE_ROOT / rel
            if path.is_file():
                yield rel, path.read_text(encoding='utf-8', errors='replace')


def _openings(text):
    return [m.group(1) for m in (*COMMAND.finditer(text), *MODULE.finditer(text))]


def test_only_the_two_doors_open_a_pdf_raw():
    found = {rel: hits for rel, text in _code_files() if rel not in DOORS and (hits := _openings(text))}
    assert not found, ('a PDF opened raw outside core/tools/pdf/pdf_meta.py — call pdf_meta, or from '
                       f'another family `core/run tools/pdf/poppler text|render`:\n{found}')


def test_the_scan_sees_the_doors_it_exempts():
    """Guards the guard: a pattern that matched nothing would pass the test above forever."""
    doors = {rel: _openings(text) for rel, text in _code_files() if rel in DOORS}
    assert doors['core/tools/pdf/pdf_meta.py'], 'the poppler door went unseen'
    assert doors['core/tools/pdf/pdf_engine.py'], 'the engine door went unseen'
