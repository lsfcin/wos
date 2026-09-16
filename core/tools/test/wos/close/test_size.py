# T1 size tool (ROADMAP.md § Cost): whether the workspace got smaller this session, and where.
# Zero-token, no network — every case builds its own throwaway repo.
#
# The number only means something if it counts what a person wrote: a vendored template or a
# generated dashboard moving by 400 lines would swamp the signal the close exists to show. That is
# why the tool asks core/hooks/file_law.py instead of holding a list, and why the cases below copy
# the real law files rather than faking them.
import os
import shutil
import subprocess

from conftest import WORKSPACE_ROOT
from platform_law import interpreter

SIZE = WORKSPACE_ROOT / 'core/tools/wos/size'
LAW = WORKSPACE_ROOT / 'core/hooks'


def _git(repo, *args):
    return subprocess.run(('git',) + args, cwd=repo, capture_output=True, text=True, encoding='utf-8')


def _repo(tmp_path):
    """A repo with the tool at its real relative path, so its own parents[3] lookup finds the law."""
    ws = tmp_path / 'ws'
    (ws / 'core/tools/wos').mkdir(parents=True)
    (ws / 'core/hooks').mkdir(parents=True)
    dest = ws / 'core/tools/wos/size'
    shutil.copy(SIZE, dest)
    os.chmod(dest, 0o755)
    for name in ('file_law.py', 'feature_law.py', 'platform_law.py',
                 'vendored.txt', 'generated.txt', 'limits.env'):
        shutil.copy(LAW / name, ws / 'core/hooks' / name)
    # The switch travels with the tool: a fixture without it would let a row claiming a switch
    # pass while the tool never asks (core/SPECS.md § AD-14).
    shutil.copy(WORKSPACE_ROOT / 'core/tools/tool_law.py', ws / 'core/tools')
    for name in ('features.txt', 'profile.txt'):
        shutil.copy(WORKSPACE_ROOT / 'core' / name, ws / 'core' / name)

    _git(ws, 'init', '-q', '-b', 'main')
    _git(ws, 'config', 'user.email', 'test@example.com')
    _git(ws, 'config', 'user.name', 'test')
    _git(ws, 'config', 'core.hooksPath', '/dev/null')
    return ws


def _commit(ws, msg='c'):
    _git(ws, 'add', '-A')
    _git(ws, 'commit', '-q', '--no-verify', '-m', msg)
    return _git(ws, 'rev-parse', 'HEAD').stdout.strip()


def _run(ws, *args):
    # BOTH ENDS NAME THE ENCODING (core/tools/test/workspace/test_encoding_ratchet.py). `size` prints `·`; decoding its stdout as
    # utf-8 while the child writes the console codepage raises UnicodeDecodeError on byte 0xb7.
    #
    # The write end used to be left to whatever the environment happened to carry, and these five
    # cases were green only because `core/run` exports PYTHONIOENCODING=utf-8 and the pre-commit
    # gate is a descendant of it. Run `pytest` directly and all five failed — a suite that passes
    # only under one of its two callers is not reporting on the tool. Set it here rather than
    # relying on an ancestor, which is exactly what `run` does for a gate.
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8'}
    return subprocess.run([interpreter(), str(ws / 'core/tools/wos/size'), *args],
                          cwd=ws, capture_output=True, text=True, encoding='utf-8', env=env)


def test_a_session_that_only_deleted_reports_a_negative_net(tmp_path):
    """The question Lucas asked: did the workspace get smaller. A close that cut 6 lines and added
    none must say so with a sign, not with a total that happens to be lower."""
    ws = _repo(tmp_path)
    (ws / 'doc.md').write_text('a\nb\nc\nd\ne\nf\n', encoding='utf-8', newline='\n')
    base = _commit(ws, 'seed')
    (ws / 'doc.md').write_text('a\n', encoding='utf-8', newline='\n')
    _commit(ws, 'cut')

    out = _run(ws, '--since', base).stdout
    assert 'session +0/-5 = -5' in out, out


