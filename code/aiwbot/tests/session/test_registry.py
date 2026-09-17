# test_registry.py — free unit test: scopes (session vs NEW), last-used defaults, message maps.
import pytest
from frontend import config
from frontend.session import msgmap, registry


@pytest.fixture
def store(monkeypatch):
    data = {"sessions": {"s1": {"backend": "opencode", "title": "t"}}, "defaults": {}}
    monkeypatch.setattr(config, "load_config", lambda: data)
    monkeypatch.setattr(config, "save_config", lambda **u: data.update(u) or data)
    return data


def test_session_scope_and_new_scope_do_not_leak_into_each_other(store):
    registry.set_setting("s1", "model", "opencode/a")
    registry.set_setting(registry.NEW, "model", "opus")
    assert registry.setting_for("s1", "model") == "opencode/a"
    assert registry.setting_for(registry.NEW, "model") == "opus"


def test_harness_of_a_session_comes_from_its_lineage(store):
    """It is fixed at creation and unchangeable afterwards, so it is read from the registry
    entry rather than from a knob."""
    assert registry.harness_for("s1") == "opencode"


def test_harness_of_the_new_scope_is_a_knob(store):
    assert registry.harness_for(registry.NEW) == registry.DEFAULT_BACKEND
    registry.set_setting(registry.NEW, "backend", "opencode")
    assert registry.harness_for(registry.NEW) == "opencode"


def test_a_turn_leaves_its_knobs_as_the_defaults_a_new_session_inherits(store):
    registry.remember_defaults("opencode", "plan", "opencode/a", "high")
    assert registry.harness_for(registry.NEW) == "opencode"
    # Coerced, not inherited: the bot runs build only, so a stored `plan` — from before the
    # decision, or from a desktop session — comes back as build (2026-07-28, AD-27 option A).
    assert registry.mode_for(registry.NEW) == "build"
    assert registry.setting_for(registry.NEW, "model") == "opencode/a"
    assert registry.setting_for(registry.NEW, "effort") == "high"


def test_writes_against_an_unknown_session_are_dropped(store):
    registry.set_setting("ghost", "model", "opus")
    assert "ghost" not in store["sessions"]


def test_scope_resolves_from_the_message_the_keyboard_sits_on(store):
    msgmap.remember_reply(100, "s1")
    msgmap.remember_pending_new(200)
    assert msgmap.scope_for_message(100) == "s1"
    assert msgmap.scope_for_message(200) == registry.NEW
    assert msgmap.scope_for_message(999) is None
