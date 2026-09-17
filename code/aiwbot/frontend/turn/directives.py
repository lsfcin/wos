# directives.py — read leading harness/model words off a bot-prefixed message, no inference.
from __future__ import annotations
from backend import backend_names, get_backend

# The panel already lets Lucas pick harness+model by tapping; this is the same choice spoken or
# typed inline ("bot, opencode glm resume o pdf"), for $0 — pure matching against what the
# backends already declare, never a triage inference call. It only reads the LEADING run of
# words and stops at the first that is neither a harness nor a model, so a prompt that merely
# mentions "opus" ("bot, escreve sobre opus dei") is left whole.

# Spoken/typed variants that are not themselves a registered backend name. Provider names live
# here as DATA, in one place — each backend's own name is added as a self-alias at runtime.
_HARNESS_ALIASES = {"claudecode": "claude", "cc": "claude", "oc": "opencode"}
# Below this a token is too short to be a model name worth matching (avoids stray 2-char hits).
_MIN_TOKEN = 3

_index_cache: list[tuple[str, str]] | None = None
_harness_cache: dict[str, str] | None = None


def _norm(text: str) -> str:
    """Compare on letters and digits only, so `glm` matches `glm-5.2` and `deepseek` matches
    `deepseek-v4-flash` without the punctuation getting in the way."""
    kept = [ch for ch in text.lower() if ch.isalnum()]
    return "".join(kept)


def _segment(model_id: str) -> str:
    """The model's own name, dropping the provider path: nvidia/z-ai/glm-5.2 -> glm-5.2."""
    tail = model_id.rsplit("/", 1)[-1]
    return tail


def _harness_map() -> dict[str, str]:
    global _harness_cache
    if _harness_cache is None:
        mapping = dict(_HARNESS_ALIASES)
        for name in backend_names():
            mapping.setdefault(name, name)
        _harness_cache = mapping
    return _harness_cache


def _index() -> list[tuple[str, str]]:
    """(harness, model_id) for every model each backend declares, favourites first so an exact
    alias like `sonnet` resolves ahead of some opencode id that merely contains the word.
    Built once (the opencode catalogue read is the panel's own one-time cost) and memoized."""
    global _index_cache
    if _index_cache is None:
        entries: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for name in backend_names():
            backend = get_backend(name)
            caps = backend.capabilities()
            ids = list(caps.favourites)
            for models in caps.groups.values():
                ids.extend(models)
            for model_id in ids:
                pair = (name, model_id)
                if pair not in seen:
                    seen.add(pair)
                    entries.append(pair)
        _index_cache = entries
    return _index_cache


def _harness_alias(word: str) -> str | None:
    mapping = _harness_map()
    return mapping.get(word)


def _model_match(token: str, prefer: str | None) -> tuple[str | None, str | None]:
    """Resolve one word to a (harness, model_id). An exact name wins over a substring, and a
    harness already named on the line pins the search to that backend."""
    norm = _norm(token)
    result: tuple[str | None, str | None] = (None, None)
    if len(norm) >= _MIN_TOKEN:
        result = _scan(norm, prefer, exact=True)
        if result[1] is None:
            result = _scan(norm, prefer, exact=False)
    return result


def _scan(norm: str, prefer: str | None, exact: bool) -> tuple[str | None, str | None]:
    found: tuple[str | None, str | None] = (None, None)
    for harness, model_id in _index():
        if prefer is not None and harness != prefer:
            continue
        segment = _norm(_segment(model_id))
        hit = segment == norm if exact else norm in segment
        if hit:
            found = (harness, model_id)
            break
    return found


def resolve(prompt: str) -> tuple[str | None, str | None, str]:
    """(harness, model, rest). Consume leading harness/model words; the rest is the real prompt.
    If EVERY word was a directive the message carried no task, so nothing is applied and the
    prompt is returned untouched — reconfiguring on a task-less message is never what was meant."""
    tokens = prompt.split()
    harness: str | None = None
    model: str | None = None
    i = 0
    while i < len(tokens):
        word = tokens[i].strip(",.").lower()
        matched_harness = _harness_alias(word)
        if matched_harness:
            harness = matched_harness
            i += 1
            continue
        model_harness, model_id = _model_match(word, harness)
        if model_id:
            model = model_id
            if harness is None:
                harness = model_harness
            i += 1
            continue
        break
    rest = " ".join(tokens[i:])
    stripped = rest.strip()
    if not stripped:
        return None, None, prompt
    return harness, model, rest
