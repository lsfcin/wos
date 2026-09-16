# Tools — Specs
> What must be true of a `core/tools/` feature, and why: how a family is named, what a
> failure has to hand back, and what work is the agent's rather than Lucas's.

Companion to [`CONTEXT.md`](CONTEXT.md), which says what this directory *is* and routes into it.
These are the constraints. They live here rather than in the head because `CONTEXT.md` is the only
enforced-read type — every session touching this folder pays for its head, while this file is read
on demand (core/SCHEMA.md § Placement).

## Naming: the directory is the feature, the file is the provider

**A family directory is the feature; the tool inside it is the provider.** `mail/gmail`,
`calendar/gcalendar`, `files/gdrive` — swapping a provider changes a leaf, never a family. This is
the workspace's provider-agnostic rule applied to the path: function in the directory, vendor at the
file.

Two sweeps have already renamed every tool path here, so **a third is not free** — check
[`ROADMAP.md`](../ROADMAP.md) before proposing one.

`auth/` is a family because it is shared across families rather than owned by any. A module imported
by more than one family belongs at this root; a module imported by exactly one belongs beside its
tool. That rule is why exactly one file sits at the root.

## An auth failure names its own fix — relay it verbatim

A dead token makes `gauth.auth()` raise `AuthExpired`, and every CLI entrypoint prints it through
`gauth.run()` instead of a traceback. That message is written **for Lucas** and already carries the
exact command *and* the address to sign in as. **Show it to him unchanged — do not paraphrase it,
and never say "you need to re-auth" on its own.**

Why the address is in the message and not in this file: Lucas has several Google accounts, so
"re-authenticate" without one is an instruction he cannot act on, and a wrong account is worse than a
failure — it authenticates fine and then reads the wrong mailbox or drive. The address is read at
runtime from `accounts.json`, so it cannot go stale here.

**Run the re-auth command yourself** — backgrounded, since it blocks until consent lands. It opens a
browser on Lucas's machine, so the only part that is his is picking the account on the consent
screen. Handing him the command to type is a chore the agent could have absorbed.

**That rule is provider-agnostic, and every new tool inherits it without asking again.** Lucas does
*only* what cannot be done from here — a click inside the provider's own UI, a consent screen, a
secret minted inside his account. Everything with a command form is the agent's, and a secret he
pastes into the conversation is stored through a builtin pipe so it never reaches argv:

```bash
printf '%s\n' '<secret>' | core/tools/<family>/<tool> auth <alias>
```

`notes/notion` is the non-OAuth shape of the same split. Tokens are per `(service, alias)` at
`~/.config/workspace-<service>/<alias>.token.json`; Drive writes (`mkdir`, `put`) use a separate
`drive-write` token from the read one.

## Adding a tool

1. Name the file for its **provider**, and put it in the directory named for the **feature** it
   delivers. Never a file at this root.
2. Create the family directory only when the tool actually lands in it — no empty `sheets/`,
   `docs/`, `maps/` waiting for a someday tool.
3. Give a family its own `CONTEXT.md` only once it holds more than one file. A one-tool family folds
   into the parent's routing table: one path hop, zero extra rows. Declaring itself early costs the
   reader a routing table that says nothing — `auth/` is the live example of the cheap side.
4. Add `# Usage: core/run tools/<family>/<name> <args> — <description>` as the **first line**.
5. Give it **no shebang and no execute bit** — `core/run` starts it. See § The interpreter below.
6. Declare any new third-party dependency in [`deps.txt`](deps.txt) — see § Declared dependencies.
7. Every Google-backed family gets a skill wrapper in `core/skills/` (ruled 2026-08-31, Lucas: add
   where missing, never half) — `gmail`, `gcalendar`, `gdrive`, `gslides`, `gforms`, `gdocs` set.
8. Save — the routing block regenerates automatically.

## The one capability with no CLI wrapper

`subagent` is the single runtime-specific thing this tree offers, so it has no file here: one
harness spawns a worker with its Agent tool, passing `core/agents/<name>.md` as the system prompt,
while Feynman and Pi take a JSON task spec through their own `subagent` tool. Wrapping it would mean
a tool that works on one machine's runtime and returns nothing on another's.

## Declared dependencies

