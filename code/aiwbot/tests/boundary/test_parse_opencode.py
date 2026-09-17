# test_parse_opencode.py — free unit test: opencode JSONL fixture -> AgentEvents satisfy the contract.
import pathlib
import sqlite3
from backend.providers.opencode import parse_events, OpencodeBackend
import backend.providers.ocstore as OC
from backend.base import check_contract

_FIX = pathlib.Path(__file__).parent.parent / "fixtures" / "opencode_pong.jsonl"


def _events():
    raw = _FIX.read_text(encoding='utf-8')
    events = parse_events(raw)
    return events


def test_opencode_has_text_and_result():
    events = _events()
    kinds = [e.kind for e in events]
    assert "text" in kinds
    assert "result" in kinds


def test_opencode_text_and_session():
    events = _events()
    texts = [e for e in events if e.kind == "text"]
    first = texts[0]
    assert first.text == "PONG"
    assert first.session_id is not None


def test_opencode_contract():
    events = _events()
    ok, reason = check_contract(events)
    assert ok, reason


_MODEL = '{"id":"z-ai/glm-5.2","providerID":"nvidia"}'


def _seed_db(path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE session (id TEXT, parent_id TEXT, directory TEXT, title TEXT, "
                "time_updated INTEGER, agent TEXT, model TEXT)")
    rows = [("ses_a", None, "/a/project", "top here", 2000, "plan", _MODEL),
            ("ses_child", "ses_a", "/a/project", "sub", 3000, "build", _MODEL),
            ("ses_other", None, "/home/lucas", "elsewhere", 4000, "build", _MODEL)]
    con.executemany("INSERT INTO session VALUES (?,?,?,?,?,?,?)", rows)
    con.commit()
    con.close()


def test_list_sessions_filters_dir_and_toplevel(tmp_path, monkeypatch):
    db = tmp_path / "opencode.db"
    _seed_db(str(db))
    monkeypatch.setattr(OC, "_db_path", lambda: db)
    items = OpencodeBackend().list_sessions("/a/project")
    assert len(items) == 1
    assert items[0]["session_id"] == "ses_a"
    assert items[0]["title"] == "top here"
    assert items[0]["updated_at"] == 2.0  # ms -> s
    assert items[0]["mode"] == "plan"           # session.agent, no join needed
    assert items[0]["model"] == "nvidia/z-ai/glm-5.2"  # providerID/id, the catalogue's form


def test_list_sessions_no_db_is_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(OC, "_db_path", lambda: tmp_path / "absent.db")
    assert OpencodeBackend().list_sessions("/a/project") == []
