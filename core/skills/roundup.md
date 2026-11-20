---
name: roundup
description: >
  Full session-close ritual: drain the lists, route session knowledge to durable files, then verify and hand off. Use at session end.
---

# Roundup skill

End the session cleanly: three judgment phases, one script, one hand-off.

Everything with a single right answer — the fast suite, the merge into develop, the push, giving the repos back — is [`core/tools/wos/roundup`](../tools/wos/roundup), run once in Phase 4. It carries this skill's name because it is the same ritual, one layer down. **Do not do its work by hand:**
this skill fires at the session's maximum context, so every command reasoned about here is paid at the most expensive turns the session will ever have.

Write directly to files. Ask only on conflict or destructive ambiguity.

Arguments: $ARGUMENTS  (focus for next session — passed through to `/handoff`)

## The output rule — a phase with nothing to say says nothing

Every phase below can find nothing, and finding nothing is the **good** case. When it does, it contributes **no line** to the final report: no header, no "nothing to do", no invented next step to fill the shape. A clean session closes in three lines. That matters more here than anywhere else — this is the most expensive turn of the session *and* the last thing read before a `/clear`, so padding is what the next session inherits and acts on.

---

## Phase 1 — Clear completed work out of the lists

```bash
find . -maxdepth 3 \( -name "ROADMAP.md" -o -name "ISSUES.md" \) 2>/dev/null | sort
git log --oneline -10
```

Read what the session touched. Then:

**Done work is deleted. Git is the history.** There is no `HISTORY.md`, no `ARCHIVE.md`, no done-log — see [`core/SCHEMA.md`](../SCHEMA.md) § No archive types. A completed item's record is its commit; re-writing it into an archive file only grows a doc nobody opens. So: delete completed `ROADMAP.md` items (`- [x]`, "done", "shipped", "merged", "✅") and resolved `ISSUES.md` items (`- [x]`, "fixed", "resolved", "closed"). For a bug, the regression spec (`test/**/b<N>-*`) is the durable proof it is dead — that is what [`core/hooks/checks/issues-gate.py`](../hooks/checks/issues-gate.py) enforces, and it outlives any writing.

**The one thing that must not be deleted.** An approach the session **tried and rejected** was never committed, so git cannot hold it. Write **one line** under `## Rejected` in the relevant `ROADMAP.md` (for a ditched goal: under `## Ditched` in `brain/GOALS.md`) with the reason. One line — not a post-mortem.

---

## Phase 2 — Route session knowledge to durable files

Route each piece of knowledge the session produced. Conflict with existing content → ask first.

| Knowledge type | Target |
|---|---|
| Non-obvious design decision + rationale | `SPECS.md` → Architecture Decisions |
| Discovered convention / coding rule | `SPECS.md` → Conventions |
| Bug found, not fixed | `ISSUES.md` of the repo that owns it, tagged `[src: agent YYYY-MM-DD]` |
| New technical work item | `ROADMAP.md` of the repo that owns it, same tag |
| Reference / link / paper / tool worth keeping | domain `refs/REFS.md` (route-by-domain — see `/inbox`) |
| Personal / admin / life / teaching task — or project task with hard deadline | the owning goal's backlog in `brain/goals/*.md`; no goal owns it → the hand-off, for Lucas to place |
| Insight about a specific life or career goal | `brain/goals/[goal].md` (achievement, backlog item, or obstacle) |
| Skill workflow improvement | the skill file directly |
| Workspace-wide rule across all projects | `AGENTS.md` |
| Critical quick-reference fact or constant needed at session start | `CONTEXT.md` — see exclusions |
| Doesn't fit cleanly | `ISSUES.md` of the repo the session worked in, tagged |

**Never `brain/INBOX.md`.** INBOX is Lucas's own capture ([`brain/CONTEXT.md`](../../brain/CONTEXT.md)); an agent's finding written there gets promoted as if Lucas had said it. *ROADMAP*: a technical milestone with agent-ready context. *Goal backlog*: personal / admin / life / teaching — append to the goal it serves, or write the goal's seed.

