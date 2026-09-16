# Core Library Schema
> The law about `.md` documents: which types exist, where a file belongs, how one that outgrew the cap
> is cut, and which words are canonical. The **tables here are load-bearing** —
> [`schema_law.py`](hooks/schema_law.py) parses them and no checker restates them. Drift is a bug.
> answers: what type a file is, where it lives, how it splits, what a word means
> enforced-by: core/hooks/checks/type-gate.py, core/hooks/entropy/entropy_naming.py,
> core/hooks/entropy/entropy_list.py, core/tools/wos/skills/validate.py

<!-- warn-exempt: the tables here are parsed, not read, so a cut moves law rather than prose — and
     the rows a reader needs least are the ones a checker needs most. The block cap still applies. -->

## The `.md` type system

**`UPPERCASE.md` is a type. `lowercase.md` is an instance.** A type means the same thing in every
folder, so uppercase names are a **closed set** — inventing one is a deliberate act (one line added
below), never an accident. Each type answers exactly one question; if you cannot say which, it does
not get a type.

| Type | The one question it answers |
|------|------------------------------|
| `AGENTS.md` | What rules always apply, and where do I start? (root only) |
| `CONTEXT.md` | What is *this directory*, and where inside it do I go? |
| `ROADMAP.md` | What do we intend to do — and what did we reject, and why? |
| `SPECS.md` | What must be true of this thing, and *why*? (contract + rationale) |
| `ISSUES.md` | What is currently **untrue** that we know about? (hand-written issues + generated measurements) |
| `README.md` | I just cloned this. What is it and how do I run it? (repo root only) |
| `REFS.md` | What external material exists, and what did we conclude about it? |
| `SKILL.md` | What procedure does the agent follow when invoked? |
| `GOALS.md` | Which goals have wind right now? (dashboard + router) |
| `INBOX.md` | Raw capture, zero taxonomy, drained to empty |
| `MEMORY.md` | Which memories exist, and what is each about? (index + router, `brain/memory/` only) |
| `SETUP.md` | How do I make this environment work? (toolchain install + config) |
| `PROJECTS.md` | Where does each internal project live — here, and outside? (root only) |
| `STATUS.md` | Is this craft chain still running, and where did it stop? (`.craft/<name>/` only) |
| `SCHEMA.md` | This file: the law about types. |

Anything else is rejected: *"add it to the allowlist if you mean it."* `STATUS.md` must stay one line
of present-tense state; `MEMORY.md` is the one type the agent writes rather than authors, and is
checked like any other file. **Where types nearly touch:** `CONTEXT.md` **never hand-lists files** —
but ask why a hand list was written before deleting it, since it may point at what the generator
cannot reach. Rules that *constrain code* go to `SPECS.md`, what the directory *is* stays in
`CONTEXT.md`. `ISSUES.md` owns the issue text and `ROADMAP.md` cites it by id. Inside `ISSUES.md` the
hand-written issues come first and every measurement sits in its own block — **never hand-edit inside
a block, never write a measured number outside one.**

### The one exception: transient initiative docs

A **cross-project rollout** is **not a new type** (ruled 2026-08-14, Lucas): it is intent, plan and
what we rejected scoped to one initiative — the ROADMAP question — so it takes a **scope suffix**,
not a name. A **session plan** the type system does not reach at all: a roadmap is structural, a
session plan lives one sitting. Membership **only shrinks**; each survivor owes a death condition on
line 3.

| File | Route | Why |
|---|---|---|
| `code/ROADMAP-spec-drive.md` | → ROADMAP-spec-drive.md | same shape, no anchor citations |
| `code/dobra/DECISIONS.md` | → that project's SPECS.md | **not a roadmap at all** — decisions are *what must be true and why*, the SPECS question |

**Every backticked `.md` name in this section is parsed as an exemption**, so naming a retired file
here to explain its history puts it straight back on the list.

## Placement: level × read-frequency

