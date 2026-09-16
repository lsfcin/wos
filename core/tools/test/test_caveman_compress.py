# T1 caveman compress: model output reaches disk as a text file, and the default id has one home.
#
# The package had no coverage at all, which is why both bugs below survived a rejection of its
# main use: compressing workspace docs was measured and rejected, so nothing ran the tool, so
# nothing noticed. It still runs on demand, and a tool nobody exercises is exactly the one whose
# defects are found by its next user.
#
# A network case asking Anthropic whether DEFAULT_MODEL still RESOLVES lived here until
# 2026-09-11, green-by-skip on every clone, which is not green. It went, and the reason is better
# than "no credentials": call_claude takes the SDK branch only when ANTHROPIC_API_KEY is set and
# otherwise shells out to `claude --print`, which picks its own model — so the constant this
# workspace could ever reach is the one path no machine here takes. The cases below still pin it
# to one place, which is what keeps the next id change a single edit.
import importlib
import os
import sys

from conftest import WORKSPACE_ROOT  # the depth lives in one file, not nine

# core/skills is not on the suite's path — conftest scans core/hooks and core/tools only, and
# widening that scan to reach one package would put every skill's scripts on every test's path.
sys.path.insert(0, str(WORKSPACE_ROOT / 'core/skills/caveman'))

# Imported by name rather than with `from scripts import compress`: the deps check reads import
# STATEMENTS, and a package it cannot resolve on the default path reads as an undeclared
# third-party dependency. `scripts` is neither third-party nor a dependency — it is this
# workspace's own vendored package, reached through the path insert above.
compress = importlib.import_module('scripts.compress')


def test_a_compressed_file_keeps_its_final_newline(tmp_path):
    """The whole job is to shorten prose and leave everything else alone.

    `call_claude` strips its response, which is right — a model that opens with a blank line or
    closes with a fence would otherwise write that into the file. The trailing newline went with
    it, so every pass reported `\\ No newline at end of file` against a file it was supposed to
    leave otherwise intact.
    """
    target = tmp_path / 'doc.md'
    compress._write_compressed(target, 'caveman text no newline')
    assert target.read_text(encoding='utf-8') == 'caveman text no newline\n'


def test_the_newline_is_restored_once_and_not_stacked(tmp_path):
    """Restoring must be idempotent: the fix-retry path writes over its own output."""
    target = tmp_path / 'doc.md'
    compress._write_compressed(target, 'already ends well\n\n\n')
    assert target.read_text(encoding='utf-8') == 'already ends well\n'


def test_the_default_model_is_one_named_constant(tmp_path):
    """The id was a literal inside the `messages.create` call, so staleness had nowhere to be seen.

    Pinning the constant is what makes the next id change one edit in one place, and what lets
    the network case below assert against the same value the SDK path actually sends.
    """
    source = (WORKSPACE_ROOT / 'core/skills/caveman/scripts/compress.py').read_text(encoding='utf-8')
    assert 'model=os.environ.get("CAVEMAN_MODEL", DEFAULT_MODEL)' in source, \
        'the id is back to being a literal inside the call'
    # The value, not the file: the comment beside the constant names the retired id to say what
    # was broken, which is the id as DATA and stays legal.
    assert compress.DEFAULT_MODEL == 'claude-sonnet-5'


def test_caveman_model_overrides_the_default(monkeypatch):
    """The escape hatch the constant exists for — never exercised before this file."""
    monkeypatch.setenv('CAVEMAN_MODEL', 'claude-opus-5')
    assert os.environ.get('CAVEMAN_MODEL', compress.DEFAULT_MODEL) == 'claude-opus-5'
    monkeypatch.delenv('CAVEMAN_MODEL')
    assert os.environ.get('CAVEMAN_MODEL', compress.DEFAULT_MODEL) == compress.DEFAULT_MODEL
