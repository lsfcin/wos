# read
> Who must read what before touching a folder — and who gets handed it instead.

Two directions, one subject. **Gates force a read**: the CONTEXT.md chain, the interface stub, the
module spec. **[`agent-context.py`](agent-context.py) supplies one** — subagents are exempt from the
chain gate ([`SPECS.md`](../SPECS.md), ruled 2026-08-15), which moves the duty of briefing a worker onto
the orchestrator, and that hook is what stops the duty being a discipline nobody keeps. It induces,
never blocks.

[`chain.py`](chain.py) holds the one definition both directions need: a path's CONTEXT.md chain, the
workspace paths named in a blob of text, and a CONTEXT.md's own `>` summary line. It was two copies
before, already drifted on whether the chain starts at the target or its parent.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`agent-context.py`](agent-context.py) | [`agent-context.pyi`](agent-context.pyi) | `blob_file`, `collect`, `inject`, `main` | PreToolUse: Agent (collect) + SubagentStart (inject) — hand a worker the context for the paths it was pointed at, so the orchestrator does not have to remember to. |
| [`bash-context-gate.py`](bash-context-gate.py) | [`bash-context-gate.pyi`](bash-context-gate.pyi) | `main` | PreToolUse: Bash — close the cat/head/grep bypass: extract workspace file paths from the command string and apply the same CONTEXT.md chain gate as context-gate.py. Known residual hole: dynamically constructed paths escape. See code/ROADMAP-verify.md W1. |
| [`chain.py`](chain.py) | [`chain.pyi`](chain.pyi) | `context_chain`, `interface_state`, `blocking_interface`, `prerequisites`, `paths_in` | chain.py — the CONTEXT.md chain of a path, and the workspace paths named in a blob of text. |
| [`context-gate.py`](context-gate.py) | [`context-gate.pyi`](context-gate.pyi) | `target_path`, `main` | PreToolUse: Read|Edit|Write|Grep|NotebookEdit — force-read the CONTEXT.md chain of the target's subtree before any other file access. Session-deduped via marker file (/tmp/claude_ctx_seen_<session_id>.txt, written by context-tracker.py). See code/ROADMAP-verify.md W1. |
| [`context-tracker.py`](context-tracker.py) | [`context-tracker.pyi`](context-tracker.pyi) | `main` | PostToolUse: Read — record CONTEXT.md/SPEC.md reads (consumed by context-gate.py / bash-context-gate.py / spec-read-gate.py) and interface-file reads (consumed by pre-read.py: interface read unlocks its source). ROADMAP-verify.md W1. |
| [`pre-read.py`](pre-read.py) | [`pre-read.pyi`](pre-read.pyi) | `codegraph_root`, `nudge`, `main` | PreToolUse: Read — block a source read while its interface stub is current. Current stub: hard block (exit 2), the stub must be read first. Stale: warn and allow. |
| [`spec-read-gate.py`](spec-read-gate.py) | [`spec-read-gate.pyi`](spec-read-gate.pyi) | `find_spec_module`, `block`, `nudge`, `main` | PreToolUse: Edit|Write — a spec-locked module (its CONTEXT.md carries `> spec:` and the referenced SPEC.md header is `status: locked`) requires that SPEC.md be Read this session before editing the module's files. See code/ROADMAP-spec-drive.md. |
<!-- routing:end -->
