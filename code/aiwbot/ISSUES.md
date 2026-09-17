# aiwbot — Issues

Log as `- [ ] [bN] <symptom> — <where>`; a FIXED flip needs a `tests/**/b<N>-*`
regression test (see code/VERIFY.md). A fixed bug's entry is DELETED — its regression spec is the
durable proof it is dead, not prose. Findings from a live audit start as notes in the session and
earn a `bN` here only if they survive the round they were found in.

Hand-written bugs only. This directory stopped being its own repo on 2026-09-12, so the entropy
and verification blocks that used to sit below are gone: the workspace's own
[`ISSUES.md`](../../ISSUES.md) scans this tree with everything else, and a second generated copy
of the same scan is the drift those checks exist to catch.

## Open
- [ ] [b6] `frontend/SPECS.md` is the contract the spec gate locks the WHOLE `frontend/` module
  with, and it describes only the audio-in-out voice pipeline. Every surface — turn, stream, text,
  session, select, interview — is edited against a contract that says nothing about it. Renamed
  from `SPEC.md` on 2026-09-12 (the old name is not a type this workspace allows); the name was the
  cheap half. Either the contract grows to cover the module, or the voice half moves to
  `frontend/voice/` and declares itself there.
- [ ] [b5] `/resume` anchor arrives with no last answer, so the message is only the reattach
  command — `frontend/session/sessions.py` `last_response`. Live 2026-08-17 on session
  `949a9cc6` ("PLAN WOS ROADMAP"): `_anchor` does ask for the body
  (`resume.py:143`), `session_block` appends it only `if body` and prints the
  `claude --resume <sid>` line unconditionally (`frontend/text/format.py:103`), so an empty
  `last_response` degrades the anchor into a bare shell command. Lucas: *"n entendi nada. ao meu
  ver era pra aparecer a última resposta da sessão"*. **Find why it returned empty for that
  session before touching the fallback** — a transcript this workspace wrote the same day is the
  easy case, so an empty answer there means the reader is wrong, not the session.

b1–b4 are closed and each is held by a regression spec under `tests/test_b<N>_*.py`; read the spec
rather than a summary of it. One of them still shapes the section below: **b4 was opencode trusting
`$PWD` over its real working directory**, so turns ran their tools in the daemon's launch directory
and filed their sessions there.


## Residual (by design)
- The eight opencode sessions b4 filed under `/home/lucas` stay out of `/resume`, which lists per
  directory and cannot rewrite where a session was recorded. They are reachable from a terminal
  (`opencode` in that directory, then its own picker). Turns from 2026-07-29 on are filed correctly.
- Bot sessions created **before** 2026-07-23 stay invisible in Claude Code's native picker: the filter
  keys on a session's originating entrypoint, which can't be rewritten after the fact. New sessions are
  fine (`CLAUDE_CODE_ENTRYPOINT=claude-vscode`, SPECS AD-8). For the old ones use the copyable
  `claude --resume <id>` shown in the `/resume` anchor.

