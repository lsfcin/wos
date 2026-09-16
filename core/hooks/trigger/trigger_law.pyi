from _typeshed import Incomplete
from pathlib import Path

HOOKS: Incomplete
MOMENTS: Incomplete
EVENTS: Incomplete
TOOLS: Incomplete
CAPABILITY_MOMENTS: Incomplete
GIT_ENTRYPOINTS: Incomplete

def ordered(moments) -> list: ...
def registrations(root: Path = ...) -> list: ...
def sites(root: Path = ...) -> dict: ...
def moments_of(row: dict, root: Path = ...) -> tuple: ...
