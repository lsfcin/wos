# test_target.py — free unit test: model/effort reach the argv, and each backend's declaration.
from backend import TurnOptions, get_backend
from backend.providers.claude import ClaudeBackend
from backend.providers.opencode import OpencodeBackend


def _claude_args(options):
    backend = ClaudeBackend()
    args = backend.build_args("oi", None, options)
    return args[1:]  # drop the resolved binary path


def test_claude_maps_model_and_effort():
    args = _claude_args(TurnOptions(model="sonnet", effort="high"))
    assert "--model" in args
    assert args[args.index("--model") + 1] == "sonnet"
    assert args[args.index("--effort") + 1] == "high"


def test_claude_omits_unset_knobs():
    args = _claude_args(TurnOptions())
    assert "--model" not in args
    assert "--effort" not in args


def test_claude_declares_aliases_as_its_whole_catalogue():
    caps = ClaudeBackend().capabilities()
    assert caps.favourites == ["sonnet", "opus", "fable"]
    assert caps.groups == {"claude": ["sonnet", "opus", "fable"]}
    assert caps.modes == ["build", "plan"]


def test_claude_effort_ladder_is_model_independent():
    backend = ClaudeBackend()
    assert backend.efforts("opus") == backend.efforts(None)
    assert backend.efforts("opus")[0] == "low"


def test_opencode_maps_model_effort_and_plan_agent():
    options = TurnOptions(mode="plan", model="opencode/big-pickle", effort="high")
    args = OpencodeBackend().build_args("oi", "ses_1", options)
    assert args[args.index("--agent") + 1] == "plan"
    assert args[args.index("-m") + 1] == "opencode/big-pickle"
    assert args[args.index("--variant") + 1] == "high"
    assert args[args.index("-s") + 1] == "ses_1"


def test_opencode_titles_a_new_session_instead_of_resuming():
    options = TurnOptions(mode="build", title="Meu titulo")
    args = OpencodeBackend().build_args("oi", None, options)
    assert args[args.index("--title") + 1] == "Meu titulo"
    assert args[args.index("--agent") + 1] == "build"
    assert "-s" not in args


def test_opencode_effort_is_per_model(monkeypatch):
    """A model with no declared effort must offer none — the vocabularies are per model."""
    backend = OpencodeBackend()
    import backend.providers.catalog as catalog
    monkeypatch.setattr(catalog, "efforts", lambda model: ["minimal", "high"])
    assert backend.efforts("any/model") == ["minimal", "high"]
    assert backend.efforts(None) == []


def test_every_registered_backend_declares_its_capabilities(monkeypatch):
    """`_ids` is pinned so the suite never shells out to `opencode models` (1.1 s, and the
    result would depend on which providers this machine happens to have configured)."""
    import backend.providers.catalog as catalog
    monkeypatch.setattr(catalog, "_ids", ["opencode/a"])
    for name in ("claude", "opencode"):
        caps = get_backend(name).capabilities()
        assert "plan" in caps.modes
