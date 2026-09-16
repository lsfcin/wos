# Commit
> The git pre-commit and post-commit pipeline: what runs on every commit, in what order, and the
> one place a commit is refused.

Contract and what each gate blocks: [`../SPECS.md`](../SPECS.md) § Git pre-commit.

Applied globally via `core.hooksPath`, so this fires in **every** repo under the workspace — which
is why `pre_commit.Commit` carries two roots and no module recomputes either. `root` is where the
machinery lives; `toplevel` is the repo being committed. They are different directories whenever a
project under `code/` commits, and conflating them is how this pipeline breaks.

A **gate** may refuse the commit by raising `Blocked`; a **generator** writes artifacts and stages
them. That split dates to the 2026-07-31 reorganisation, when a single 385-line file had drifted out
of its own execution order. Order is fixed in `pre_commit.stages()` and is not alphabetical:
`lint` runs last because ESLint needs the `.d.ts` that `interfaces` writes.

`Blocked` is the only unhappy way out, and that is the design: `core/hooks/SPECS.md` promises a hook
that blocks names its fix, and a second exit path is what once let a rejection reach the agent as
"No stderr output" — a refusal with no reason attached, costing a round of investigation each time.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`gates.py`](gates.py) | [`gates.pyi`](gates.pyi) | `source_quality`, `duplication_and_terms`, `lint` | The pre-commit stages that may REFUSE: line counts, duplication, facade boundaries, terms, lint. |
| [`gates_project.py`](gates_project.py) | [`gates_project.pyi`](gates_project.pyi) | `project_contract` | What a code/ project must declare before it can commit: verify contract, goal link, spec, branch shape, .md type, citations, gitlink. |
| [`generators.py`](generators.py) | [`generators.pyi`](generators.pyi) | `prepare`, `routing`, `issues`, `interfaces`, `skills` | The pre-commit stages that WRITE: brain stats, routing tables, interface stubs, skill mirrors. |
| [`post_commit.py`](post_commit.py) | [`post_commit.pyi`](post_commit.pyi) | `main` | Auto-push feature/* after a commit, so work survives a dead session and reaches the other machine. |
| [`pre_commit.py`](pre_commit.py) | [`pre_commit.pyi`](pre_commit.pyi) | `Blocked`, `git`, `spawn`, `Commit`, `collect` | The git pre-commit pipeline: what every stage shares, and the one place a commit is refused. |
<!-- routing:end -->
