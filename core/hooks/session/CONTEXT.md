# session
> Session lifecycle: start, prune, precompact wipe, and the SessionStart nudges.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`compass-nudge.py`](compass-nudge.py) | [`compass-nudge.pyi`](compass-nudge.pyi) | `main` | SessionStart — a soft, ignorable reminder that the compass review hasn't run in a while, so the inspiring work waiting can gently resurface. NOT a nag: one line, in-session only, trivial to skip. Paired with /compass (the gentle strategic review). Tone law lives in brain/FOUNDATIONS.md — "what has good wind", never guilt. Mirrors the inbox-nudge pattern. |
| [`context-meter.py`](context-meter.py) | [`context-meter.pyi`](context-meter.pyi) | `state_file`, `announced`, `mark`, `message`, `main` | UserPromptSubmit — say what the next turn costs, once per threshold crossed. |
| [`inbox-nudge.py`](inbox-nudge.py) | [`inbox-nudge.pyi`](inbox-nudge.pyi) | `read_body`, `count_entries`, `main` | SessionStart — warn Lucas + agent when brain/INBOX.md has piled up past a threshold, so capture doesn't silently grow and scatter. The drain runs HERE, at session start where context is cheap — /roundup only counts, and hands /inbox to the next session (core/skills/roundup.md § Phase 3). |
| [`mirror-heal.py`](mirror-heal.py) | [`mirror-heal.pyi`](mirror-heal.pyi) | `heal_skills`, `report_permissions`, `main` | SessionStart — regenerate the generated content that a `git pull` cannot bring with it, and report the generated content that must NOT regenerate itself. |
| [`notify.py`](notify.py) | [`notify.pyi`](notify.pyi) | `last_sent`, `mark`, `muted`, `line`, `tell` | Notification, PreCompact — tell Lucas out of band when the session stopped needing a keyboard and started needing him. |
| [`precompact-wipe.py`](precompact-wipe.py) | [`precompact-wipe.pyi`](precompact-wipe.pyi) | `main` | PreCompact — wipe this session's CONTEXT.md and interface markers so both chains are re-read after compaction (injected context may be summarized away). See code/ROADMAP-verify.md W1. Switched off: the seen-markers survive compaction, so the chain is not re-read. |
| [`session-prune.py`](session-prune.py) | [`session-prune.pyi`](session-prune.pyi) | `stale`, `main` | SessionStart — delete session marker stores older than 2 days. See code/ROADMAP-verify.md W1. |
| [`start-session.sh`](start-session.sh) | — | — | Neutral session-start entrypoint |
| [`statusline.py`](statusline.py) | [`statusline.pyi`](statusline.pyi) | `remembered`, `remember`, `bar`, `line`, `main` | statusLine — the context window as a line that is always on screen, and the trend across it. |
| [`transcript.py`](transcript.py) | [`transcript.pyi`](transcript.pyi) | `find`, `last_context` | The session's own transcript, read cheaply: where it is, and what the last turn carried. |
<!-- routing:end -->
