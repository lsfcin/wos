# caveman — Specs
> Global registration, the `$HOME` wiring, and the local adaptations that are the re-sync cost.

## Registered globally, not mirrored into `.claude/skills/`

`core/tools/wos/sync-skills` mirrors flat `core/skills/*.md` files into `.claude/skills/`. This is a
folder-shaped skill and sits outside that mirror deliberately: the suite is exposed **globally**, to
every project, which is the reach it had before vendoring and what it is for — one registration, no
project/user name collision.

It used to live in `~/.agents/skills/` + `~/.claude/hooks/`, outside version control: invisible to
the second machine, lost on a fresh clone, and unmodifiable without editing untracked files in
`$HOME`. Vendoring makes the workspace the source of truth, the same rule the rest of `core/`
follows; the global symlinks keep the reach.

## Wiring

`~/.claude/settings.json` points at `~/.claude/hooks/caveman-*.js|sh`, which are symlinks into
[`hooks/`](hooks/CONTEXT.md). Editing anything under `~/.claude/hooks/caveman-*` or
`~/.agents/skills/caveman` means editing this directory — they are links, not copies.

```bash
core/run tools/wos/sync-global-skills            # link
core/run tools/wos/sync-global-skills --check    # verify (exit 1 if stale/broken/missing)
```

Which files get linked, and what triggers each hook: [`hooks/CONTEXT.md`](hooks/CONTEXT.md).

## Commands

`/caveman [lite|full|ultra|wenyan-lite|wenyan|wenyan-ultra]` sets the level; `/caveman commit`,
`review`, `compress <file>`, `crew`, `help`, `stats` reach the subfiles. The pre-fold spellings
(`/caveman-commit`, `/cavecrew`, …) are still mapped by `hooks/mode-tracker.js`.

`stats` never reaches the model: the hook blocks the prompt and returns the numbers directly.

`commit.md`, `review.md`, `compress.md` and `cavecrew.md` are independent modes with their own
output style — the base rules do not stack onto them.

## Local adaptations — the re-sync cost

Keep this list short: it is what a re-sync with upstream has to reconcile.

1. **Seven skills folded into one.** `caveman-commit/-review/-compress/-help/-stats` and `cavecrew`
   became subfiles here; their frontmatter was stripped (a subfile is not a skill).
2. **Four files split to satisfy the workspace size gate** (≤200 lines), behaviour verified
   unchanged: `config.js` (274) → `config` + `flagfile` + `safepath`; `stats.js` (346) → `stats` +
   `stats-data` + `stats-pricing` + `stats-format`; `compress.py` (254) → `compress` + `prompts` +
   `safety`; `validate.py` (213) → `validate` + `extract`. Two of these removed genuine duplication
   (the symlink-safety block was copied between `safeWriteFlag` and `appendFlag`; the savings math
   was copied across three formatters). Public APIs are re-exported, so importers were untouched.
   **No exemption was taken** — a `.vendor` marker that would have switched the gates off was tried
   and rejected: vendored code complies with our rules like everything else, and this directory is
   absent from `core/hooks/vendored.txt` on purpose.
3. **`hooks/mode-tracker.js`** — added `/caveman <sub>` dispatch and a legacy map so the old
   per-command spellings still resolve; `crew`/`help` are one-shot and never write the flag.
4. **`hooks/activate.js`** — resolves `SKILL.md` one level up (vendored layout) with the old plugin
   path as fallback; strips the router table + `$ARGUMENTS` from the SessionStart injection; pulls
   the worked examples from `modes.md` so a session loads one level instead of six.
5. **Hook filenames** lost their `caveman-` prefix (`activate.js`, not `caveman-activate.js`) — the
   directory already says caveman. The `$HOME` links keep the prefixed names `settings.json` expects.
6. **First-line comments added to `scripts/__main__.py` and `scripts/benchmark.py`** — the two
   modules upstream left with neither a `#` comment nor a docstring, so the routing generator could
   not describe them. One line each, above the first import; nothing else moved.
7. **`SKILL.md`'s `description:` was shortened to fit `hoist.DESC_LIMIT`** (360), which the routing
   table truncates past — and a truncated description is a finding, not a rendering
   (`core/SCHEMA.md` § What a description must say). What was cut is the enumeration of
   the six levels and six sub-commands, which this router documents below anyway; every **trigger
   phrase** the harness matches on was kept, since those are what the field is for.
8. **`scripts/benchmark.py` glob mode is dead** and was left alone. It resolves
   `parents[3]/tests/caveman-compress`, a path from the upstream repo layout that exists in neither
   the old global install nor here. Explicit-pair mode (`benchmark_pair(orig, comp)`) works. Fix it
   upstream, not locally, or the next re-sync conflicts.
