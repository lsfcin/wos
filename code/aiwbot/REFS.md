# aiwbot — References

Prior art and alternatives weighed for this bot, kept so the rejected paths don't get re-litigated from memory. Full landscape + the pivot rationale: [`brain/goals/workspace-os.md`](../../brain/goals/workspace-os.md).

## The three architecture patterns

| # | Pattern | Example | Verdict |
|---|---------|---------|---------|
| A | CLI-wrapper subprocess | our old bot (`core/tools/telegram_daemon.py`) | superseded — fork/divergence |
| B | Agent-SDK single-process | linuz90/claude-telegram-bot | **chosen shape**, rebuilt in Python behind a swappable boundary |
| C | Session-native official | Remote Control, Channels | rejected — 100% Claude Code lock-in |

## B — linuz90/claude-telegram-bot (the reference)
<https://github.com/linuz90/claude-telegram-bot> — MIT, Bun/TypeScript, ~451★. Whole Anthropic coupling
sits in one `src/session.ts` `query()` call; also `src/handlers/streaming.ts`, `src/handlers/commands.ts`, `docs/personal-assistant-guide.md`.

- **Lineage**: `query({ prompt, options: { resume: sessionId } })` — plain resume, **no fork**, captures `session_id` once and never overwrites → one id, one transcript. Same behavior as our `claude -p --resume <id>` without `--fork-session` (AD-3).
- **Session model**: one global current session + saved history of the last 5, switched via a `/resume` tap-picker. Ours differs: many parallel sessions disambiguated by which message you reply to.
- **UX worth stealing** (still open on our ROADMAP): streaming live-edit of one message; `!`/`/stop` interrupt + queueing; extended-thinking budget by keyword; `ask_user` MCP → inline buttons (Claude interviews you mid-task); `send_file` MCP; voice/photo/doc ingestion; command-safety allowlist.
- Frames Claude Code as a personal assistant pointed at a CLAUDE.md folder — our `brain/` concept.

Deeper notes: memory `reference_linuz90_bot`.

## C — the official Anthropic paths (rejected, not forgotten)
- **Remote Control** — `claude --remote-control [name]` / `/rc`. One local session mirrored real-time across terminal + phone + web. The "Google Doc" dream, zero code.
- **Channels** — `/plugin install telegram@claude-plugins-official`. Official Telegram bridge pushing DMs into the one open session, with native `reply` / `react` / `edit_message` tools — it already does the threading + working-message UX we hand-built.
- **Why rejected**: both bind the project 100% to Claude Code, against the provider-agnostic principle ("não quero ser refém do claude code"). Revisit only if that trade-off is deliberately reversed.
- Note: as of AD-8 these are no longer required for *native session visibility* — the `CLAUDE_CODE_ENTRYPOINT` env var achieves that without lock-in.

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
- **Live-session roster**: `~/.claude/sessions/<pid>.json` (`kind`, `entrypoint`, `name`), pid-scoped, managed by `claude agents`. This is what `--bg` background agents registered in — the reason bot sessions once appeared in VSCode, and the reason each turn spawned an extra session (AD-3).
- **`history.jsonl`** is the up-arrow prompt history, NOT the picker index.

