# Core SPECS
> Architecture decisions and conventions for the Core agent library.

<!-- warn-exempt: one decision per section, each carrying the reason it was made. Cutting to the warn
     means deleting decisions or the reasons behind them, which is what raised the cap on 2026-09-06.
     The block cap still applies: past it this file is cut, not excused. -->


## Conventions

- **An untracked file opts out of every check this workspace has** (2026-08-15) — and keeps giving
  instructions while it rots. That is what the `.gitignore` allowlist discipline buys.
- **Sequence the prohibition BEFORE the rename** (2026-08-16): the ban deletes most of the citations
  outright, so doing it first shrinks the sweep instead of moving pointers that are about to vanish.
  Corollary: **a rule only a careful reader applies is one the corpus outruns.**
- **A finding older than a week is a hypothesis — re-run it before spending a decision on it**
  (2026-08-14). **A list keeps the command that produced a finding, never the list.**
- **The entropy dashboard verifies a rename; `git grep` only finds where to start** (2026-08-17) —
  `git grep` reads *this* repo and every project under `code/` is a separate one. Corollary: **an
  incomplete rename is indistinguishable from entropy in the leaves, and is fixable only in the
  generator.**
- **One number answering two questions is the same bug as two numbers answering one** (2026-09-06),
  and only the second shape is obvious. Before moving a constant, read every caller: a shared one is
  not a single source of truth, it is two rules that happen to agree so far.
- **A ruling that lives only in writing gets re-reported forever** — either the data file carries the
  decision or expect to make it again (AD-16 band 1 → 2, cheapest form).
- **A check proving something *happened* beats one proving nothing errored** (2026-08-14). Bugs that
  exit 0, block with no message, or write a file nobody re-reads survive precisely by being mute, so
  ask *"what does this produce, and is it there?"* before reading code behind an exception.
- **Does the claim describe the TEXT or the EXECUTION?** (Lucas, 2026-08-24.) That question picks the
  instrument, not *"grep is forbidden"*. For a **textual** claim grep is fine, but **the negative
  assert is the check** — source-reading with only positive asserts is defective. For a **runtime**
  claim a substring is a proxy already caught passing wrongly, so **run it and watch**; if it cannot
  be run, read the source with comments stripped and say so. Hence also **a test case matches the
  exact basename, never a suffix**: `endswith` let a Read payload reach the Bash gate, and the case
  passed *by not blocking*.
- **A command whose exit status is a gate never goes inside a pipe** (2026-08-13): in `a | tail && b`
  the status is `tail`'s, so a failed merge still pushes. Use `set -e` and no pipes, or capture the
  status — filtering output is for inspection, never for decision.
- **A `.md` section is cited by name and by the file it is now in** — never by number (2026-08-15),
  because a number ages silently on the first insert. Both halves block at commit now, so the shape
  is `citation-gate.py`'s message rather than a sentence here.
- **A filename is one word, and the whole word** (Lucas, 2026-07-23): `architect` > `arch`. A name
  repeating its parent's namespace is noise, and generic names are reserved for the flow that earns
  them.
- New skill, flat: copy `core/skills/_template.md`. As a suite: `core/skills/<suite>/SKILL.md` plus
  `<name>.md` subfiles — always preferred to flat skills with a long prefix past two of them.
- New Google service: import `auth/gauth.py`, define `SCOPES` and the service name, follow
  `files/drive_core.py`, and register the recovery command in `gauth._REAUTH_CMD` in the same commit
  the CLI gains `--reauth` — a test checks every command in that table names a tool that exists. A
  provider **without** OAuth follows `notes/notion` (AD-12). Tokens live in `~/.config/workspace-*/`
  and are never committed.

### AD-01 — AGENTS.md as the universal entrypoint (2026-06-18)
`WORKSPACE.md` became `AGENTS.md`. Every runtime reads it natively or through `@AGENTS.md` in
`CLAUDE.md`, which removes the discovery fork between agents.

