# Brain — Specs
> Goal file format, section growth triggers, signals, dynamics, timing, and backlog conventions.

## Goal File Structure — Organic Growth

Goal files grow from seed to full. No section required at creation.

**Minimum viable seed:**
```
# [ area | horizon ] goal title
- [ ] [short-id] first backlog item
```

Area — `health` body, sleep, exercise, checkups · `career` research, papers, teaching, academic positioning, grants · `craft` the things being built for their own sake as work — research projects, software, the workspace itself · `finances` money, taxes, admin, investments · `fun` hobbies, play, exploration, anything done for its own sake · `spiritual` reflection, meaning, inner life, values.
Horizon: `now` / `near` / `year` / `dream`

`craft` was in nine goal files and in none of the five areas this list declared until 2026-09-18, found by the dashboard counting every workspace commit as `health` — the goals were right and the list was short.

**Growth triggers** — add section when useful, not before:

| Section | Add when... |
|---------|-------------|
| description | scope worth writing down |
| `>**signals**` | want to reason about priority |
| `>**dynamics**` | diagnosing stall, or after meaningful work session |
| `>**fears**` | stalling on goal, or stakes feel high |
| `>**analysis**` | need strategic synthesis on fears or block |
| `## selected next achievement` | always on once backlog exists — ease-start always filled |
| `>**timing**` | external anchor or window worth naming |
| `## stats` | written by `core/hooks/brain/brain_stats.py` on every commit — never by hand |

`## stats` reads `touches: a/b/c/d/e/f` — **month / trimester / semester / year / 2-year / 4-year**, the periods in `core/hooks/brain/brain_common.py`. Named here once rather than on every goal file:
it was a six-row table in each of them until 2026-08-31, ~320 lines of the corpus that nothing read, while `GOALS.md` built its dashboard from git directly.

**A goal file is written in whatever language its owner thinks in.** The rest of the durable `.md` corpus is English because an agent re-reads it every session; a goal file's reader is the owner, and translating their own motivation into a second language costs the thing that makes it work.
Exempt, ruled 2026-08-31, and out of the repo scope entirely since 2026-09-11.
`brain/goals/CONTEXT.md`'s routing table inherits the exemption — it is generated from these files' first lines.

## Signals

Display order always: impact · requirement · engagement

- **impact**: `forgettable` / `useful` / `meaningful` / `transformative`
- **requirement**: `optional` / `expected` / `essential`
- **engagement**: `reluctant` / `indifferent` / `motivated` / `thrilled`

Rule: 80% energy → transformative/meaningful × motivated/thrilled. Essential-only goals get minimum viable effort.

## Dynamics (agent-filled)

Update during compass review or when diagnosing stall.

- **mode**: `overprocessing` / `pressured` / `avoidant` / `pragmatic` / `relaxed` / `immersed`
- **motion**: `blocked` / `stalled` / `looping` / `advancing` / `steady` / `intense`
- **source**: `intrinsic` / `structured` / `external`

## Fears Block

Raw data, no interpretation. Four fields:
- **what**: specific negative outcome or emotional experience avoided
- **when**: situations that trigger it
- **why**: origins — perceived beliefs, past experiences, internal expectations
- **how**: current behavioral response — barriers, patterns in the way

## Analysis Block (agent-filled)

Synthesis on top of fears:
- How the goal is being handled
- Science-backed strategies for the specific block or fear
- Practical, precise, grounded in behavioral science and self-regulation research

## Backlog Ordering Policy

- Selected achievement = always first unchecked `[ ]` item in backlog
- Remaining unchecked = ordered by the owner's judgment — **by live motivation first, deadlines second**
  (ordering wins over pressure; see § Rationale below). Deadlines are a gentle reminder, never the organizing axis.
- Done items = move to `## done` section, **no topo do bloco**: `compress_done` mantém as três primeiras linhas e descarta o resto no próximo commit, sem avisar. Uma conquista escrita no fim do bloco desaparece silenciosamente — foi o que aconteceu em 2026-08-28. O bloco é mais-novo-primeiro.
- Achievement format: `[short-id] description` — short-id is 2–4 word kebab-case short name
- Optional inline timing: `> [ ] [id] description — Jun 01`
- On check-off: use `/compass` (the "close a win" move — folds the retired `/brain-finished`)

## Compass Interview — outputs & moves

`/compass` is a gentle strategic *interview*, not a report. Beyond diagnostics it writes back what the owner decides, using these moves:

- **almost-there** — a goal a step from a milestone/mvp/finish. No dedicated field: inferred from backlog `[x]`/`[ ]` ratio + `motion: advancing` + recent git touches + `closure` proximity. Compass surfaces its ease-start ("a step from done").
- **timing negotiation** — "is this the right moment, or better timing?" → if later, push the goal's `target` (chosen, not slipped).
- **ditch** — dropping a goal that no longer makes sense: move the whole goal file's entry to one line under `## Ditched` in `brain/GOALS.md`, then delete the goal file. A valid move, never a failure.
- **defer** — keep the goal, push its `target` forward. Distinct from ditch.
- **close a win** — flip `[ ]`→`[x]`, move to the `done` block, advance the selected achievement, write a fresh ease-start, set `motion: advancing`, acknowledge the win (the folded `/brain-finished`).

**Backlog item format:**
```
> [ ] [short-id] description
> [x] [short-id] completed item
```

## Timing Fields

| Field | Meaning |
|-------|---------|
| `target` | when does this feel naturally right? personal rhythm, not obligation |
| `anchor` | external timing anchor intentionally chosen (conference, semester, commitment) |
| `closure` | what outcome makes this feel complete enough to release? |
| `tolerance` | what actually happens if missed? negotiable, costly, or mostly symbolic? |
| `fallback` | if window closes, how does this evolve instead of collapse? |

## Selected Next Achievement Block

```
## selected next achievement
    [short-id] full description

**ease-start**
smallest action that bypasses the emotional or cognitive barrier — specific, doable now
steps to proceed afterwards
```

Ease-start always filled, never blank.

### Ease-start quality bar (agent-written)

An ease-start is a **do-it-now launcher**, never a vague reminder. The rule: *don't say "go look" — hand over the thing already loaded.* Every ease-start must carry, when they exist:

- **the exact link/handle** — the real URL, phone number, WhatsApp contact, file path, app name (not "open the portal" but "open `plataformabrasil.saude.gov.br` → Novo Projeto").
- **numbered steps** — the concrete click-path from cold start to first real action.
- **the content pre-staged** — if there's a form/message/doc to produce, drop the draft text or point to where the draft already lives (`academy/.../outputs/...`), so it's copy-paste not create-from-zero.
- **a 5–10 min ceiling** — the first action must fit one sitting; if it can't, the ease-start is too big.

When the compass/inbox skill lacks a real link or path, it must **go fetch or ask for it** before writing the ease-start — never ship a placeholder. A generic ease-start is a bug.

## Model Routing (agent-filled)

Optional per-goal hints so a session on this goal starts at the right power/cost. Vocabulary is shared with `core/skills/prepare.md` — provider-agnostic (function in the name, model as data):

- **level**: `low` / `medium` / `high` / `max` — capability class. Maps to the "decide → write → execute" split: `max`/`high` decides & writes, `medium`/`low` executes.
- **effort**: `low` / `medium` / `high` / `max` — reasoning depth / thoroughness for the run.

Placed as a `>**routing**` block near `>**signals**`. Example: `>**routing** \nhigh · high` for a research goal like cria; `low · low` for a startapp stub. The router (or `/prepare`) reads it to pick the actual model. Never write a model/provider name in the field itself.

## Rationale — why Brain is shaped this way

> Folded in from `brain/FOUNDATIONS.md` 2026-07-30: a spec says what must be true, its rationale says why. Keeping them apart made the *why* a file nobody opened. Every line below is a cited result, and each one is load-bearing for a design choice above.

- **Non-completion = emotion regulation failure**, not laziness (Steel 2007; Sirois & Pychyl 2013). Fix the emotional mechanism, not the discipline.
- **Perfectionism = ego-protection**. Completing exposes work to judgment. The `fears` block surfaces this so it cannot operate invisibly.
- **Writing a specific plan closes open loops** without completing the task (Masicampo & Baumeister 2011). Specific `ease-start` steps discharge Zeigarnik tension.
- **Maximizers get worse outcomes AND less satisfaction** than satisficers (Parker 2007). `closure` pre-commits the satisficing threshold *before* perfectionism can move the goalposts.
- **Autonomous motivation outperforms willpower** for sustained creative work (Deci & Ryan, SDT; 2022 meta-review).
  Design for alignment, not obligation.
- **Small consistent progress is self-reinforcing**: wins → satisfaction → importance → expectancy → more wins (Strand et al. 2025). Celebrate `[x]`, not just final delivery.
- **Fear made workable, not eliminated**, reduces its behavioural grip (ACT — Wolitzky-Taylor 2015, d≈1.0). The `fears` block is not therapy, it is intelligence.
- **External timing supplements internal motivation** without replacing it (Ariely & Wertenbroch 2002). `anchor` dates are chosen, never imposed.
- **Ordering by motivation beats deadline pressure**. Energy follows what has wind, not the clock (SDT). Reviews order by live motivation first; deadlines surface gently and second.
- **Ditching and deferring are strategic moves, not failures**. A satisficer releases cleanly rather than dragging every open loop (Parker 2007). The compass offers the drop as a valid option, never a verdict.
- **Timing is negotiated, not imposed**. *"Is this the right moment, or is there better timing?"* — moving a chosen `target` is alignment, not slippage.
