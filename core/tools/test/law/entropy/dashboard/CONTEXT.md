# dashboard
> The checks that are about the REPORT rather than about the tree: what a list may claim, and
> what the count was last time.

Split from [`../`](../CONTEXT.md) 2026-08-25, when the parent passed the hard file cap. The boundary is
the one [`core/hooks/entropy/dashboard/`](../../../../../hooks/entropy/dashboard/CONTEXT.md) already
uses next door: every check in `core/hooks/entropy/` answers one question about the tree, and these
modules ask all of them and render the answer. A test of the rendering belongs with the rendering.

**A list reports its own repo and nothing else** (ruled 2026-09-04). The root used to sum every
nested project into a table it committed, and those projects are repos its git ignores — so the
number described a disk, and the clone without them read the same commit as red. Each one recomputes
what it checks rather than reading what was written: the trend's baseline comes from git, never from
yesterday's memory, because a count anything else could write into is the drift these checks catch.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260902_a_generated_list_is_red_on_the_clone_that_did_not_write_it.py`](test_b20260902_a_generated_list_is_red_on_the_clone_that_did_not_write_it.py) | [`test_b20260902_a_generated_list_is_red_on_the_clone_that_did_not_write_it.pyi`](test_b20260902_a_generated_list_is_red_on_the_clone_that_did_not_write_it.pyi) | — | b20260902 regression — the workspace's own list describes the workspace, never this disk. |
| [`test_b5_list_commits.py`](test_b5_list_commits.py) | [`test_b5_list_commits.pyi`](test_b5_list_commits.pyi) | — | B5 regression — the list's writer owns its artifact, so a written list is never left loose. |
| [`test_b9_dry_run.py`](test_b9_dry_run.py) | [`test_b9_dry_run.pyi`](test_b9_dry_run.pyi) | — | B9 regression — a verification run is not a write. |
| [`test_entropy_trend.py`](test_entropy_trend.py) | [`test_entropy_trend.pyi`](test_entropy_trend.pyi) | `git`, `commit`, `repo` | T0 the entropy trend (core/hooks/entropy/dashboard/entropy_trend.py): a bare count let every session write "flat" while the real number climbed, so the header carries a baseline instead. Zero-token, runs in verify-fast. |
| [`test_report_shape.py`](test_report_shape.py) | [`test_report_shape.pyi`](test_report_shape.pyi) | `report` | T0 what the report shows, and what it stays quiet about: a clean check is a table row, never a section. |
<!-- routing:end -->
