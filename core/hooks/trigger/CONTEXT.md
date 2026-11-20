# trigger
> When a feature fires, read from the registrations rather than from where its file sits.

Split out of this directory's root on 2026-08-18, the day it landed: the root holds the law and its two entrypoint families, and two more modules there put it past the crowding signal.

[`trigger_law.py`](trigger_law.py) answers **when**, the fourth question beside what a file *is*, what a name *may be* and what is *switched on*. Its data files are declarations that already existed: a harness `settings.json`, the `pre-commit` dispatcher's own stage order, and the `SETUP.md` install step registering what must live outside this repo.

[`hook_reach.py`](hook_reach.py) is the walk — which file an entrypoint goes on to run. It is deliberately moment-free, which is what keeps the pair acyclic.

**A feature this cannot place is reported, never guessed.** That is the whole difference from the directory convention it replaced, which put the always-loaded norms at *on save* because the file generating them runs then.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`hook_reach.py`](hook_reach.py) | [`hook_reach.pyi`](hook_reach.pyi) | `target`, `chain`, `code`, `index`, `reaches` | Which files a hook ENTRYPOINT actually reaches. The sibling of hook_input.py one level up: that one parses what comes INTO a hook, this one says what a hook goes on to RUN. |
| [`hooktime.py`](hooktime.py) | [`hooktime.pyi`](hooktime.pyi) | `commands`, `timed`, `floor`, `main` | What the enforcement layer COSTS when it fires, in seconds, read from the registrations rather than from a hardcoded list. Usage: core/run hooks/trigger/hooktime.py [--reps N] [--config PATH]. No network, no model. |
| [`trigger_law.py`](trigger_law.py) | [`trigger_law.pyi`](trigger_law.pyi) | `ordered`, `registrations`, `sites`, `moments_of` | WHEN it fires. The fourth law module: file_law.py says what a file IS, schema_law.py what a name MAY BE, feature_law.py which features are LIVE — this one says at which moment a live feature runs. Like the other three it reads its answer out of declared files rather than holding one. |
<!-- routing:end -->
