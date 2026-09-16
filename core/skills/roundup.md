---
name: roundup
description: Full session-close ritual: drain the lists, route session knowledge to durable files, then verify and hand off. Use at session end.
---

# Roundup skill

End the session cleanly: three judgment phases, one script, one hand-off.

Everything with a single right answer — the verification gate, the entropy dashboard, branch
promotion — is [`core/tools/wos/roundup`](../tools/wos/roundup), run once in Phase 4. It carries
this skill's name because it is the same ritual, one layer down. **Do not do its work by hand:**
this skill fires at the session's maximum context, so every command reasoned about here is paid at
the most expensive turns the session will ever have.

Write directly to files. Ask only on conflict or destructive ambiguity.

Arguments: $ARGUMENTS  (focus for next session — passed through to `/handoff`)

## The output rule — a phase with nothing to say says nothing

Every phase below can find nothing, and finding nothing is the **good** case. When it does, it
contributes **no line** to the final report: no header, no "nothing to do", no invented next step
to fill the shape. A clean session closes in three lines. That matters more here than anywhere
else — this is the most expensive turn of the session *and* the last thing read before a `/clear`,
so padding is what the next session inherits and acts on.

---

## Phase 1 — Clear completed work out of the lists

```bash
find . -maxdepth 3 \( -name "ROADMAP.md" -o -name "ISSUES.md" \) 2>/dev/null | sort
git log --oneline -10
```

Read what the session touched. Then:

**Done work is deleted. Git is the history.** There is no `HISTORY.md`, no `ARCHIVE.md`, no done-log
— see [`core/SCHEMA.md`](../SCHEMA.md) § No archive types. A
completed item's record is its commit; re-writing it into an archive file only grows a doc nobody
opens. So: delete completed `ROADMAP.md` items (`- [x]`, "done", "shipped", "merged", "✅") and
resolved `ISSUES.md` items (`- [x]`, "fixed", "resolved", "closed"). For a bug, the regression spec
(`test/**/b<N>-*`) is the durable proof it is dead — that is what
[`core/hooks/checks/issues-gate.py`](../hooks/checks/issues-gate.py) enforces, and it outlives any writing.

**The one thing that must not be deleted.** An approach the session **tried and rejected** was never
committed, so git cannot hold it. Write **one line** under `## Rejected` in the relevant
`ROADMAP.md` (for a ditched goal: under `## Ditched` in `brain/GOALS.md`) with the reason. One line
— not a post-mortem.

---

## Phase 2 — Route session knowledge to durable files

Route each piece of knowledge the session produced. Conflict with existing content → ask first.

| Knowledge type | Target |
|---|---|
| Non-obvious design decision + rationale | `SPECS.md` → Architecture Decisions |
| Discovered convention / coding rule | `SPECS.md` → Conventions |
| Bug found, not fixed | `ISSUES.md` |
| New technical work item (project has `ROADMAP.md`) | `ROADMAP.md` |
| Reference / link / paper / tool worth keeping | domain `refs/REFS.md` (route-by-domain — see `/inbox`) |
| Personal / admin / life / teaching task — or project task with hard deadline | the owning goal's backlog in `brain/goals/*.md` (or `brain/INBOX.md` if no goal owns it yet) |
| Insight about a specific life or career goal | `brain/goals/[goal].md` (achievement, backlog item, or obstacle) |
| Skill workflow improvement | the skill file directly |
| Workspace-wide rule across all projects | `AGENTS.md` |
| Critical quick-reference fact or constant needed at session start | `CONTEXT.md` — see exclusions |
| Doesn't fit cleanly | `brain/INBOX.md` — triaged in Phase 3 |

**Goal backlog vs ROADMAP.** *ROADMAP*: project has `ROADMAP.md` AND the item is a technical
milestone with agent-ready context. *Goal backlog*: personal / admin / life / teaching — append to
the backlog of the goal it serves, or write the goal's seed if none exists yet. Neither fits (no
owning goal, no technical milestone) → `INBOX.md`. Unclear → INBOX.

**CONTEXT.md exclusions.** Routing-block changes → ignore, hooks auto-sync them. Behavioral cues
("be careful with X", "prefer Y") → `SPECS.md` Conventions or `AGENTS.md`. Decisions + rationale →
`SPECS.md` Architecture Decisions. Write to `CONTEXT.md` only for a critical constant, invariant, or
quick-start command needed at the *next* session's start, that fits nowhere above.

**Memory**: only if the knowledge is homeless across every file above. Filesystem is source of truth.

---

## Phase 3 — Count the INBOX, do not drain it

**Counting is this phase; draining is the next session's first act.** A drain opens links with the
video and web tools — the most expensive work the workspace does — and this is the most expensive
turn it has. Ruled 2026-08-25, after a close that drained zero entries *because* of the price and
left 19 sitting.

**Run nothing.** The count is already in this session's context: `INBOX-NUDGE` printed it at
SessionStart, and it prints *only* above the threshold, so no line means nothing to do. Re-counting
here is a command bought at the worst price to learn what the session was told for free.

So: if the nudge fired and `$ARGUMENTS` names no other focus, hand `/inbox` to Phase 5 as the next
session's `Next action`, with the count. Otherwise this phase says nothing.

---

## Phase 4 — Close

Commit the session's work first — the script stops on a dirty tree, because a commit message is
judgment and everything below assumes a clean one. Then, once:

```bash
core/run tools/wos/roundup
```

It runs the verification contract, writes both generated blocks of the root `ISSUES.md` — the
verification result and the regenerated entropy findings (workspace repo — and commits them
itself, under `chore(issues)`, so no session ever writes that message by hand), merges `feature/*` → `develop` → `main`
and pushes, then prints what the close measured. **Every line it printed is the hand-off's State
block** — copy them, do not re-derive them, and **do not name them here**: a list of labels in a
skill is a second copy of the script's output that rots silently, which is exactly how this file
promised three lines while the script printed six.

It refuses to promote, and says why, when the verification gate is **red** or when a target branch
is **behind origin** (a parallel session is mid-flight). Those are decisions, not failures: report
the reason, never work around it. One case the script cannot see — the branch holds work that is
incoherent on its own (a half-applied refactor, a test deleted before its replacement lands) — is
yours to pass in: `core/tools/wos/roundup --no-promote "<reason>"`. *"The milestone is not finished"*
is **not** a reason: green, coherent, partial work belongs on `develop`, where the other machine
can see it.

---

## Phase 5 — Hand off

Run `/handoff $ARGUMENTS`. It decides whether a hand-off is warranted at all — with the work
finished and no next action it deletes `outputs/handoff.md` and writes nothing, which is the output
rule applied to itself. Do not pre-empt that judgment here, and do not write a block by hand if it
declines. Then report, in this order, **omitting every line with nothing behind it**:

- what was deleted, from which list — one line, only if something was
- what was written, one line per file — only files actually written this phase
- every line Phase 4 printed, verbatim

Nothing else. No session summary, no next steps: `/handoff` just emitted those, and repeating them
is the padding this skill exists to not produce. Close with one instruction — start the next
session with `Read outputs/handoff.md and plan what you'll do in this session.` — **plan, never
"continue"**; the rationale is in [`handoff.md`](handoff.md). Or, if `/handoff` skipped, nothing.
