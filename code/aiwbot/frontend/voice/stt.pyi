import pathlib
from _typeshed import Incomplete

confident: Incomplete

def run(path: pathlib.Path, model, hotwords: str | None = None) -> str: ...
def transcribe(path: pathlib.Path) -> str: ...
