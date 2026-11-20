# session
> Session lifecycle: start, prune, precompact wipe, and the SessionStart reminders.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`context-meter.py`](context-meter.py) | [`context-meter.pyi`](context-meter.pyi) | `state_file`, `announced`, `mark`, `compacted_state_file`, `announced_compaction` | UserPromptSubmit — say what the next turn costs, once per threshold crossed. |
| [`downloads.py`](downloads.py) | [`downloads.pyi`](downloads.pyi) | `folders`, `recent`, `report`, `main` | UserPromptSubmit — when the prompt says "baixei", name the files that just landed. |
| [`mirror-heal.py`](mirror-heal.py) | [`mirror-heal.pyi`](mirror-heal.pyi) | `heal_skills`, `report_permissions`, `main` | SessionStart — regenerate the generated content that a `git pull` cannot bring with it, and report the generated content that must NOT regenerate itself. |
| [`notify.py`](notify.py) | [`notify.pyi`](notify.pyi) | `last_sent`, `mark`, `muted`, `line`, `tell` | Notification, PreCompact — tell Lucas out of band when the session stopped needing a keyboard and started needing him. |
| [`precompact-wipe.py`](precompact-wipe.py) | [`precompact-wipe.pyi`](precompact-wipe.pyi) | `main` | PreCompact — wipe this session's CONTEXT.md and interface markers so both chains are re-read after compaction (injected context may be summarized away). See code/ROADMAP-verify.md W1. Switched off: the seen-markers survive compaction, so the chain is not re-read. |
| [`reminders.py`](reminders.py) | [`reminders.pyi`](reminders.pyi) | `read_body`, `count_entries`, `inbox`, `compass`, `publish` | SessionStart — the soft reminders, in one voice: what has piled up, what has gone unreviewed, what has not reached the public repo, a disk filling up, and the PRs waiting on a watched repo. One file, five switches, and at most one message. |
| [`session-prune.py`](session-prune.py) | [`session-prune.pyi`](session-prune.pyi) | `stale`, `main` | SessionStart — delete session marker stores older than 2 days. See code/ROADMAP-verify.md W1. |
| [`start-session.sh`](start-session.sh) | — | — | Neutral session-start entrypoint |
| [`statusline.py`](statusline.py) | [`statusline.pyi`](statusline.pyi) | `remembered`, `remember`, `bar`, `line`, `main` | statusLine — the context window as a line that is always on screen, and the trend across it. |
| [`transcript.py`](transcript.py) | [`transcript.pyi`](transcript.pyi) | `find`, `last_context`, `context_limit`, `is_compacted` | The session's own transcript, read cheaply: where it is, and what the last turn carried. |
<!-- routing:end -->
