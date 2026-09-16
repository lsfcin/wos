# skills — Specs
> Contract for creating, editing, and syncing a skill, plus the folder-shaped global-skill exception.

## Creating a skill

1. Copy [`_template.md`](_template.md) → `<name>.md` (lowercase, kebab-case).
2. Fill the YAML frontmatter: `name`, `description` — `description` is the menu text an agent sees,
   so keep it actionable. `sync-skills` validates both and reports whichever is missing.
3. Write the body: terse, prescriptive instructions the model follows when the skill fires.
4. Nothing. Saving the file regenerates the mirrors — `core/hooks/postedit/sync.sh` runs the sync on
   any write under `core/skills/`. To do it by hand anyway: `core/run tools/wos/sync-skills`, then
   `core/run tools/wos/sync-skills --check` to confirm nothing is stale. (The launcher dispatches
   on the shebang, so the bash tools run as bash.)

After sync the skill is invocable in every program: `/skill-name [args]`, or by natural-language
trigger matching `description`.

## Editing an existing skill

Edit `core/skills/<name>.md`. That is the whole procedure — the save regenerates.

**The mirrors are generated copies and git does not track them** (the `.gitignore` mirror block
holds the 2026-08-29 ruling, and the guarantee it rides on is the post-edit sync below). One
source, four published copies, because every harness looks in its own directory. Never edit a
mirror: the next sync overwrites it, and `--check` compares by content, so the edit is reported as
`STALE` against the source rather than kept.

### What regeneration actually covers, and the one gap

| Moment | Covered by | Immediate? |
|--------|-----------|------------|
| install / fresh clone | `SETUP-clone.md` § Skill mirrors | yes |
| edit a skill | `core/hooks/postedit/sync.sh` | yes |
| create a skill | `core/hooks/postedit/sync.sh` | yes |
| **delete a skill** | `orphans prune`, inside the pre-commit generator | **no — one commit behind** |

Delete is the gap and it is structural, not an oversight: PostToolUse fires on Edit and Write, and
removing a skill is an `rm`, which no hook observes. So a deleted skill's copies survive in the
mirrors until the next commit prunes them, and until then the harness still lists a skill whose
source is gone. If that matters in the moment, run the sync by hand.

## Case-sensitivity

Linux is case-sensitive; the source directory is `core`, lowercase. A hand-built symlink target
spelled `Core/...` dangles — that was the root cause of a `Failed to parse skill` error on opencode
startup. `sync-skills` computes every target path itself now, so the hazard survives only for a
symlink built by hand outside the tool.

## Excluded from mirroring

`_template.md`, `*.original.md` (caveman-compress backups), and `CONTEXT.md` are excluded;
`sync-skills` skips them. `SPECS.md` is not on that exclusion list yet — this file is the first
instance in `core/skills/`, and it exposes the gap: `core/tools/wos/skills/mirror.py`'s `is_skill()`
will read it as an unregistered skill (no frontmatter) until `SPECS` is added there too.

## Global (folder-shaped) skills

A skill needed in every project, not only this workspace, lives as a directory with its own
`SKILL.md`, subfiles, hooks and scripts, instead of a flat `core/skills/<name>.md` — `caveman/` is
the case. `sync-skills` globs flat `core/skills/*.md`, so a directory is invisible to it by
construction; exposure runs through `core/tools/wos/sync-global-skills` instead. One registration per
skill: giving a global skill a flat `core/skills/<name>.md` too would register the same name twice,
once per project scope and once per user scope. Worked example, the `$HOME` wiring, and the sync
commands: [`caveman/CONTEXT.md`](caveman/CONTEXT.md) and [`caveman/SPECS.md`](caveman/SPECS.md).
