# B9 regression — a verification run is not a write.
#
# test_features_wiring checks every registered hook, and one of them is the entropy dashboard,
# which rewrote ISSUES.md (and every nested repo's local list) on each check — measured 2026-08-30
# blocking two merges in one session, because git refuses to start one over a dirty tracked file.
# The dashboard now reports without writing when it sees --dry-run, WOS_DRY_RUN, or the LAW_CHECK
# environment the wiring check already exports. This spec holds that boundary: a check-shaped run must
# leave the working tree byte-identical.
import os
import subprocess
import sys

from conftest import WORKSPACE_ROOT

DASHBOARD = WORKSPACE_ROOT / 'core/hooks/entropy/dashboard/entropy-dashboard.py'
WATCHED = [WORKSPACE_ROOT / 'ISSUES.md',
           WORKSPACE_ROOT / 'code/voti/ISSUES.md',
           WORKSPACE_ROOT / 'code/gira/ISSUES.md']


def _snapshot():
    return {p: p.read_bytes() for p in WATCHED if p.exists()}


def _dashboard(*args, env_extra=None):
    env = {**os.environ, **(env_extra or {})}
    out = subprocess.run([sys.executable, str(DASHBOARD), *args], cwd=WORKSPACE_ROOT, env=env,
                         stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180, encoding='utf-8')
    assert out.returncode == 0, out.stderr
    return out


def test_the_wiring_check_environment_writes_nothing():
    before = _snapshot()
    out = _dashboard(env_extra={'LAW_CHECK': '1'})
    assert '[dry-run]' in out.stdout, 'a check run must say it did not write'
    assert _snapshot() == before


def test_the_explicit_flag_writes_nothing():
    before = _snapshot()
    out = _dashboard('--dry-run')
    assert '[dry-run]' in out.stdout
    assert _snapshot() == before
