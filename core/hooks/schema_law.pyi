from _typeshed import Incomplete
from pathlib import Path

WORKSPACE_ROOT: Incomplete
SCHEMA: Incomplete
TRANSIENT_HEADING: str
RETIRED_HEADING: str
TYPE_ROW: Incomplete
SCOPED_ROW: Incomplete
RETIRED_ROW: Incomplete
BACKTICKED_MD: Incomplete
SCOPES: Incomplete

def load_law(schema_path: Path = ...) -> tuple[set, set]: ...
def load_scopes(schema_path: Path = ...) -> dict: ...
def load_retired(schema_path: Path = ...) -> dict: ...
