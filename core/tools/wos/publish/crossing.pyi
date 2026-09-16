import pathlib
from _typeshed import Incomplete
from typing import NamedTuple

ROOT: Incomplete
FLOOR: Incomplete
REGISTRY: Incomplete

class Floor(NamedTuple):
    target: pathlib.Path
    roots: tuple[str, ...]
    files: tuple[str, ...]
    trees: tuple[str, ...]
    absent: dict[str, str]

def floor() -> Floor: ...
def tracked() -> list[str]: ...
def eligible(f: Floor) -> set[str]: ...

class Claim(NamedTuple):
    path: str
    feature: str

def claims(scope: str = 'general') -> list[Claim]: ...
def expand(seeds: list[Claim], pool: set[str]) -> list[Claim]: ...
def closure(seeds: list[str], pool: set[str]) -> set[str]: ...

class Report(NamedTuple):
    crossing: set[str]
    orphans: set[str]
    unclaimed_imports: list[tuple[str, str]]
    by_feature: dict[str, set[str]]

GENERATED: Incomplete

def report() -> Report: ...
