# close
> Coverage for the session-close ritual: what the script really does, and what the skills claim.

Split from [`../`](../CONTEXT.md) 2026-08-25, when the size tool pushed that directory past the
crowding signal — the same mirroring rule [`../diagram/`](../diagram/CONTEXT.md) follows, so the file
testing a surface is found by knowing the name of the surface. What stayed next door asks whether
the workspace's **declarations** agree with each other; everything here asks what happens when a
session ends.

**One ritual, two layers, and they fail differently.**
[`test_roundup.py`](test_roundup.py) runs the real script against throwaway workspaces — a fake
`core/tools/wos/roundup` inside a tmp repo, so `ROOT` equals `WORKSPACE` and the gitflow and entropy
paths are reachable at all. [`test_roundup_skills.py`](test_roundup_skills.py) guards what cannot be
asserted in bash: that the skill does not re-inline the work the script took over, that it counts
the INBOX rather than draining it at the most expensive turn, and that neither skill names the state
lines the script prints. [`test_size.py`](test_size.py) covers the number the close leads with.

Zero-token, no network. Each test builds its own repo and bare origin; nothing touches the real
workspace.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`test_b20260831_scattered_lists_never_push.py`](test_b20260831_scattered_lists_never_push.py) | [`test_b20260831_scattered_lists_never_push.pyi`](test_b20260831_scattered_lists_never_push.pyi) | `roundup` | b20260831 regression — a project's commits reach its remote, and the session close is where. |
| [`test_b20260911_a_session_s_approvals_drift_the_rendered_permission_config.py`](test_b20260911_a_session_s_approvals_drift_the_rendered_permission_config.py) | [`test_b20260911_a_session_s_approvals_drift_the_rendered_permission_config.pyi`](test_b20260911_a_session_s_approvals_drift_the_rendered_permission_config.pyi) | — | b20260911 regression — the close re-renders the permission config the session drifted. |
| [`test_projects_map.py`](test_projects_map.py) | [`test_projects_map.pyi`](test_projects_map.pyi) | `repomap` | T1 the projects map (PROJECTS.md): what a redraw fills in, never erases, and when it may commit. |
| [`test_roundup.py`](test_roundup.py) | [`test_roundup.pyi`](test_roundup.pyi) | — | T1 roundup tool (core/SPECS.md § AD-09): the deterministic half of the session-close ritual. Zero-token, no network — every case builds its own throwaway repo. |
| [`test_roundup_skills.py`](test_roundup_skills.py) | [`test_roundup_skills.pyi`](test_roundup_skills.pyi) | — | T0 the session-close skills (core/SPECS.md § AD-09): what bash cannot assert about the other layer. Zero-token, no network. |
| [`test_size.py`](test_size.py) | [`test_size.pyi`](test_size.pyi) | — | T1 size tool (ROADMAP.md § Cost): whether the workspace got smaller this session, and where. Zero-token, no network — every case builds its own throwaway repo. |
<!-- routing:end -->
