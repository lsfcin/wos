# copilot
> Provider shim: translates Copilot hook payloads onto the canonical gates.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`copilot-agent.sh`](copilot-agent.sh) | — | — | Copilot wrapper that honors .agentrc.json and runs session-start and hooks |
| [`copilot-post-tool.py`](copilot-post-tool.py) | [`copilot-post-tool.pyi`](copilot-post-tool.pyi) | `emit_allow`, `main` | Copilot PostToolUse hook: regenerate interfaces, sync context, record read-trackers. |
| [`copilot-pre-tool.py`](copilot-pre-tool.py) | [`copilot-pre-tool.pyi`](copilot-pre-tool.pyi) | `emit_allow`, `gate`, `main` | Copilot PreToolUse hook: enforce workspace read/edit/terminal policy via the canonical core/hooks scripts. The gates are located relative to THIS file, never from the workspace root: pointing at a spelled-out directory is what left this shim calling a dead `.hooks/` for a full day after the hooks moved into core/ (2026-07-31). |
| [`copilot-session-start.py`](copilot-session-start.py) | [`copilot-session-start.pyi`](copilot-session-start.pyi) | `load_input`, `read_workspace_excerpt`, `load_caveman_context`, `main` | Copilot SessionStart hook: inject workspace policy context + caveman rules. |
| [`copilot_shared.py`](copilot_shared.py) | [`copilot_shared.pyi`](copilot_shared.pyi) | `load_input`, `session_id`, `normalize_path`, `collect_paths`, `first_string` | Shared plumbing for the Copilot pre/post tool shims: payload extraction + canonical hook exec. |
<!-- routing:end -->
