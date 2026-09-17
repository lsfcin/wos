# session
> Session lifecycle: start, prune, precompact wipe, and the SessionStart nudges.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`context-meter.py`](context-meter.py) | [`context-meter.pyi`](context-meter.pyi) | `state_file`, `announced`, `mark`, `message`, `main` | UserPromptSubmit — say what the next turn costs, once per threshold crossed. |
| [`mirror-heal.py`](mirror-heal.py) | [`mirror-heal.pyi`](mirror-heal.pyi) | `heal_skills`, `report_permissions`, `main` | SessionStart — regenerate the generated content that a `git pull` cannot bring with it, and report the generated content that must NOT regenerate itself. |
| [`notify.py`](notify.py) | [`notify.pyi`](notify.pyi) | `last_sent`, `mark`, `muted`, `line`, `tell` | Notification, PreCompact — tell Lucas out of band when the session stopped needing a keyboard and started needing him. |
| [`nudges.py`](nudges.py) | [`nudges.pyi`](nudges.pyi) | `read_body`, `count_entries`, `inbox`, `compass`, `publish` | SessionStart — the soft reminders, in one voice: what has piled up, what has gone unreviewed, and what has not reached the public repo. One file, three switches, and at most one message. |
| [`precompact-wipe.py`](precompact-wipe.py) | [`precompact-wipe.pyi`](precompact-wipe.pyi) | `main` | PreCompact — wipe this session's CONTEXT.md and interface markers so both chains are re-read after compaction (injected context may be summarized away). See code/ROADMAP-verify.md W1. Switched off: the seen-markers survive compaction, so the chain is not re-read. |
| [`session-prune.py`](session-prune.py) | [`session-prune.pyi`](session-prune.pyi) | `stale`, `main` | SessionStart — delete session marker stores older than 2 days. See code/ROADMAP-verify.md W1. |
| [`start-session.sh`](start-session.sh) | — | — | Neutral session-start entrypoint |
| [`statusline.py`](statusline.py) | [`statusline.pyi`](statusline.pyi) | `remembered`, `remember`, `bar`, `line`, `main` | statusLine — the context window as a line that is always on screen, and the trend across it. |
| [`transcript.py`](transcript.py) | [`transcript.pyi`](transcript.pyi) | `find`, `last_context` | The session's own transcript, read cheaply: where it is, and what the last turn carried. |
<!-- routing:end -->
