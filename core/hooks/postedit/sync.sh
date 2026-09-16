# Keep generated indexes fresh: the CONTEXT.md routing block and the codegraph.
# Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script:
# it relies on $file, $dir, $TSC and find_tsconfig from the caller.

# ── Sync the routing blocks: the directory's CONTEXT.md, and the index of a cut type ──
# The FILE is passed, not its directory. Both are needed and only the file carries both: the
# synchronizer derives the directory itself, and a part's index is found from the part's own
# name. Passing "$dir" behind a CONTEXT.md test also meant a workspace-root .md never synced
# at all, since the root's routing block lives in AGENTS.md.
sh "$RUN" hooks/routing/context_synchronizer.py "$file" 2>/dev/null

# ── Sync the skill mirrors: the same job, one directory over ──────────────────
# A skill mirror IS a generated index, so it belongs in this stage rather than a fifth fragment.
#
# THIS IS THE GUARANTEE THAT LETS THE MIRRORS LEAVE GIT (ISSUES.md B8). They are copies of
# core/skills/*.md published where each harness looks, and Lucas's ruling is that generated content
# may be untracked *provided regeneration is automatic*. Until this line existed, a skill edit
# reached the mirrors only at commit time, so an agent that edited a skill and then used it in the
# same session read the OLD body.
#
# WHAT THIS DOES NOT COVER, and it is not a hedge: PostToolUse fires on Edit and Write. Deleting a
# skill is an `rm`, which no hook sees, so a deleted skill's mirrors are pruned at commit by
# `orphans prune` inside sync-skills -- not at the moment of deletion. Install, edit and create are
# immediate; delete is one commit behind. Stated in core/skills/SPECS.md rather than left implied.
#
# AND NONE OF THOSE MOMENTS BELONGS TO THE MACHINE THAT RECEIVES a pull, which is why
# core/hooks/session/mirror-heal.py now carries the same guarantee at SessionStart.
case "$file" in
	"$WORKSPACE_ROOT"/core/skills/*.md)
		sh "$WORKSPACE_ROOT/core/run" tools/wos/sync-skills >/dev/null 2>&1 \
			&& printf '✓ skill mirrors synced\n' \
			|| printf '⚠️  sync-skills failed — run `core/run tools/wos/sync-skills` to see why\n'
		;;
esac

# ── codegraph sync — keep index fresh after every source edit ─────────────────
if [[ "$file" == "$WORKSPACE_ROOT"/code/* ]]; then
	case "$file" in
		*.pyi|*.d.ts|*.dart.api|*.texif|*.csvif) : ;;  # generated — skip
		*.py|*.js|*.ts|*.tsx|*.dart|*.jsx)
			cg_root=""; cg_dir=$(dirname "$file")
			while [ "$cg_dir" != "/" ]; do
				[ -d "$cg_dir/.codegraph" ] && cg_root="$cg_dir" && break
				cg_dir=$(dirname "$cg_dir")
			done
			if [ -n "$cg_root" ]; then
				codegraph sync "$cg_root" 2>&1 | head -1
			else
				proj_root=$(echo "$file" | grep -oP "^${WORKSPACE_ROOT}/code/[^/]+")
				[ -n "$proj_root" ] && printf "⚠️  no codegraph index — run: codegraph init %s\n" "$proj_root"
			fi
			;;
	esac
fi
