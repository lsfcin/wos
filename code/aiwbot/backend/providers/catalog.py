# catalog.py — opencode's model catalogue: configured ids + per-model effort/context metadata.
from __future__ import annotations
import json
import pathlib
import subprocess
import time
from .. import binaries
from . import ocstore

# The offline declaration opencode ships: every provider it knows (3311+ models), each model
# carrying `reasoning_options` and `limit.context`. Free to read, no network, no key.
_MODELS_JSON = ".cache/opencode/models.json"
# ...but it lists providers we have no auth for, so the CONFIGURED subset still comes from the
# CLI (~1.1 s, 478 ids here). Both are memoized for the daemon's life — never per keyboard render.
_LIST_ARG = "models"
_LIST_TIMEOUT = 20
# The shortlist is what Lucas actually reaches for, read from opencode's own history. A curated
# "cheap and good" guess was wrong by a wide margin: it offered models used once while the real
# top three had 91, 42 and 15 sessions in the window. Frequency ranks, recency breaks ties.
RECENT_DAYS = 30
SHORTLIST = 6
# Fallback for a machine with no opencode history yet — cheap levels first, since a first-time
# shortlist should at least not be expensive.
_FALLBACK_PROVIDERS = ("opencode", "alibaba-coding-plan")
_PER_PROVIDER = 2

_ids: list[str] | None = None
_meta: dict | None = None


def _read_metadata() -> dict:
    path = pathlib.Path.home() / _MODELS_JSON
    data: dict = {}
    if path.is_file():
        raw = path.read_text(encoding='utf-8')
        data = json.loads(raw)
    return data


def metadata() -> dict:
    """The whole provider -> models declaration, parsed once (3 MB) per process."""
    global _meta
    if _meta is None:
        _meta = _read_metadata()
    return _meta


def _entry(model_id: str) -> dict:
    """models.json entry for a `provider/model` id — note ids can carry a second slash
    (`openrouter/qwen/qwen3-coder`), so only the FIRST segment is the provider."""
    provider, _, rest = model_id.partition("/")
    providers = metadata()
    block = providers.get(provider) or {}
    models = block.get("models") or {}
    return models.get(rest) or {}


def efforts(model_id: str) -> list[str]:
    """Effort vocabulary this model accepts for `--variant`. Empty for the toggle /
    budget_tokens / no-reasoning shapes: offering values the CLI would reject is worse than
    offering nothing (SPECS AD-11). Vocabularies vary per MODEL, not per provider."""
    entry = _entry(model_id)
    options = entry.get("reasoning_options") or []
    values: list[str] = []
    for option in options:
        kind = option.get("type")
        if kind == "effort":
            listed = option.get("values") or []
            values = [value for value in listed if value]
            break
    return values


def context_window(model_id: str) -> int | None:
    """Declared context window, so an opencode session can report X% like claude does (AD-9)."""
    entry = _entry(model_id)
    limit = entry.get("limit") or {}
    return limit.get("context")


def _run_list() -> list[str]:
    """Configured ids from the CLI. A missing/failing opencode degrades to an empty catalogue
    rather than breaking the keyboard — the caller reports that as its own state, not as an
    empty picker (which is how the systemd PATH gap first surfaced, as a wrong error message)."""
    ids: list[str] = []
    binary = binaries.find("opencode")
    proc = None
    if binary:
        try:
            proc = subprocess.run([binary, _LIST_ARG], capture_output=True, text=True,
                                  encoding='utf-8', errors='replace',
                                  timeout=_LIST_TIMEOUT)
        except (OSError, subprocess.SubprocessError):
            proc = None
    if proc is not None and proc.returncode == 0:
        out = proc.stdout
        lines = out.splitlines()
        ids = [line.strip() for line in lines if "/" in line]
    return ids


def model_ids() -> list[str]:
    global _ids
    if _ids is None:
        _ids = _run_list()
    return _ids


def groups() -> dict[str, list[str]]:
    """Configured models bucketed by provider — the first level of the drill-down."""
    grouped: dict[str, list[str]] = {}
    for model_id in model_ids():
        provider = model_id.split("/", 1)[0]
        bucket = grouped.setdefault(provider, [])
        bucket.append(model_id)
    return grouped


def _fallback() -> list[str]:
    grouped = groups()
    picks: list[str] = []
    for provider in _FALLBACK_PROVIDERS:
        listed = grouped.get(provider) or []
        picks.extend(listed[:_PER_PROVIDER])
    return picks


def favourites() -> list[str]:
    """The one-tap shortlist: most-used first, from the last RECENT_DAYS of opencode history.
    Ranked entries are intersected with the configured catalogue, so a model that lost its
    provider stops being offered instead of failing at dispatch."""
    cutoff = (time.time() - RECENT_DAYS * 86400) * 1000
    ranked = ocstore.recent_models(cutoff)
    configured = set(model_ids())
    picks = [model for model, _, _ in ranked if model in configured]
    return picks[:SHORTLIST] or _fallback()
