# ZCode
> ZCode hook registration, skills mirror, and session artifacts for this workspace.

The registration contract — what ZCode spawns, how its events map onto the canonical ones,
and what is still unverified while the workspace is untrusted — is [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`skills/`](skills/CONTEXT.md) | ZCode's discovery point for the skill library: generated copies of core/skills, not tracked. |

| File | Description |
|------|-------------|
| [`SPECS.md`](SPECS.md) | What ZCode must spawn, how its events map onto the canonical ones, and what is still unverified. |
| [`config.json`](config.json) | ZCode hook registrations — one PreToolUse entry into core/hooks/dispatch.py, plus the tracker, session and compaction hooks. |
<!-- routing:end -->
