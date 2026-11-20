# T1 links/cfpages secrets: the delivery roster comes from the panel rows, and a course is never dropped in silence.
import importlib.machinery
import importlib.util
import json
import pathlib

import pytest

_CFPAGES = pathlib.Path(__file__).resolve().parents[1] / 'links' / 'cfpages'


def _cfpages():
    loader = importlib.machinery.SourceFileLoader('cfpages', str(_CFPAGES))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader('cfpages', loader))
    loader.exec_module(module)
    return module


def test_the_roster_comes_from_the_panel_rows_and_a_course_is_never_skipped(tmp_path, monkeypatch, capsys):
    """2026-10-17: the roster was read from a `## entregue` list the panel had replaced, so `secrets --push`
    shipped a TURMAS without ai4good and every matrícula was refused. The panel rows are the source now."""
    cf = _cfpages()
    course = tmp_path / 'classes' / 'ai4good'
    course.mkdir(parents=True)
    page = course / 'disciplina.md'
    page.write_text('<!-- painel:dados-va1\nedson: git=---\nthiago b.: git=---\n-->\n'
                    '<!-- painel:dados-va2\nedson: brw=---\n-->\n', encoding='utf-8', newline='\n')
    (course / 'segredos.env').write_text('MATRICULA_EDSON=1\nMATRICULA_THIAGO_B=2\nDUPLAS=\n', encoding='utf-8', newline='\n')
    monkeypatch.setattr(cf.pages, 'CLASSES', tmp_path / 'classes')
    monkeypatch.setattr(cf, '_HERE', tmp_path)  # no real site secrets in the captured output
    cf.cmd_secrets(push=False)
    out = capsys.readouterr().out.splitlines()
    turmas = json.loads(next(line[len('TURMAS='):] for line in out if line.startswith('TURMAS=')))
    assert turmas == {'ai4good': {'matriculas': {'edson': '1', 'thiago b.': '2'}, 'duplas': []}}
    page.write_text('# no panel\n', encoding='utf-8', newline='\n')
    with pytest.raises(SystemExit, match='no painel:dados rows'):
        cf.cmd_secrets(push=False)
