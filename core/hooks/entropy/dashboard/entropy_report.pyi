from _typeshed import Incomplete

START: str
END: str
SEED: str

def local_seed(repo: str) -> str: ...

SECTIONS: Incomplete

def render(findings: dict, scanned: int, root, name: str = '', trend: str = '') -> str: ...
