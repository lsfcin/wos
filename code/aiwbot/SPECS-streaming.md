# Streaming and bubbles
> How an answer arrives bubble by bubble, what is sealed, and what spend means.
> governs: frontend/ streaming

### AD-23 — An answer is a conversation, and every bubble of it is repliable (2026-07-27)

Two rules, and the second is what makes the first safe.

**Long answers split at paragraph boundaries on purpose.** Not as a 4096 rescue — as the shape of
the thing. Lucas: *"talvez fosse até uma estratégia de UX partir a resposta em várias mensagens
pra parecer mais como uma conversação"*. `split_html` takes a soft size (`reply.SOFT_CHARS = 900`)
past which the chunk ends at the next blank line, so a bubble never stops mid-thought; Telegram's
hard cap still wins, and a run of blank lines can never seal an empty chunk. The same path
delivers the `/resume` anchor, which is why `ANCHOR_BODY_MAX` is gone: that 3000-char mid-word
clip, not Telegram's limit, produced the `[…]` Lucas reported.

**Every message the bot sends for one turn anchors to that turn's session.** `reply.deliver`
returns all of them and callers map all of them, because Lucas replies to whichever bubble he
happens to be reading, not to the last one. Anchoring only the tail meant a reply to an earlier
bubble missed `session_for_reply` and fell through to INBOX capture — the turn silently did not
continue. That failure is *created* by splitting, so the two rules ship together and the message
map is sized for bubbles (`msgmap.MAX = 400`), not for turns.

**Corollary, reversing F2's reply anchor.** F2 led every answer with `continua [ABC] TÍTULO`
because Telegram quotes a message from its start, so the session name had to be the first line.
The reasoning was sound and aimed at the wrong reader: the bot's answer is already `do_quote`d
onto Lucas's own message, so the thread is visible without announcing it. The line is deleted,
not demoted; the id and title live in the footer (`[ABC] TÍTULO · claude · sonnet · build ·
$0.031`), which is where he asked for them. `answer.py` now owns the answer message's shape —
`format.py` stays shared text formatting, and the split is what kept it under the size gate.

### AD-24 — Occupancy is the last request; anything summed is spend (2026-07-27, b3)

A turn is not one API request. A turn that uses tools makes several, and each one re-reads the
whole conversation from cache — so **any total over a turn measures money, and only the last
request measures how full the window is.** Summing them put 100–200%+ in the footer of Lucas's
answers; over real transcripts the same sum reaches 5921%, 6507% and 32533%. The denominator was
never the problem — the learned windows were a correct 1,000,000.

The subtle part, and the reason this is a spec and not a patch note: the wrong number is *not
always visibly wrong*. One real session summed to a perfectly plausible 62% when the truth was
5%. A bug that only sometimes looks like a bug is one that survives review, so the rule is
structural rather than a range check.

It lives on the boundary, as `CliBackend.occupancy(session_id, cwd)` — every CLI records a
per-message token breakdown in its own store, so each backend reads occupancy from there and the
run's summary object is never trusted for it. claude takes the transcript's last assistant
message; opencode takes `ocstore.last_turn`, which is also the first time an opencode answer
reports a percentage at all. `ocstore.py` had documented this exact trap for opencode's
accumulating `tokens_*` columns and the claude path walked into it anyway — one backend
remembering a rule is not the same as the boundary enforcing it.

Belt and braces on top: `format.context_pct` withholds any share above 100%, because a share of
the window cannot exceed the window. A visibly missing number is a better bug report than a
confidently wrong one.

### AD-25 — Streaming seals bubbles; it never rewrites one (2026-07-27, F4 Stages 1–3)

Painting an answer as it arrives could easily have contradicted AD-23, which says a long answer is
several bubbles and every one of them is repliable. It does the opposite — it makes AD-23
*continuous* — and the reason is a property, not a convention:

**`split_html` is prefix-stable.** Its loop is a single forward pass whose boundaries are decided only
from lines already consumed, so appending text can change nothing but the **last** chunk.
Property-tested over 25 corpora × every line-boundary prefix of each: zero violations. Therefore
every chunk but the last is already final, and a bubble can be sent the moment it appears and
**never touched again**. Each is anchored on arrival rather than at the end of the turn, so a
reply to bubble 1 continues the session while bubble 3 is still being written — strictly better
than the batch path, which could only anchor once everything existed.

Three rules follow, and they are the ones to preserve:

1. **Only text that can no longer change is rendered.** `markdown.stable_prefix` settles
   everything up to the last blank line *outside an open code fence* — a parity count, not a
   regex, because inside a fence a blank line is code, not a paragraph break. The unsettled tail
   rides as escaped plain text; rendering it would make it flicker between literal and formatted
   as closing markers land.
2. **One code path for streamed and finished.** `answer.block` delegates to `answer.frames`, so
   the shipped answer *is* a frame with no pin and a footer. That is what makes the AD-23
   non-regression test meaningful rather than two implementations that happen to agree today.
3. **Throttling drops, never queues.** The gate is a clock check inside `paint()`, not a
   background ticker, so nothing races the end of the turn. A paint already in flight is
   discarded, which is lossless because every frame recomputes from the whole accumulated text —
   and it is what stops a fast stream from piling requests up behind a ~200 ms round trip (AD-20).

The cadence itself (`MIN_INTERVAL`, `MIN_GROWTH`) is a **UX knob Lucas tunes by reading real turns
in the chat**, not a rate-limit constant — it went 1.5 s → 5 s → 3 s in one session. Tests pin the
*spacing invariant against the constant*, never a literal, so tuning never edits a test. Telegram's
native `ChatAction.TYPING` carries the gap between repaints and is deliberately lit on the FIRST
delta, independent of the repaint gate, so the wait before the first visible words is never silent.

Streaming stays behind `TurnOptions.stream` because it changes the CLI's invocation: the rollback
has to be reachable from Lucas's phone — one line in `config.json` plus a restart, never a code
change. `painter.STREAM_SEAL` is the finer-grained rollback that gives up sealing while keeping
live text.

### AD-26 — The bot hosts the MCP server; the turn is named by the URL (2026-07-27, F4 Stage 4)

`ask_user` only works in linuz90's bot because the SDK runs the agent **in-process**: its tool
handler awaits a button press in the same process that owns the chat. aiwbot drives a
**subprocess CLI**, the opposite shape — a stdio MCP server would be spawned *by* that CLI, a
child of it, with no way to reach the daemon's Telegram state.

So the relationship is inverted: **the daemon hosts an HTTP MCP server in its own event loop, and
each turn points its CLI at it** (`--mcp-config '<json>' --strict-mcp-config`). The handler runs
where the chat already lives, blocks the agent's turn exactly like the in-process version, and no
Phase D rewrite is needed. It is plain JSON-RPC 2.0 over `aiohttp` — the `mcp` SDK would be a new
dependency for ~40 lines.

**The turn a question belongs to comes from the URL path** (`/mcp/<token>`), never from the
payload: an MCP request carries no turn id, and turns run concurrently as PTB tasks, so there is
nothing else to correlate on. The token is registered before the backend starts and released in a
`finally`, so it cannot outlive its turn. Two consequences that are easy to get wrong:

- **The handshake must be a pure function of the request.** Measured: one `claude -p` run sends
  `initialize` *three times*. A server holding per-connection state would answer the repeats from
  a half-built session.
- **`--strict-mcp-config` is not optional.** Without it the turn also loads whatever MCP servers
  Lucas configured for interactive Claude Code — a different tool surface than the one the turn
  was reasoned about with.
