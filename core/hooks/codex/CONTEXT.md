# Codex
> Translate Codex lifecycle events and patches into the canonical workspace hook protocol.

`policy.py` reuses the dispatcher, post-edit pipeline and prompt meter. `patch.py` reconstructs contents without writing, checking every changed path. Shell reads reach the trackers with a successful status or full-text proof; truncated and dynamic reads do not. Routine success is silent; model context carries only common actionable messages, deduplicated.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`patch.py`](patch.py) | [`patch.pyi`](patch.pyi) | `locate`, `updated`, `changes` | Translate Codex apply_patch into complete file contents without writing anything. |
| [`policy.py`](policy.py) | [`policy.pyi`](policy.pyi) | `shell_commands`, `read_command`, `shell_reads`, `succeeded`, `invoke` | Codex lifecycle adapter: translate tool payloads and reuse the canonical WOS dispatcher. |
<!-- routing:end -->