The first test is **is it still true?** — against code, tests and `git log`, never memory; an untrue
ESSENTIAL is the most expensive object here. Then level, per *section*: **ESSENTIAL** = work comes out
wrong · **IMPORTANT** = work comes out slower · **DESIRABLE** = nothing changes, git holds it.
Read-frequency is a property of the enforcement layer, not a guess: **HOT** = `CONTEXT.md` (the only
enforced-read type), `AGENTS.md` and `MEMORY.md` (system prompt), `GOALS.md` and `ROADMAP.md`
(induced-hot by the root `README.md`); **COLD** = everything else; **MACHINE-READ** = `SCHEMA.md`.
Where the axes meet: hot+essential **KEEP** · cold+essential **PROMOTE**, it is arriving too late to
prevent the error · hot+important **REDIRECT** behind one pointer line · cold+important **KEEP** ·
desirable **CUT**. **A provider's own directory is not a placement, it is an escape** — no type owns
it, no check reads it, and it dies with the harness; symlink it in and it is an instance again.

**The REDIRECT recipe, in order**, and the order is what pays: (1) delete what a hook already enforces
— except a number that changes how you write *before* the hook can speak, so the size caps stay;
(2) move constraints to a sibling `SPECS.md`; (3) move data out; (4) delete stale claims; (5) keep
identity and navigation only. **Open the child `CONTEXT.md` and the file's own routing block first** —
most of what looks movable is already written better elsewhere. What replaces a moved section is one
thin pointer line, never an instruction; the check fires on an over-size head *and* a modal. **A
constraint sitting in a `CONTEXT.md` head is the standard defect.** Compression is last and measured
worthless — placement beats phrasing.

## No archive types

`ARCHIVE.md`, `HISTORY.md` and `.log/done.md` are **deleted, not renamed** — a file that is "never
auto-loaded, ask explicitly" is doing git's job. The [`deletion`](norms/deletion.md) norm applies
*inside* a file too; keep a finished line only when the next session needs it to *extend* the work,
as present-tense state. The one thing git cannot hold is an approach *tried and rejected*: one line
under `## Rejected` in the relevant `ROADMAP.md`, or `## Ditched` in `brain/GOALS.md`.

## Routing depth and locality (structural policy)

Four axes, **deliberately separate** — conflating them produced the wrong "flatten everything" call.

| Axis | Rule | Enforced by |
|---|---|---|
| **locality** | many small local `CONTEXT.md` = good, never consolidate to "reduce clutter" — granularity is what makes weak models navigate | judgement |
| **depth** | cap hops to content, not file count; **measure** before adding a routing level | judgement |
| **crowding** | `WARN_FILES` asks for a look, `BLOCK_FILES` is the cap | `entropy_crowding.py`, dashboard |
| **routing** | a subdirectory under `FOLD_FILES` is folded into its parent's table, not linked | `workspace_scanner.py` |
| **document size** | `BLOCK_LINES` and `BLOCK_CHARS` both cap one authored file; a root that sheds parts routes to them | `line_counts.py`, dashboard |

Splitting an over-full directory *adds a hop*, so crowding and depth trade directly: pay the hop only
when the split removes more table than it adds — a directory in the dozens pays, one just over the
signal does not. Numbers live in [`limits.env`](hooks/limits.env), never in a second copy — this
table named four of them until 2026-09-06 and every one went stale the day they moved; offenders
live in [`ISSUES.md`](../ISSUES.md). Prose is capped at the same number as code, but a part's readers are
*sessions deciding whether to read it*, so the index must carry enough to decide without opening
anything. Also: **no session reads the corpus, it reads a chain**, so a routing table costs row
*count* per chain.

## When a document outgrows its type

### The four disposal routes

An off-allowlist `UPPERCASE.md` is *unclassified*, not wrong. **Ask *is this still true* before *what
type is this*.** Route what survives: **generated** or **hand-authored content** → lowercase instance ·
**hand-authored constraint** → `SPECS.md` · **a question no type answers** → a new type, which only
`SETUP.md` ever qualified for.

