# aiwbot — P2: backend + model + effort selection

Plan for the P2 line in [ROADMAP.md](ROADMAP.md). Extends [SPECS-capability.md](SPECS-capability.md) AD-10 with the surfaces measured on 2026-07-23 and records the UX decisions Lucas made the same day.

## Why this ranks here
It is a **money lever**, not a nicety: a claude turn costs ~$0.11 even when trivial, and this workspace has 6 configured opencode providers including free `opencode/*` levels. Routing a throwaway phone question to a free model must cost **one tap**, which is what fixes the ranking of every UX decision below.

## Verified surfaces (2026-07-23) — extends AD-10

| fact | value |
|------|-------|
| claude models | `--model fable\|opus\|sonnet` (aliases) or a full id (`claude-fable-5`) |
| claude effort | `--effort low\|medium\|high\|xhigh\|max` (one vocabulary, all models) |
| opencode catalogue | **478** models across **6** configured providers: openrouter 339, nvidia 82, google 21, ollama-cloud 18, alibaba-coding-plan 12, opencode 6 |
| `opencode models` cost | **1.1 s** per call → memoize in-process, never per keyboard render |
| opencode effort | `--variant`, and the vocabulary is **per model**, not per provider |
| `models.json` shapes | `effort`+values ×1578 · `toggle` ×939 · `budget_tokens` ×502 · none ×3311 |
| effort value sets seen | `low,medium,high` · `high,max` · `minimal,low,medium,high` · `low,medium,high,xhigh,max` · `max` alone … |

`~/.cache/opencode/models.json` is the offline declaration: per model `reasoning_options` and `limit.context`. It lists **every** provider (3311+ models), so the configured subset still has to come from `opencode models`.

**opencode picker parity is cheaper than the roadmap assumed.** The sqlite `session` row already carries everything but the preview — no message/part join needed for three of the four bits:

| bit | source |
|-----|--------|
| mode | `session.agent` (`build`/`plan`) |
| model + effort | `session.model` = JSON `{"id","providerID","variant"}` |
| context used | per-message occupancy, **not** `session.tokens_*` — those columns are lifetime totals. See "What the build changed" below. |
| context window | `models.json` → `limit.context` for that model id |
| preview | last `message` with `role=assistant` → its `part` rows of `type=text` |

Filtering by role matters: `part` rows of `type=text` also carry the **user's** message and `<system-reminder>` blocks, so a naive "last text part" preview would quote Lucas back at himself.

## Decisions

**D1 — morphing panel on the anchor keyboard** (Lucas). The answer bubble keeps its mode row plus one summary button; tapping it swaps the *same* message's markup for a menu, and picking a value applies it and swaps back. No new bubbles, no permanently heavy bubble, reuses `mode.py`'s optimistic-edit trick.

**D2 — favourites + provider drill-down** (Lucas). A short curated row covers the one-tap case;
`mais…` opens provider → paginated model list so the full 478 stay reachable without typing.

**D3 — switching backend starts a new session** (forced by AD-3, not a preference). A lineage belongs to its provider: a claude session id cannot be resumed by opencode. So "switch backend" is mapped to *the next turn opens a fresh session on that backend, carrying the title over*, and the callback answer says so out loud. Model and effort do apply to the running session (both CLIs accept them on resume), but a switch clears them: they are provider-specific strings and mean nothing to the other side.

**D4 — callback_data carries no session id.** The panel always edits the anchor message, and `reply_map` already maps that message_id → session_id, so the whole 64-byte budget is free for values (`openrouter/qwen/qwen3-coder-next` fits comfortably). AD-5 still governs labels.

**D5 — the frontend offers only what the backend declares.** No effort row for a model whose `reasoning_options` is `toggle`/`budget_tokens`/absent — an honest omission beats a picker whose values the CLI will reject.

## Steps

- [x] **1 — boundary.** `TurnOptions` gains `model` + `effort`. New `backend/caps.py` with
      `Capabilities(modes, favourites, groups)`; boundary gains `capabilities()` and `efforts(model)`,
      defaulting to empty in `CliBackend`. New `backend/providers/catalog.py` memoizes `opencode models` and
      reads `models.json` for `reasoning_options` + `limit.context`.
- [x] **2 — build_args.** claude maps `--model`/`--effort`; opencode maps `-m`/`--variant`/
      `--agent build|plan` (closing the mode gap AD-10 found) and `--title` for new sessions.
- [x] **3 — panel.** `frontend/select/panel.py`: the D1 state machine over `p:*` callback_data, with a
      shared paginated keyboard helper. Per-session settings persisted through a generalized
      `sessions.setting_for`/`set_setting` (`mode_for`/`set_mode` refactored onto it, not copied).
- [x] **4 — wiring.** `bot.py` threads the session's model/effort into `TurnOptions`; a pending
      backend switch (D3) dispatches with `session_id=None`. The anchor in `resume.py` gets the
      same root markup.
- [x] **5 — opencode picker parity.** `_row_to_item` fills `model`, `mode`, `context_used`,
      `context_window`, `preview` from the table above.
- [~] **6 — frontend split.** 14 files + the panel is past the point the size hook warns at.
      Boundaries: Telegram primitives (`reply`, `htmlsplit`) / text (`format`, `markdown`, `inline`,
      `phrases`) / interaction (the rest). Pure moves, done last so nothing gets moved twice.
- [x] **7 — docs + ship.** SPECS AD-11 (capability declaration + D3 semantics), ROADMAP, CONTEXT
      routing, `make test` green, merge to develop → main.

## Verification
Free: `make test`. Live (~$0.20): `make smoke` — plus one real cheap-model turn to prove the money lever actually saves money.

## What the build changed about the plan

1. **Step 6 landed on a different boundary.** The layer split (`tg/` + `text/`) was never what the size gate was complaining about — `sessions.py` was, at 194 lines. Cutting it by responsibility (`registry.py` = what the bot remembers, `sessions.py` = what the providers report) fixed the real pressure; the folder grouping stays open in ROADMAP Housekeeping as optional layout work.
2. **Context % for opencode was nearly wrong.** `session.tokens_*` looked like the obvious source and read 175% of the window on a real session: they accumulate over the whole session. Occupancy had to come off the last assistant message, which is a query — hence the new `session_detail` boundary method and the "list is an index, the page pays for detail" rule (SPECS AD-12).
3. **Effort is per model, not per backend.** The plan already suspected this; `models.json` confirmed four `reasoning_options` shapes and half a dozen different value sets. `efforts(model)` takes the model for that reason.
4. **Two label bugs only the rendered keyboard showed.** `short_model` folds any id containing a family name, so openrouter's page listed four different models as `fable`/`haiku`/`opus`/ `sonnet` — fixed with `format.model_label` (qualified ids keep their own last segment). And the paged view carried two identical `‹` meaning different things, so every back button now names its destination (`‹ provedores`).

## Open

- **Favourites are derived, not configurable.** `catalog._FAVOURITE_PROVIDERS` takes the first two models of `opencode` and `alibaba-coding-plan` — the flat-fee/free providers. That is a guess at which cheap models are actually good. If the shortlist is wrong in daily use, make it a `config.json` list rather than tuning the constant.
- **`/new` does not inherit the panel.** A fresh session starts on claude with no model and no effort; the knobs are per session and set after the fact. If starting cheap becomes the common case, the fix is a bot-level default rather than another flag on `/new`.
