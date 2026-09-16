from _typeshed import Incomplete
from pathlib import Path

AUTHORED: Incomplete
STEM_OK: Incomplete
SCAFFOLD_DIR: Incomplete
UPPERCASE_MD: Incomplete
TYPE_NAME: Incomplete
DIR_OK: Incomplete
PAPER_DIR: Incomplete
UNTYPEABLE: Incomplete
JS_LIKE: Incomplete
JS_STEM: Incomplete

def check_shape(path: Path, allowed: set) -> str | None: ...
def untracked_routing_targets(files: list, root: Path) -> list: ...
def check_dirs(path: Path, root: Path) -> str | None: ...
def check_placement(path: Path, scopes: dict, root: Path) -> str | None: ...