**A generated measurement goes where its question already has a type**, and lands in a tracked file —
**a ratchet that is not tracked cannot ratchet**. **A declaration table takes none of these routes:**
`features.txt`,
`profile.txt`, `limits.env`, `deps.txt`, `vendored.txt`, `generated.txt` and `extensionless.txt` are
hand-authored data read by exactly one law module, **never prose**. **The extension names the shape:**
`.tsv` for a table with a header row, `.txt` for one value per line, `.env` for `key=value`.

### A type that outgrows the cap is cut

**Cutting is the rule; a sibling file is the exception and needs Lucas's explicit OK** — the
[`cap`](norms/cap.md) norm, stated once here for every type. Delete what repeats, what nobody reads,
and what a generator already derives: a split preserves the mass across more files, which is how this
workspace reached nine roadmaps. Two traps: a deleted file's row in the transient table keeps its
exemption alive, and the document you are deleting can be the sole record of something live. **An
approved sibling is `TYPE-<name>.md` with the unsuffixed file as the index**, name lowercase
kebab-case — `type-gate.py`, `entropy_naming.TYPE_SLUG` and `citation-gate.LIST_NAMES` each read
that shape and none of them states it. The index keeps what is true of every sibling, any list the
type's rule says lives in one place, and the generated routing table. The check that makes "as small as
possible" checkable: **a reader who has read only the index names the sibling that answers their
question, and is never wrong.**

### What a part publishes about itself

A part's header exists for one reader — the index's generated table — and every field answers *should
I open this file?*, never *what does it say?* **The two errors are not symmetric:** skipping a part
that held what the task needed is silent, opening one that was not is a visible read, so a field that
only saves a read is cut. **The header is `>` lines under the H1, not YAML frontmatter**, and **a
wrapped field is one field**: a `>` line that is not itself a `key:` continues the one above it, parsed
for everyone by [`routing/header.py`](hooks/routing/header.py). Every part opens with two to three
sentences and no key; then `priority` and `blocked-by` on ROADMAP, `answers` on SCHEMA, `governs` on
SPECS (the same job as a `> spec:` line), `feature` on SETUP, `enforced-by` on both.

#### Every field that names our own code is verified

`enforced-by`, `blocked-by`, `governs` and `spec` name paths; `feature` names the registry.
[`entropy_fields.py`](hooks/entropy/entropy_fields.py) checks each against the tree — blocking on what
a commit adds, reporting on everything. It never reaches prose, and inside `governs` reads only
path-shaped tokens.

### What a description must say

Three rules: **name the question the file answers, not its topic** — a topic makes the open-or-skip
decision a coin flip; **add the discriminator**, what is in here as opposed to the file next door;
**two to three sentences**, bounded by `hoist.DESC_LIMIT`, prose first and `key:` fields after. **A
truncated description is a finding, not a rendering** — fix the source, never the cut. **Everything
countable is counted, never declared**, because a hand-kept count in `ROADMAP.md` went stale four
times. And **the table names the marker in words, not the emoji.**

## Vocabulary

**workspace-os** is also written `wos` · `WOS` · `w-os` · `W-OS`; **craft flow** means the `/craft`
skill and `core/flows/craft/`; **Front** is a top-level workstream in `ROADMAP.md`. **Neither a Front
number nor a bug number is a citable identifier** — closed items are deleted, so the number is a dead
pointer the day the work lands. Numbering is legal only inside `ROADMAP.md` / `ROADMAP-<name>.md` and
in commit messages; **a bug id is never reused** (ruled 2026-08-31), new ids are durable names
`b<YYYYMMDD>-<name>`, and a bug cited outside its list is named by id.

### Terms with one meaning

