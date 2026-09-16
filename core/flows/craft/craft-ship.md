---
description: Loops 5-6.5 of the craft flow — user test, ship the branch, and extract any skill the run earned.
args: <carry file>
---
## Loop 5 — User Test

**Level:** medium. **Input:** `4b-code.md`. **Output:** `5-user.md`.

Author and run one automated **complex user scenario** end-to-end (e2e-cmd from Carry, or script the real entrypoint:
CLI invocation, HTTP flow, UI driver — whatever the project's `run`/verify skill uses). It must chain multiple criteria
in one realistic path, not re-run unit tests. Evaluate the observed output against `expected-result` from Loop 0.

```markdown
## Carry
<copied>

## User Test
scenario: <one paragraph, user's voice>
script: <path> run: <command>
observed: <key output lines>
matches-expected-result: yes|no <diff if no>
```

**Flags:** e2e fails while units are green → `RETURN loop=3 reason=integration-gap`; output is correct per tests but
wrong per intent → `RETURN loop=0 reason=intent-mismatch` (user decides).

## Loop 6 — Ship

**Level:** low. **Input:** `5-user.md` (or `0-clarify.md` on the padaria path). **Output:** `6-ship.md`.

Verify the working tree contains only in-scope changes (diff vs plan `files` + `.craft/`); update the project
`ROADMAP.md` line to done with a one-line outcome; delete `.craft/<name>/` unless `keep-trail: yes`; commit (normal
writing, project's commit conventions) and push the feature branch. Do not merge — that is the user's call.

**Spec promotion (SDD).** Before deleting `.craft/<name>/`, if the chain touched a `code/` module, distill its durable
contract into the module's `SPEC.md` (create from `code/_templates/module.SPEC.md` if absent): fold the Carry `criteria`
C1..Cn and Loop 3's `boundaries` into the spec's `## Invariants`/`## Examples`, point `## Examples` at the new tests
(`4a-tests.md`), and set the `CONTEXT.md` `> spec: SPEC.md` line + `status: locked`. This converts the ephemeral
per-feature journal into a durable per-module contract — a new module born this way satisfies the `1d` new-module gate
on the same commit. See `code/ROADMAP-spec-drive.md`.

```markdown
## Carry
<copied>

## Ship
diff-scope: clean | extras: <list>
roadmap: updated <path>
commit: <hash> pushed: yes|no
leftovers: <follow-ups routed to ROADMAP/INBOX, or none>
```

**Flags:** out-of-scope files or secrets in diff → `RETURN loop=4b reason=dirty-tree`; push rejected → report BLOCKED,
never force-push.

**Status (mandatory):** Loop 6 mutates the chain's status field — `<project>/.craft/<name>/STATUS.md`. The file opens
with `# <name> — chain status` (every `.md` needs a first line the routing generator can read) and its status line is
`status: active | blocked-flag-pending-user | abandoned | shipped \| commit: <hash or none> \| last-loop: <N> \|
last-updated: <date>`. Loop 0 creates the file with `status: active, last-loop: 0`. Anything beyond that line is
**present-tense state** — what is still true and what it waits on. Never a completion report: `STATUS.md` is a
live-state file, and *done work is deleted* applies here as everywhere. Any loop that raises a RETURN the orchestrator
cannot auto-route (per `Return Flags`, e.g. two consecutive returns or any `RETURN loop=0`) sets `status:
blocked-flag-pending-user, last-loop: <N>` and stops. The chain's status is therefore always inspectable: a
workspace-wide `/craft --status` summarizer is `cat code/*/.craft/*/STATUS.md` — surfaces in-flight and abandoned chains
(e.g. `isoroll-module/.craft/floor-fog-spike` and `.craft/painter-mvp-1`, both stopped pre-ship without status, motivate
this mechanism).

**STATUS.md ALSO carries a provider-routing header line** that Loop 0 writes when the chain starts and Loop 6 mirrors on
ship:

```
provider: <nvidia|openrouter|opencode|anthropic|copilot> | level-map: <row-id> | chain-deleg: <none|deleg=<from>→<to>>
```

The `/craft --status` summarizer therefore also surfaces provider + delegation per in-flight chain (`cat
code/*/.craft/*/STATUS.md` shows which chains are running on free nvidia vs spending openrouter credits). Empty
`level-map:` on a non-blocked chain ⇒ the orchestrator never resolved routing — file a bug.

### Second-opinion verifier (Voyager-style, closes the self-review gap)

Loops 1 and 3 currently do *same-session* adversarial review — the same high-level session that wrote the
plan/architecture grades it. Voyager (Wang 2023) separates "self-verification" as a distinct prompt; Anthropic's
best-practices doc is explicit that *a reviewer running in a fresh subagent context evaluates the result on its own
terms, not the reasoning that produced it*. From 2026-07, /craft adds:

- **Loop 3 — architecture second-opinion.** Before Loop 3's own `verdict: PASS`, the orchestrator spawns a **fresh
  low-level session** (haiku-level — verifier, not author) reading only `2-ground.md` + the proposed `3-arch.md` +
  Carry.
  It returns ONE line: `OK crit-covered:` (criteria homes confirmed) | `GAP <criterion-id> <one-line defect>`. Any
  non-OK line escalates Loop 3 to high; if high also fails to close the gap, escalate per the existing RETURN protocol
  (→ Loop 1 or max-level orchestrator ruling).
- **Loop 6 — ship second-opinion.** Same pattern: fresh low-level session reads `5-user.md` + the project context +
  Carry, returns `OK diff matches plan: clean` | `EXTRA <file>` | `MISSING-CRIT <criterion-id>`. Out-of-scope files or
  unmet criteria fold into the existing `extras:` / `RETURN loop=4b reason=dirty-tree` paths. The verifier never edits —
  pure audit.

The verifier is **fresh** (own context, not the executor's), **cheap** (haiku), and **silent unless wrong**. This
matches Voyager's separate-self-verification primitive directly. Same-executor self-review remains the first line of
defense in Loops 1 and 3; the verifier is the gate that closes the loop on biases the executor cannot see in its own
work.

---

## Loop 6.5 — Skill Extraction (Voyager-style skill library)

After Loop 6 ship (and before deleting `.craft/<name>/` unless `keep-trail: yes`), one low-level executor reads the
chain's `3-arch.md` (Adversarial pins / medium-executor traps section) + `4b-code.md` attempt log + `5-user.md`
flag-and-fix, extracts any *reusable design pattern*, and appends it (frontmatter: domain tags + provenance link to the
kept `.craft/` or commit hash) to `core/flows/.craft-skills/<domain>.md`. New `domain` files are created as needed;
sub-domains reuse an existing file. Loop 1 plan-review is then instructed to grep `core/flows/.craft-skills/` for
relevant prior patterns **before** authoring a new plan — Voyager's "skill library" primitive, made durable across runs.

The skill registry is small by construction: only patterns that would otherwise die with the chain. If nothing reusable
exists (the common case for `padaria` and small `standard` chains), Loop 6.5 writes nothing and the registry doesn't
grow — Voyager's library accrues skills; /craft accrues *patterns* and only when they're worth saving.

Extract is one low-level session, ~30 lines, optional `keep-trail: yes` chains only.
