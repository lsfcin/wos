# T1 panel/ask: a spent quota or a broken call falls to the next model, the first verdict wins, and none at all stops with every reason. Models faked.
import importlib.machinery
import importlib.util
import pathlib

import pytest

_ASK = pathlib.Path(__file__).resolve().parents[2] / 'panel' / 'ask'

CODEX_LIMIT = "ERROR: You've hit your usage limit. Upgrade to Pro or try again at 4:31 PM."
AGY_QUOTA = 'Error: Individual quota reached. Resets in 73h6m3s.\nAGY_ERROR: {"status":"RESOURCE_EXHAUSTED"}'


def _tool():
    loader = importlib.machinery.SourceFileLoader('panel_ask', str(_ASK))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('panel_ask', loader))
    loader.exec_module(module)
    return module


def _model(code: int, text: str):
    return lambda prompt: (code, text)


def test_a_spent_quota_falls_to_the_next_model_and_names_the_one_that_answered():
    panel = _tool()
    chain = (('codex', 'gpt', _model(1, CODEX_LIMIT)), ('argon', 'g4', _model(0, AGY_QUOTA)),
             ('flash', 'g3', _model(0, 'Verdict: 9/10')))
    who, answer, misses = panel.ask('q', chain)
    assert who == 'flash g3'
    assert answer == 'Verdict: 9/10\n'
    assert [m.split(':')[0] for m in misses] == ['codex', 'argon']
    assert all('quota' in m for m in misses)


def test_agy_exiting_zero_on_a_spent_quota_is_still_no_verdict():
    assert _tool().failed(0, AGY_QUOTA).startswith('quota')


def test_a_broken_call_is_reported_as_broken_not_as_quota():
    why = _tool().failed(127, 'codex not found')
    assert why.startswith('exit 127') and 'quota' not in why


def test_no_model_answering_stops_with_every_reason():
    panel = _tool()
    chain = (('codex', 'gpt', _model(1, CODEX_LIMIT)), ('flash', 'g3', _model(0, '')))
    with pytest.raises(SystemExit, match='(?s)codex: quota.*flash: empty answer'):
        panel.ask('q', chain)


def test_a_binary_off_path_is_found_where_the_vendor_installs_it(tmp_path, monkeypatch):
    panel = _tool()
    exe = tmp_path / 'codex'
    exe.write_text('#!/bin/sh\n', encoding='utf-8', newline='\n')
    exe.chmod(0o755)
    monkeypatch.delenv('CODEX', raising=False)
    monkeypatch.setattr(panel.shutil, 'which', lambda name: None)
    assert panel.find('codex', 'CODEX', (str(exe),)) == str(exe)
    assert panel.find('codex', 'CODEX', (str(tmp_path / 'missing'),)) is None
