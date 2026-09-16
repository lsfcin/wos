# ESLint + Prettier for TypeScript under code/ (R1-R6).
# Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script:
# it relies on $file, $dir, $TSC and find_tsconfig from the caller.

# ── ESLint + Prettier for TypeScript projects under code/ (R1-R6) ─────────────
# The edit-time half of `lint-typescript` (core/SPECS.md § AD-14); gates/lint.sh is the
# commit-time half that blocks. Prettier WRITES the file, so this is the half a switched-off
# feature must really stop — a warn left running would be harmless, a rewrite is not.
if [[ "$file" == "$WORKSPACE_ROOT"/code/* ]] && [[ "$file" == *.ts ]] && [[ "$file" != *.d.ts ]] \
	&& sh "$RUN" hooks/feature_law.py --enabled lint-typescript; then
	# Walk up to nearest eslint.config.js (ESLint 9 flat config = full R1-R6 enforcement)
	proj_dir=""
	_d=$(dirname "$file")
	while [ "$_d" != "/" ]; do
		if [ -f "$_d/eslint.config.js" ]; then
			proj_dir="$_d"
			break
		fi
		_d=$(dirname "$_d")
	done
	if [ -n "$proj_dir" ]; then
		PRETTIER_BIN="$proj_dir/node_modules/.bin/prettier"
		ESLINT_BIN="$proj_dir/node_modules/.bin/eslint"
		if [ -x "$PRETTIER_BIN" ]; then
			(cd "$proj_dir" && "$PRETTIER_BIN" --write "$file" 2>/dev/null) \
				&& printf "✓ prettier: %s\n" "$(basename "$file")"
		fi
		if [ -x "$ESLINT_BIN" ]; then
			LINT_OUT=$(cd "$proj_dir" && "$ESLINT_BIN" "$file" 2>&1 | head -40)
			[ -n "$LINT_OUT" ] && printf "⚠️  ESLint (R1-R6):\n%s\n" "$LINT_OUT"
		fi
	fi
fi
