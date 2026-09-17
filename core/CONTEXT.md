# Core
> Agent library: skills, agents, prompts, flows, tools. Provider-agnostic.

**Runtime-agnostic** — no provider-specific code. Skills invoke via `/skill-name`. Tools call via
bash. Flows orchestrate agents. `agents/lead.md` is the entrypoint for any research task; it plans
and spawns the specialist workers beside it.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`agents/`](agents/CONTEXT.md) | Agent definitions; load as system prompt to spawn a specialist worker. |
| [`flows/`](flows/CONTEXT.md) | Workflow protocols; each names the agents and steps to execute. |
| [`hooks/`](hooks/CONTEXT.md) | The enforcement layer: git hooks, agent lifecycle hooks, and the Level 0 checks they run. |
| [`norms/`](norms/CONTEXT.md) | Rules obeyed rather than enforced. One file each; `AGENTS.md`'s rule block is generated from them. |
| [`refs/`](refs/CONTEXT.md) | Captured references for the agent library / workspace-os scaffold — level-1 links in [REFS.md](refs/REFS.md). |
| [`skills/`](skills/CONTEXT.md) | Agent skills — provider-agnostic workflows invoked as slash commands or by instruction. |
| [`tools/`](tools/CONTEXT.md) | CLI tools callable via bash, one directory per family; routing block auto-synced on save. |

| File | Description |
|------|-------------|
| [`SCHEMA-layers.md`](SCHEMA-layers.md) | The frontmatter every skill, agent, norm and flow declares, and how they compose. The document law — types, placement, cutting, vocabulary — is the index, [`SCHEMA.md`](SCHEMA.md); this part is the prompt-loaded half, because a `.md` a session reads and a frontmatter block a runtime parses are two different contracts. |
| [`SCHEMA.md`](SCHEMA.md) | The law about `.md` documents: which types exist, where a file belongs, how one that outgrew the cap is cut, and which words are canonical. The **tables here are load-bearing** — [`schema_law.py`](hooks/schema_law.py) parses them and no checker restates them. Drift is a bug. |
| [`SPECS.md`](SPECS.md) | Architecture decisions and conventions for the Core agent library. |
| [`features.txt`](features.txt) | Every toggleable feature this workspace has, declared: what group it belongs to, how hard it enforces, whether it is general or Lucas-specific, and whether it can actually be switched off. Read by core/hooks/feature_law.py; the answers live in core/profile.txt. |
| [`harnesses.txt`](harnesses.txt) | Supported agent harnesses and their relative skill mirror locations name	skills_dir	commands_dir |
| [`levels.txt`](levels.txt) | What KIND OF WORK gets which level. The horizontal axis; core/tools/wos/levels is the vertical one — which concrete model fills a level, per harness — and that is the ONLY place a model id appears. A level is a capacity, never a vendor's product name (core/hooks/entropy/entropy_vendor.py). |
| [`permissions.txt`](permissions.txt) | Neutral permission levels: what an agent may do without asking. Tab-separated columns: kind   level | rule level   guarded | standard | open key    summary | tradeoff | mode (for kind=level); allow | ask | deny (for kind=rule) value  prose (for kind=level); neutral action name (for kind=rule) |
| [`profile.txt`](profile.txt) | Which features are switched on by default, and the settings that are not switches. The registry is core/features.txt; this file holds only the answers. Read by core/hooks/feature_law.py. |
| [`public.txt`](public.txt) | Which trees may cross into the public repo at all, and where it is checked out. Read by core/tools/wos/publish/crossing.py; the per-feature half of the answer lives in core/features.txt. |
| [`run`](run) | The one command that runs anything in core/: find this clone's interpreter, then exec with it. |
<!-- routing:end -->
