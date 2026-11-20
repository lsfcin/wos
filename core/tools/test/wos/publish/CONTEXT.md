# publish
> Coverage for the one-way sync: what the floor refuses, and what the destination is left holding.

Split out of [`../`](../CONTEXT.md) 2026-09-18 at the crowding signal, and named for the code it covers the way [`../close/`](../close/CONTEXT.md) and [`../diagram/`](../diagram/CONTEXT.md) are —
so a surface and its coverage stay one word apart. What stayed next door asks whether the workspace agrees with its own declarations; these ask what happened at the other end of a copy.

Both cases are regressions from 2026-09-17, the day the first project crossed, and both are about a verdict that read clean while something was wrong: a refusal that could not let one project out, and a sync that copied bytes and stopped.

Zero-token, no network. Each builds its own repo and bare origin; nothing touches the real workspace.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260917_a_refused_tree_cannot_let_one_project_out.py`](test_b20260917_a_refused_tree_cannot_let_one_project_out.py) | [`test_b20260917_a_refused_tree_cannot_let_one_project_out.pyi`](test_b20260917_a_refused_tree_cannot_let_one_project_out.pyi) | — | b20260917 regression — the floor's precedence: the longest prefix wins, both ways. |
| [`test_b20260917_the_sync_never_finished_at_the_destination.py`](test_b20260917_the_sync_never_finished_at_the_destination.py) | [`test_b20260917_the_sync_never_finished_at_the_destination.pyi`](test_b20260917_the_sync_never_finished_at_the_destination.pyi) | — | b20260917 regression — the sync copied bytes and stopped: three ways the DESTINATION was left unfinished, each of which reported clean. |
| [`test_b20261119_publish_vs_lock.py`](test_b20261119_publish_vs_lock.py) | [`test_b20261119_publish_vs_lock.pyi`](test_b20261119_publish_vs_lock.pyi) | `target` | b20261119-publish-vs-lock regression — the sync takes the target's branch lock and gives it back. |
<!-- routing:end -->
