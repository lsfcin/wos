# choices.py — what a scope may be offered: the backends' declarations, asked per dimension.
from __future__ import annotations
from backend import backend_names, get_backend
from ..session import registry

# harness is absent from a live session on purpose: no CLI can import the other's transcript, so
# a running lineage can never change harness (SPECS AD-11). It exists only in the NEW scope.
LABELS = {"h": "harness", "m": "model", "e": "effort"}
# Which effort values earn the two visible slots when the ladder has to be cut. By NAME, not by
# position: claude's ladder is low..max but opencode's vocabularies are irregular ([high, max],
# [minimal, low, medium, high]), so any positional rule picks something different on each.
# Lucas: "medium e high, raramente uso low".
EFFORT_PREFERRED = ("medium", "high")
_SESSION_DIMS = ("m", "e")
_NEW_DIMS = ("h", "m", "e")


def _caps(scope: str):
    name = registry.harness_for(scope)
    backend = get_backend(name)
    return backend.capabilities()


def harness_values(scope: str) -> list[str]:
    return backend_names()


def model_values(scope: str) -> tuple[list[str], bool]:
    """(shortlist, whether a drill-down exists). claude's three aliases ARE its catalogue, so it
    gets no `all`; opencode's hundreds across six providers always do."""
    caps = _caps(scope)
    sizes = [len(models) for models in caps.groups.values()]
    total = sum(sizes)
    deep = total > len(caps.favourites)
    return caps.favourites, deep


def groups(scope: str) -> dict[str, list[str]]:
    """provider -> models, the drill-down's two levels. `provider` here means who supplies the
    key (nvidia, openrouter) — the sense opencode uses. The harness is the CLI above it."""
    caps = _caps(scope)
    return caps.groups


def effort_values(scope: str) -> list[str]:
    """Whatever the harness declares for the chosen model — empty when that model has no effort
    knob at all (opencode's toggle/budget_tokens shapes), and empty for opencode before a model
    is picked, where the vocabulary is simply unknown (SPECS AD-11)."""
    name = registry.harness_for(scope)
    backend = get_backend(name)
    model = registry.setting_for(scope, "model")
    return backend.efforts(model)


def preferred(dim: str) -> tuple[str, ...]:
    """Values that get the visible slots when the list is cut. Only effort has an opinion."""
    return EFFORT_PREFERRED if dim == "e" else ()


def values_for(scope: str, dim: str) -> tuple[list[str], bool]:
    """(values, whether a drill-down hides behind them) for any dimension, so callers branch
    on the dimension once, here, instead of at every use."""
    deep = False
    if dim == "h":
        values = harness_values(scope)
    elif dim == "m":
        values, deep = model_values(scope)
    else:
        values = effort_values(scope)
    return values, deep


def warm() -> None:
    """Ask every backend for its declaration once, at startup. opencode builds its catalogue by
    shelling `opencode models` (839 ms measured here) and parsing a 3 MB models.json (26 ms),
    then memoizes both for the process's life — so without this the FIRST model or menu tap
    after each daemon restart pays ~865 ms BEFORE the callback is answered. That is the whole
    "button feels slow" complaint on a restarted daemon, and it is the only part of a tap that
    was ever ours to lose: warm, every path measures under 1 ms (F3c).

    Provider-agnostic on purpose — it asks the boundary, never opencode's catalogue directly, so a
    third backend with its own expensive declaration is warmed by existing."""
    for name in backend_names():
        backend = get_backend(name)
        caps = backend.capabilities()
        favourites = caps.favourites
        if favourites:
            backend.efforts(favourites[0])


def menu_dims(scope: str) -> list[str]:
    """Which dimensions this scope can actually change. A dimension with nothing to offer is
    dropped rather than shown and then refused — `effort` is the one that disappears."""
    keys = _NEW_DIMS if scope == registry.NEW else _SESSION_DIMS
    usable = []
    for key in keys:
        values, _ = values_for(scope, key)
        if values:
            usable.append(key)
    return usable
