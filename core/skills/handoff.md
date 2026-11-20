---
name: handoff
description: Emit a copy-pasteable resume prompt for the next session. For the full session-close ritual use /roundup, which calls this.
---

# Handoff skill

Produce the resume prompt for the next session. Capture only what is **not already in project files** — reference the file instead of repeating it.

Arguments: $ARGUMENTS  (focus for next session)

## Decide first — is there anything to hand off?

**If the work is finished and there is no next action, do not emit a resume prompt.** Writing one *manufactures* a next action at the last turn before a `/clear` — the output rule ([`roundup.md`](roundup.md) § The output rule) applied to the hand-off itself. That is not a rare edge case; it is how a session that closed properly ends.

Skipping is one line: *nothing open — no hand-off written.* Nothing else, and stop here. The handoff this session opened is already gone — taking it deleted it.

**A taken handoff's threads are this session's.** Each one is finished, moved to its `ROADMAP.md` or `ISSUES.md`, or carried into this session's own handoff — never dropped. **A handoff file's existence means exactly one thing: its threads are open.**

Hand off when work is mid-flight, a decision is pending, or a trial remains unresolved. If unsure, write it: a dropped thread costs the next session its reconstruction.

## Gather state

**If [`core/tools/wos/roundup`](../tools/wos/roundup) ran this session, every line it printed *is*
the State block — copy them verbatim and gather nothing.** They are the same facts, already paid for. Re-deriving them costs a second round of git at the session's most expensive turn, and lets the two disagree. Which lines it prints is the script's business, never this file's: naming them here is a copy that goes stale without failing anything.

Only when it did not run (`/handoff` invoked mid-session, standalone):

```bash
git branch --show-current 2>/dev/null
git rev-parse --short HEAD 2>/dev/null
git status --short 2>/dev/null | wc -l
git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads 2>/dev/null
git log --oneline main..develop 2>/dev/null | wc -l
```

Cite a verification result only if one is fresh from this session; otherwise say "not run".

**Report sync divergence, never fix it.** `/handoff` can be invoked mid-session, so merging here risks promoting unverified work. Just state what is unpushed or unpromoted (`[ahead N]` on any branch, or `develop` ahead of `main`) so a session resumed on another machine knows what it is missing.
Promotion is `/roundup` Phase 4 — point there if anything is behind.

## Output

**One handoff per repository** (Lucas, 2026-11-10): `outputs/handoff-<key>.md`, the key being the repository's path under the workspace (`workspace`, `code-apptime`). `core/run tools/wos/handoff --json` lists this session's repositories in `repos`, ranked by confirmed Edit/patch lines; each block holds only that repository's threads. Prepare one block per repository with open threads in a temporary file and publish it with `--write <file> --repo <path>`. A pending file is never overwritten: sections from sessions that never met accumulate, and re-writing replaces only this session's own. The measurement's limits: shell/script writes, full-file replacements and implicit deletions are not counted, and the shared dirty tree never is. Native session variables identify the session; when unavailable, pass `--session` and `--agent`. Local code: no model call.

**A handoff is opened by taking it**: `core/run tools/wos/handoff --take <key>` prints every pending section and deletes the file, and `handoff-gate` refuses any other read.

**Never spawn a successor session.** Decided 2026-08-13 ([`core/SPECS.md`](../SPECS.md) § AD-09):
`claude --bg` can start a fresh-context agent but cannot move the terminal Lucas types into, so a spawned successor would work the same branch *unattended, in parallel with the live session*. Prepare the artifact; let Lucas move his own attention.

**Every section earns its place or is omitted.** Delete empty headers; no placeholders. The caps below keep the next session from rereading project lists.

**Name what you decided alone.** git holds what changed and never the option that was rejected, so a choice a session made for Lucas without asking is invisible the moment it lands — and the longer it holds, the more expensive it is to reopen. List them; the point is that he can object cheaply, while the alternative is still live. The durable record is [`roundup.md`](roundup.md) Phase 2's job (a design decision goes to `SPECS.md` → Architecture Decisions, Context / Decision / Consequences);
this section only makes sure he *sees* the ones nobody asked him about.

**Say it once.** If a fact is already in a list — a `ROADMAP.md` item, a `ISSUES.md` entry, a `SPECS.md` decision — point at the file; do not restate it. The next session reads those anyway, and a hand-off that duplicates them is a second copy to keep in sync.

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

> Resume prompt ready — written to `<returned path>`. Open a new session and start it with: `Roda <returned resume>, depois entra em plan mode e discute comigo em detalhes (em pt-br) qual vai ser o plano pra essa sessão.` — one line per repository handed off. **Plan, never "continue"** (Lucas, 2026-08-16): planning reads the whole list and surfaces blocked decisions before work resumes. **Take, then plan** (Lucas, 2026-11-10): the take deletes a file, which plan mode forbids, so the prompt is pasted outside it; an exemption written in the prompt and a non-deleting `--peek` were rejected — text cannot outrank the harness, and a peek lets two sessions read the same threads.

**A command handed to Lucas stands alone** (Lucas, 2026-11-17): absolute paths, never a `cd` relative to this session's directory — a chained relative `cd` failed on 2026-11-11.
