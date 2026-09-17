# caps.py — capability declaration: what modes/models a backend may actually be offered.
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Capabilities:
    """What the frontend is allowed to put on a keyboard for one backend. Provider data,
    not code: the picker renders exactly what lands here and never guesses a value the CLI
    would reject (SPECS AD-11). Effort is NOT here — its vocabulary depends on the chosen
    model (opencode), so it comes from `AgentBackend.efforts(model)` instead.
    `favourites` is the one-tap shortlist; `groups` (provider -> models) is the drill-down
    behind it, for catalogues too big to be one flat keyboard."""
    modes: list[str] = field(default_factory=list)
    favourites: list[str] = field(default_factory=list)
    groups: dict[str, list[str]] = field(default_factory=dict)
