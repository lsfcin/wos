# T0 downloads hook (ROADMAP.md § Legibility, [downloads-hook]): "baixei" names what just landed. Zero-token, verify-fast.
#
# Three promises. It speaks only when the prompt says it downloaded something, because every other
# prompt would pay for a list nobody asked for. It lists only the window limits.env declares,
# newest first. And a folder this machine does not have is skipped, never a traceback.
import importlib.util
import json
import os
import subprocess

from conftest import WORKSPACE_ROOT

NOW = 1_800_000_000.0  # a fixed instant: the suite reads no clock (b20260905)

HOOK = WORKSPACE_ROOT / 'core/hooks/session/downloads.py'
_spec = importlib.util.spec_from_file_location('downloads', HOOK)
downloads = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(downloads)


def _file(folder, name, age):
    path = folder / name
    path.write_bytes(b'x' * 2048)
    stamp = NOW - age
    os.utime(path, (stamp, stamp))
    return path


def _run(prompt):
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_TOOL_INPUT'}
    return subprocess.run(['sh', str(WORKSPACE_ROOT / 'core/run'), 'hooks/session/downloads.py'],
                          input=json.dumps({'prompt': prompt, 'session_id': 't'}),
                          capture_output=True, text=True, encoding='utf-8', env=env, check=False)


def test_it_fires_on_the_words_and_nowhere_else():
    for said in ('baixei o pdf', 'Baixado agora', 'acabei de fazer o DOWNLOAD', 'downloads?',
                 'acabei de baixar novamente', 'ele baixou', 'tô baixando'):
        assert downloads.SAID.search(said), said
    for quiet in ('oi', 'revisa o capítulo 3', 'baixa prioridade', 'abaixo do limite'):
        assert not downloads.SAID.search(quiet), quiet


def test_a_neutral_prompt_injects_nothing():
    done = _run('revisa o capítulo 3')
    assert done.returncode == 0 and done.stdout == ''


def test_only_the_window_newest_first(tmp_path):
    a, b = tmp_path / 'a', tmp_path / 'b'
    a.mkdir()
    b.mkdir()
    old = _file(a, 'old.pdf', 3600)
    mid = _file(a, 'mid.pdf', 600)
    new = _file(b, 'new.zip', 30)
    _file(b, '.hidden', 10)
    (b / 'folder').mkdir()
    found = [path for _age, _size, path in downloads.recent([a, b], NOW, 1800)]
    assert found == [new, mid] and old not in found


def test_a_missing_folder_or_a_repeated_one_is_harmless(tmp_path):
    _file(tmp_path, 'one.pdf', 5)
    found = downloads.recent([tmp_path / "absent", tmp_path, tmp_path], NOW, 1800)
    assert len(found) == 1


def test_the_report_caps_and_says_what_it_cut(tmp_path):
    rows = [(i * 60.0, 2048, tmp_path / f'f{i}.pdf') for i in range(5)]
    text = downloads.report(rows, cap=3, window=1800, searched=[tmp_path])
    assert all(f'f{i}.pdf' in text for i in range(3))
    assert 'f3.pdf' not in text and '2 more' in text


def test_nothing_recent_still_answers(tmp_path):
    text = downloads.report([], cap=3, window=1800, searched=[tmp_path])
    assert 'nothing' in text and str(tmp_path) in text


def test_the_window_and_cap_come_from_limits_env():
    body = HOOK.read_text(encoding='utf-8')
    assert 'DOWNLOADS_WINDOW' in body and 'DOWNLOADS_MAX' in body
    limits = (WORKSPACE_ROOT / 'core/hooks/limits.env').read_text(encoding='utf-8')
    assert 'DOWNLOADS_WINDOW=' in limits and 'DOWNLOADS_MAX=' in limits