### AD-02 — A `description:` frontmatter is mandatory on skills (2026-06-18)
Every `core/skills/*.md` carries YAML frontmatter with `name:` and `description:`.
`context_synchronizer.py` reads `description:` (block scalars included) to populate the routing table,
so a missing one is a skill the table cannot describe.

### AD-03 — `auth/gauth.py` is the shared auth module (2026-06-18, moved 2026-08-14)
Google OAuth2 is centralized, one credentials file serving every Google-backed tool. It sits in
`auth/` because four families import it — a threshold, not an address (AD-12). Where the tokens land
is `core/tools/SPECS.md`, beside the code that writes them.

### AD-04 — Slides are edited in place, with no local format (2026-08-14, revokes Slidev)
**Revokes the 2026-06-18 decision for Slidev and the Google Slides → Slidev port**, which rested on the
source of truth not being agent-editable. It **is**: `batchUpdate` writes and repositions elements
remotely, and motion authors as a generated slide sequence that survives PDF export. The port only
produced a second copy to keep in sync, so Slidev was **deleted**, not demoted, and course material
stays where the students see it. Tool: `core/tools/slides/gslides`; API: `core/tools/slides/SPECS.md`.

### AD-06 — A skill's `refs/` folder sits beside the skill (2026-07-05)
References a skill accumulates live at the **same level as the skill file**, never inside a generated
mirror, because a mirror is regenerated and anything in it is lost. What the sync copies and what it
leaves alone is `core/skills/SPECS.md`.

### AD-07 — Sub-skills group into a suite folder (2026-07-05)
Skills sharing a namespace group into `core/skills/<suite>/` with `SKILL.md` as parent router, and
the parent **never implements operational logic** — it routes. Nothing is inherited: each sub-skill
carries complete frontmatter, which `validate.py` checks at every commit.

