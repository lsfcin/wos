# B11 regression — a credential file is written tight, by the writer, on every system.
#
# The Google token directories landed at 775 with 664 token files: any local account could read
# a live refresh token, and nothing in the workspace set a mode when it wrote. platform_law owns
# the boundary (secure_dir / secure_file) and gauth applies it where it writes. Ruling 2026-08-31
# (Lucas): tightening must not break multi-user local use — tokens live per-HOME, so another
# account's own tool runs keep working; what stops is every other account reading THIS one's.
import os
import pathlib
import stat
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))  # core/tools, for gauth
from platform_law import is_owner_only, secure_dir, secure_file  # noqa: E402

posix_only = pytest.mark.skipif(os.name != 'posix',
                                reason='mode bits are the POSIX answer; an ACL system owes the '
                                       'boundary its own and this file must not fake one')


@posix_only
def test_secure_dir_leaves_a_directory_owner_only(tmp_path):
    d = tmp_path / 'workspace-drive'
    d.mkdir()
    secure_dir(d)
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
    assert is_owner_only(d)


@posix_only
def test_secure_file_makes_an_existing_file_owner_only(tmp_path):
    f = tmp_path / 'token.json'
    f.write_text('{}', encoding='utf-8', newline='\n')
    os.chmod(f, 0o664)
    secure_file(f)
    assert stat.S_IMODE(f.stat().st_mode) == 0o600


@posix_only
def test_the_token_config_dir_is_written_tight(tmp_path, monkeypatch):
    monkeypatch.setattr(pathlib.Path, 'home', classmethod(lambda cls: tmp_path))
    import gauth  # noqa: E402  (needs the core/tools path set above)
    d = gauth.config_dir('drive')
    assert d.is_dir()
    assert stat.S_IMODE(d.stat().st_mode) == 0o700
