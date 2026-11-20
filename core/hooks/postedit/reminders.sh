# Reminders, never blocks: first-line description, facade boundary, CONTEXT.md line 2 and goal link.
# Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script:
# it relies on $file, $dir, $TSC and find_tsconfig from the caller.

# ── First-line description reminder ────────────────────────────────────────────
if [ "$CLAUDE_TOOL_NAME" = "Edit" ]; then
	first=$(head -1 "$file" 2>/dev/null)
	missing=false
	case "$file" in
		*.py)                   echo "$first" | grep -qE '^\s*#'    || missing=true ;;
		*.js|*.ts|*.tsx|*.dart) echo "$first" | grep -qE '^\s*//'   || missing=true ;;
		*.css|*.scss)           echo "$first" | grep -qE '^\s*/\*'  || missing=true ;;
		*.html)                 echo "$first" | grep -qE '^\s*<!--' || missing=true ;;
		*.yaml|*.yml|*.toml)    echo "$first" | grep -qE '^\s*#'   || missing=true ;;
		*.tex)                  echo "$first" | grep -qE '^\s*%'   || missing=true ;;
		*.md)                   echo "$first" | grep -qE '^\s*#'   || missing=true ;;
	esac
	$missing && printf "💬 FIRST-LINE MISSING: %s\n   Add a description comment as line 1.\n" "$file"
fi

# ── Facade reminder ────────────────────────────────────────────────────────────
case "$file" in
	*.ts|*.tsx|*.js|*.jsx|*.py|*.dart)
		has_facade=false
		for _f in "$dir/index.ts" "$dir/index.tsx" "$dir/index.js" "$dir/__init__.py" "$dir/index.dart"; do
			[ -f "$_f" ] && has_facade=true && break
		done
		if ! $has_facade; then
			_n=$(find "$dir" -maxdepth 1 -type f \
				\( -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.py" -o -name "*.dart" \) \
				! -name "index.*" ! -name "__init__.py" ! -name "*.d.ts" ! -name "*.pyi" \
				2>/dev/null | wc -l)
			[ "$_n" -ge 1 ] && printf "💬 NO FACADE: %s has %d file(s) — add index.ts / __init__.py / index.dart\n" "$dir" "$_n"
		fi
		;;
esac

# ── CONTEXT.md line-2 description reminder ─────────────────────────────────────
if [ "$(basename "$file")" = "CONTEXT.md" ]; then
	line2=$(sed -n '2p' "$file" 2>/dev/null)
	printf '%s' "$line2" | grep -qE '^>\s*\S' \
		|| printf "💬 CONTEXT.md DESCRIPTION MISSING: %s\n   Add '> One-line description' as line 2.\n" "$file"
fi

# ── CONTEXT.md project-goal-link reminder — code/<proj>/CONTEXT.md only ───────
if [ "$(basename "$file")" = "CONTEXT.md" ] && [ "$(dirname "$dir")" = "$WORKSPACE_ROOT/code" ]; then
	line3=$(sed -n '3p' "$file" 2>/dev/null)
	printf '%s' "$line3" | grep -qE '^>\s*goal:\s*(\[[^]]+\]\([^)]+\)|none)\s*$' \
		|| printf "💬 CONTEXT.md GOAL LINK MISSING: %s\n   Add '> goal: [name](../../brain/goals/<name>.md)' or '> goal: none' as line 3.\n" "$file"
fi
