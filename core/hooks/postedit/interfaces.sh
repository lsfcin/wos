# Regenerate the interface next to the file just edited — .pyi, .d.ts, .dart.api, .texif.
# Sourced by core/hooks/post-edit.sh — a FRAGMENT, not a standalone script:
# it relies on $file, $dir, $TSC and find_tsconfig from the caller.
#
# The second of `interface-stubs`' two paths (core/SPECS.md § AD-14). This half is what
# keeps the stub current WITHIN a session; generators/interfaces.sh is what stages it into
# the commit. Switch off only one and read/pre-read.py silently stops enforcing, because it
# blocks a source read only while the stub beside it is current.
if sh "$RUN" hooks/feature_law.py --enabled interface-stubs; then

# The stub generators live in Python now (stubgen/stubs.py), which is the ONE copy of every
# stubgen and tsc invocation -- the reason the sourced fragment existed at all. These two shims keep
# this file's call sites unchanged while that copy stays single; both resolve the interpreter
# through `run`, so no venv layout is named here.
emit_pyi() { sh "$RUN" hooks/stubgen/stubs.py "$1"; }
emit_dts() { TSC="$2" sh "$RUN" hooks/stubgen/stubs.py "$1"; }

# ── Interface regeneration ──────────────────────────────────────────────────────
case "$file" in
	*.py)
		emit_pyi "$file" && printf "✓ .pyi: ${file%.py}.pyi\n"
		;;
	*.js)
		if [ -n "$TSC" ]; then
			emit_dts "$file" "$TSC" && printf "✓ .d.ts: ${file%.js}.d.ts\n"
		fi
		# jsconfig.json is an EDITOR AID, never a build config — the same role
		# core/tools/wos/sync-global-skills already assigns it. It carried
		# declaration/emitDeclarationOnly/outDir for years and could not honour any
		# of them: a file named jsconfig.json implies noEmit:true, and "outDir": "."
		# lands in tsc's default exclude list, so the config excluded its own
		# directory (TS18003, zero inputs). Declarations are emitted per file, by
		# emit_dts above — one call site now, in core/hooks/stubgen/stub_one.sh.
		if [ ! -f "$dir/jsconfig.json" ]; then
			cat > "$dir/jsconfig.json" << 'EOF'
{
	"compilerOptions": {
		"allowJs": true, "checkJs": false, "target": "ES2020"
	},
	"include": ["*.js"]
}
EOF
			printf "✓ jsconfig.json scaffolded: %s\n" "$dir"
		fi
		;;
	*.ts)
		if [ -n "$TSC" ]; then
			tsconfig=$(find_tsconfig "$dir")
			if [ -n "$tsconfig" ]; then
				proj_root=$(dirname "$tsconfig")
				decl_cfg="$proj_root/tsconfig.declarations.json"
				if [ -f "$decl_cfg" ]; then
					# Project-specific declarations config — handles complex typeRoots (e.g. Foundry VTT).
					# noEmitOnError:false allows partial emission despite unresolved globals; suppress
					# diagnostic noise since errors are expected (Foundry globals are bundler-only).
					"$TSC" -p "$decl_cfg" >/dev/null 2>&1 || true
					printf "✓ .d.ts regenerated: %s\n" "$proj_root"
				else
					emit_dts "$file" "$TSC" && printf "✓ .d.ts: ${file%.ts}.d.ts\n"
				fi
			else
				emit_dts "$file" "$TSC" && printf "✓ .d.ts: ${file%.ts}.d.ts\n"
				# Same outDir-lands-in-exclude defect as the jsconfig template above.
				# noEmit is not implied here — that half is jsconfig's name, not tsc's default.
				cat > "$dir/tsconfig.json" << 'EOF'
{
	"compilerOptions": {
		"declaration": true, "emitDeclarationOnly": true,
		"outDir": ".", "target": "ES2020", "strict": true
	},
	"exclude": []
}
EOF
				printf "✓ tsconfig.json scaffolded: %s\n" "$dir"
			fi
		fi
		;;
	*.csv|*.tsv)
		sh "$RUN" tools/assets/inspect "$file" 2>/dev/null \
			&& printf "✓ .csvif: %sif\n" "$file"
		;;
	*.dart)
		sh "$RUN" hooks/stubgen/dart-api-extract.py "$file" 2>/dev/null
		;;
	*.tex)
		sh "$RUN" hooks/stubgen/tex-interface-gen.py "$file" 2>/dev/null
		# Term consistency check (warn-only; requires terms.yaml in paper root)
		paper_root="$dir"
		while [ "$paper_root" != "/" ] && [ ! -f "$paper_root/terms.yaml" ]; do
			paper_root=$(dirname "$paper_root")
		done
		# No `-x` test any more: the tool lost its execute bit with its shebang, and asking
		# whether a Python file is executable is the POSIX habit that made all 33 of them
		# unrunnable here. Ask whether it EXISTS; `run` answers how to start it.
		if [ -f "$paper_root/terms.yaml" ] && [ -f "$WORKSPACE_ROOT/core/tools/paper/terms" ]; then
			sh "$RUN" tools/paper/terms "$paper_root" 2>/dev/null | grep -E "^[[:space:]]|^⚠" || true
		fi
		;;
	*.bib)
		sh "$RUN" hooks/stubgen/tex-interface-gen.py --bib-check "$file" 2>/dev/null
		;;
esac

fi  # interface-stubs
