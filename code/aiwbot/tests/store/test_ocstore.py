# test_ocstore.py — free unit test: opencode sqlite reads — last assistant turn + occupancy.
import json
import sqlite3
import backend.providers.ocstore as ocstore

_ASSISTANT = {"role": "assistant",
              "tokens": {"total": 10434, "input": 6467, "output": 63,
                         "cache": {"read": 3904, "write": 100}}}
_USER = {"role": "user"}


def _seed(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE message (id TEXT, session_id TEXT, time_created INTEGER, data TEXT)")
    con.execute("CREATE TABLE part (id TEXT, message_id TEXT, session_id TEXT, "
                "time_created INTEGER, data TEXT)")
    messages = [("m1", "s1", 10, json.dumps(_ASSISTANT)),
                ("m2", "s1", 20, json.dumps(_USER))]
    con.executemany("INSERT INTO message VALUES (?,?,?,?)", messages)
    parts = [("p1", "m1", "s1", 11, json.dumps({"type": "text", "text": "resposta do agente"})),
             ("p2", "m1", "s1", 12, json.dumps({"type": "step-finish"})),
             ("p3", "m2", "s1", 21, json.dumps({"type": "text", "text": "pergunta do Lucas"}))]
    con.executemany("INSERT INTO part VALUES (?,?,?,?,?)", parts)
    con.commit()
    con.close()


def _db(tmp_path, monkeypatch):
    path = tmp_path / "opencode.db"
    _seed(str(path))
    monkeypatch.setattr(ocstore, "_db_path", lambda: path)


def test_last_turn_reads_the_assistant_not_the_trailing_user_message(tmp_path, monkeypatch):
    """The user's own message is a type=text part too, so a naive scan quotes Lucas back."""
    _db(tmp_path, monkeypatch)
    text, _ = ocstore.last_turn("s1")
    assert text == "resposta do agente"


def test_last_turn_reports_occupancy_not_lifetime_spend(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch)
    _, used = ocstore.last_turn("s1")
    assert used == 6467 + 3904 + 100


def test_last_turn_empty_without_an_assistant_message(tmp_path, monkeypatch):
    _db(tmp_path, monkeypatch)
    assert ocstore.last_turn("ghost") == ("", None)


def test_context_used_none_when_nothing_was_counted():
    assert ocstore.context_used({"tokens": {"input": 0}}) is None


def test_model_of_joins_provider_and_id():
    raw = '{"id":"z-ai/glm-5.2","providerID":"nvidia","variant":"default"}'
    assert ocstore.model_of(raw) == "nvidia/z-ai/glm-5.2"
    assert ocstore.model_of(None) is None
