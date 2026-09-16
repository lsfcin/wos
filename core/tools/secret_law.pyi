import pathlib
import re
from _typeshed import Incomplete
from typing import NamedTuple

FORMATTED_CPF: Incomplete
BARE_CPF: Incomplete
PASSWORD: Incomplete
CPF_LABEL: str
CPF_WINDOW: int

def redact_line(line: str, in_cpf_context: bool) -> str: ...
def redact(text: str) -> str: ...

SECRET_FILE: str
CREDENTIALS: tuple[tuple[str, re.Pattern[str]], ...]

class Finding(NamedTuple):
    path: pathlib.Path
    line: int
    kind: str

def scan_text(text: str, path: pathlib.Path) -> list[Finding]: ...

FIXTURES: Incomplete

def scan(path: pathlib.Path) -> list[Finding]: ...
def scan_all(paths: list[pathlib.Path]) -> list[Finding]: ...
