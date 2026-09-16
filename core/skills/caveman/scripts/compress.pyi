from .detect import should_compress as should_compress
from .prompts import build_compress_prompt as build_compress_prompt, build_fix_prompt as build_fix_prompt
from .safety import is_sensitive_path as is_sensitive_path, strip_llm_wrapper as strip_llm_wrapper
from .validate import validate as validate
from pathlib import Path

MAX_RETRIES: int
MAX_FILE_SIZE: int
DEFAULT_MODEL: str

def call_claude(prompt: str) -> str: ...
def compress_file(filepath: Path) -> bool: ...
