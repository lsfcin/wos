---
name: publish
description: Rebuild the public repo from this workspace and push it — what crosses, what the target regenerates, and the target's own suite as the gate. One way: nothing is ever edited on the far side.
---

# Publish skill

Arguments: $ARGUMENTS — nothing, or `--check` to report the gap and stop.

---

## Why this exists

The public repo his students clone is **rebuilt from this one and never edited on the far side**.
That direction is the whole design, and the failure it invites is silence: for weeks the sync
reported `0 difference(s)` while 34 pointers inside the target's generated blocks aimed at files the
floor refuses — including `core/CONTEXT.md` routing to `core/experiments/`, a REFUSED tree. Nothing
was wrong with the copy. What was missing was **the destination finishing the job**, and the reason
it never did is that `push` used `--no-verify`, so no generator and no gate ever ran over there.

So this is not "run the sync". It is the whole loop, and the last two steps are what make it honest.

## Protocol

1. **Read the gap.** `core/run tools/wos/publish/repo` — how many files cross, how many lines, and
   the orphan count. **An orphan is a finding**: a tracked, eligible file no feature claims is one
   the workspace carries without being able to say what for. `--orphans` lists them. The target is
   zero, and the fix is a `ships` entry in `core/features.txt` or a refusal with its reason in
   `core/public.txt` — never a file quietly left out.
2. **Stop here on `--check`.** Report the number and do nothing else.
3. **Sync.** `core/run tools/wos/publish/repo --sync`. This refuses **before the first byte** on a
   credential, copies what is missing or stale, deletes what no longer crosses, carries the
   executable bit through the index, and then runs the generators **in the target** so its routing
   tables describe its tree. A `FAILED` line means a generator did not run: fix that before pushing,
   because the alternative is publishing a table of a tree that does not exist.
4. **Prove it settled.** Run `--sync` again. It must report `0 difference(s)`. Anything else is an
   oscillation — the sync and a generator disagreeing about the same bytes — and the bug is HERE,
   never in the target.
5. **Push.** `core/run tools/wos/publish/repo --push`. It branches `feature/sync-<date>`, commits
   **with the target's full pre-commit pipeline running**, merges through `develop` to `master` by
   `--no-ff`, and pushes both. This is the one step that leaves the machine, so it is Lucas's call.
6. **Read a refusal as the answer, not the obstacle.** If the target's gate or its own suite refuses
   the commit, that is the single most valuable output this loop produces: four defects invisible
   from this workspace were found exactly that way. **Fix it HERE and re-run from step 3** — never on
   the far side, and never with `--no-verify`.

## What is not this skill's job

- **Editing the target.** Ever. It is rebuilt, and a hand edit there is destroyed by the next sync
  with no record that it existed.
- **Deciding what crosses.** That is `core/public.txt` (the floor and its refusals) and the `ships`
  column of `core/features.txt` (the claims). Both carry their own reasons; read them there.
- **The target's `ROADMAP.md`, `ISSUES.md` and `.gitignore`.** The target writes its own two lists
  by the 2026-09-04 per-repo ruling, and the sync generates the third for it.
