# The agent-library layers
> The frontmatter every skill, agent, norm and flow declares, and how they compose. The document law
> — types, placement, cutting, vocabulary — is the index, [`SCHEMA.md`](SCHEMA.md); this part is the
> prompt-loaded half, because a `.md` a session reads and a frontmatter block a runtime parses are two
> different contracts.
> answers: what fields each layer requires, which layer may point at which
> enforced-by: core/tools/wos/skills/validate.py


**Execution metadata lives on the executor (agent), never on the skill.** A skill is a trigger, a flow
is a procedure, an agent is the thing that runs. The graph is a **sparse typed DAG**, one direction;
skills do not point at skills. Provider and model names appear **only in generated runtime mirrors**,
never in `core/` source. **No flow is privileged** — realism comes from validation running over *every*
flow, [`flows/_template.md`](flows/_template.md) included, which is a template and not a reference
implementation. [`wos/skills/validate.py`](tools/wos/skills/validate.py) enforces every field below
plus the `uses:` DAG and is wired into `core/hooks/pre-commit`, so nothing here restates its messages.

### Layer: skill — `core/skills/<name>.md`

`name` (kebab-case, matching the filename) and `description` (actionable, drives the menu, ends with
"Invoke with /name [args]."); optionally `flow`, what a THIN skill dispatches to. **No `model`, `level`,
`tools` or `subagents`** — execution detail, pushed down. THIN and FAT are both valid. A skill's
`refs/` folder sits **beside the skill file**, never under `.claude/` or `.opencode/`, which are
mirrors `sync-skills` prunes. **Sub-skills group into a suite folder**: the parent stays flat and is
the only file mirrored, and sub-skills drop the parent's prefix from their filenames.

### Layer: agent — `core/agents/<name>.md`

`name`, `description` (what evidence or output this worker produces) and `level` — `low` | `medium` |
`high` | `max`, the provider-agnostic effort ladder. **Workers** also declare `tools` and `output`,
plus `defaultProgress` when long-running; an **orchestrator** carries the first three only, inheriting
the full toolset and owning no single artifact. `level` is the source of truth and a runtime needing a
concrete model sets it **by hand** per mirror — there is no generator. **No `thinking:` and no
`model:` in source.**

### Layer: norm — `core/norms/<name>.md`

`name` and a one-line `description` of what obeying the rule buys, which feeds the routing table and
never `AGENTS.md`. **The body is the published rule, verbatim** — written into `AGENTS.md` as one
bullet by [`routing/norms.py`](hooks/routing/norms.py), no rendering, no wrapping. `AGENTS.md` is
always loaded, so a norm's body is its entire cost: a rule needing a paragraph of rationale is a
`SPECS.md` section plus a pointer. **Order comes from [`features.txt`](features.txt)**, not the
directory listing — two ordered lists of one set is the asymmetry this workspace keeps paying for.

### Layer: flow — `core/flows/[<skill>/]<name>.md`

A flow owned by a dispatcher skill lives in `core/flows/<skill>/` and its **filename equals the command
tail** (`flows/research/scout.md` ⟺ `research scout`); unowned flows stay flat, and validation is
recursive. `description`, `args`, `type` (`research-brief` | `utility` | `domain`) and `confirm`
(`plan` = stop for an explicit yes, `none` = summarize and continue); optionally `agents`, and `uses`,
where absent means leaf. The disciplines each `type` owes are **copied verbatim from**
[`flows/_template.md`](flows/_template.md), which holds the canonical wording — tool-discipline and
integrity always, required-artifacts and provenance and scale-gate by type. Symmetry is required
*within* a type, not flattened across all flows. The `craft` cluster is **engineering**: its own
protocol, exempt by path. Known asymmetry: `engineering` is not in the `type` enum, so the exemption is
positional rather than typed; the fix is queued in [`ROADMAP.md`](../ROADMAP.md).

### Composition and cycles

**Flows compose** — `uses: <flow>, <flow>`. Composite versus leaf is **not a type**; there is no
separate orchestrator layer. A **definitional** cycle (A built from B, B from A) lives in the `uses:`
graph and is **forbidden**, because expanding it never bottoms out; the guard is a static DAG check no
exemption escapes. An **execution** cycle (a flow returns to step 2) lives in the runtime trace and is
**allowed**, because state changes each pass so it makes progress; the guard is a declared numeric
iteration cap plus an exit condition, which is **not statically checkable** — do not try to enforce it
with the DAG check, which forbids cycles where the cap *permits* them, bounded. So a trace may revisit
a flow without breaking the DAG: `A → B → C → A → …` is legal because the graph holds only `A → B` and
`A → C`, and the back-arrow is *`A`'s own bounded loop*. A cycle whose state does not change is a hang.

