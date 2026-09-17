# test_sessions.py — free unit test: cross-backend /resume aggregation + registry adopt/mode.
import pytest
from frontend.session import registry, sessions
from frontend import config


class _Fake:
    def __init__(self, items):
        self._items = items

    def list_sessions(self, cwd):
        return list(self._items)

    def session_detail(self, session_id, cwd):
        return {}


@pytest.fixture
def two_backends(monkeypatch):
    cx = _Fake([{"session_id": "c1", "title": "alpha bug", "updated_at": 30},
                {"session_id": "c2", "title": "gamma", "updated_at": 10}])
    oc = _Fake([{"session_id": "o1", "title": "beta feature", "updated_at": 20}])
    fakes = {"claude": cx, "opencode": oc}
    monkeypatch.setattr(sessions, "backend_names", lambda: ["claude", "opencode"])
    monkeypatch.setattr(sessions, "get_backend", lambda name: fakes[name])
    # keep adopt writes off the real config
    store = {"sessions": {}}
    monkeypatch.setattr(config, "load_config", lambda: store)
    monkeypatch.setattr(config, "save_config", lambda **u: store.update(u) or store)
    return store


def test_recent_merges_and_sorts_newest_first(two_backends):
    items = sessions.recent(5, "", "/cwd")
    order = [it["session_id"] for it in items]
    assert order == ["c1", "o1", "c2"]
    assert [it["backend"] for it in items] == ["claude", "opencode", "claude"]


def test_recent_respects_limit(two_backends):
    items = sessions.recent(2, "", "/cwd")
    assert [it["session_id"] for it in items] == ["c1", "o1"]


def test_recent_filters_by_title_query(two_backends):
    items = sessions.recent(5, "beta", "/cwd")
    assert [it["session_id"] for it in items] == ["o1"]


def test_count_counts_filtered(two_backends):
    assert sessions.count("", "/cwd") == 3
    assert sessions.count("gamma", "/cwd") == 1


def test_recent_adopts_shown_into_registry(two_backends):
    sessions.recent(5, "", "/cwd")
    saved = two_backends["sessions"]
    assert saved["c1"]["backend"] == "claude"
    assert saved["o1"]["backend"] == "opencode"


def test_adopt_preserves_existing_mode(two_backends):
    two_backends["sessions"]["c1"] = {"mode": "plan"}
    registry.adopt("c1", "claude", "alpha bug", 30)
    assert two_backends["sessions"]["c1"]["mode"] == "plan"
    assert two_backends["sessions"]["c1"]["title"] == "alpha bug"
