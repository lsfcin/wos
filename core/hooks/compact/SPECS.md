# compact — Specs
> What the rtk shim may rewrite, what it must leave alone, and the two harness facts it rests on.

Companion to [`CONTEXT.md`](CONTEXT.md), which says what this directory is and routes into it.

## Why a shim sits in front of `rtk hook claude`

rtk parses the **first line** of a Bash payload and nothing else, and when that line is not
rewritable it declines the whole call. Measured over 5,628 Bash calls in this workspace's
transcripts (2026-08-15):

| Shape | Before the shim |
|---|---|
| `git status` | rewritten |
| `cd x; git status` (one line) | both rewritten |
| `cd x` ⏎ `git status` | **nothing** rewritten |
| `git status` ⏎ `ls -la` | line 1 only |

**23.4% of calls open with `cd`**, spending rtk's single shot on it, and **1,249 rewritable commands
sit on lines 2+** — 783 of them `git`. Single-line `;` and `&&` chains were never affected.

## The safety contract

**The shim must never reshape shell it cannot read.** It splits a payload only when every line
stands alone as a simple command; a heredoc, a block keyword, a line continuation or an odd quote
count sends the untouched payload to `rtk hook claude` and passes its verdict through unchanged.

**The bail is always the safe direction.** Failing to compact costs tokens; corrupting a command
costs correctness. The live example the tests hold: a commit message quoted across two lines, whose
second line begins with a word that is also a command name — split naively, writing becomes an
executable. Risk cases in `core/tools/test/workspace/gates/test_bash_compact_rewrite.py` deliberately
outnumber success cases.

**A missing binary must fail open.** Compaction is an optimisation, so no rtk means the command runs
exactly as written, never blocked and never altered.

## Where the shim is registered, and why exactly once

**`~/.claude/settings.json`, never the project file.** Claude Code merges hooks across settings
scopes and runs *all* matches, so a project entry does not replace a global one — it runs beside it.
For weeks both `rtk hook claude` (global) and this shim (project) fired on every Bash call, returning
two competing `updatedInput` values for a payload both could rewrite, with no documented precedence.

Registering globally also covers sessions started **inside nested `code/*` repos**, which carry no
project settings of their own and would otherwise get line-1-only compaction. The one-line
registration and the check that verifies it: [`SETUP-compaction.md`](../../../SETUP-compaction.md)
§ RTK — Claude Code registration.

## Three undocumented harness facts this rests on

All verified by experiment on Claude Code 2.1.218, none stated in the hooks documentation:

1. `PreToolUse` **does** apply `hookSpecificOutput.updatedInput`.
2. It does so **without** requiring `permissionDecision: "allow"` — checked with two check hooks
   differing in exactly that field; both rewrote. This matters beyond convenience: setting `allow`
   to buy a rewrite would auto-approve every command the shim touches, so not needing it keeps
   compaction out of the permission system entirely.
3. **Hooks matching the same tool in different settings scopes all fire.** Scope selects *whether* a
   hook runs, never which one wins.

**Why the double-wiring never corrupted a command: rtk is idempotent.**
`rtk hook check "rtk grep foo ."` returns it unchanged, so a second pass over an
already-rewritten payload is a no-op rather than `rtk rtk grep`. That is a property of rtk, not a
guarantee this repo owns — which is precisely why the wiring was reduced to one registration instead
of being left to it.

## Compaction is invisible in the chat, by design

Nothing tells the model to type `rtk grep` — `rtk init --show` reports `RTK.md: not found` and both
`CLAUDE.md` files as unconfigured, because commit `804ab0a` moved that writing out. The model sends a
plain command, the hook rewrites it afterwards, and the UI renders **what was sent**. So a session
shows no sign of compaction even when it is working perfectly.

This once read as "rtk stopped running". It is not evidence of anything: the visible `rtk` prefix
and the rewrite are two different mechanisms, and only the first was ever removed. Use the counter
below, never the chat.

## The adoption counter

The shim appends one `verdict\tlines` row per Bash call to `/tmp/claude_rtk_compact_<session_id>.tsv`
— verdict ∈ `split-rewrote` · `split-noop` · `delegated-rewrote` · `delegated-noop` · `no-rtk`.
`core/tools/wos/roundup` reads it at session close and prints the share rewritten.

It exists because **this bug would have read as a flat zero on day one** and nothing was watching.
`rtk gain` measures tokens *saved* and cannot see this: it only counts rewrites that ran, so a shim
reaching no commands at all looks identical to one that is merely idle. Adoption and savings are
different questions and need different instruments.

Ephemeral by design — per session, in `/tmp`, same store convention as `hook_input.seen_file()`.
The **trend** belongs in `core/experiments/`, not in a file that would churn git on every command.
Writing a row must never be able to break the command being counted, so every failure there is
swallowed.

Upstream reports the opposite of both at various versions (`claude-agent-sdk-python#381`, open;
`claude-code#15897`, closed then observed fixed in 2.1.168), so this is version-dependent.
**Re-test after a harness upgrade, and never by re-reading configuration** — run a command through a
live session and watch `rtk gain`'s counter move. The configuration looked correct for weeks while
every multi-line call went uncompacted, and the delta test that first caught it was itself misread,
because the test payload was written in the same multi-line style that was the bug.