## Voice alternatives (2026-07-29)
- **Fish Audio S2.1 Pro** — [reel](https://www.instagram.com/reel/DbXVmc4hIxH/), [src: web:instagram.com]: open-weight TTS pitched as ~5x cheaper than ElevenLabs, demoed holding multiple speakers and interruptions. Lucas asked whether it helps aiwbot's STT/TTS. **Assessed: no, not for the voice reply.** aiwbot's TTS is Kokoro-82M running locally (C5/C6)
  — cost per character is already zero and nothing leaves the machine, so "cheaper than ElevenLabs" is not a lever here.
  It becomes interesting only if Kokoro's pt-BR quality is the complaint, which it has not been; keep as the first thing
  to try if it ever is.

## System-1 decision & message triage (2026-09-28)
- **JEV vs Laya** — [reel](https://www.instagram.com/reel/Dd1SON3tqGZ/?utm_source=ig_web_copy_link), [src: web:instagram.com]: Kem @ GlitchCatClub review of JEV (TypeSafe AI) vs Laya (Convai, Apache 2.0). Fast decision primitives (boolean, choice, score) in a single call. Primary use case: instant, low-cost Telegram DM/message triage without running a full LLM. Task in `ROADMAP.md`.

## Telegram assistant UX benchmarks (2026-09-28)
- **Mira (`mira.tg` / `miracodeai/mira`)** — [site](https://mira.tg/), [src: web:mira.tg]: personal AI assistant native to Telegram with tool/app integrations (GitHub, Google Calendar, Notion, Linear) directly from chat, plus open-source PR reviewer on GitHub. Useful benchmark for aiwbot command UX and app integrations. Task in `ROADMAP.md`.

- [OpenHarness — gittrend.io](https://www.instagram.com/reel/DePGHMiki4X/?rpxt=dmx1d3RyOHNna2dr) — [src: web:instagram.com] Demonstration names autonomous-ai/openharness and claims native terminals, cross-machine sessions and encrypted relay; verify claims and Linux support before adoption. Assessment: ROADMAP.md, Housekeeping.

- [C] [Hype-versus-reality carousel and official tool checks](https://help.blotato.com/start-with-an-ai-agent/llm/automations.md) — [src: web:instagram.com] Creator opinions; bars are estimates, not printed scores or benchmarks; [capture](https://www.instagram.com/p/DeZjFVZALGO/); assessment: ROADMAP.md [rated-tools].
- [V] [Unsloth browser control](https://unsloth.ai/docs/basics/browser-use.md) — [src: web:instagram.com] Restricted browser/network; memory depends on quantization and vision; [capture](https://www.instagram.com/reel/DfEDl31NaQg/); assessment: ROADMAP.md [unsloth-browser].
- [C] [Package hallucinations](https://www.lasso.security/blog/ai-package-hallucinations) — [src: web:instagram.com] Original benign package experiment: 30k downloads, not 30m victims; [capture](https://www.instagram.com/reel/DfE78eZqVkd/); assessment: ROADMAP.md [dependency-provenance].
- [P] [Harness²](https://github.com/google-research/harness2) — [src: web:instagram.com] Fixed-weight harness optimization costs extra runs; control judge/sandbox; [capture](https://www.instagram.com/reel/Dewrk9ax1LP/); assessment: ROADMAP.md [harness2].
- [V] [Backboard R-CLI](https://github.com/Backboard-io/Backboard-R-CLI) — [src: web:instagram.com] Model-agnostic CLI; 30%/90% savings lack a matched controlled comparison; [capture](https://www.instagram.com/reel/DdJqqm0xprR/); assessment: ROADMAP.md [r-cli].
- [C] [VoiceStudio local voice](https://github.com/debpalash/VoiceStudio) — [src: web:instagram.com] App/model licences differ; OmniVoice noncommercial; demo Mac has 64 GB; [capture](https://www.instagram.com/reel/De1zlGniBQp/); assessment: ROADMAP.md [voice-studio].
- [V] [Programmatic tool composition](https://blog.cloudflare.com/code-mode-mcp/) — [src: web:instagram.com] Tool-definition footprint saving, not universal whole-task token saving; [capture](https://www.instagram.com/reel/DeypYeWN5hL/); assessment: ROADMAP.md [code-mode].
- [C] [pstack verification patterns](https://github.com/cursor/plugins/tree/main/pstack) — [src: web:instagram.com] Completion/invariant patterns; throughput and portability not established; [capture](https://www.instagram.com/p/De6cbtKjjXg/); assessment: ROADMAP.md [pstack].
- [V] [Programmatic tool composition](https://www.anthropic.com/research/advanced-tool-use) — [src: web:instagram.com] Programmatic composition/filtering; assess without adopting MCP; [capture](https://www.instagram.com/reel/De6pmMnBu2x/); assessment: ROADMAP.md [code-mode].
- [V] [Task-specific models and Jev](https://docs.scaledown.ai/introduction) — [src: web:instagram.com] Narrow task heads; summaries generate; schema validity is not correctness; [capture](https://www.instagram.com/reel/Devav4iBMF5/); assessment: ROADMAP.md [scaledown].
- [C] [Dessa speech preview](https://block.xyz/dessa) — [src: web:instagram.com] Speech preview; primary page unread, release/licence/access unverified; [capture](https://www.instagram.com/p/De_ghm7DMTo/); assessment: ROADMAP.md [dessa].
- [C] [Brands Decoded Claude Code advice](https://support.claude.com/en/articles/11647753-how-do-usage-and-length-limits-work) — [src: web:instagram.com] The 100–200k quality chart explicitly says its source was invented; [capture](https://www.instagram.com/p/DefaJVojOSp/); assessment: ROADMAP.md [context-evidence].

- [C] Cross-harness session reports — [src: Claude/Codex sessions, 26–30 Oct 2026] Caller/callee inventory, quota claims, executable discovery and background-job recipes are reports to verify; assessment: ROADMAP.md [cross-harness-delegation].
- [Hex](https://lucassf.pages.dev/wos/hex) — [src: github:anomalyco/hex] Local dictation; compare Portuguese, Linux shortcut/paste and latency. Task: ROADMAP.md [stt-ubuntu-shortcut].
- [Claude quality](https://lucassf.pages.dev/wos/claude-quality) · [capture](https://lucassf.pages.dev/wos/claude-quality-reel) — [src: Anthropic; Instagram/albert.olgaard] April 2026 client/context/effort fixes concern other versions; deliberate degradation is unproven. Task: ROADMAP.md [cross-harness-delegation], [model-regression].
- [Respan](https://lucassf.pages.dev/wos/respan) — GitHub/respanai; Instagram DfMoeX7ij47: provider-format gateway, not CLI-session adapter; author speed figures unreplicated; hedging costs extra calls. Task: ROADMAP.md [respan-gateway].
- [Infinity](https://lucassf.pages.dev/wos/infinity) — GitHub/hydro-project; Instagram De9or1Jienw: hibernation/tool events; 75k waiting states do not imply 75k simultaneous inferences. Task: ROADMAP.md [infinity-runtime].
- [Claude advisor](https://lucassf.pages.dev/wos/advisor) — Instagram/sully.omarr: stronger-model consultation; savings unverified, advisor may increase tokens; [post](https://lucassf.pages.dev/wos/advisor-post); task: ROADMAP.md [advisor].
