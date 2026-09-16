# Setup — a working clone
> What must exist before anything else in this workspace runs: the permission level the installing
> agent works under, the interpreter every tool is spawned with, and the gates that fire on commit.
> Run these in order and stop at the first check that will not pass.
> feature: permissions, declared-deps, github-auth, git-hooks, skill-mirrors
> enforced-by: core/tools/test/workspace/test_setup_executable.py

The five-part contract, and the handover rule for the one step marked `agent: no`: [`SETUP.md`](SETUP.md).

<!-- steps:start -->

## Agent permissions
> feature: `permissions` · agent: yes

**This step runs first, and its position is the point.** Every step after it is an agent editing
files and running commands; how often it has to stop and ask is decided here.

The levels and what each one costs are declared in [`core/permissions.txt`](core/permissions.txt),
in one sentence each. **Read them out and let the person choose**; never summarise them here, or
this file becomes a second copy that disagrees with the first.

**Precondition**
```bash
core/run tools/wos/permissions --check     # exit 0 = a level is answered and rendered
```

**Install** — idempotent. It installs the safest level **without asking**, so a clone with nobody
watching still ends up configured, and only then offers the choice:
```bash
core/run tools/wos/permissions --set guarded    # safe default, no question asked
core/run tools/wos/permissions                  # print the levels; offer to raise it
```

**Verify**
```bash
core/run tools/wos/permissions --check
```

The policy is versioned; the rendered `.claude/settings.local.json` is git-ignored, because a
versioned `bypassPermissions` would arrive switched on for whoever cloned next.

## The venv
> substrate: yes · agent: yes

One virtualenv at the workspace root, shared by every tool and the suite. `code/*` repos own theirs.

The venv keeps its executables in a directory whose name differs per machine, so nothing below
spells it: `sh core/run --python` prints this clone's interpreter and exits non-zero when there
isn't one, which makes it both the precondition and the path.

**Precondition** `sh core/run --python`

**Install** — `python3` is the creating interpreter and comes from the system, not the venv:
```bash
python3 -m venv .venv              # no-op if .venv already exists
"$(sh core/run --python)" -m pip install --upgrade pip
```

**Verify** `"$(sh core/run --python)" -c "import sys; print(sys.prefix)"` — this `.venv`, not the
system prefix.

## Declared dependencies
> feature: `declared-deps` · agent: yes

[`core/tools/deps.txt`](core/tools/deps.txt) declares every external dependency with its install
command, its check, and **what its absence looks like** — a missing dep makes a tool return a worse
answer rather than an error. The rule: [`core/tools/SPECS.md`](core/tools/SPECS.md) § Declared
dependencies.

**Precondition** — also the install plan, in one command:
```bash
core/run tools/wos/deps            # every dep, ok/MISSING, with the install line for each miss
```

**Install** — run what it printed. Rows marked `apt` need `sudo`; if you cannot get it, hand that
row to Lucas, naming the package and the `breaks` line printed beside it.

**Verify** `core/run tools/wos/deps --check` — exit 0 means nothing is missing.

## GitHub account
> feature: `github-auth` · agent: no

`core/hooks/post-commit` auto-pushes every `feature/*` branch, so an unauthenticated clone finds out
at its first commit.

**Precondition**
```bash
gh auth status                     # a logged-in host means this step is done
```

**Install** — the agent installs the CLI, and **`gh auth login` is the one part it cannot do**: the
device flow needs a terminal it can type into.
```bash
core/run tools/wos/deps --feature github-auth    # prints the install line for THIS machine's manager
```

**Needs you:** one command, in your own terminal, and nothing else — hand over exactly this:

> Run `gh auth login`. Pick **GitHub.com**, then **HTTPS**, then **Login with a web browser**. It
> shows an eight-character code, opens GitHub, and you paste the code and approve.

Wait for them, then finish it yourself — this part is not theirs:
```bash
gh auth setup-git                  # registers gh as git's credential helper, which fixes push
```

**Verify** — both halves, because authentication and pushing fail separately:
```bash
gh auth status
git push --dry-run origin HEAD
```

## Git hook
> feature: `git-hooks` · agent: yes

Applies `core/hooks/pre-commit` to **every** repo on the machine — that global reach is the point,
since projects under `code/` are their own repos.

**Precondition** `git config --global core.hooksPath`

**Install**
```bash
git config --global core.hooksPath "$PWD/core/hooks"
```

**Verify** `test -f "$(git config --global core.hooksPath)/pre-commit" && echo "hook reachable"` —
the path must resolve to a dispatcher, not just be a string.

## Executable bits
> feature: `git-hooks` · agent: yes

Git carries the execute bit, so a normal clone arrives correct. This step is for an archive export,
a filesystem that drops modes, a `umask` that strips it.

**Only the shell entrypoints git or a harness starts by path need a bit.** Nothing under
`core/tools/` does — those are spawned as `core/run tools/<family>/<leaf>`, so the launcher names
the interpreter and the bit is never consulted.

**Precondition** `test -x core/hooks/pre-commit && test -x core/hooks/post-edit.sh && echo "set"`

**Install** — idempotent by nature:
```bash
chmod +x core/hooks/post-edit.sh core/hooks/pre-commit \
         core/hooks/post-commit core/hooks/copilot/copilot-agent.sh \
         core/hooks/session/start-session.sh
```

**Verify** `find core/hooks -type f -name "*.sh" ! -perm -u+x` — no output. Any line is a file
that will fail to run.

## Skill mirrors
> feature: `skill-mirrors` · agent: yes

Every harness looks for skills in its own directory, so `core/skills/<name>.md` is published as a
copy into `.claude/skills/`, `.opencode/skills/`, `.zcode/skills/` and `.claude/commands/`. **Those
copies are generated and git does not track them**, which is why this step is not optional: a fresh
clone has the sources and none of the copies, so every `/<skill>` is missing until it runs.

They are copies rather than symlinks (ruled 2026-08-29), so freshness is regeneration at the four
moments that change a skill: this step, the post-edit hook, the pre-commit generator, and
`SessionStart` — the only one belonging to the machine that RECEIVES a `git pull`.

**Precondition** `core/run tools/wos/sync-skills --check`

**Install** — idempotent; it also prunes mirrors whose source skill is gone or switched off:
```bash
core/run tools/wos/sync-skills
```

**Verify** `core/run tools/wos/sync-skills --check` — prints `OK: all mirrors and command files in
sync`. Any `MISSING` / `STALE` / `ORPHAN` line names the file and the source it disagrees with.

<!-- steps:end -->
