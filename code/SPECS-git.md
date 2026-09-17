# Git Flow
> Which branches exist, what may be committed where, and when work is pushed.
> governs: every repo under code/, and the workspace repo itself
> enforced-by: core/hooks/git/gitflow_gate.py, core/hooks/post-commit

## Git Branching (Git Flow)

All projects under `code/` follow Git Flow:

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, tagged releases only |
| `develop` | Integration branch — all features merge here |
| `feature/<name>` | New work — branch from `develop`, merge back to `develop` |
| `release/<version>` | Stabilization — branch from `develop`, merge to `main` + `develop` |
| `hotfix/<name>` | Urgent fix — branch from `main`, merge to `main` + `develop` |

**Rules:**
- Never commit directly to `main`
- `develop` must always build and pass tests
- Feature branches: short-lived, one concern each
- Tag `main` on every release: `v<semver>`

**Enforcement.** `core/hooks/git/gitflow_gate.py` (pre-commit block 1e) **hard-blocks** in `code/`
repos: any commit on `main`/`master`/`develop`, or on a branch not matching
`feature/*`/`release/*`/`hotfix/*`. Emergency bypass: `git commit --no-verify`. Migration note: a project still
committing to `main`/`master` directly must create `develop` and switch to `feature/*` before its
next commit, or the gate blocks it.

**Scope of the gate** (moved here from `AGENTS.md` 2026-07-30, when the always-loaded root
stopped restating rules a hook already enforces): the gate covers every `code/*` repo **and the
workspace repo itself**. Paper repos (`academy/papers/*`) and other nested repos are **exempt** —
Overleaf is authoritative there and co-authors commit straight to the default branch.

**The bypass leaves no trace** outside the commit message, which is the only reason it is
dangerous. So when using `--no-verify`: state the reason in the commit message, and file a TODO to
pay it back. An undocumented bypass is indistinguishable from the gate never having run.

**Push policy** (moved here from `AGENTS.md` for the same reason; the ritual lives in
`core/skills/roundup.md`). Two machines share this workspace, so **unpushed work is invisible
work** and `main` is the sync point, not a release tag. `feature/*` auto-pushes via
`core/hooks/post-commit`; promotion to `develop`/`main` happens in `/roundup` Phase 5 behind a green
verification run; `/handoff` only *reports* divergence and never merges.

**No pull request is required, and no branch is protected** — ruled 2026-08-31 (Lucas), after an
audit found the PR rule honoured in 3 of 18 repos and contradicting the promotion it was written
beside: a solo repo whose promotion already sits behind a green verify run gains nothing from a
round trip through GitHub. The green run is the gate. What is now enforced instead is the law this
file already stated and nothing measured — `core/hooks/git/branch_debt.py` counts a repo with
commits its remote does not have, and a repo with no remote at all, so *invisible work* is a number
in [`ISSUES.md`](../ISSUES.md) rather than a sentence here.
