# Workspace OS

A personal operating system for working with coding agents. It is a git repository that holds projects, research and life management side by side, plus an enforcement layer that makes an agent navigate, verify and clean up after itself without being asked each time.

The design principle is one line: **the file system is the source of truth.** Nothing that matters lives only in an agent's memory, a chat history, or a machine's config — if it is real, it is a file, and it is versioned.

## Running it

```bash
./verify.py fast     # every Level 0 check + unit tests. The global pre-commit gate runs this.
./verify.py full     # adds the network-marked tests
core/run hooks/entropy/dashboard/entropy-dashboard.py   # the drift report → ISSUES.md
```

Setting up a fresh machine is a separate question, answered by [`SETUP.md`](SETUP.md). What each gate blocks, and the contract a new agent's shim must satisfy, is in [`core/hooks/SPECS.md`](core/hooks/SPECS.md).

## Where things are

Every directory carries a `CONTEXT.md` saying what it is and where to go inside it. That chain is the routing system, and reading it is enforced rather than suggested.

| Directory | What lives there |
|---|---|
| [`core/`](core/CONTEXT.md) | The agent library — skills, flows, agents, CLI tools, and the hooks. Provider-agnostic: no vendor name appears in a path or a verb |
| [`code/`](code/CONTEXT.md) | Software projects, each its own git repo |
| [`academy/`](academy/CONTEXT.md) | Research, teaching, papers, university administration |
| [`brain/`](brain/CONTEXT.md) | Personal OS: goals, attention, ideas, inbox. The agent collaborates here rather than serving |
| [`branches/`](branches/CONTEXT.md) | Life management — health, finances, home construction |
| [`models/`](models/CONTEXT.md) | Local model checkpoints and weights |
| `outputs/` | Generated artifacts, untracked |

Two files at the root are read before anything else: [`AGENTS.md`](AGENTS.md), the rules that always apply, and [`ROADMAP.md`](ROADMAP.md), what is intended and what was rejected.

## What the enforcement layer buys you

Every item below is a hook that can block, not advice an agent may skip. Each is listed with the failure it exists to prevent, because a rule whose cost you can see and whose benefit you cannot is a rule that gets switched off.

**Navigation — so a big repo does not cost a big context.**

| Feature | What it buys you |
|---|---|
| `CONTEXT.md` chain gate | An agent cannot touch a file in a folder it has not oriented in — including through `cat` and `grep`, which is where the bypass used to be. It arrives knowing the neighbourhood instead of guessing from a filename |
| Interface-first reads | Reading a source file is blocked while its generated stub is current, so the agent reads 30 lines of signatures instead of 200 lines of body. The stubs regenerate on every save, so they cannot go quietly stale |
| Generated routing tables | Each directory's file list writes itself from first-line comments. Nobody maintains an index, and an index nobody maintains is the one that lies |
| Facade discipline | Cross-module imports that reach around `index` / `__init__` are blocked, so module boundaries stay real and a rename does not become an archaeology project |

**Restraint — so the codebase does not rot at agent speed.**

| Feature | What it buys you |
|---|---|
| Size limits (`core/hooks/limits.env`) | Forces graph-shaped design: small single-responsibility files with explicit imports. An agent that cannot grow a file has to actually decompose it |
| Duplication gate | jscpd blocks a commit whose staged files clone existing logic. Copy-paste is the failure mode agents are fastest at |
| `verify:fast` contract | A project declaring the script must be green to commit. Discovered by convention, so a new project opts in by naming a script, not by wiring anything |
| Bug-fix gate | A bug cannot be flipped to FIXED without a matching regression test. "It works now" stops being a claim and becomes a file |
| Spec-locked modules | Editing a module with a locked contract requires having read that contract this session |

**Drift control — so entropy is counted, not felt.**

| Feature | What it buys you |
|---|---|
| The `.md` type system | `UPPERCASE.md` names are a closed allowlist and each answers exactly one question, so there is one place a given fact belongs and inventing a file is a deliberate act. Rules in [`core/SCHEMA.md`](core/SCHEMA.md) |
| Entropy dashboard | Naming, placement, pointer integrity, crowding and size run as deterministic checks over this repo and every nested one, into [`ISSUES.md`](ISSUES.md). A number that must shrink, instead of a feeling that the repo is messy |
| Done work is deleted | Finished items are cut, never ticked. Git is the history, so a roadmap's length measures remaining work rather than accumulated pride |

**Cost — so long sessions stay affordable.**

| Feature | What it buys you |
|---|---|
| [Caveman](core/skills/caveman/CONTEXT.md) | Compresses the agent's own writing ~65% without touching technical content. Off with a sentence when precision matters |
| [rtk](https://github.com/rtk-ai/rtk) | Compresses *tool* output — git, test runners — before it reaches the context. 60-90%, transparent, nothing to type |
| Session close ritual | `/roundup` drains the session's lists into durable files and promotes the branch; `/handoff` writes the next session's opening prompt, and refuses when there is nothing open |

## Features beyond the repo

[`core/tools/`](core/tools/CONTEXT.md) holds CLI tools callable from any agent's bash — no MCP, no per-agent wiring. **The directory is the feature, the file is the provider**, so swapping a vendor changes a leaf and never a family: `mail/gmail`, `calendar/gcalendar`, `files/gdrive`, `slides/gslides`, `docs/gdocs`, `notes/notion`, `web/search`, `paper/papers`, `video/video`.

## Agent support

Claude Code, GitHub Copilot, opencode, and Antigravity all run the same canonical hooks through a thin shim.
Adding another means implementing three hook points against a documented stdin/exit-code contract — see [`core/hooks/SPECS.md`](core/hooks/SPECS.md) § Canonical behaviour, and the contract a new agent's shim must satisfy.

## Cloning it for yourself

Clone the repo, open your own coding agent, and tell it to follow [`SETUP.md`](SETUP.md) — **the harness you already opened is the installer.** There is no `curl | sh` and there is not going to be one: an installer would have to be ported to every agent, while a procedure works on whichever one you have. Every step there declares how to tell it is already done, an idempotent install, and a check that proves it worked, so the agent runs the whole thing and hands you back the short list only you can finish — an API key, a consent screen, a device pairing. Agents with skill support can open the same file with `/install`.

Dependencies are declared in [`core/tools/deps.txt`](core/tools/deps.txt), with what each one's absence *looks like* — the expensive ones do not announce themselves as missing, they just return a worse answer. `core/tools/wos/deps` checks them all.

Installing only a **subset** works: every feature is declared in [`core/features.txt`](core/features.txt), the answers for this machine live in [`core/profile.txt`](core/profile.txt), and `core/tools/wos/features --on|--off <name>` is how one is switched. What crosses into the public copy and what never does is [`core/public.txt`](core/public.txt), which carries its own reasons.
