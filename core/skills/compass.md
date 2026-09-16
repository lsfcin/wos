---
name: compass
description: Gentle strategic review of Brain: what has good wind, reorder by motivation, ditch guilt-free, close wins, next easy start.
---

A gentle strategic review of Brain — a thinking partner, not a taskmaster. Surface what has good
wind, reorder energy by motivation, negotiate timing, offer guilt-free ditching, close wins, and
hand Lucas the next easy start.

Arguments: $ARGUMENTS

## Protocol

Read: `brain/GOALS.md` + all files in `brain/goals/` (skip `_template.md`). Read `brain/SPECS.md` § Rationale
if you need to recalibrate the tone.
Run: `git log --oneline --since="14 days ago" -- brain/goals/`

This is an **interview**, not a report. Propose lightly, let Lucas choose, then write back what he
decides. Guiding law: **ordering by motivation wins over deadlines/pressure** — always.

### 1. Read the wind

1. Cross-reference prescribed priority (signals: impact × engagement) vs actual git touches.
2. Detect **almost-there** goals — a step from a milestone / mvp / finish. Infer it (no dedicated
   field) from: backlog `[x]`/`[ ]` ratio, `motion: advancing`, recent git touches, `closure` proximity.
3. Parse `anchor`/`target` per goal — compute the countdown, but **hold it lightly**: a deadline is a
   secondary, gentle signal, never the organizing axis.
4. Diagnose each goal — read `>**dynamics**` and `>**fears**`: gap type = fear/avoidance ·
   drift/lost-interest · deliberate-park.

### 2. Surface — "what has good wind", never "what you're behind on"

- Lead with the 2–3 goals that have the best wind (engagement × impact) **and** the almost-there ones
  ("this is a step from done").
- Mention any near deadline **gently and secondarily** — never as pressure, and always with an
  ease-start already in hand.

### 3. The interview — reorder energy by motivation

Walk Lucas through the surfaced goals, one light touch each. Motivation is the primary axis:

- **almost-there** → "this is a step from done — want to finish it? here's the easy start: <ease-start>".
- **timing** → "is this the right moment, or is there better timing?" If later, push the `target`
  (chosen, not slipped) — a first-class move, not a failure.
- **ditch / defer** → "does this still make sense? if not, we can drop it — that's a good strategic
  move, not a loss." True ditch → **delete the goal file** and leave one line under
  `## Ditched` in `brain/GOALS.md` with the reason (git holds the file; the reason is the only
  thing git cannot recover). Defer → push `target`.
- **reorder** → reorder selected achievements / focus by Lucas's *live* motivation. Deadlines never
  override motivation here.

### 4. Close a win  (folded from the old /brain-finished)

When Lucas marks something done, in that goal file:

a. Flip `> [ ] [<id>]` → `> [x] [<id>]` in `## backlog`.
b. Move the `> [x] [<id>] ...` line to the top of the `<!-- done:start -->…<!-- done:end -->` block.
c. Advance `## selected next achievement` to the next `> [ ]` backlog item.
d. Write a fresh `**ease-start**` for it — meet the ease-start quality bar in `brain/SPECS.md`
   (real link/handle, numbered steps, content pre-staged, 5–10 min ceiling; fetch or ask if missing).
e. Set `>**dynamics**` motion → `advancing`.
f. Acknowledge the win — one short, genuine sentence before moving on.

### Write back

Each touched goal file:
- `>**dynamics**` — mode · motion · source
- `>**analysis**` — if stalled, refresh with science-backed strategies
- reordered backlog / updated selected achievement + ease-start / pushed `target` / done-marks — as agreed.

`brain/GOALS.md`:
- `>**pareto**` — 2–3 top goals with one-line rationale each
- `>**gap**` — gaps found, each with diagnosed type

Ditched goals → goal file deleted, one line under `## Ditched` in `brain/GOALS.md`. Then write today's date to
`brain/.log/compass-last.txt` (format: YYYY-MM-DD).

### Tone

"Here's what has good wind" — not "here's what you're behind on."
Ordering by motivation wins over deadlines. Ditching is a strategic move, not a failure.
Timing is negotiated, not imposed. Hand him the easy start — never tell him to "go look."
End with one question that opens the conversation.