### AD-08 — Flows: ownership, composition and cycles (2026-07-23)
Extends AD-07 to the flow layer; the full contract is [`SCHEMA-layers.md`](SCHEMA-layers.md) §
*Composition and cycles* and only the decision is here. **Ownership decides placement**: a flow owned
by a dispatcher skill lives in `core/flows/<skill>/` with its filename equal to the command tail; an
unowned flow stays flat. The axis is **independence of invocation**, not composition. **"Flow" is the
canonical word** — a loop runs end to start with one exit, while our procedures branch, escape and
compose. **No flow is privileged**: the exemplar is `flows/_template.md`, and realism comes from
validation running over every flow, the template included (Lucas: *"a template should be a template.
just that."*).

### AD-09 — Session close: judgment in the skill, determinism in the script (2026-08-14)
`core/tools/wos/roundup` and `core/skills/roundup.md` are one ritual a level apart; a second word for
the same thing *is* the drift. Judgment stays in the skill, anything with a right answer stays in the
script, where it costs one call instead of reasoned writing in the session's most expensive turns. Which
lines the script prints is the script's business — the skills copy verbatim and name none.

- **A phase with nothing to say contributes no line**, and that applies to the hand-off itself: with
  the work finished, emitting a resume prompt fabricates one, so `/handoff` may refuse — and refusing
  **deletes** `outputs/handoff.md`. **The file existing means exactly one thing, that work is open.**
- **Dirt in the working tree has two possible owners and the script cannot tell them apart**, so it
  prints the paths and **asks** rather than asserting; `--leave-dirty` answers "not mine".
- **Promotion fast-forwards without checkout** (`git fetch . <src>:<dst>`), so it never touches the
  working tree — that, and no general claim about merges, is what makes it safe over someone's dirt.
- **The script refuses and says why** (red verify, target behind origin). A branch incoherent on its
  own enters through `--no-promote "<reason>"`; an unfinished milestone is not one, because green
  partial work belongs on `develop`.
- **No session spawns its successor** — an agent cannot move the terminal Lucas types in, so a
  successor would only work the same branch in parallel with the live one.
- **The close COUNTS the inbox; the next session drains it** (2026-08-25), because draining opens links
  with the video and web tools in the most expensive turn of all.

Guarded by [`core/tools/test/wos/`](../core/tools/test/wos/CONTEXT.md) — the tool against throwaway
workspaces, the skills against re-inlining work the script already owns.

### AD-10 — `core/tools/` classifies by capability; the provider is the leaf (2026-08-14)
**Directory = what the tool does, file = who provides it** (`mail/gmail`, `files/gdrive`), so changing
provider changes a leaf and never a family; a folder named for a manufacturer classifies on the wrong
axis. Two refinements stop it becoming a crowding own-goal: **create the family only when the tool
arrives**, and **write a `CONTEXT.md` only from the second file on**, since the routing generator
folds a sub-threshold directory into its parent unless it declares itself. Declared cost: this was
the **second** time every `core/tools/` path changed, and a third is not free.

### AD-11 — A read uses the strongest consent the account has already given (2026-08-14)
When an alias holds a write token the read path uses **it** and never asks for a second. Edit consent
already contains read consent, so another trip to the browser buys no security — it only creates two
tokens that die independently, which is what happened. Accounts granted read alone stay untouched.

### AD-12 — A provider without OAuth keeps its auth beside the tool (2026-08-14)
`notes/notion` authenticates by integration secret, so it does not import `auth/gauth.py` and the
module holding the secret lives **in the family**. Not an exception to AD-10: it is the locality rule
— *a module imported by exactly one family lives beside the tool* — meeting the auth rule. The two
consequences the CLI carries are rules about tools, so they live with the tools:
[`core/tools/SPECS.md`](tools/SPECS.md) § A provider without OAuth.

### AD-13 — A subagent skips the context gate; whoever invokes it delivers the context (2026-08-15)
A worker handed **an explicit path** never needed the `CONTEXT.md` chain, and forcing it is a large
share of a small start, re-read every turn. It replaces an exemption that already existed **by
accident** — a worker inheriting its parent's seen-set skipped the gate only in folders the parent
happened to have visited. The gate protecting contracts still fires for everyone; which field tells a
worker apart is `hook_input.is_subagent`'s own docstring.

The duty moved to the orchestrator and a hook discharges it: `read/agent-context.py` reads the paths
cited in the `Agent` prompt and hands the worker each folder's `>` line. **It induces, never blocks.**
The briefing is **per turn** rather than per worker, so several workers in one turn get the union of
cited paths: too broad, never wrong, and unsolvable otherwise — a worker's only id is born after the
prompt has passed. The join and its measurement: `core/experiments/subagent-context-chain.md`.

### AD-14 — A capability that cannot be switched off is a finding, not a feature (2026-08-16)
The ablation bench ran once and produced **no** signal, for one reason: nothing could be switched off
one at a time. While that stays true nothing here is measurable. So the registry is the **instrument**,
not a configuration system: `core/features.txt` declares each capability, `core/profile.txt` holds this
machine's answers, and `feature_law.py` is the third law module. It **names** which hook, skill or tool
is wired and never restates the rule that hook applies.

- **The `wired` column is honest or it is useless** — a row claiming a switch it does not have makes
  the ablation report "no effect" for something never switched off. What that column may hold is
  `core/features.txt`'s own head; a second copy here is the drift the law modules exist to catch.
- **`WOS_FEATURES_OFF` only subtracts.** There is no `WOS_FEATURES_ON`: an ablation run answers *what
  does this workspace cost without X*, and switching something on is a versioned decision in the
  profile, not a variable that dies with the shell.

**The ablation runs OUTSIDE the workspace** (Lucas, 2026-08-17) — a system does not run the experiment
on itself. The harness builds **variants** of a checkout, one capability missing from each, from the
public repository, which makes that repo a **hard precondition** and forces a synthetic task suite.
So there are two shutdown routes and `wired` knows only the first: an **in-process switch**, which is
`is_enabled()` in the file applying the rule; and a **clone variant**, built without the capability at
all, which only the ablation harness uses.

**Every capability is ablatable; not every one has an in-process switch** (Lucas: *"ALL features of the
WOS should be toggleable"*). `n/a` in `wired` means *"no in-process switch"*, never *"exempt"*. **What
is measurable is decided by the wiring point, never by the group** — classifying by group would have
discarded the registry's highest-signal row, a compaction feature running on every Bash call. **A
feature crossing layers is honest only when every layer consults the law** (2026-08-17): one half
switched off is not switched off.

**The honesty test asks ONE question — would switching this off change anything? — and answers it the
strongest way each row allows**, because searching for the literal short name inside the named file has
nowhere to land for a shared wiring point. That is what **makes one legal**: a group with an invokable
boundary is checked by behaviour rather than by grep, which passes on a guard in an unreachable branch. How
each row is answered is `test_features_wiring.py`, and that is the only place it should be written.

### AD-15 — What an always-loaded rule must prove to keep its place (2026-08-17)
Applies to text loaded in **every session**: `AGENTS.md`, `CONTEXT.md` heads, always-listed skills. The
question is **not length**. It is: *could this be a tool parameter, an enum, or a hook's error message
instead of writing?*

| column | when | what happens |
|---|---|---|
| **delete** | a **blocking, ratcheted** gate already applies it | the writing goes; the hook is the rule |
| **move** | a check *could* apply it, but none does today | **stays in the writing** until a gate blocks |
| **keep** | judgment no check can hold | stays, and its reason stays with it |

**The discriminator between `delete` and `move` is blocking, not the existence of a detector.**
`UPPERCASE.md = a type` left `AGENTS.md` because `type-gate.py` stops the commit; `DONE WORK IS
DELETED` stayed, because the finished-work detector never reached a blocking gate — deleting writing on
the strength of a report trades enforcement for nothing.

**Counterweights, because indiscriminate pruning is the one way this makes things worse:** context is
never cruft, **no deletion is justified by character count alone**, and this governs **always-loaded**
text only. It is not a cost item — the gain is enforcement, not tokens.

### AD-16 — Doubt is not charged when asserting; it is charged when storing (2026-08-17)
Asking for doubt in writing is the cheap half and has already been tried: this workspace is thick with
*re-run it, never quote it*, and that prevented neither the wrong number that steered a front for three
weeks nor four asserted-then-retracted explanations of one hook. The question is not how to request
caution but **where caution becomes a gate**. Three bands:

1. **Rule written, nothing checking — the cheap win.** The two rules this workspace cited as proof it
   knew how to doubt went unverified for months: INDUCED wearing ENFORCED's costume.
2. **Enforced by construction.** Write the claim **where a parser already reads** and it is audited on
   every commit for free. That is what law-in-data does, which makes *"a checker that restates the law
   is the drift checkers exist to catch"* a doubt rule at heart.
3. **Not chargeable — stop trying.** The truth of a fresh technical claim, spoken in a turn. What the
   workspace does instead is **make the error cheap and its discovery fast**.

**Corollary: a claim about our own enforcement layer is checked at the call site, never at the
module.** Owning a detector and charging for it are separate facts.

### AD-17 — Delegation is mandatory where an executor reads the assignment; elsewhere it is advice (2026-08-17)
The ask was a guaranteed way to route cheap work to a cheaper level, with the **plan** as the trigger —
the moment work is cut into tasks is the cheap point to decide who executes each one. **That trigger
is already built**: the Loop 1 plan table in `core/flows/craft/craft.md` carries `level` and `effort`
per task row, and that loop's adversarial review charges that each row be executable by its level.

**What is missing is an executor that reads it.** Inside `/craft` there is one; outside it nothing
reads the tag, so it is advice. **Hence the reading of the expensive-level-heavy split: it measures how
much work bypasses the flow that routes**, not per-task indiscipline. The lever is routing more work
through `/craft`, not building a second router beside it. **Delegating ≠ parallelising**: offered a
shape with parallel workers Lucas chose **no parallelism** (2026-08-17).
