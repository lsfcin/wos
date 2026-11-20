# vcs
> Coverage for `core/hooks/git/`: branch shape, push diagnosis, and the mirror a pull leaves stale.

What these share is that the operator learns the result here or not at all — a push that failed and a branch that moved under a running session are both silent in git's own output, so what the hook names as the cause is the whole of what anyone knows.

**Named `vcs/` and not `git/`, which would match the hook directory.** pytest puts the parent `gates/` on `sys.path` for the test files that stay there, and a bare `git/` directory under it is an importable namespace package (PEP 420) — so `import git` inside this repo would reach these tests instead of GitPython the day anything depends on it. A shadowing trap that fires years later is worth one word of convention.

**It fired again on 2026-09-13**, which is why shared fixtures here live in `vcs_repos.py` and not in a `conftest.py`: three files in this directory import `WORKSPACE_ROOT` from the ROOT conftest by bare name, so a `conftest.py` beside them wins on `sys.path` and collection dies for the whole directory. Same trap, second mechanism — pytest's fixture merging is not what breaks, the bare import is.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_auto_push.py`](test_auto_push.py) | [`test_auto_push.pyi`](test_auto_push.pyi) | — | T0 the auto-push hook's diagnosis. core/hooks/post-commit is the only place most sessions ever learn that pushing failed, so what it names as the cause is the whole of what the operator knows. |
| [`test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.py`](test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.py) | [`test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.pyi`](test_b20260901_a_mirror_never_reaches_the_machine_that_pulled_it.pyi) | — | b20260901-a-mirror-never-reaches-the-machine-that-pulled-it regression. |
| [`test_branch_debt.py`](test_branch_debt.py) | [`test_branch_debt.pyi`](test_branch_debt.pyi) | — | T0 the branch-debt signals: a repo is a finding when work lives in only one place, and never otherwise. Zero-token, runs in verify-fast. |
| [`test_lock.py`](test_lock.py) | [`test_lock.pyi`](test_lock.pyi) | — | T1 the branch lock (core/hooks/git/SPECS.md): one agent session per repo, people never gated. Zero-token, no network — every case builds a throwaway repo whose GitHub origin is rewritten to a local bare repo, so `governed` sees the profile's owner and every push lands on disk. |
| [`vcs_repos.py`](vcs_repos.py) | [`vcs_repos.pyi`](vcs_repos.pyi) | `git`, `commit`, `repo`, `cloned` | The git repos every vcs case needs, built once instead of per file. |
<!-- routing:end -->