**CONTEXT.md exclusions.** Routing-block changes → ignore, hooks auto-sync them. Behavioral cues ("be careful with X", "prefer Y") → `SPECS.md` Conventions or `AGENTS.md`. Decisions + rationale → `SPECS.md` Architecture Decisions. Write to `CONTEXT.md` only for a critical constant, invariant, or quick-start command needed at the *next* session's start, that fits nowhere above.

**Memory**: only if the knowledge is homeless across every file above. Filesystem is source of truth.

### The boundary question — what belongs in the WOS at all

One pass over what this session actually touched, asking the question the routing table above never asks: **should this be in the workspace, and in this shape?** (Lucas, 2026-09-18.) Three answers worth writing down, and only a real one:

- **Does not belong here** — it is a project's, a nested repo's, or nobody's. Say where it goes.
- **Belongs, wrong shape** — right tree, wrong file, wrong type, or a word doing two jobs. An asymmetry found is written down even when it is not fixed (`AGENTS.md`).
- **Could be a satellite repo** — a subtree big enough and separate enough to own its own git, the way every `code/*` and `academy/papers/*` already does. Costed by what it would BREAK: how many hooks name its path, how many goal files point into it, and what the pointer check stops being able to follow.

Nothing to say → say nothing, by the output rule at the top. This phase is a question, not a deliverable, and a session that touched one file owes one sentence or none.

---

## Phase 3 — Count the INBOX, do not drain it

**Counting is this phase; draining is the next session's first act.** A drain opens links with the video and web tools — the most expensive work the workspace does — and this is the most expensive turn it has. Ruled 2026-08-25, after a close that drained zero entries *because* of the price and left 19 sitting.

**Run nothing.** The count is already in this session's context: `INBOX-REMINDER` printed it at SessionStart, and it prints *only* above the threshold, so no line means nothing to do. Re-counting here is a command bought at the worst price to learn what the session was told for free.

So: if the reminder fired and `$ARGUMENTS` names no other focus, hand `/inbox` to Phase 5 as the next session's `Next action`, with the count. Otherwise this phase says nothing.

---

## Phase 4 — Close

Commit the session's work first, in every repo this session holds: the script stops on a dirty tree (exit 2), because a commit message is judgment. Then, once:

```bash
core/run tools/wos/roundup
```

[`core/tools/wos/roundup`](../tools/wos/roundup) covers exactly the repos the branch lock says this session holds ([`core/hooks/git/SPECS.md`](../hooks/git/SPECS.md)). Green fast suite → the feature merges into `develop`, which is pushed. Red → only the feature is pushed. Only after a confirmed push does it switch back to `develop` and let the repo go; a failed push keeps the repo held. It commits nothing and never moves `main`. **Every line it printed is the hand-off's State block** — copy them, do not re-derive them.

A merge it refused (develop diverged, a conflict) is a decision, not a failure: report the line, never work around it. Work that is incoherent on its own (a half-applied refactor) is yours to pass in: `core/run tools/wos/roundup --draft`. *"The milestone is not finished"* is **not** a reason: green, coherent, partial work belongs on `develop`, where the other machine can see it.

---

## Phase 5 — Hand off

Run `/handoff $ARGUMENTS`. It decides whether a hand-off is warranted at all — with the work finished and no next action it writes nothing, which is the output rule applied to itself. Do not pre-empt that judgment here, and do not write a block by hand if it declines. Then report, in this order, **omitting every line with nothing behind it**:

- what was deleted, from which list — one line, only if something was
- what was written, one line per file — only files actually written this phase
- every line Phase 4 printed, verbatim

Nothing else. No session summary, no next steps: `/handoff` just emitted those, and repeating them is the padding this skill exists to not produce. Close with one instruction: the resume prompt [`handoff.md`](handoff.md) § Output words. Or, if `/handoff` skipped, nothing.
