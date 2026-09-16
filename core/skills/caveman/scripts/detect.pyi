from _typeshed import Incomplete
from pathlib import Path

COMPRESSIBLE_EXTENSIONS: Incomplete
SKIP_EXTENSIONS: Incomplete
CODE_PATTERNS: Incomplete

def detect_file_type(filepath: Path) -> str: ...
def should_compress(filepath: Path) -> bool: ...
