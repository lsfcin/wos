---
name: handoff
description: Emit a copy-pasteable resume prompt for the next session. For the full session-close ritual use /roundup, which calls this.
---

# Handoff skill

Produce the resume prompt for the next session. Capture only what is **not already in project files** — reference the
file instead of repeating it.

Arguments: $ARGUMENTS  (focus for next session)

> **Narrow by design.** This emits only the resume prompt. To also archive completed work, route session knowledge to
> durable files, drain the INBOX, and run the verification gate first, use `/roundup` — it runs those phases, then calls
> `/handoff`.

## Decide first — is there anything to hand off?

**If the work is finished and there is no next action, do not emit a resume prompt.** Writing one
*manufactures* a next action at the last turn before a `/clear` — the output rule
([`roundup.md`](roundup.md) § The output rule) applied to the hand-off itself. That is not a rare
edge case; it is how a session that closed properly ends.

Skipping is one command and one line:

```bash
rm -f outputs/handoff.md
```

Then say: *nothing open — no hand-off written.* Nothing else, and stop here.

Deleting is the point. **The file's existence means exactly one thing: a thread is open.** Leaving
the previous session's block in place would let the next window resume a thread that closed
sessions ago, and a stub saying "nothing open" costs a read to learn there is nothing to read.

Hand off when any of these is true: work is mid-flight, a decision is pending, or something was
tried and left unresolved. Ambiguity resolves toward writing it — a hand-off nobody needed costs
one read; a thread dropped silently costs the session that re-derives it.

## Gather state

**If [`core/tools/wos/roundup`](../tools/wos/roundup) ran this session, every line it printed *is*
the State block — copy them verbatim and gather nothing.** They are the same facts, already
paid for. Re-deriving them costs a second round of git at the session's most expensive turn, and
lets the two disagree. Which lines it prints is the script's business, never this file's: naming
them here is a copy that goes stale without failing anything.

Only when it did not run (`/handoff` invoked mid-session, standalone):

```bash
git branch --show-current 2>/dev/null
git rev-parse --short HEAD 2>/dev/null
git status --short 2>/dev/null | wc -l
git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads 2>/dev/null
git log --oneline main..develop 2>/dev/null | wc -l
```

Cite a verification result only if one is fresh from this session; otherwise say "not run".

**Report sync divergence, never fix it.** `/handoff` can be invoked mid-session, so merging here risks
promoting unverified work. Just state what is unpushed or unpromoted (`[ahead N]` on any branch, or
`develop` ahead of `main`) so a session resumed on another machine knows what it is missing.
Promotion is `/roundup` Phase 4 — point there if anything is behind.

## Output

**Write the block to `outputs/handoff.md`, then print it.** The file is the deliverable; the
print is a convenience. A path is what survives a `/clear` — the next session opens by reading
it, with no block to carry across by hand, which is why
[`core/hooks/session/context-meter.py`](../hooks/session/context-meter.py) names this same path
at `CTX_LOUD`. Overwrite it: the newest hand-off is the only one worth resuming, and `outputs/`
is gitignored, so nothing durable is lost.

**Never spawn a successor session.** Decided 2026-08-13 ([`core/SPECS.md`](../SPECS.md) § AD-09):
`claude --bg`
can start a fresh-context agent but cannot move the terminal Lucas types into, so a spawned
successor would work the same branch *unattended, in parallel with the live session*. Prepare
the artifact; let Lucas move his own attention.

**Every section earns its place or is omitted** — the same rule as the phases in
[`roundup.md`](roundup.md). A section with nothing behind it is deleted, header and all; there is
no "none.", no placeholder, no shape to fill. Last session's ran to 48 lines and 3 of its 5
open threads were already written in `ROADMAP.md` — that is what these caps exist to stop.

**Name what you decided alone.** git holds what changed and never the option that was rejected, so a
choice a session made for Lucas without asking is invisible the moment it lands — and the longer it
holds, the more expensive it is to reopen. List them; the point is that he can object cheaply, while
the alternative is still live. The durable record is [`roundup.md`](roundup.md) Phase 2's job (a
design decision goes to `SPECS.md` → Architecture Decisions, Context / Decision / Consequences);
this section only makes sure he *sees* the ones nobody asked him about.

**Say it once.** If a fact is already in a list — a `ROADMAP.md` item, a `ISSUES.md` entry, a
`SPECS.md` decision — point at the file; do not restate it. The next session reads those anyway,
and a hand-off that duplicates them is a second copy to keep in sync.

Print the block between the `---` markers:

---

```
## Resume — [PROJECT] — [DATE]

### Next action
[If $ARGUMENTS: use as directive. Else: the single next step, from ROADMAP + current state.]

### Worked on
[≤3 bullets, and only what no list already holds. Shipped work is in git and the ROADMAP —
 what belongs here is what a reader of those files would still not know.]

### Open threads
[Discussed but unresolved — dead ends and what was tried. Omit the whole section if there are none.]

### Decided without asking
[One line each: the choice, and the option not taken. Only choices Lucas could reasonably have made
 differently — not every judgement call. Point at the SPECS.md AD if one was written. Omit if none.]

### State
[Every line core/tools/wos/roundup printed this session, verbatim, in its order.
 If it did not run this session, one line: "roundup not run".]
[≤2 files worth opening first, one line each, only if not obvious from ROADMAP.]
```

---

After printing:

> Resume prompt ready — written to `outputs/handoff.md`. Open a new session (`/clear` or a fresh
> window) and start it with: `Read outputs/handoff.md and plan what you'll do in this session.`
> **Plan, never "continue"** — ruled 2026-08-16 (Lucas). "Continue" makes a session start at the
> next action this file names and never look up; planning forces it to read the whole list first,
> which is what surfaces blocked decisions and cross-item ordering. The session that ruled it opened
> that way and closed six decision items that had been open for weeks because nobody had asked which
> ones were blocking. Pasting the block itself
> works too, but the file is what survives if this session dies first.
