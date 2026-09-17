# labels.py — fit a model id into a button: provider prefix, then compress only if it overflows.
from __future__ import annotations
from .. import config

# A button is a quarter of the bubble, so roughly this many characters survive. Compression is
# progressive and starts here: a name that already fits is never touched, because an abbreviation
# you have to decode costs more than a long name you can read.
BUDGET = 12
_SEP = "·"
# Provider abbreviations. `opencode` and `openrouter` share a four-letter prefix, so mechanical
# prefixing cannot separate them — these are display data, chosen once. Canonical ids are
# untouched everywhere else; only the button label is short.
_PROVIDERS = {"opencode": "oc", "openrouter": "or", "ollama-cloud": "ol",
              "alibaba-coding-plan": "al", "nvidia": "nv", "google": "go",
              "anthropic": "an", "claude": ""}
# Tokens that carry no information in a picker: every model there is a model, and "latest" is
# what you get anyway. Dropped first, before anything readable is touched.
_NOISE = ("latest", "instruct", "preview", "chat", "it")
# Vendors write separators three ways in the same catalogue (`deepseek-v4-flash`,
# `flux_1-kontext-dev`, `flux.1-dev`), so all of them tokenize the same. The version dot goes
# too — Lucas: "you can ditch the `.`, I'll know that 52 means 5.2" — which also stops a label
# like `or.glm5.2` from carrying two dots that mean different things.
_SEPARATORS = "-_."


def provider_short(provider: str) -> str:
    """Two letters for a known provider, first two of the id for anything new."""
    known = _PROVIDERS.get(provider)
    result = known if known is not None else provider[:2]
    return result


def _aliases() -> dict:
    """Hand-picked overrides, by full model id, from config.json. The automatic rule contracts
    `deepseek-v4-flash` to `dev4fl`; someone who reads that name daily may prefer `dsv4f`, and
    that is a preference no algorithm should be guessing."""
    return config.load_config().get("model_aliases", {})


def _drop_noise(tokens: list[str]) -> list[str]:
    kept = [token for token in tokens if token not in _NOISE]
    return kept or tokens


def _contract(tokens: list[str]) -> str:
    """Alpha tokens shrink to two letters, tokens carrying a version number stay whole — the
    digits are what distinguishes `glm-5.1` from `glm-5.2`. Contracting beats truncating because
    it keeps the tail: `qwen3-coder` and `qwen3-coder-next` cut to the same nine characters but
    contract to `qwen3co` and `qwen3cone`."""
    parts = []
    for token in tokens:
        digits = any(char.isdigit() for char in token)
        parts.append(token if digits else token[:2])
    return "".join(parts)


def _tokens(name: str) -> list[str]:
    flat = name
    for separator in _SEPARATORS:
        flat = flat.replace(separator, " ")
    return flat.split()


def _fit(name: str, budget: int) -> str:
    """Progressive, and only as far as it has to go: separators out, then noise words, then
    contraction, then a hard cut. Separators go first because they cost a character and carry
    nothing — `glm-5.2` reads the same as `glm5.2`."""
    tokens = _tokens(name)
    result = "".join(tokens)
    if len(result) > budget:
        tokens = _drop_noise(tokens)
        result = "".join(tokens)
    if len(result) > budget:
        result = _contract(tokens)
    if len(result) > budget:
        result = result[:budget]
    return result


def _split(model_id: str) -> tuple[str, str]:
    """`nvidia/deepseek-ai/deepseek-v4-flash` -> ("nvidia", "deepseek-v4-flash"). The middle
    segment is the vendor namespace, which the provider prefix already implies."""
    provider = ""
    name = model_id
    if "/" in model_id:
        provider, _, rest = model_id.partition("/")
        name = rest.rsplit("/", 1)[-1]
    return provider, name


def model_label(model_id: str | None, budget: int = BUDGET, qualify: bool = True) -> str | None:
    """Button label for a model: `nv·glm5.2`. Bare aliases (claude's `opus`) carry no provider
    and, being short already, pass through untouched. `qualify=False` drops the prefix for a
    list that is already one provider's — inside nvidia's own page every row would read `nv·`,
    which spends three of about twelve characters saying where you already are."""
    result = None
    if model_id:
        alias = _aliases().get(model_id)
        provider, name = _split(model_id)
        prefix = provider_short(provider) if provider and qualify else ""
        head = f"{prefix}{_SEP}" if prefix else ""
        room = budget - len(head)
        fitted = _fit(name, room)
        result = alias or f"{head}{fitted}"
    return result
