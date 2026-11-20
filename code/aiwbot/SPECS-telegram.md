# The Telegram surface
> Panels, buttons, tables and speech-to-text: what the chat client can render.
> governs: frontend/

### AD-5 — Telegram `InlineKeyboardButton` labels don't render multi-line
Discovered live (2026-07-22): a `\n` inside a button's `text` doesn't produce a multi-line button —
Telegram clients render everything as one line and truncate it. Any "rich" per-item display (title + preview + meta) has to live in the *message text* instead, where `\n` works normally; buttons stay single-line tap targets, order-matched to a numbered list in the text (see `frontend/session/resume.py`).

### AD-13 — Panel layout: at most four per row, framed by two controls
*Lucas's design, 2026-07-23 — second iteration.* The first cut was a fixed 5-column grid padded with invisible braille-blank buttons, chosen so every cell was square and column N of one row sat above column N of the next. **Abandoned the same day**: Telegram divides a row's width evenly between its buttons, so five columns meant ~8-character labels, and model ids truncated past the point of telling apart (`claude-fable-latest` vs `claude-haiku-latest`). Lucas: *"desisti do grid, tá custoso em termos de usabilidade."*

The rule now is positional rather than geometric:

- **At most four buttons per row, and rows may hold fewer.** No padding — a shorter row simply has wider buttons. Labels get ~12 characters instead of ~8.
- **The first button is always `+` (open) or `‹` (back one level).** It was an `x` that jumped straight to the mode row; Lucas replaced it 2026-07-23 because a single control that always cancels reads wrong inside a tree — `‹` walks menu → values → providers → a provider's models back up one step at a time.
- **The last button is always `···` / `−`** (expand / collapse the value list), wherever it lands.
- So a collapsed picker is one row of `x`, **two** values, `···` — or **three** values when the list fits and there is nothing to expand.
- Rows split **evenly**, not greedily: five buttons become 3+2, never 4+1. Width is shared inside a row, so a greedy tail would stretch one lone button across the whole bubble.
- The pager is a row of its own (`‹ N/M › −`), which is what keeps the collapse control last.

Two behaviours this layout forces, both discovered by rendering the real states:

1. **The selected value is pinned first whenever the list is truncated**, including when it was chosen in the drill-down and is not in the shortlist at all. Two visible slots out of five means a picker showing `low medium ···` while `high` is set — invisible state. Selected-first is the one rule that always shows it.
2. **`‹` and `«` are different controls.** Back-one-level and previous-page both sit in the leftmost slot of their row, so identical glyphs would stack vertically meaning two different things. Paging uses the double angles `«` `»`.
3. **A dimension with nothing to offer is not shown at all.** `effort` disappears from the menu when the chosen model declares no effort vocabulary — including opencode before any model is picked, where the vocabulary is simply unknown. This replaced an alert saying "esse modelo não expõe controle de esforço", which was both unreachable-by-intent and, worse, was the generic message for *any* empty list (see AD-15).

The mode row is not a picker and keeps fixed positions: `+ [ BUILD ] PLAN`, only the bracket moves.

### AD-14 — `/new` gives up ForceReply to carry the panel
Telegram accepts exactly **one** `reply_markup` per message: `ForceReply` *or* an inline keyboard, never both. A bare `/new` used to send a `ForceReply` (which focuses the keyboard and pre-anchors the reply); carrying the harness/model/effort grid means giving that up. Lucas chose the single bubble with buttons (2026-07-23), so `/new` now answers with a config bubble you adjust and then reply to by hand. `/new <prompt>` and the `bot ` prefix are unchanged: they start immediately on the inherited defaults.

### AD-18 — Pipe-tables render as row blocks, never a `<pre>` box (2026-07-26)
Telegram has no table syntax at all. Boxing a table in `<pre>` (the original b1 rendering) fails on both axes a table has: `<pre>` escapes its contents, so cell markdown freezes into literal `**`; and it does not wrap, so it overflows. Measured over 412 tables from real agent answers, **95% carried inline markdown** and **0 of 412** fit a phone-width monospace bubble (median widest row 151 chars) — so there is no narrow case worth a second code path. `frontend/text/table.py` renders each row as a labelled block (`<b>name</b>` then `header: value` lines), labelling values only when a row has siblings to tell apart. The bug this closes is ISSUES b1.

### AD-19 — STT: one punctuated carrier prompt, plus a confidence hallucination guard (2026-07-26)
Whisper imitates the style of what it is primed with, so punctuation is bought by a punctuated `initial_prompt`, not by any decode flag. But `initial_prompt` and faster-whisper's `hotwords=` share one conditioning slot, so the jargon rides *inside* a punctuated carrier (`hotwords.CARRIER`)
rather than in a competing arg — priming for punctuation alone had turned "bote" into "Pode".
Separately, Whisper hallucinates words on near-silent audio and no decode setting stops it (VAD only shortened the garbage), so the guard is the model's own `avg_logprob`: real transcripts scored -0.15..-0.48, garbage -1.49, threshold `_MIN_LOGPROB = -0.9`; a rejected transcript rides the C3 fail-safe. `no_speech_prob` is 0.000 for every file once VAD strips the silence — not a usable signal. Corollary convention: **`format.plain` is `html.escape`, never speech** — TTS input goes through `speech.to_speech`, not `plain`. Contract in `frontend/SPECS.md`.

