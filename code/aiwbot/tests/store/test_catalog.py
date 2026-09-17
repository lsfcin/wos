# test_catalog.py — free unit test: opencode catalogue — effort vocabularies, groups, favourites.
import backend.providers.catalog as catalog

_META = {
    "anthropic": {"models": {
        "claude-opus-4-8": {"reasoning_options": [{"type": "effort",
                                                   "values": ["low", "high", "max"]}],
                            "limit": {"context": 1000000}},
    }},
    "nvidia": {"models": {
        "z-ai/glm-5.2": {"reasoning_options": [{"type": "toggle"}],
                         "limit": {"context": 200000}},
        "budgeted": {"reasoning_options": [{"type": "budget_tokens"}]},
        "plain": {},
    }},
    "sarvam": {"models": {
        "sarvam-30b": {"reasoning_options": [{"type": "effort",
                                              "values": [None, "low", "high"]}]},
    }},
}


def _fake_meta(monkeypatch):
    monkeypatch.setattr(catalog, "_meta", _META)


def test_effort_values_come_from_the_model_entry(monkeypatch):
    _fake_meta(monkeypatch)
    assert catalog.efforts("anthropic/claude-opus-4-8") == ["low", "high", "max"]


def test_second_slash_belongs_to_the_model_not_the_provider(monkeypatch):
    _fake_meta(monkeypatch)
    assert catalog.context_window("nvidia/z-ai/glm-5.2") == 200000


def test_toggle_and_budget_shapes_declare_no_effort(monkeypatch):
    _fake_meta(monkeypatch)
    assert catalog.efforts("nvidia/z-ai/glm-5.2") == []
    assert catalog.efforts("nvidia/budgeted") == []
    assert catalog.efforts("nvidia/plain") == []


def test_undeclared_model_degrades_to_empty(monkeypatch):
    _fake_meta(monkeypatch)
    assert catalog.efforts("who/knows") == []
    assert catalog.context_window("who/knows") is None


def test_null_effort_values_are_dropped(monkeypatch):
    _fake_meta(monkeypatch)
    assert catalog.efforts("sarvam/sarvam-30b") == ["low", "high"]


def test_groups_bucket_by_first_segment(monkeypatch):
    monkeypatch.setattr(catalog, "_ids", ["opencode/a", "opencode/b", "openrouter/x/y"])
    groups = catalog.groups()
    assert groups == {"opencode": ["opencode/a", "opencode/b"], "openrouter": ["openrouter/x/y"]}


def test_favourites_rank_by_how_much_each_model_was_used(monkeypatch):
    """The curated guess was wrong by a wide margin, so the shortlist reads real history."""
    ids = ["nvidia/a", "nvidia/b", "opencode/c"]
    monkeypatch.setattr(catalog, "_ids", ids)
    ranked = [("nvidia/b", 42, 200.0), ("nvidia/a", 91, 100.0), ("gone/x", 5, 300.0)]
    monkeypatch.setattr(catalog.ocstore, "recent_models", lambda cutoff: sorted(
        ranked, key=lambda item: (item[1], item[2]), reverse=True))
    assert catalog.favourites() == ["nvidia/a", "nvidia/b"]


def test_a_model_no_longer_configured_is_not_offered(monkeypatch):
    """Its provider may be gone; offering it would only fail at dispatch."""
    monkeypatch.setattr(catalog, "_ids", ["nvidia/a"])
    monkeypatch.setattr(catalog.ocstore, "recent_models",
                        lambda cutoff: [("gone/x", 99, 1.0), ("nvidia/a", 1, 1.0)])
    assert catalog.favourites() == ["nvidia/a"]


def test_no_history_falls_back_to_the_cheap_levels(monkeypatch):
    ids = ["openrouter/x", "alibaba-coding-plan/glm-5", "opencode/a", "opencode/b", "opencode/c"]
    monkeypatch.setattr(catalog, "_ids", ids)
    monkeypatch.setattr(catalog.ocstore, "recent_models", lambda cutoff: [])
    assert catalog.favourites() == ["opencode/a", "opencode/b", "alibaba-coding-plan/glm-5"]
