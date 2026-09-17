from dataclasses import dataclass, field

@dataclass
class Capabilities:
    modes: list[str] = field(default_factory=list)
    favourites: list[str] = field(default_factory=list)
    groups: dict[str, list[str]] = field(default_factory=dict)
