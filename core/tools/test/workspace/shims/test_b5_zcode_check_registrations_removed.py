# T0 B5 regression — the zcode check instruments are out and stay out. Zero-token, verify-fast.
#
# The check registrations (SessionStart dump + WebFetch deny) were instruments, not gates: they
# measured one trusted session (2026-09-04, Sonda 2) and were removed the same session. Nothing
# stops a future session from re-staging them — the deny check blocks every WebFetch and the dump
# check writes /tmp/zcode_check/ on every start, so a silent re-staging would degrade every
# workspace session. This spec holds the removal: the registration names no check, and the
# check directory is gone. Findings from the one run they got: core/experiments/zcode-hook-protocol.md.
import json

from conftest import WORKSPACE_ROOT


def test_b5_the_zcode_registration_names_no_check():
    config = json.loads((WORKSPACE_ROOT / '.zcode/config.json').read_text(encoding='utf-8'))
    commands = [h['command'] for ev in config['hooks']['events'].values()
                for m in ev for h in m['hooks']]
    checks = [c for c in commands if 'check' in c.lower()]
    assert not checks, f'check registrations are back in .zcode/config.json: {checks}'


def test_b5_the_check_directory_is_gone():
    assert not (WORKSPACE_ROOT / 'core/hooks/zcode').exists(), (
        'core/hooks/zcode/ is back -- the 2A direct registration made the adapter home and both '
        'checks done work; git history holds them'
    )