| Term | Definition |
|------|------------|
| **feature** | Something **this workspace authors** that can be switched off in-process, declared in [`features.txt`](features.txt) — one layer or a combination. Third-party machine state is not a feature; it is a `SETUP.md` step plus a `deps.txt` line. The test: if switching it off leaves nothing running to observe the difference, it is substrate |
| **layer** | One of `hooks · tools · skills · agents · flows · norms` — each names a directory under `core/`, except `norms` |
| **norm** | A rule that exists only as written words and is obeyed rather than enforced — the INDUCED half of the line whose ENFORCED half is `file_law.py` / `schema_law.py` / `feature_law.py`. A norm that acquires a checker becomes a hook |

### Retired tokens

**A rename is finished when its old token appears nowhere.** This table *is* the assertion:
`entropy_list.py` fails if any token below survives in a tracked file, this file excepted. Add a row
the moment a rename lands, and delete the prose that would otherwise explain it.

| Retired token | Replacement | Retired |
|---------------|-------------|---------|
| `loop-engineering` | `craft` | 2026-07-23 |
| `loop-router` | `route` | 2026-07-23 |
| `loop-architecture` | `architect` | 2026-07-23 |
| `LOOP-TREE` | `tree.md` | 2026-07-23 |
| `KNOWN-BUGS` | `ISSUES.md` | 2026-07-30 |
| `/loops` | `/craft` | 2026-08-17 |
| `BUGS.md` | `ISSUES.md` | 2026-08-19 |
| `WATCHLIST.md` | `core/refs/REFS.md` | 2026-08-20 |
| `.loop` | `.craft` | 2026-08-20 |
| `parsed-by` | — retired unfilled | 2026-08-25 |
| `pre-read.sh` | `read/pre-read.py` | 2026-09-02 |
| `fanout` | `crowding` | 2026-09-14 |
| `shard` | `part` | 2026-09-14 |
| `ledger` | `list` | 2026-09-14 |
| `seam` | `boundary` | 2026-09-14 |
| `tier` | `level` | 2026-09-14 |
| `slug` | `name` | 2026-09-14 |
| `probe` | `metadata` | 2026-09-14 |
| `column cap` | `document cap` | 2026-09-14 |
| `mail-triage` | `mail` | 2026-09-16 |

**One retired token can owe four replacements, and the cell holds only the commonest.** `slug` names
four ideas, and they do not flatten into one: a link's `short name`, a feature's or file's `name`, a
bracketed `item id`, and a bug's `id`.

**A rename whose old spelling is also a real word needs a shape, not a token** — a row that fails on
correct prose trains people to ignore the check, so `/loops` and `.loop` are rows while `Frente`→
`Front` is a citation shape inside `citation-gate.py`. Not yet swept, so not yet listed:
`SPEC.md`→`SPECS.md`.

### A vendor's model name is data, never a directive

**Ruled 2026-08-17 (Lucas): *"nothing in WOS should be tied to a specific vendor/company/model."*** A
list assigns a **level** — `low` · `medium` · `high` — and which KIND of work earns which level is
[`levels.txt`](levels.txt). Which model FILLS a level is data, in two places and nowhere else:
[`tools/wos/levels`](tools/wos/levels) per harness, [`flows/craft/routing.md`](flows/craft/routing.md)
per provider. **A shape, not a token:**
`**model: opus**` is a directive and forbidden; `` `model: opus` `` in prose reporting a measurement is
data. `entropy_vendor.py` matches the bolded assignment and nothing else.

<!-- routing:start -->
## Routing

| Part | Description | Answers | Enforced by |
|------|-------------|---------|-------------|
| [`SCHEMA-layers.md`](SCHEMA-layers.md) | The frontmatter every skill, agent, norm and flow declares, and how they compose. The document law — types, placement, cutting, vocabulary — is the index, [`SCHEMA.md`](SCHEMA.md); this part is the prompt-loaded half, because a `.md` a session reads and a frontmatter block a runtime parses are two different contracts. | what fields each layer requires, which layer may point at which | core/tools/wos/skills/validate.py |
<!-- routing:end -->