def test_a_vendored_or_generated_md_is_not_counted(tmp_path):
    """A generated file is authored by nobody and a vendored one by someone else. Counting either
    would let a regenerated dashboard read as a session that wrote 400 lines."""
    ws = _repo(tmp_path)
    (ws / 'doc.md').write_text('mine\n', encoding='utf-8', newline='\n')
    base = _commit(ws, 'seed')

    generated = next(p for p in (LAW / 'generated.txt').read_text(encoding='utf-8').splitlines()
                     if p.strip() and not p.startswith('#') and p.strip().endswith('.md'))
    target = ws / generated.strip()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('x\n' * 50, encoding='utf-8', newline='\n')
    _commit(ws, 'regen')

    out = _run(ws, '--since', base).stdout
    assert 'session +0/-0 = +0' in out, out
    assert '1 .md files' in out, out


def test_without_a_session_it_reports_the_corpus_only(tmp_path):
    """A close on a machine with no transcript still answers how big the corpus is. A report that
    failed here would fail the close, and no measurement is worth that."""
    ws = _repo(tmp_path)
    (ws / 'doc.md').write_text('a\nb\n', encoding='utf-8', newline='\n')
    _commit(ws, 'seed')

    r = _run(ws)
    assert r.returncode == 0
    assert r.stdout.startswith('size: 1 .md files · 2 lines')
    assert 'session' not in r.stdout


def test_the_attribution_names_the_directory_that_moved_most(tmp_path):
    """'The workspace shrank' is not actionable; 'core/skills shrank 180 lines' is."""
    ws = _repo(tmp_path)
    for d in ('big', 'small'):
        (ws / d).mkdir()
        (ws / d / 'doc.md').write_text('x\n', encoding='utf-8', newline='\n')
    base = _commit(ws, 'seed')
    (ws / 'big/doc.md').write_text('x\n' * 30, encoding='utf-8', newline='\n')
    (ws / 'small/doc.md').write_text('x\n' * 3, encoding='utf-8', newline='\n')
    _commit(ws, 'grow')

    out = _run(ws, '--since', base).stdout
    assert 'big +29' in out, out
    assert out.index('big') < out.index('small') if 'small' in out else True


def test_the_delta_obeys_the_same_scope_the_corpus_does(tmp_path):
    """b20260912 — `--scope repo` filtered the corpus and not the delta, so this repo's own
    debt was reported with every line a content tree had moved folded into it. The roadmap item
    that debt belongs to names this exact command as its observable, which made it unverifiable."""
    ws = _repo(tmp_path)
    (ws / 'core').mkdir(exist_ok=True)
    (ws / 'core/doc.md').write_text('x\n', encoding='utf-8', newline='\n')
    (ws / 'code/thing').mkdir(parents=True)
    (ws / 'code/thing/doc.md').write_text('x\n', encoding='utf-8', newline='\n')
    base = _commit(ws, 'seed')
    (ws / 'code/thing/doc.md').write_text('x\n' * 40, encoding='utf-8', newline='\n')
    _commit(ws, 'grow the content tree')

    scoped = _run(ws, '--scope', 'repo', '--since', base).stdout
    assert 'session +0/-0 = +0' in scoped, scoped
    assert '+39/-0 = +39' in _run(ws, '--since', base).stdout


def test_a_missing_transcript_is_not_a_failure(tmp_path):
    """--session for an id with no transcript: the corpus half still prints, exit 0."""
    ws = _repo(tmp_path)
    (ws / 'doc.md').write_text('a\n', encoding='utf-8', newline='\n')
    _commit(ws, 'seed')

    r = _run(ws, '--session', 'no-such-session-id')
    assert r.returncode == 0
    assert r.stdout.startswith('size: 1 .md files')
    assert 'session +' not in r.stdout
