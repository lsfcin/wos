# aiwbot — Roadmap

## Context
Provider-agnostic rebuild of the workspace Telegram bot. The old bot (core/tools/telegram_daemon.py)
shells `claude -p` per message (fork/divergence). Official Anthropic Remote Control + Channels solve sync but lock us 100% into Claude Code — against the provider-agnostic principle. Direction: streaming, single-lineage, with a swappable backend boundary (linuz90's architecture, rebuilt in Python). Providers become interchangeable data. Full design + research: brain/goals/workspace-os.md.

Design of everything already shipped lives in the [SPECS.md](SPECS.md) family (AD-1…AD-33); the P2/P3 plans in [ROADMAP-p2.md](ROADMAP-p2.md) / [ROADMAP-p3.md](ROADMAP-p3.md).

### Known limits (won't chase)
- **VSCode picker needs a window reload** to pick up newly created sessions (the extension caches its list). Terminal `claude --resume` re-reads every time. `Ctrl+Shift+P → Reload Window` is the quick way.
- **`resume.RULER_WIDTH = 44`** — eyeball estimate of how wide the monospace ruler must be to out-measure a 64-char preview line. Re-tune if the `/resume` bubble ever looks padded or breathes.

## Finish plan — settled 2026-07-26 (supersedes the 2026-07-23 ranking)

Lucas: *"I really want to finish that bot asap, all of it."* The 2026-07-23 lens still holds — each item scored by *does this remove a reason Lucas has to go back to the PC?* — but the open list is now sequenced as a **finish line**, not an open-ended backlog.

**Finish line = through `ask_user`.** Once the bot can interview Lucas mid-task it is fully away-from-PC capable. **show-me** and **Phase D** stay parked past the line: show-me degrades via artifacts (Lucas 2026-07-23), and Phase D is a structural rewrite that buys cost/latency, not a new capability.

### F4 — shipped through Stage 4; Stage 5 is what is left
Design and measurements: SPECS AD-24…AD-33. Streaming and `ask_user` are live on both providers.

**Live now:** `"stream": "true"` in `~/.config/aiwbot/config.json` defaults; ask is on by default.
Rollbacks, least drastic first: `"ask": "false"` + restart (turns invoked as they were before ask) → `painter.STREAM_SEAL = False` (one freezing bubble, live text kept) → `"stream": "false"` + restart (back to batch delivery). None of them is a code change.

### F4 Stage 5 — the last one: `ask_user` in anger
Not a demo. A genuinely underspecified task handed over while away from the PC, letting the agent interview its way to something usable. What it tests is judgement rather than plumbing: whether the agent asks at the *right* moments, whether it asks too much or too little, whether a 55-minute wait behaves when the answer takes twenty, and whether a long interview leaves the chat readable. Closing this closes F4.

### Telegram's rich text editor — assessed 2026-07-27, mostly NOT actionable
Lucas asked whether the new editor ([blog](https://telegram.org/blog/communities-editor-invisible-messages/pt-br)) lets us format better: *"pelo visto tem headers. será que tabelas?"*. It announces "um editor de texto avançado com suporte para títulos, tabelas, listas, citações e blocos de código".

**Checked against the API rather than the blog.** PTB 22.8 implements **Bot API 10.0**, whose entity list is `BOLD, ITALIC, CODE, PRE, BLOCKQUOTE, EXPANDABLE_BLOCKQUOTE, SPOILER, UNDERLINE, STRIKETHROUGH, TEXT_LINK, …` — **no `HEADING`, no `TABLE`.** The editor is a *client-side composer* for humans typing in the app; it is not new surface a bot can send. So headings stay bold-caps (AD-14) and **AD-18's pipe-tables-as-row-blocks remains correct, not a workaround**.
Nothing to do. Re-check if a future Bot API adds the entities.

- [ ] **Worth taking, and available today: `<blockquote expandable>`** (`EXPANDABLE_BLOCKQUOTE`).
      Collapses a long passage behind a "show more" the reader opens on demand. It is the one
      genuinely new-to-us lever the assessment turned up, and it fits the long-answer problem F5
      attacked from the other side — candidate for the *tail* of a long answer, or for the
      transcript echo of a long voice note. Not scheduled; it interacts with AD-23's splitting,
      so decide it after F4 lands rather than tangling two shape changes at once.

### Past the finish line — parked, not scheduled (Lucas 2026-07-26)
Both survive here because they are real gaps, not because they are queued. Promote one only when a concrete session's cost makes it worth more than it costs.
- [ ] **show-me: outbound media + channel awareness** (from INBOX 2026-07-22) — **demoted to last by
      Lucas 2026-07-23**: "if the model needs it, it can build an artifact anyway", so the gap degrades
      instead of blocking. Kept on the list because the degraded path costs a round trip every time.
      Two halves: (1) **outbound** — the agent emits a file path or artifact URL and the bot ships the
      actual file/preview into the chat (`send_photo`/`send_document`), needing a sentinel convention
      the frontend strips plus size/type guards; (2) **channel awareness** — the turn knows whether it
      arrived from Telegram or VSCode, so the agent picks *how* to check with Lucas (send the image vs.
      "look at your screen"). Injectable per-turn on `TurnOptions`, same as mode. Lucas's words:
      *"garantir que o modelo tem como me mostrar NO telegram o que ele precisar, enviar pdfs, links,
      talvez focar em artifacts seja mais fácil… garantir essa parte de 'checar' … remotamente"*.
- [ ] **Phase D — persistent mode + more backends**: claude via SDK `ClaudeSDKClient`, opencode via
      `--attach` server (only if per-message cost annoys); copilot backend; retire/thin the workspace
      bot to INBOX-only capture. Biggest structural rewrite — last on purpose.
- [ ] **triage-decision-model**: avaliar modelo de decisão System-1 (JEV/Laya) para triagem e classificação prévia de mensagens/áudios no aiwbot com latência e custo mínimos (ref em `REFS.md`).
- [ ] **mira-benchmark**: avaliar padrões de UX do mira.tg e repo miracodeai/mira no GitHub para benchmarking de assistente/agente no Telegram (integração GitHub/Notion via chat) (ref em `REFS.md`).
- [ ] **backend-zcode**: implementar provedor Z-Code (Z.ai / GLM) como novo `AgentBackend` em `backend/providers/zcode.py` para execução de tarefas via Telegram (INBOX 2026-09-27).
- [ ] **backend-antigravity**: implementar provedor Antigravity (`backend/providers/antigravity.py`) no aiwbot e avaliar como backend default no Telegram para evitar limites frequentes de cota do Claude (INBOX 2026-09-27).
- [ ] **stt-ubuntu-shortcut**: expor comando CLI / endpoint leve de transcrição de áudio do aiwbot para atalho de sistema operacional no Ubuntu (gravação rápida de microfone → transcrição via Whisper do aiwbot → cursor/clipboard) (INBOX 2026-10-01). Compare Hex for Portuguese dictation, Linux shortcut/paste and latency; keyword agent invocation is separate. Ref: REFS.md [Hex].

## Housekeeping

- [ ] [mobile-session-relay] Assess one owned path for continuing a desktop session from Telegram without competing polling or commands in the capture queue; coordinate ../../core/ROADMAP.md, Desktop hyperagent (Claude-session report, 23 Oct 2026).
- [ ] Assess OpenHarness (REFS.md) and which backend/session capabilities can serve the desktop hyperagent, preserving session lineage; application assessment in ../../core/ROADMAP.md (high priority, week).
- [ ] Measure idle model memory and assess releasing unused models without harming voice capture or session continuity (INBOX 2026-10-14).
- [~] **`backend/providers/opencode.py` is at 194/200** after the ask config landed, and `claude.py` at 176.
      Both warn, neither blocks. The boundary the next touch should cut along is already visible: the
      **config/env** half (`_ask_config`, `env`, `supports_ask`, the timeout) is a different
      responsibility from the **parsing** half (`parse_events`, `LineStream`, `_line_to_event`), and
      claude already splits exactly that way (`claudeparse.py`). Do it when something needs adding,
      not now — an empty split is churn.

## Rejected
Tried or measured, then dropped — recorded so a dead idea does not resurface looking new.
- **`concurrent_updates(True)`** — overlaps separate taps but does nothing for a single tap's latency (the actual complaint), while widening the race on `config.json`'s non-atomic write.
  The floor is one round trip (~222 ms); no trick beats it, because a Telegram client renders an
  inline keyboard purely from server state — no optimistic update, no local echo.
- **Forcing IPv4 to Telegram** — measured *slower* than the IPv6 default (203 vs 191 ms median).
- **A fixed 5-column panel grid** (padded with invisible cells for squareness) — 5 columns meant ~8-char labels and model ids stopped being distinguishable. Positional grid ≤4/row instead (AD-13).
- **Scrolling/marquee button text** — a label is static; animating costs one `editMessageReplyMarkup` per frame at ~1.5 s each → sub-1 fps, and flood control. The only richer Telegram component is a Web App webview needing an HTTPS page — revisit only if buttons stop being enough.
- **Telegram's rich text editor as new bot surface** — see the assessment above: client-side composer only, no `HEADING`/`TABLE` entity in Bot API 10.0.

## Verification
- Free (every change): `make test`. Live milestone (~$0.20): `make smoke`.

## Backlog

- [ ] [advisor] Compare executor-plus-advisor with current model routing on matched tasks, measuring quality, retries, total tokens and quota consumption. Ref: REFS.md [advisor] (Instagram lead).

- [ ] [infinity-runtime] Assess Infinity yielding/hibernation and tool events against existing orchestration: persisted state, interruption recovery, session continuity, memory and bounded concurrency; waiting states are not simultaneous model inference. Ref: REFS.md [Infinity].

- [ ] [respan-gateway] Assess Respan against existing provider integration: format/tool fidelity, streaming, fallback, observability and total cost; hedging can duplicate billed requests. Model-request routing is distinct from CLI session management. Ref: REFS.md [Respan]. Assess model-API paths only; preserve existing CLI-session adapters.

- [ ] [cross-harness-delegation] Compare matched agent tasks for quality, cost, quota, startup discovery and process/log supervision; preserve dated Claude/Codex reports as hypotheses, not executable recipes. Shared assessment: ../../core/ROADMAP.md [cross-harness-delegation]. Include [model-regression] checks of client/model versions, effort, context and settings before switching backend/model; historical incidents do not prove intent.

- [ ] [context-evidence] Compare focused context, planning and meaningful verification with existing practice using measured local outcomes, not the creator's invented 100k quality cutoff. Ref: REFS.md [context-evidence].

- [ ] [dessa] Assess the actual release/access/licence state and relevance to Portuguese voice interaction before considering any integration; retain secondary-only primary-page limitations. Ref: REFS.md [dessa].

- [ ] [scaledown] Compare narrow classification/extraction/summarization baselines for correctness and cost, distinguishing schema validity, semantic accuracy, generation and hosted availability. Ref: REFS.md [scaledown].

- [ ] [pstack] Assess completion criteria, invariants, behavior evidence and bounded parallel work against our existing workflow; separate portability and throughput claims from demonstrated facts. Ref: REFS.md [pstack].

- [ ] [code-mode] Compare code-owned tool composition and filtered results with the current workflow, retaining direct calls where useful and requiring no Model Context Protocol adoption. Ref: REFS.md [code-mode].

- [ ] [voice-studio] Assess one Portuguese narration/voice-interface sample with actual model licence, memory, latency and export constraints; reuse the existing VoiceStudio reference. Ref: REFS.md [voice-studio].

- [ ] [r-cli] Compare one matched coding task for quality, total tokens/cost, memory-service behavior and portability before changing a harness or provider. Ref: REFS.md [r-cli].

- [ ] [harness2] Compare controlled harness-improvement loops with existing orchestration, including model-call budget, held-out evaluation, judge bias and retained sandbox restrictions. Ref: REFS.md [harness2].

- [ ] [dependency-provenance] Assess how dependency-source verification and locked inventories cover the documented hallucinated-package risk; use the original benign case and reviewed study in teaching. Ref: REFS.md [dependency-provenance].

- [ ] [unsloth-browser] Assess a bounded browser task with documented permission/network limits and memory headroom before selecting a local browser-agent setup. Ref: REFS.md [unsloth-browser].

- [ ] [rated-tools] Assess the relevant voice, meeting, workflow, prototype and media tools against current needs; preserve creator ratings as opinion and numerical bar lengths as estimates. Ref: REFS.md [rated-tools].

- [ ] [atomic-telegram] Reproduce the current bot failure, then compare Atomic Agent's matching Telegram code path for a fix; its GAIA score says nothing about our integration. Ref: ../../core/refs/REFS.md [Atomic Agent].

<!-- routing:start -->
## Routing

| Part | Description |
|------|-------------|
| [`ROADMAP-p2.md`](ROADMAP-p2.md) | ← add description |
| [`ROADMAP-p3.md`](ROADMAP-p3.md) | ← add description |
<!-- routing:end -->
