# caveman
> Ultra-compressed communication mode — vendored suite: router skill, mode subfiles, hooks, scripts.

Upstream: **[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman)** — the caveman modes,
the commit/review/compress skills, the cavecrew presets and the activate / mode-tracker / stats /
statusline hooks all originate there. Vendored here and adapted; the upstream project keeps the
credit for the idea and the original implementation.

A **folder-shaped** skill: `SKILL.md` is the router, everything beside it is a subfile of that
router. It registers globally rather than through `.claude/skills/`, which is what puts it in every
project instead of only this workspace.

Global registration, the `$HOME` symlinks and their sync command, and the local adaptations that a
re-sync has to reconcile: [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`hooks/`](hooks/CONTEXT.md) | Claude Code lifecycle hooks for the caveman suite — activation, mode tracking, stats, statusline. |
| [`scripts/`](scripts/CONTEXT.md) | Compression CLI behind `/caveman compress <file>` — detect file type, call the model, validate, retry. Upstream-synced (adapted, not verbatim). |

| File | Description |
|------|-------------|
| [`SKILL.md`](SKILL.md) | Ultra-compressed communication mode — router. Cuts token usage ~75% by speaking like a smart caveman while keeping full technical accuracy, across six intensity levels and six sub-commands. Use when the user says "caveman mode", "talk like caveman", "less tokens", "be brief", or invokes /caveman. Also auto-triggers when token efficiency is requested. |
| [`SPECS.md`](SPECS.md) | Global registration, the `$HOME` wiring, and the local adaptations that are the re-sync cost. |
| [`cavecrew.md`](cavecrew.md) | Subfile of the `caveman` skill. Reached via `/caveman crew` (legacy `/cavecrew`). Decision guide only — it spawns nothing itself. |
| [`commit.md`](commit.md) | Subfile of the `caveman` skill. Reached via `/caveman commit` (legacy `/caveman commit`). Independent mode: it defines its own output style; the base caveman rules do not stack on top. |
| [`compress.md`](compress.md) | Subfile of the `caveman` skill. Reached via `/caveman compress <file>` (legacy `/caveman-compress`). Independent mode. Scripts live in `scripts/` next to this file. |
| [`modes.md`](modes.md) | Caveman — intensity levels, worked |
| [`review.md`](review.md) | Subfile of the `caveman` skill. Reached via `/caveman review` (legacy `/caveman-review`). Independent mode: it defines its own output style; the base caveman rules do not stack on top. |
<!-- routing:end -->
