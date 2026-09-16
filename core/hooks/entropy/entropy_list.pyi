from _typeshed import Incomplete
from entropy_corpus import enforcement_paths as enforcement_paths, tracked_files as tracked_files
from pathlib import Path

ITEM_ID: Incomplete

def retired_hits(files: list, retired: dict, exempt: set) -> list: ...
def item_ids(path: Path) -> set: ...
def duplicate_ids(namespaces: dict) -> dict: ...

STRIKETHROUGH: Incomplete
CODE_SPAN: Incomplete
DATED_REPORT: Incomplete
SETTLED: Incomplete
TICKED_ITEM: Incomplete
LIST_FILES: Incomplete
PLACEHOLDER: str

def finished_work_hits(files: list, exempt: set) -> list: ...
def unanswered_placeholders(files: list, exempt: set) -> list: ...

WIKI_LINK: Incomplete

def goal_vocabulary(goals_dir: Path) -> set: ...
def wiki_link_hits(files: list, vocabulary: set, exempt: set) -> list: ...