Every external thing the tool surface needs is one row in [`deps.txt`](deps.txt): what installs it,
what checks it, which feature owns it, and **what its absence looks like**. `core/tools/wos/deps`
runs the checks; `core/tools/test/wos/test_deps.py` fails on any third-party import missing a row.

**Why the `breaks` column is the point.** These deps were found because four of them had been
installed by hand into `.venv` and never written down, so a fresh clone lost the feature
*silently* — the tool did not crash, it returned a worse answer. The expensive one cost a full
session: without `secretstorage`, yt-dlp fails with `failed to decrypt cookie (AES-CBC) ... Possibly
the key is wrong?`, which reads like a wrong password and is a missing module. A dependency list
that only names packages would not have saved that session; one that names the *symptom* does.

**The import half is enforced, the binary half is declared.** An ast walk cannot be fooled about
imports, so a new `import` fails the suite until it is declared. A binary invoked through a shell
string (`pandoc`, `ffmpeg`, `pdftotext`, `flutter`) cannot be found by any scan, so those rows are
kept honest by their check alone. Do not let the file imply otherwise.

## The interpreter

**A tool runs under the workspace venv, never under whatever python the caller happens to have.**
The venv holds the declared dependencies; the system interpreter holds none of them. Sixteen tools
carried `#!/usr/bin/env python3` and worked only because sessions happened to start with the venv
active — `core/tools/paper/terms` imports `yaml`, and the pre-commit term gate that calls it would
have skipped silently on a clean machine.

**A tool is spawned as `core/run tools/<family>/<leaf>`, and carries no shebang at all.** The
launcher asks the filesystem which venv layout is present — the POSIX one or
`.venv/Scripts/python.exe` — so the interpreter is answered once, for gates and tools alike.

**A shebang here would be a per-machine value in a versioned file**, since a shebang cannot
resolve a relative path and would have to name this clone's venv absolutely. That is the defect
[`core/hooks/SPECS.md`](../hooks/SPECS.md) says `run` exists to remove, so a tool carrying one puts
the two specs in direct contradiction — the state this workspace was in until the port reached
these files.

**A check whose evidence is the defect cannot report it.** While the shebang was the convention,
`is_code_file` read it as proof a file was live code and the extensionless law read it as proof the
name was deliberate — so all 33 tools were unrunnable on any clone but one, and every check that
looked at them passed. Both laws ask about shape now; `file_law.is_tool_entrypoint` is the one
definition.

## A step an agent must never skip has to cost one call

**If a step is mandatory, its tool takes the whole batch.** A tool that handles one item at a time
turns a mandatory step into N decisions, and an agent mid-thread will take the exit at some N.

The evidence cost two rounds of wording. `core/skills/inbox.md` ordered link extraction in
emphatic writing — *"not optional and not a judgement call"*, plus an explicit instruction to loop
in a single bash call — and the step was still skipped, because `core/tools/video/video` took
`args[0]` and a drain with eight links was eight invocations. **The instruction was never the
defect.** Rewriting it a third time would have failed the same way; the tool learned `--from
<file>` instead, and the decision count went from N to one.

So a tool that a skill *requires* is designed batch-first: many arguments or a file to read them
out of, one block of output per item, a summary line naming the failures, and **no item's failure
ends the run**. This is the one-action rule for agent-facing text pointed at the tool rather than
at the text — the text can only name one action if the tool offers one.

## A provider without OAuth

The decision — that the module holding the secret lives in the family rather than in `auth/` — is
[`core/SPECS.md`](../SPECS.md) § AD-12. Its two consequences moved here on 2026-09-06 because they
constrain **how a tool is written**, not where a module sits, and a rule belongs beside the code it
governs.

**The split is the Google split; what changes is which half belongs to whom.** For any provider,
**Lucas does only what has no command form** — a click in the provider's UI, a consent screen, a
secret minted inside his account (his correction, 2026-08-14: *"run it for me and ask me to do only
what only I myself can do"*). The secret enters through **stdin** via a builtin pipe, never as an
argument: argv is readable by any process of the user and survives in shell history.

**A 404 is a sharing failure until proven otherwise**, because the same code means "not connected to
this integration" and "no such id", and the first is far more common — content is *invisible* to the
integration, not forbidden. The message says so in that order.
