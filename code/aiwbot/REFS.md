# aiwbot — References

Prior art and alternatives weighed for this bot, kept so the rejected paths don't get re-litigated
from memory. Full landscape + the pivot rationale: [`brain/goals/workspace-os.md`](../../brain/goals/workspace-os.md).

## The three architecture patterns

| # | Pattern | Example | Verdict |
|---|---------|---------|---------|
| A | CLI-wrapper subprocess | our old bot (`core/tools/telegram_daemon.py`) | superseded — fork/divergence |
| B | Agent-SDK single-process | linuz90/claude-telegram-bot | **chosen shape**, rebuilt in Python behind a swappable boundary |
| C | Session-native official | Remote Control, Channels | rejected — 100% Claude Code lock-in |

## B — linuz90/claude-telegram-bot (the reference)
<https://github.com/linuz90/claude-telegram-bot> — MIT, Bun/TypeScript, ~451★. Whole Anthropic coupling
sits in one `src/session.ts` `query()` call; also `src/handlers/streaming.ts`, `src/handlers/commands.ts`,
`docs/personal-assistant-guide.md`.

- **Lineage**: `query({ prompt, options: { resume: sessionId } })` — plain resume, **no fork**, captures
  `session_id` once and never overwrites → one id, one transcript. Same behavior as our
  `claude -p --resume <id>` without `--fork-session` (AD-3).
- **Session model**: one global current session + saved history of the last 5, switched via a `/resume`
  tap-picker. Ours differs: many parallel sessions disambiguated by which message you reply to.
- **UX worth stealing** (still open on our ROADMAP): streaming live-edit of one message; `!`/`/stop`
  interrupt + queueing; extended-thinking budget by keyword; `ask_user` MCP → inline buttons (Claude
  interviews you mid-task); `send_file` MCP; voice/photo/doc ingestion; command-safety allowlist.
- Frames Claude Code as a personal assistant pointed at a CLAUDE.md folder — our `brain/` concept.

Deeper notes: memory `reference_linuz90_bot`.

## C — the official Anthropic paths (rejected, not forgotten)
- **Remote Control** — `claude --remote-control [name]` / `/rc`. One local session mirrored real-time
  across terminal + phone + web. The "Google Doc" dream, zero code.
- **Channels** — `/plugin install telegram@claude-plugins-official`. Official Telegram bridge pushing
  DMs into the one open session, with native `reply` / `react` / `edit_message` tools — it already does
  the threading + working-message UX we hand-built.
- **Why rejected**: both bind the project 100% to Claude Code, against the provider-agnostic principle
  ("não quero ser refém do claude code"). Revisit only if that trade-off is deliberately reversed.
- Note: as of AD-8 these are no longer required for *native session visibility* — the
  `CLAUDE_CODE_ENTRYPOINT` env var achieves that without lock-in.

## Community bots (surveyed, not adopted)
- RichardAtCT/claude-code-telegram (~2735★)
- grinev/opencode-telegram-bot (~946★)

## Claude Code internals we depend on (undocumented, verified live 2026-07-23)
These are observed behaviors of a closed CLI — re-verify if `claude` upgrades.

- **Transcript store**: `~/.claude/projects/<cwd with / → ->/<session-id>.jsonl`, one file per session.
- **`ai-title`** jsonl event = the picker's AI-generated title; latest occurrence wins (AD-7).
  `--name` writes a separate `custom-title` record instead.
- **`CLAUDE_CODE_ENTRYPOINT`** — decides the recorded entrypoint (`claude-vscode` / `cli` / `sdk-cli`).
  The native picker lists a session based on its **originating** entrypoint and hides `sdk-cli`. Only
  `claude-vscode` is accepted as an override; `cli` silently falls back (AD-8).
- **`modelUsage[model]`** in the `-p --output-format json` result carries token breakdown **and**
  `contextWindow` → context % for free (AD-9).
- **Live-session roster**: `~/.claude/sessions/<pid>.json` (`kind`, `entrypoint`, `name`), pid-scoped,
  managed by `claude agents`. This is what `--bg` background agents registered in — the reason bot
  sessions once appeared in VSCode, and the reason each turn spawned an extra session (AD-3).
- **`history.jsonl`** is the up-arrow prompt history, NOT the picker index.

## Voice alternatives (2026-07-29)
- **Fish Audio S2.1 Pro** — [reel](https://www.instagram.com/reel/DbXVmc4hIxH/), [src: web:instagram.com]: open-weight
  TTS pitched as ~5x cheaper than ElevenLabs, demoed holding multiple speakers and interruptions. Lucas asked whether it
  helps aiwbot's STT/TTS. **Assessed: no, not for the voice reply.** aiwbot's TTS is Kokoro-82M running locally (C5/C6)
  — cost per character is already zero and nothing leaves the machine, so "cheaper than ElevenLabs" is not a lever here.
  It becomes interesting only if Kokoro's pt-BR quality is the complaint, which it has not been; keep as the first thing
  to try if it ever is.

