# skills
> Agent skills — provider-agnostic workflows invoked as slash commands or by instruction.

`core/skills/<name>.md` is the only place to edit a skill — the `.opencode/skills/`,
`.claude/skills/`, `.zcode/skills/` and `.claude/commands/` mirrors are generated copies that git
does not track.

How to create or edit a skill, the sync commands, the case-sensitivity hazard, what's excluded from
mirroring, and the folder-shaped global-skill pattern (`caveman/`): [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`caveman/`](caveman/CONTEXT.md) | Ultra-compressed communication mode — vendored suite: router skill, mode subfiles, hooks, scripts. |
| [`foundry/`](foundry/CONTEXT.md) | Foundry VTT v14 module dev reference — skill suite. |
| [`prepare/`](prepare/CONTEXT.md) | Prepare a raw prompt for an agent: optimize, contextualize, and recommend level/effort settings. |

| File | Description |
|------|-------------|
| [`SPECS.md`](SPECS.md) | Contract for creating, editing, and syncing a skill, plus the folder-shaped global-skill exception. |
| [`_template.md`](_template.md) | One-line summary of what this skill does and when to invoke it. |
| [`calendar.md`](calendar.md) | List upcoming events and query date ranges from Google Calendar across all configured accounts (personal, cin, ufrpe). |
| [`compass.md`](compass.md) | Gentle strategic review of Brain: what has good wind, reorder by motivation, ditch guilt-free, close wins, next easy start. |
| [`craft.md`](craft.md) | Run the craft flow: develop a feature in file-relayed loops with model autorouting (clarify → plan → ground → architecture → TDD → code → user test → ship). |
| [`dedup.md`](dedup.md) | Semantic duplication audit for a code project, defaulting to the one in the working directory: near-duplicate logic that the verbatim-clone gate misses. |
| [`drive.md`](drive.md) | List, search, and download files from Google Drive across all configured accounts (personal, cin, ufrpe). |
| [`foundry.md`](foundry.md) | Foundry VTT v14 module dev reference — router. Load relevant subfiles before working. |
| [`gdocs.md`](gdocs.md) | Read and edit Google Docs in place across all configured accounts — markdown round trip or surgical batchUpdate, comments included. |
| [`gforms.md`](gforms.md) | Google Forms as versioned specs: create, edit and read answers across all configured accounts — a form written as JSON, applied in one call. |
| [`gmail.md`](gmail.md) | Triage Gmail across all configured accounts — classify, confirm routes, write to brain/INBOX.md. |
| [`gslides.md`](gslides.md) | Read and edit Google Slides decks in place across all configured accounts — deck as navigable text, edits through batchUpdate. |
| [`handoff.md`](handoff.md) | Emit a copy-pasteable resume prompt for the next session. For the full session-close ritual use /roundup, which calls this. |
| [`inbox.md`](inbox.md) | Triage brain/INBOX.md — route each entry to a goal, task, reference, project doc, writing draft, or delete. Cross-domain front door: reaches into code ROADMAP/ISSUES and domain refs/, not just brain/. |
| [`install.md`](install.md) | Install this workspace on the machine you are running on: check every step in SETUP.md, report what is missing, and execute it. Takes one feature short name, or nothing for everything. |
| [`iso-visual.md`](iso-visual.md) | Isoroll visual-semantics reference: image-to-text conventions, known model failure modes, and how to verify visual output. Load before touching isoroll guides, kits, sprites or scenes. |
| [`prepare.md`](prepare.md) | Turn a raw task into an optimized agent prompt: interviews for intent, classifies the task, recommends model and effort. |
| [`research.md`](research.md) | Execute a research workflow from the workspace Core research system. |
| [`roundup.md`](roundup.md) | Full session-close ritual: drain the lists, route session knowledge to durable files, then verify and hand off. Use at session end. |
<!-- routing:end -->
