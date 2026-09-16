from _typeshed import Incomplete
from pathlib import Path

OUTER_FENCE_REGEX: Incomplete
SENSITIVE_BASENAME_REGEX: Incomplete
SENSITIVE_PATH_COMPONENTS: Incomplete
SENSITIVE_NAME_TOKENS: Incomplete

def is_sensitive_path(filepath: Path) -> bool: ...
def strip_llm_wrapper(text: str) -> str: ...
