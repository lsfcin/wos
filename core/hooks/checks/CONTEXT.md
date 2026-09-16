# checks
> Standalone blocking checks the commit and edit hooks run.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`check-duplication.py`](check-duplication.py) | [`check-duplication.pyi`](check-duplication.pyi) | `main` | Pre-commit duplication gate — jscpd over the repo; blocks when a clone involves a staged file. No baseline: touching a file with a legacy clone means extracting it now (ROADMAP-verify.md W2). |
| [`citation-gate.py`](citation-gate.py) | [`citation-gate.pyi`](citation-gate.pyi) | `citation_exempt_paths`, `staged_files`, `citation_hits`, `limit_exempt_paths`, `limit_hits` | Level 0: a roadmap item number is not a citable identifier outside the roadmap family. |
| [`first-line-gate.py`](first-line-gate.py) | [`first-line-gate.pyi`](first-line-gate.pyi) | — | PreToolUse, capability write — a new file must open by saying what it is. |
| [`heredoc-gate.py`](heredoc-gate.py) | [`heredoc-gate.pyi`](heredoc-gate.pyi) | `targets`, `body_writes`, `in_workspace`, `written_paths`, `main` | PreToolUse: Bash — a shell heredoc that writes a workspace file meets none of the file gates. |
| [`issues-gate.py`](issues-gate.py) | [`issues-gate.pyi`](issues-gate.pyi) | `bug_ids`, `fixed_ids`, `repo_root`, `has_spec`, `main` | PreToolUse: Edit|Write on ISSUES.md — the FIXED gate. A bug may not leave this file without executable proof: flipping one to FIXED, or deleting its section, requires a matching regression spec (a file named *b<N>[_-]* under a test/ directory of this repo). |
| [`line_counts.py`](line_counts.py) | [`line_counts.pyi`](line_counts.pyi) | `report`, `main` | The line-count gate: warn and block on authored lines, at the two numbers limits.env declares. |
| [`memory-gate.py`](memory-gate.py) | [`memory-gate.pyi`](memory-gate.pyi) | — | PreToolUse, capability write — a memory is written when Lucas asks for one, never on the agent's own initiative. |
| [`retired-gate.py`](retired-gate.py) | [`retired-gate.pyi`](retired-gate.pyi) | `main` | PostToolUse, capability `write` — a retired token reaches the agent at the edit, not at the close. |
| [`size-gate.py`](size-gate.py) | [`size-gate.pyi`](size-gate.pyi) | — | PreToolUse, capability write — refuse a write that would put an authored code file over the cap. |
| [`type-gate.py`](type-gate.py) | [`type-gate.pyi`](type-gate.pyi) | `check_name`, `failures_for`, `main` | Level 0 gate (core/SCHEMA.md § The .md type system): a staged file must be a known .md type or a well-shaped instance, must sit where its type is allowed to live, must give the routing table something to write about it, and a CONTEXT.md must not hand-list files. Zero-token, no LLM. |
| [`write_payload.py`](write_payload.py) | [`write_payload.pyi`](write_payload.pyi) | `block`, `target`, `written_size` | What every write gate needs from its stdin: which file is being written, and how big it would get. |
<!-- routing:end -->
