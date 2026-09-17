# Questions and answers
> An agent that asks: how the question is carried, positioned, and answered.
> governs: frontend/ question handling

### AD-27 — An unanswered question returns text, and plan mode cannot ask at all (2026-07-27)

Two limits of the CLI, both measured against the binary rather than read off documentation, both
load-bearing:

**The tool call dies at ~60 s** ("Tool timed out. No answer got.") — nothing next to the hour
Lucas wants to answer in, away from his phone. `MCP_TOOL_TIMEOUT` (ms, in the subprocess env)
lifts it, and the bot's own `ask.WAIT_SECONDS` is set *below* the raised ceiling so the wait that
ends first is always ours. That ordering is what makes the next rule reachable:

**Every exit of a wait is a string.** Timeout, a turn that ended, a bubble Telegram refused — all
return *content* the agent can act on ("siga com a hipótese mais razoável e diga qual assumiu"),
never an MCP error. An error aborts the turn and throws away everything the agent had already
worked out; a sentence costs it one paragraph. Lucas's call, and the reason `ask()` has no raising
path at all.

**Plan mode refuses the whole MCP surface**: `claude -p --permission-mode plan` answers the call
with *"Cannot call mcp__aiwbot__ask_user while in plan mode"*, and an explicit `--allowedTools`
does **not** lift it. So `supports_ask` is a function of the *options*, not of the provider —
claude asks in build mode and never in plan. This is a real gap, because plan mode is exactly
where interviewing matters most; the substitute that measures out is
`--permission-mode bypassPermissions --tools "Read,Grep,Glob"` (read-only built-ins, MCP intact,
verified live), which trades plan mode's own prompt for the ability to ask. Not adopted
unilaterally — it changes what `mode=plan` means, so it is Lucas's call before Stage 5.

### AD-29 — A bubble carries its question and its position (2026-07-28)

Three shape rules, all from Lucas reading real turns:

**The voice transcript rides inside the answer, quoted, at the top of every bubble** — not in a
bubble of its own. The standalone echo (F2) cost a message and scrolled out of reach exactly when
the answer was long enough to need it. Repeated per bubble, any bubble he scrolls back to still
says what it answers. It is escaped and clipped (`LEAD_CHARS`), because it is arbitrary speech.

**Every bubble ends with its position**, `(2/3)`. The total is unknowable while the answer is
still arriving — bubble 3 exists only once the text that fills it does — so a bubble is born
carrying `(2)`, and **one closing pass** stamps the totals once the turn ends (Lucas asked for
exact positions everywhere, 2026-07-28). That pass is the single exception to AD-25, which is why
the rule reads "a sealed bubble is not rewritten *while the answer is streaming*" rather than
"never": prefix-stability guarantees the counter is the only thing that changes, and the pass runs
after the live bubble is finished, so the answer completes first and the stamping trails it.

**Bubbles are paced apart, one per paint.** `cadence.BUBBLE_GAP` is the floor between one bubble
appearing and the next; `MIN_INTERVAL` only ever paced repaints of the live bubble, and conflating
the two is why the cadence appeared to do nothing. A stream that outruns the gap waits rather than
losing text: the held text lands whole as the next bubble. `_grow` posts **exactly one** bubble per
paint however far ahead the stream has run — posting every chunk that already fits would land
three in the same second and undo the pause. The gap is a floor, never an added delay: a stream
slower than it passes through untouched, and the first bubble is never held back, because the
working message already is bubble one.

**`·` is a divider, never an opener.** It separates (`· · ·`, `provider · modelo`), so it must not
lead a line: `pensando…`, not `· pensando…`.

The furniture is budgeted BEFORE the split, not appended after: a chunk sized to the full limit
and then given a lead and a counter is a message Telegram rejects — and only ever on the long
voice answers this exists to serve.

### AD-30 — A question ends the segment above it (2026-07-29, from the first real interview)

An `ask_user` question is its own message, so the live bubble stops being the last thing in the
chat the moment one is posted. Everything the agent writes afterwards is an answer to that
question and must appear BELOW it — a live bubble that kept growing put the answer above the
question that prompted it.

So an answer is delivered in **segments**: a contiguous run of bubbles at the bottom of the chat.
`painter.cut()` ends one — repainting the closing bubble **without the pin** (with a question
pending, a status line claims work that is actually blocked on Lucas) and deleting it outright
when nothing but the status ever reached it. The next paint opens a fresh bubble below the
question. Three consequences, each of which broke once before it was pinned:

- **The closing delivery renders only the current segment** (`painter.tail_of`). Handing it the
  whole answer reposted everything written before the question underneath it.
- **Bubbles are numbered across the answer, not per segment**, so an interview does not restart at
  `(1)` after every question. Questions are not counted — they are not answer text.
- **A bubble is recorded undecorated** (`bubbles.bare`). Restamping a chunk that already carried
  `(1)` produced `(1) (1/10)`. Telegram hands back the plain rendering of a message, never the HTML
  that was sent, so the record is the only way to restamp at all.

Every counter, split and stamp here is **string formatting in `answer.py` — zero tokens, no model
involved.** That is why it can be relied on: the shape of a reply is never something the agent
chose or could get wrong.

Two shape rules from the same session: the counter closes the ANSWER (before the footer, hard
against the final word, never adrift on its own line), and the footer never gets a bubble of its
own — an answer ending on a paragraph break used to leave a blank line before `· · ·` that the
splitter read as a place to break.

**Both of the last two bugs passed every assertion in the file** and were caught by printing the
bubbles and reading them. Eyeball the output when the shape changes.

### AD-32 — A question carries its choices, and keeps its answer (2026-07-29, from the first opencode interview)

Three shape rules, all from Lucas reading a real interview on his phone. The interview itself
worked; what it looked like did not.

**The choices are written in the MESSAGE; the buttons are their numbers.** Options came back cut —
*"Cada mensagem vira sessão nov…"* — because a label is clipped to what a full-width button holds
and Telegram truncates rather than wraps (AD-5). Clipping was the wrong half to give up: it saved
the layout by making the choice unreadable. So the option is listed in full where newlines work,
and the key under it is `1`, `2`, `3` — a number never truncates on any phone, and `/resume` had
already settled this exact trade the same way. The tap still carries an INDEX, so the agent
receives the whole sentence it wrote, however it was displayed.

**An answered question shows its answer.** Nothing in the chat said what had been chosen: scrolling
back, Lucas could see what was asked and never what was decided. The answer is written into the
same bubble, in italic, under the question — one message, not a new one, because a separate bubble
would scroll away from what it answers exactly as the standalone voice echo did (AD-29). The
keyboard goes at the same time, so a stale tap cannot pretend the question is still open, and the
"reply to this message" hint goes with it — an instruction to do something already done.

**What the chat shows is not what the agent gets.** The three unanswered exits (timeout, ended,
expired) are instructions *to the model* — "siga com a hipótese mais razoável" — so quoting them
into the chat would put words in Lucas's mouth. They collapse to `sem resposta`; the agent still
receives its full sentence. The bubble is rebuilt from the text the bot SENT, never from
`message.text`, for the same reason AD-30 records: Telegram hands back a plain rendering.

`ask.py` hit the 200-line gate during this change and split along the line the gate exposed:
`ask.py` is the **broker** (tokens, futures, who is waiting) and `askshape.py` is the **view**
(what Lucas reads and taps). Nothing in the view knows about a future.
