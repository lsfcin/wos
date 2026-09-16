# Workspace Setup
> How to make this environment work on a new machine: toolchain install and per-machine config.
> The steps live in the parts; this file is what is true of all of them.

What the workspace *is* and what each feature buys you: [`README.md`](README.md). What the gates
enforce: [`core/hooks/SPECS.md`](core/hooks/SPECS.md). This file is only the install.

**This is a procedure an agent executes, not writing a human reads and improvises from.** You cloned
the repo and opened your own coding agent; *that agent* is the installer. There is no `curl | sh`
and there is not going to be one — an installer would have to be ported to every harness, while a
procedure works on whichever one you already opened. `/install` is a doorway into this file for
agents that support skills; it adds nothing, and this file never depends on it.

**[`SETUP-clone.md`](SETUP-clone.md) is first, always** — nothing else runs until it is done, and the
permission level it sets decides how often every later step has to stop and ask. The other three are
independent of each other; the table below is alphabetical, not an order.

**Every step has the same parts, and an agent runs them in this order:**

| Part | Contract |
|---|---|
| `> feature:` | which feature the step installs. Skip the step, lose exactly that feature |
| `> substrate: yes` | installs no feature — it installs what every feature *runs on*. Switching off the interpreter the switch itself executes on produces no ablation signal, so there is nothing to ablate and no registry row |
| **Precondition** | a command that says whether the step is *already done*. Run it first, always |
| **Install** | idempotent. Running it twice must be a no-op, never a second copy |
| **Verify** | a command proving the thing works. **A step is done when its check passes, never when its config looks right** |

`agent: no` marks the short list an agent cannot finish **alone** — an API key, a consent screen, a
device pairing. It has never meant the agent steps back: it runs everything it can, then hands the
human one remaining part, already set up and named as a single action. A **secret** the agent asks
for and writes itself; an **act only a person can perform** it reduces to one exact click, says what
happens next, and verifies afterwards. The human receives **one action, not an investigation** — a
step that leaves someone reading documentation has not been installed, it has been delegated.

Third-party machine state this workspace does not author is a step plus a `core/tools/deps.txt`
line, never a feature. Everything in the parts is per-machine state git cannot carry; everything
else is versioned, because the file system is the source of truth.

## Already wired — nothing to do

Versioned, and they activate on their own after a clone. Listed so a newcomer does not go looking
for an install step; they are not steps and have no checks.

| Feature | Why nothing is needed |
|---|---|
| Claude Code hooks | `.claude/settings.json` is in the repo; Claude Code reads it when the workspace is opened, and `core/hooks/` activates immediately |
| ZCode hooks | `.zcode/config.json` is in the repo and ZCode reads it at every session start — but project-scope hooks stay **inert until the workspace is trusted in the client** (one-time, per machine; `agent: no` — open the workspace in ZCode and accept the trust prompt; until then each session warns "workspace hook(s) pending review; disabled for this session"). Measured on this machine 2026-09-04: after trust, the canonical gates fire like Claude Code's ([`core/experiments/zcode-hook-protocol.md`](core/experiments/zcode-hook-protocol.md)). Until trust lands on a fresh machine, zcode enforces nothing at edit time; the git gates still fire, and the rtk shim still runs from ZCode's user scope ([`SETUP-compaction.md`](SETUP-compaction.md)) |
| opencode policy plugin | `.opencode/plugins/workspace-policy.js` is a project-level plugin, auto-loaded from the workspace root. Helpers live in `.opencode/wp-helpers.js`, outside `plugins/` so opencode does not load them as a second plugin |
| Antigravity hooks | `.agents/hooks.json` is in the repo; Antigravity / Gemini reads it on startup and delegates lifecycle events to `core/hooks/antigravity/antigravity_policy.py` |
| Copilot hook registration | `.github/hooks/workspace-policy.json` and `.github/hooks/rtk-rewrite.json` are inert config files until Copilot itself is installed |
| The feature registry | `core/features.txt` and `core/profile.txt` are versioned, and `core/hooks/feature_law.py` reads them where they sit |

The one exception is rtk for Claude Code: its code is versioned but its registration is not, which
is why [`SETUP-compaction.md`](SETUP-compaction.md) § RTK — Claude Code registration is a step.

**Before running the steps, read your profile** — it decides which of them you need, and
`core/features.txt` says what each feature buys, so a step is judged before it is run.

```bash
core/run tools/wos/features                 # every feature, grouped, with your answer
core/run tools/wos/features --off <name>    # one you do not want; its install step is then moot
```

## Verification

Does the install work? This is the whole-install check; each step's own Verify is in its part.

```bash
core/run tools/wos/deps --check                           # every declared dependency present
git config --global core.hooksPath                    # the global gate is wired
"$(sh core/run --script stubgen)" --version && tsc --version   # interface generators are reachable
node --input-type=module -e "import('$PWD/.opencode/plugins/workspace-policy.js').then(m=>console.log(typeof m.WorkspacePolicy))"
# Expected: function
./verify.py fast                                      # the workspace's own suite
```

The suite runs in parallel (`pytest-xdist`, `-n auto`) because it is bound by process **spawn**
rather than by work, and the pre-commit gate runs all of it on every commit at the workspace root.
Without xdist it still runs, serial, and says so.

Whether each *gate* then behaves as promised is a different question, answered by
[`core/hooks/SPECS.md`](core/hooks/SPECS.md) § One dispatcher, and the table it reads.

## Per-project setup

Each project under `code/` is its own git repo and owns its environment. A project whose setup
cannot be inferred from its code carries its own `SETUP.md`.

- [`code/SETUP.md`](code/SETUP.md) — per-language quick start, facade templates, codegraph
- [`academy/SETUP.md`](academy/SETUP.md) — LaTeX toolchain, paper compilation
- [`core/tools/video/SETUP.md`](core/tools/video/SETUP.md) — the video tool's model and cookie state

<!-- routing:start -->
## Routing

| Part | Description | Feature | Enforced by |
|------|-------------|---------|-------------|
| [`SETUP-accounts.md`](SETUP-accounts.md) | Everything that reaches a service off this machine: web search, the shared Google OAuth behind six tools, the Forms API's separate project, the Telegram capture bridge, and the CIn VPN. Five of the six need a human for one browser action or one password, and each says exactly which one. | web-search, google-auth, forms, telegram-capture, vpn-cin | core/tools/test/workspace/test_setup_executable.py |
| [`SETUP-clone.md`](SETUP-clone.md) | What must exist before anything else in this workspace runs: the permission level the installing agent works under, the interpreter every tool is spawned with, and the gates that fire on commit. Run these in order and stop at the first check that will not pass. | permissions, declared-deps, github-auth, git-hooks, skill-mirrors | core/tools/test/workspace/test_setup_executable.py |
| [`SETUP-compaction.md`](SETUP-compaction.md) | The two halves of what shrinks a session: rtk compresses tool output before it reaches the context, caveman compresses the agent's own writing. Each needs a binary and a registration, and in both cases the registration is the part that silently reverts. | rtk-compaction, caveman | core/tools/test/workspace/test_setup_executable.py |
| [`SETUP-interfaces.md`](SETUP-interfaces.md) | The outside programs the edit-time and commit-time gates shell out to: the stub generators that produce what the read gate hands an agent instead of a source file, the TypeScript linter, and the LaTeX toolchain the paper checks need. Skip one and its gate stops firing rather than failing. | interface-stubs, lint-typescript, latex | core/tools/test/workspace/test_setup_executable.py |
<!-- routing:end -->
