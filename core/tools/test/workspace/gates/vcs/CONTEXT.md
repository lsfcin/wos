# vcs
> Coverage for `core/hooks/git/`: branch shape, push diagnosis, and the mirror a pull leaves stale.

What these share is that the operator learns the result here or not at all — a push that failed and
a branch that moved under a running session are both silent in git's own output, so what the hook
names as the cause is the whole of what anyone knows.

**Named `vcs/` and not `git/`, which would match the hook directory.** pytest puts the parent
`gates/` on `sys.path` for the test files that stay there, and a bare `git/` directory under it is
an importable namespace package (PEP 420) — so `import git` inside this repo would reach these
tests instead of GitPython the day anything depends on it. A shadowing trap that fires years later
is worth one word of convention.

**It fired again on 2026-09-13**, which is why shared fixtures here live in `vcs_repos.py` and not
in a `conftest.py`: three files in this directory import `WORKSPACE_ROOT` from the ROOT conftest by
bare name, so a `conftest.py` beside them wins on `sys.path` and collection dies for the whole
directory. Same trap, second mechanism — pytest's fixture merging is not what breaks, the bare
import is.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_auto_push.py`](test_auto_push.py) | [`test_auto_push.pyi`](test_auto_push.pyi) | — | T0 the auto-push hook's diagnosis. core/hooks/post-commit is the only place most sessions ever learn that pushing failed, so what it names as the cause is the whole of what the operator knows. |
| [`test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.py`](test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.py) | [`test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.pyi`](test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.pyi) | — | b20260901-a-mirror-never-reaches-the-machine-that-pulled-it regression. |
| [`test_b20260913_the_close_reports_the_branch_it_is_about_to_promote.py`](test_b20260913_the_close_reports_the_branch_it_is_about_to_promote.py) | [`test_b20260913_the_close_reports_the_branch_it_is_about_to_promote.pyi`](test_b20260913_the_close_reports_the_branch_it_is_about_to_promote.pyi) | — | b20260913 regression — the close may not publish a finding against the branch it is merging. |
| [`test_branch_debt.py`](test_branch_debt.py) | [`test_branch_debt.pyi`](test_branch_debt.pyi) | — | T0 the branch-debt signals: a repo is a finding when work lives in only one place, and never otherwise. Zero-token, runs in verify-fast. |
| [`test_branch_marker.py`](test_branch_marker.py) | [`test_branch_marker.pyi`](test_branch_marker.pyi) | `marker_path`, `repo`, `run` | T0 the branch-drift warning (core/hooks/SPECS.md § Branch drift): HEAD moving under a session must be said out loud, exactly once, and must never block. |
| [`vcs_repos.py`](vcs_repos.py) | [`vcs_repos.pyi`](vcs_repos.pyi) | `git`, `commit`, `repo`, `cloned` | The git repos every vcs case needs, built once instead of per file. |
<!-- routing:end -->
