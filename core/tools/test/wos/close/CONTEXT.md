# close
> Coverage for the session-close ritual: what the script really does, and what the skills claim.

Split from [`../`](../CONTEXT.md) 2026-08-25, when the size tool pushed that directory past the crowding signal — the same mirroring rule [`../diagram/`](../diagram/CONTEXT.md) follows, so the file testing a surface is found by knowing the name of the surface. What stayed next door asks whether the workspace's **declarations** agree with each other; everything here asks what happens when a session ends.

**One ritual, two layers, and they fail differently.**
[`test_roundup.py`](test_roundup.py) runs the real script against throwaway workspaces — a fake `core/tools/wos/roundup` inside a tmp repo, so `ROOT` equals `WORKSPACE` and the gitflow and entropy paths are reachable at all. [`test_roundup_skills.py`](test_roundup_skills.py) guards what cannot be asserted in bash: that the skill does not re-inline the work the script took over, that it counts the INBOX rather than draining it at the most expensive turn, and that neither skill names the state lines the script prints. [`test_size.py`](test_size.py) covers the number the close leads with.

Zero-token, no network. Each test builds its own repo and bare origin; nothing touches the real workspace.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_handoff.py`](test_handoff.py) | [`test_handoff.pyi`](test_handoff.pyi) | `repo`, `log`, `patch` | One handoff per repository: sections accumulate until a session takes them, and taking deletes. |
| [`test_roundup.py`](test_roundup.py) | [`test_roundup.pyi`](test_roundup.pyi) | `held`, `close` | T1 roundup tool (core/hooks/git/SPECS.md § Close): every repo this session holds goes back to develop. Zero-token, no network — each case builds a throwaway repo with a bare origin, held through the real lock, and runs the real script on it. |
| [`test_roundup_skills.py`](test_roundup_skills.py) | [`test_roundup_skills.pyi`](test_roundup_skills.pyi) | — | T0 the session-close skills (core/SPECS.md § AD-09): what bash cannot assert about the other layer. Zero-token, no network. |
| [`test_size.py`](test_size.py) | [`test_size.pyi`](test_size.pyi) | — | T1 size tool (ROADMAP.md § Cost): whether the workspace got smaller this session, and where. Zero-token, no network — every case builds its own throwaway repo. |
<!-- routing:end -->
