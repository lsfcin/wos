# dashboard
> The checks that are about the REPORT rather than about the tree: what a list may claim, and
> what the count was last time.

Split from [`../`](../CONTEXT.md) 2026-08-25, when the parent passed the hard file cap. The boundary is the one [`core/hooks/entropy/dashboard/`](../../../../../hooks/entropy/dashboard/CONTEXT.md) already uses next door: every check in `core/hooks/entropy/` answers one question about the tree, and these modules ask all of them and render the answer. A test of the rendering belongs with the rendering.

**A list reports its own repo and nothing else** (ruled 2026-09-04). The root used to sum every nested project into a table it committed, and those projects are repos its git ignores — so the number described a disk, and the clone without them read the same commit as red. The report and its trend history live in this machine's `outputs/state/`, never in git (2026-11-19).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b9_dry_run.py`](test_b9_dry_run.py) | [`test_b9_dry_run.pyi`](test_b9_dry_run.pyi) | — | B9 regression — a verification run is not a write. |
| [`test_entropy_trend.py`](test_entropy_trend.py) | [`test_entropy_trend.pyi`](test_entropy_trend.pyi) | — | T0 the entropy trend (core/hooks/entropy/dashboard/entropy_trend.py): a bare count let every session write "flat" while the real number climbed, so the header carries a baseline instead. Zero-token, runs in verify-fast. The window is the thing to get right: a baseline from outside it is invented. |
| [`test_report_shape.py`](test_report_shape.py) | [`test_report_shape.pyi`](test_report_shape.pyi) | `report` | T0 what the report shows, and what it stays quiet about: a clean check is a table row, never a section. |
<!-- routing:end -->
