import pytest
from _typeshed import Incomplete
from collections.abc import Generator

LOADER: Incomplete
publish: Incomplete
SESSION: str

@pytest.fixture
def target(tmp_path, monkeypatch) -> Generator[Incomplete]: ...
def test_the_sync_takes_the_lock_before_its_first_byte(target) -> None: ...
def test_a_landed_push_leaves_the_repo_free(target) -> None: ...
