# b20261119 regression — the root ISSUES.md is authored whole and held to the cap like any file.
#
# Its generated blocks left git on 2026-11-19 (core/hooks/git/SPECS.md § Close). A waiver in
# core/hooks/generated.txt then exempted a file with nothing generated in it, and the size tool
# weighed the most-read list at zero.
import fnmatch

import file_law
from conftest import WORKSPACE_ROOT


def test_the_root_list_is_not_waived():
    patterns = [line.strip() for line in (WORKSPACE_ROOT / 'core/hooks/generated.txt')
                .read_text(encoding='utf-8').splitlines() if line.strip() and not line.startswith('#')]
    assert not any(fnmatch.fnmatch('ISSUES.md', p) for p in patterns)


def test_the_root_list_is_under_the_cap():
    text = (WORKSPACE_ROOT / 'ISSUES.md').read_text(encoding='utf-8')
    limits = file_law.load_limits()
    assert len(text.splitlines()) < limits['BLOCK_LINES'] and len(text) < limits['BLOCK_CHARS']
