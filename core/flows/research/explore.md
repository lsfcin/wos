---
description: Autonomous experiment loop — try ideas, measure results, keep what works, discard what doesn't, repeat.
args: <idea>
type: utility
confirm: plan
---
## Tool Discipline (Read First)

Tool names are literal. Use only tools visible in the current tool set. See `core/tools/` for runtime-specific mappings.

- If a tool returns `Tool not found`, map to the canonical visible tool or record the capability as blocked.

Start an explore optimization loop for: $@

## Step 1: Gather

If `explore.md` and `explore.jsonl` already exist, ask the user if they want to resume or start fresh.
If `CHANGELOG.md` exists, read the most recent relevant entries before resuming.

Otherwise, collect the following from the user before doing anything else:
- What to optimize (test speed, bundle size, training loss, build time, etc.)
- The benchmark command to run
- The metric name, unit, and direction (lower/higher is better)
- Files in scope for changes
- Maximum number of iterations (default: 20)

## Step 2: Environment

Ask the user where to run:
- **Local** — run in the current working directory
- **New git branch** — create a branch so main stays clean
- **Virtual environment** — create an isolated venv/conda env first
- **Docker** — run experiment code inside an isolated Docker container

Do not proceed without a clear answer.

## Step 3: Confirm

Present the full plan to the user before starting:

```
Optimization target: [metric] ([direction])
Benchmark command:   [command]
Files in scope:      [files]
Environment:         [chosen environment]
Max iterations:      [N]
```

Ask the user to confirm. Do not start the loop without explicit approval.

## Step 4: Run

Initialize the session: create `explore.md`, run the baseline, and start looping.

Each iteration: edit → run benchmark → record result → keep or revert → repeat. Do not stop unless interrupted or `maxIterations` is reached.

Record every metric exactly as the benchmark reported it — never invent, extrapolate, or smooth numbers. A failed or crashed run is recorded as a failure with its error output, not skipped.

After the baseline and after meaningful iteration milestones, append a concise entry to `CHANGELOG.md` summarizing what changed, what metric result was observed, what failed, and the next step.
