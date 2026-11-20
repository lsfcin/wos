# b20260901 regression — no tracked file in this workspace is a git symlink.
#
# A profile file was stored as mode 120000 pointing at ../USER.md. Windows git runs with
# core.symlinks=false, so that clone materialised a 10-byte text file whose whole content was the
# string `../USER.md`, handed to every reader instead of Lucas's profile.
#
# The ruling this restores is SETUP-clone.md § Skill mirrors (2026-08-29): native symlinks under Git
# Bash need Developer Mode, a privilege out of proportion to this workspace. The skill mirrors became
# copies then; this one file never followed. The class check is the point — a symlink is invisible on
# the machine that creates it and only misreads on the other one, so nothing local ever reports it.
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
GIT_SYMLINK_MODE = '120000'


def _tracked_modes() -> list:
    """(mode, path) for every file the index carries, straight from git."""
    done = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-s'],
                          capture_output=True, text=True, encoding='utf-8')
    rows = []
    for line in done.stdout.splitlines():
        fields = line.split(maxsplit=3)
        if len(fields) == 4:
            rows.append((fields[0], fields[3]))
    return rows


def test_no_tracked_file_is_a_symlink() -> None:
    links = [path for mode, path in _tracked_modes() if mode == GIT_SYMLINK_MODE]
    assert not links, (
        f'tracked symlinks reach the Windows clone as text files holding their own target: {links}. '
        'Point the reader at the real path, or generate a copy — SETUP-clone.md § Skill mirrors.')


if __name__ == '__main__':
    sys.exit(0)
