# T0 pr-reminder (academy/administration/ROADMAP.md [docs-ufrpe-pr-inbox]): an open PR is one INBOX entry until it closes. Zero-token, gh faked.
import importlib.util
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location('reminders', ROOT / 'core/hooks/session/reminders.py')
reminders = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reminders)

HEAD = '# inbox\n\n---\n\n<!-- add entries below, newest first -->\n\n'
NOW = 1_800_000_000.0


def setup(tmp_path, monkeypatch, prs, body='uma ideia solta\n— via aiwbot · 2026-11-17\n'):
    inbox = tmp_path / 'INBOX.md'
    inbox.write_text(HEAD + body, encoding='utf-8', newline='\n')
    monkeypatch.setattr(reminders, 'INBOX', inbox)
    monkeypatch.setattr(reminders, 'PR_STATE', tmp_path / 'state.json')
    monkeypatch.setattr(reminders.feature_law, 'setting', lambda k, d='': 'dono/repo' if k == 'pr-watch' else d)
    monkeypatch.setattr(reminders, '_open_prs', lambda repo: prs)
    return inbox


def pr(n, title='Adiciona calendário 2027'):
    return {'number': n, 'title': title, 'author': {'login': 'alguem'}, 'url': f'https://github.com/dono/repo/pull/{n}'}


def test_a_new_pr_becomes_one_entry_and_is_said(tmp_path, monkeypatch):
    inbox = setup(tmp_path, monkeypatch, [pr(3)])
    line = reminders.prs(now=NOW)
    text = inbox.read_text(encoding='utf-8')
    assert 'PR aberto em dono/repo #3: "Adiciona calendário 2027"' in text
    assert 'uma ideia solta' in text and line.startswith('PRS: 1')


def test_the_entry_is_not_duplicated_and_leaves_when_the_pr_closes(tmp_path, monkeypatch):
    inbox = setup(tmp_path, monkeypatch, [pr(3)])
    reminders.prs(now=NOW)
    assert reminders.prs(now=NOW + reminders.PR_EVERY) == ''
    assert inbox.read_text(encoding='utf-8').count('#3:') == 1
    monkeypatch.setattr(reminders, '_open_prs', lambda repo: [])
    reminders.prs(now=NOW + 2 * reminders.PR_EVERY)
    text = inbox.read_text(encoding='utf-8')
    assert '#3:' not in text and 'uma ideia solta' in text


def test_gh_failing_changes_nothing(tmp_path, monkeypatch):
    body = 'PR aberto em dono/repo #3: "x" (de a) — u\nrevisar\n— via pr-reminder · 2026-11-18\n'
    inbox = setup(tmp_path, monkeypatch, None, body)
    assert reminders.prs(now=NOW) == ''
    assert inbox.read_text(encoding='utf-8') == HEAD + body
    assert not (tmp_path / 'state.json').exists()


def test_inside_the_throttle_gh_is_not_asked(tmp_path, monkeypatch):
    setup(tmp_path, monkeypatch, [pr(3)])
    (tmp_path / 'state.json').write_text(json.dumps({'checked': NOW}), encoding='utf-8', newline='\n')
    asked = []
    monkeypatch.setattr(reminders, '_open_prs', lambda repo: asked.append(repo) or [])
    reminders.prs(now=NOW + 60)
    assert asked == []