### AD-20 — A panel tap costs exactly one Telegram round trip (2026-07-27)

Measured, not reasoned about: bot-side work on every warm callback path is **under 1 ms**, while one call to `api.telegram.org` is **222 ms** median from Lucas's machine. Anything that felt slow about a button was therefore a count of round trips, never our compute — and the count was wrong in three places (two sequential calls per tap, three on a value choice, plus an 839 ms `opencode models` shell on the first tap after each restart).

The rule that follows: **one tap issues one `answerCallbackQuery` and at most one `editMessageReplyMarkup`, concurrently.** `panel._redraw` is the single place both are sent, via `asyncio.gather`; `_route` threads a choice's toast through as an argument so no branch is tempted to answer a second time. Anything a backend computes to draw a keyboard is warmed at startup (`choices.warm`, through the boundary) rather than lazily on the button.

This is a floor, not a target: a Telegram client renders an inline keyboard purely from server state, so no local echo or optimistic client update exists to beat one round trip. The button's built-in spinner is the only instant feedback there is, and clearing it is already what `answerCallbackQuery` does. `concurrent_updates(True)` is deliberately **not** enabled — it overlaps separate taps but does nothing for a single tap's latency, while widening the race on `config.json`'s non-atomic read-modify-write. Regression spec: `tests/test_f3c_tap_latency.py` asserts the round-trip *count*, since the duration is not ours to hold.

### AD-21 — The STT conditioning prompt is prose, end to end (2026-07-27, corrects AD-19)

AD-19 shipped `initial_prompt` as punctuated carrier sentences **followed by the bare `HOTWORDS` list**, reasoning that the two only had to share one conditioning slot. Measured against Lucas's chuveiro voice note, that shape scores **0.0 punctuation marks per 100 words** — the priming failed outright, and he reported it as "punctuation didn't work".

Three prompt shapes, same audio, same model:

| prompt shape | punctuation | `claude sonnet` |
|---|---|---|
| sentences, then bare word list (AD-19, shipped) | **0.0**/100w | ✗ `claudsonner` |
| bare word list, then sentences (tail punctuated) | **1.1**/100w | ✓ |
| jargon dissolved *into* the sentences | **22.5**/100w | ✓ |

The middle row is what kills the obvious theory: the carrier sat at the tail, where whisper weights hardest, and punctuation still died. **A bare word list anywhere in the prompt suppresses punctuation.** So the rule is: the conditioning prompt is prose from end to end, and the way to teach the STT a new word is to put it in a sentence someone could have said. `HOTWORDS` survives as the *checklist* — the existing coverage test now doubles as the guard that every listed word really appears in a sentence.

Second, independent cause of the same complaint: **no model name was in the vocabulary at all** —
no `claude`, no `sonnet`, no `opus`. `claude sonnet` had nothing to anchor to, came back as `claudsonner`, and so the F3a spoken directive silently never fired. Naming a model out loud is a first-class way to steer a turn, so the models belong in the primed vocabulary like any jargon.

### AD-22 — A picker reorders only to rescue a hidden selection (2026-07-27)

`_ordered` hoisted the current value to the front unconditionally, so every model pick reshuffled the buttons under Lucas's thumb. The behaviour exists for a real reason — a picker that hides what is set is worse than one that reorders — but that reason only applies when the selection would fall outside the drawn slots. Claude's handful of aliases all fit on one row, so there was nothing to rescue and the motion was pure noise. Hoisting is now conditional on the selection actually being cut off; a list that already shows its selection keeps its declared order.

### AD-28 — Build only, so the panel opens on the knobs (2026-07-28)

Lucas took option A of AD-27: plan mode is not supported through the bot. Two things follow, and both are the point rather than side effects.

**Mode is coerced, not offered.** `registry.mode_for` returns `build` whatever is stored, so a session started on the PC in plan mode and continued from the phone silently becomes a build turn instead of inheriting a mode the bot cannot honour. The knob survives on the boundary (`TurnOptions.mode`, each backend's mapping) — restoring plan is one line if a future CLI stops blocking MCP in it — but nothing in the bot writes anything else.

**The panel lost a level.** BUILD/PLAN was a two-option segmented control with one reachable option, and the `+` that used to open the dimension menu existed only to get past it. Both are gone: the root keyboard IS harness/model/effort, so the panel costs one tap where it cost two.
Keyboards already sitting in the chat still carry `p:mode:*` buttons, so that callback stays routed — to a redraw of the current panel, never to setting a mode.
