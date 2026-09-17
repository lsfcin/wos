# wos
> Tools that act on the workspace itself: spec list, contract check, skill mirrors.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`close/`](close/CONTEXT.md) | What a session close writes, and what it does with each artifact afterwards. |
| [`diagram/`](diagram/CONTEXT.md) | The workspace drawn from its own declarations: one generated HTML picture, zero tokens, no model. |
| [`publish/`](publish/CONTEXT.md) | What crosses into the public repo his students clone, what no feature claims, and the refusal that runs before the first byte is copied. |
| [`session/`](session/CONTEXT.md) | What a session costs and what fills it, read from the local transcripts. No network, no model. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`deps`](deps) | — | — | check every dependency declared in core/tools/deps.txt, reporting what each miss breaks; --check exits 1 on any miss |
| [`features`](features) | — | — | list every toggleable feature from core/features.txt with its answer in core/profile.txt; --findings counts what cannot be switched off; --check exits 1 on any registry/profile disagreement; --scoreboard reports what each feature actually did |
| [`levels`](levels) | — | — | print the work→level map from core/levels.txt with the level each agent definition declares; --set re-renders every harness's agent files from those declarations; --check exits 1 when a rendered file no longer matches the declaration. |
| [`permissions`](permissions) | — | — | print the permission levels declared in core/permissions.txt with the one this machine answered in core/profile.txt; --set switches level and re-renders every harness config; --check exits 1 when a rendered config no longer matches the answer |
| [`roundup`](roundup) | — | — | the deterministic half of the /roundup ritual. Verification gate, entropy regen, branch promotion. Prints the state facts /handoff copies and anything that needs a decision; nothing else. |
| [`size`](size) | — | — | how big the authored .md corpus is, and how much of it this session added or removed, and where. Zero-token, no network. Called by core/tools/wos/roundup at every close (ROADMAP.md § Cost: "every session reports whether the workspace got smaller"), and runnable alone any time. |
| [`skills/mirror.py`](skills/mirror.py) | [`skills/mirror.pyi`](skills/mirror.pyi) | `is_skill`, `is_command`, `disabled`, `list_skills`, `list_commands` | Mirror generation for the skill library: listing, copy mirrors, command-file copies, and orphan pruning. A LIBRARY, not an entrypoint — core/tools/wos/sync-skills drives it and owns the CLI. |
| [`skills/validate.py`](skills/validate.py) | [`skills/validate.pyi`](skills/validate.pyi) | `frontmatter`, `validate_skills`, `validate_flows`, `validate_flow_loops`, `validate_flow_dag` | Frontmatter validation for every layer of the agent library — skills, flows, the flow composition DAG, and agents. The law is core/SCHEMA.md and core/SCHEMA-layers.md; this only enforces it. A LIBRARY, not an entrypoint — core/tools/wos/sync-skills owns the CLI. |
| [`spec-contract-check`](spec-contract-check) | — | — | verify every spec-locked module has a complete SPEC.md contract (Inputs/Outputs/Invariants filled); optionally type-check declared edges. Exit 1 on any gap. See code/ROADMAP-spec-drive.md. |
| [`spec-scan`](spec-scan) | — | — | list of module SPEC.md status (locked|draft|optout|none) Spec-driven-development coverage ratchet. A module = a dir with a CONTEXT.md under code/. See code/ROADMAP-spec-drive.md. |
| [`sync-global-skills`](sync-global-skills) | — | — | link workspace-vendored global skills into $HOME |
| [`sync-skills`](sync-skills) | — | — | regenerate skill mirrors from core/skills/*.md |
<!-- routing:end -->
