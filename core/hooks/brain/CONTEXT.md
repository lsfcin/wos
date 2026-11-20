# brain
> brain/ attention stats and the GOALS.md dashboard.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`_templates/`](_templates/CONTEXT.md) | The shape of a brain/ — CONTEXT.md, GOALS.md, INBOX.md and two goal shapes, with nobody's content in them. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | Goal file format, section growth triggers, signals, dynamics, timing, and backlog conventions. |
| [`brain_attention.py`](brain_attention.py) | [`brain_attention.pyi`](brain_attention.pyi) | `parse_owns`, `governing_repo`, `harvest`, `Attention`, `count` | Brain attention — what commits actually touched a goal, across every repo in the workspace. |
| [`brain_common.py`](brain_common.py) | [`brain_common.pyi`](brain_common.pyi) | `workspace_rel`, `areas`, `git`, `replace_block` | Brain stats — shared config, git helpers, and block replacement. |
| [`brain_dashboard.py`](brain_dashboard.py) | [`brain_dashboard.pyi`](brain_dashboard.pyi) | `bar`, `area_from_file`, `timing_display`, `parse_goal_file`, `update_goals_table` | Brain stats — GOALS.md dashboard rendering (area/goal bars, active-goals table). |
| [`brain_stats.py`](brain_stats.py) | [`brain_stats.pyi`](brain_stats.pyi) | `trend_label`, `build_stats_block`, `compress_done`, `load_goal_files`, `staged_goal_files` | Brain attention tracker — per-file stats, done compression, commit orchestration. |
| [`memory-gate.py`](memory-gate.py) | [`memory-gate.pyi`](memory-gate.pyi) | — | PreToolUse, capability write — this workspace keeps no memory store, so a harness writing one is refused and handed the file that owns the fact. |
<!-- routing:end -->
