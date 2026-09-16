from _typeshed import Incomplete
from pathlib import Path

GIT_VARS: Incomplete

def test_no_git_variable_survives_into_the_suite() -> None: ...
def test_a_fixture_write_cannot_reach_the_workspace_index(tmp_path: Path): ...
