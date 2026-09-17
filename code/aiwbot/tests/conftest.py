# conftest.py — fixtures shared by the panel tests: an in-memory config and a fake backend.
import pytest
from frontend.select import choices
from frontend import config
from .panelkit import Fake


@pytest.fixture
def store(monkeypatch):
    data = {"sessions": {"s1": {"backend": "opencode", "title": "t"}}, "defaults": {}}
    monkeypatch.setattr(config, "load_config", lambda: data)
    monkeypatch.setattr(config, "save_config", lambda **u: data.update(u) or data)
    monkeypatch.setattr(choices, "get_backend", lambda name: Fake())
    return data
