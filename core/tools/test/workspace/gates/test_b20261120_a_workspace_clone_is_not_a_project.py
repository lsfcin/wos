# b20261120 regression — a workspace clone checked out under code/ is judged as the workspace.
#
# The public repo lives at code/wos, so the project contract asked every new core/ CONTEXT.md in it
# for a `> spec:` the workspace never asks of core/, and refused the sync. Ruled 2026-11-20 (Lucas,
# panel concurring): the repo's shape decides, not its location — and only both markers together.
import sys
import types

import pytest

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / 'core/hooks/commit'))
import gates_project  # noqa: E402


def _repo(root, name, markers):
    top = root / 'code' / name
    for marker in markers:
        (top / marker).parent.mkdir(parents=True, exist_ok=True)
        (top / marker).write_text('# m\n', encoding='utf-8', newline='\n')
    top.mkdir(parents=True, exist_ok=True)
    return types.SimpleNamespace(toplevel=top, root=root)


@pytest.mark.parametrize('markers, project', [
    ((), True),
    (('AGENTS.md',), True),
    (('core/SCHEMA.md',), True),
    (gates_project.WORKSPACE_MARKERS, False),
])
def test_only_a_workspace_shaped_repo_under_code_escapes_the_project_rules(tmp_path, markers, project):
    assert gates_project._under_code(_repo(tmp_path, 'thing', markers)) is project


def test_the_workspace_itself_is_never_a_project():
    commit = types.SimpleNamespace(toplevel=WORKSPACE_ROOT, root=WORKSPACE_ROOT)
    assert gates_project._under_code(commit) is False
