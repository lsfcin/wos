# Craft — Runtime Spawn Recipes
> How the orchestrator actually spawns a loop, per runtime. Verbatim recipes; no improvisation.

Load **only the section for the runtime you are running in**, and only in the orchestrator, at the
first spawn. The flow itself is runtime-agnostic — all state lives in `.craft/` files — so this file
is the one place that knows about `opencode run`, the Claude Code `Agent` tool, and the rest.

The spawn prompt body is in [`craft.md`](craft.md) § Orchestration; the level → model table it
resolves against is in [`routing.md`](routing.md).

## Spawn procedure per runtime

Verbatim recipes a fresh-level executor follows without improvisation. The orchestrator picks ONE runtime based on where
it is running; never mix in a single chain.

**opencode** (subprocess per loop — required for level diversity):

opencode's in-session `task` / `subagent` tool does NOT take a `model=` argument — subagents invoked via `task` inherit
the orchestrator's own model (per opencode docs §Agents → Model: *"If you don't specify a model, … subagents will use
the model of the primary agent that invoked the subagent"*). For an orchestrator that needs different-level models per
loop, that inheritance collapses every level onto the orchestrator's model. The way to get true level routing in
opencode
is therefore to spawn each loop as a **fresh `opencode run` subprocess** carrying the resolved model in `-m`, NOT via
the in-session `task` tool. Each subprocess is its own opencode session with its own active model — exactly the "fresh,
cheap session that reads exactly one file" the Core Principle calls for.

```bash
# orchestrator (loop-server session at $PROJECT_ROOT), per loop N with level $LEVEL:
RESOLVED=$(read_level_map "$PROVIDER" "$LEVEL")   # e.g. nvidia/z-ai/glm-5.2
opencode run \
  --model "$RESOLVED" \
  --agent "craft-$LEVEL" \
  --auto \
  --dir "$PROJECT_ROOT" \
  "Read core/flows/craft/craft.md, section 'Loop $N' plus 'Core Principle',
   'Autorouting', 'Level → provider → model mapping', 'Return Flags'. Then read
   $PROJECT_ROOT/.craft/$SLUG/$INFILE. Execute Loop $N. Append your output to
   $PROJECT_ROOT/.craft/$SLUG/$OUTFILE following the embedded template. End your
   section with: executor: craft-$LEVEL model=$RESOLVED level=$LEVEL deleg=$DELEG.
   Reply with ONE line: OK <verdict> | FLAG <flag line> | BLOCKED <reason>." \
  2>&1 | tail -n 1
# orchestrator captures the last stdout line as the verdict; the executor's appended
# file section survives the subprocess exit (it wrote to disk before printing).
```

Notes a fresh orchestrator must read:
- Loops are strictly serial — `wait` for each subprocess before spawning the next (each loop reads the previous loop's
  output file).
- `--auto` auto-approves non-denied permissions; the executor needs `read`, `edit`, `bash`, `glob`, `grep`. Without
  `--auto` the subprocess hangs on the first permission prompt and you cannot answer it from the orchestrator's session.
- Special case: `padaria` chains skip level routing by design (one medium session does plan+code+ship). For padaria the
  in-session `task` tool is fine — no per-level model mix needed, same model throughout.
- The executors are pinned agent types `craft-low` / `craft-medium` / `craft-high` defined in
  `.opencode/agents/craft-*.md`; **their frontmatter does NOT carry a `model:` line** (stripped per the agnostic
  principle — see [`prior-art.md`](prior-art.md) § Research provenance). The `-m <RESOLVED>` passed to `opencode run`
  selects the executor's model; the `--agent craft-<level>` selects the role.
- If `opencode run` is unavailable in a degraded environment, fall back to manual mode: the user opens a fresh opencode
  TUI session per loop, sets the model with `/model <RESOLVED>`, runs `@craft-<level> "<spawn-prompt>"`. The flow is
  unchanged.

**Claude Code** (Agent tool per loop):

Spawn via the native `Agent` tool with `subagent_type: 'craft-low'|'craft-medium'|'craft-high'` and the spawn-prompt
body above. The agent's frontmatter `model: haiku|sonnet|opus` IS the level alias Claude Code resolves to the latest
low/medium/high-level short name — Anthropic's own dogfood pattern (see [`prior-art.md`](prior-art.md) § Research provenance,
source s8). No subprocess shelling; no `-m` needed.

**Copilot CLI / anything else**: the user opens a fresh session per loop with the spawn-prompt and picks the model from
the active provider's level-map. Recipe status — copy the executor bodies, adjust the frontmatter for the runtime.

## Runtime portability

The flow itself is runtime-agnostic — all state lives in `.craft/` files, so any agent that reads files and runs git can
execute a loop. Only the **pinned executor definitions** are per-runtime (same body, different frontmatter dialect):

| Runtime | Executor definitions | Frontmatter `model` (default fallback) | Status |
|---|---|---|---|
| Claude Code | `.claude/agents/craft-{low,medium,high}.md` | `haiku 4.5 \| sonnet 5 \| opus 4.8` (anthropic) | in place |
| opencode | `.opencode/agents/craft-{low,medium,high}.md` (`mode: subagent`) | `nvidia/deepseek-ai/deepseek-v4-flash \| nvidia/deepseek-ai/deepseek-v4-pro \| nvidia/z-ai/glm-5.2` — **default to nvidia** (free) in this workspace; overridable per-spawn to any provider in the availability check. | in place |
| Copilot CLI | `.github/agents/craft-*.md` **in the target project's repo** (or `~/.copilot/agents/`) | GitHub Models free-level id | recipe only — copy the Claude Code bodies, adjust frontmatter |
| anything else | none — manual mode: user opens a fresh session per loop with the spawn prompt and picks the model from the active provider's level-map | — | always works |

Adapting to a new runtime ≈ 30 min: mirror the three executor bodies, translate the frontmatter, dry-run one padaria
task.

**rtk note:** the rtk hook rewriting shell commands (`grep` → `rtk grep`, test runners, git) is compatible — verified
that `grep executor` output passes through intact, and rtk's compression of test output is *aligned* with this flow's
token economy. If any audit output looks over-filtered, bypass with `rtk proxy <cmd>`.