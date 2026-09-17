# test_labels.py — free unit test: fitting a model id into a button label.
from frontend import config
from frontend.select import labels


def _no_aliases(monkeypatch):
    monkeypatch.setattr(config, "load_config", lambda: {})


def test_a_name_that_fits_is_only_stripped_of_separators(monkeypatch):
    """Compression you have to decode costs more than a long name you can read, so it starts
    only when the budget is actually exceeded."""
    _no_aliases(monkeypatch)
    assert labels.model_label("nvidia/z-ai/glm-5.2") == "nv·glm52"


def test_the_vendor_namespace_is_dropped(monkeypatch):
    """`deepseek-ai/` says nothing the model name and provider prefix do not."""
    _no_aliases(monkeypatch)
    assert labels.model_label("nvidia/deepseek-ai/deepseek-v4-flash") == "nv·dev4fl"


def test_every_separator_style_tokenizes_the_same(monkeypatch):
    """One catalogue writes `-`, `_` and `.` for the same job."""
    _no_aliases(monkeypatch)
    assert labels.model_label("nvidia/x/flux_1-kontext-dev") == "nv·fl1kode"


def test_the_version_dot_goes_too(monkeypatch):
    """Lucas: "I'll know that 52 means 5.2". It also stops a label carrying two dots that mean
    different things."""
    _no_aliases(monkeypatch)
    assert labels.model_label("nvidia/moonshotai/kimi-k2.6") == "nv·kimik26"


def test_version_digits_survive_contraction(monkeypatch):
    """They are what tells `glm-5.1` from `glm-5.2`."""
    _no_aliases(monkeypatch)
    long = labels.model_label("openrouter/z/qwen3-coder-next")
    assert "3" in long


def test_contraction_keeps_names_apart_where_truncation_would_not(monkeypatch):
    _no_aliases(monkeypatch)
    short = labels.model_label("openrouter/qwen/qwen3-coder")
    longer = labels.model_label("openrouter/qwen/qwen3-coder-next")
    assert short != longer


def test_inside_one_providers_page_the_prefix_is_dropped(monkeypatch):
    """Three of twelve characters spent saying where you already are."""
    _no_aliases(monkeypatch)
    assert labels.model_label("nvidia/z-ai/glm-5.2", qualify=False) == "glm52"


def test_a_bare_alias_passes_through(monkeypatch):
    _no_aliases(monkeypatch)
    assert labels.model_label("opus") == "opus"


def test_a_configured_alias_wins_over_the_rule(monkeypatch):
    """The rule contracts deepseek to `de`; someone reading that name daily may prefer `ds`,
    and that is a preference no algorithm should be guessing."""
    monkeypatch.setattr(config, "load_config",
                        lambda: {"model_aliases": {"nvidia/deepseek-ai/deepseek-v4-flash": "nv·dsv4f"}})
    assert labels.model_label("nvidia/deepseek-ai/deepseek-v4-flash") == "nv·dsv4f"


def test_every_provider_abbreviation_is_unique(monkeypatch):
    """`opencode` and `openrouter` share four letters, so a mechanical prefix cannot tell them
    apart — the map exists for that and must not grow a collision."""
    shorts = [labels.provider_short(name) for name in labels._PROVIDERS if name != "claude"]
    assert len(shorts) == len(set(shorts))
