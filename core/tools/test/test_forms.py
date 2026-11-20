# T1 forms: a form written as JSON must reach the API as the form that was written.
import json

import pytest
from conftest import WORKSPACE_ROOT, needs

import forms_spec

# A discipline folder holds more than one kind of JSON, and the glob below cannot tell them apart
# from the outside. Named, never sniffed: a spec whose `items` key is misspelled must fail loudly
# rather than be quietly skipped for not looking like a form — that is the whole point of the glob.
NAO_SAO_FORMULARIOS = {
    'drive_sync.json',      # estado do sync, escrito por core/tools/files/drive_sync.py
    'tecnologias.json',     # a árvore de tecnologias, lida por build_tecnologias.py
}

SPECS = [p for p in sorted((WORKSPACE_ROOT / 'academy/teaching/classes').glob('*/*.json'))
         if not p.name.startswith('.') and p.name not in NAO_SAO_FORMULARIOS]


def test_a_section_is_a_page_break_and_never_a_question():
    """A section carries no answer; typing it as a question would create a blank field."""
    reqs = forms_spec.requests({"items": [{"type": "section", "title": "Trabalho"}]})
    item = reqs[0]["createItem"]["item"]
    assert item["pageBreakItem"] == {}
    assert "questionItem" not in item


def test_the_other_option_stays_an_other_and_does_not_become_a_choice():
    reqs = forms_spec.requests({"items": [
        {"type": "radio", "title": "Trabalha?", "options": ["Sim", "Não"], "other": True},
    ]})
    options = reqs[0]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]["options"]
    assert options == [{"value": "Sim"}, {"value": "Não"}, {"isOther": True}]


def test_the_description_is_written_before_any_item_exists():
    """create() cannot carry a description, so it is a batchUpdate — and order decides."""
    reqs = forms_spec.requests({
        "description": "Anônimo.",
        "items": [{"type": "text", "title": "Nome do curso"}],
    })
    assert "updateFormInfo" in reqs[0]
    assert reqs[0]["updateFormInfo"]["updateMask"] == "description"
    assert "createItem" in reqs[1]


def test_items_land_in_the_order_they_were_written():
    """Every createItem names its own index; a repeated one silently reorders the form."""
    spec = {"items": [{"type": "text", "title": f"q{i}"} for i in range(5)]}
    indexes = [r["createItem"]["location"]["index"] for r in forms_spec.requests(spec)]
    assert indexes == [0, 1, 2, 3, 4]


def test_a_scale_carries_its_bounds_and_its_labels():
    reqs = forms_spec.requests({"items": [
        {"type": "scale", "title": "Ambiente", "low": 1, "high": 5,
         "lowLabel": "caótico", "highLabel": "silencioso", "required": True},
    ]})
    question = reqs[0]["createItem"]["item"]["questionItem"]["question"]
    assert question["required"] is True
    assert question["scaleQuestion"] == {
        "low": 1, "high": 5, "lowLabel": "caótico", "highLabel": "silencioso"}


def test_an_unknown_type_fails_here_rather_than_at_the_api():
    """A typo must not travel to Google as a request the error message cannot explain."""
    with pytest.raises(ValueError):
        forms_spec.requests({"items": [{"type": "slider", "title": "?"}]})


def test_every_form_lucas_applies_still_compiles():
    """Guards the content, not just the builder: a broken spec is a class with no survey.

    Discovered by glob rather than listed, because a spec is added per discipline and a
    listed path would leave the next turma's form untested without saying so.
    """
    needs('academy/teaching')
    if not (WORKSPACE_ROOT / 'academy/teaching/classes').is_dir():
        pytest.skip('academy/teaching not checked out on this machine')
    assert SPECS, 'no form spec found under academy/teaching/classes/*/'
    for path in SPECS:
        spec = json.loads(path.read_text(encoding='utf-8'))
        reqs = forms_spec.requests(spec)
        assert len(reqs) == len(spec["items"]) + 1, path  # every item, plus the description
