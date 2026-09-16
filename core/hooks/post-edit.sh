#!/usr/bin/env bash
# PostToolUse, capability `write` — regenerates interfaces, checks first-line comment, syncs CONTEXT.md

HOOKS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$HOOKS_DIR/../.." && pwd)"
RUN="$WORKSPACE_ROOT/core/run"

input_json="${CLAUDE_TOOL_INPUT:-$(cat)}"

# LEAVE BEFORE STARTING PYTHON. Registered on `.*` -- and it must stay that way, because a matcher
# listing tool names is the whitelist b20260901 retired -- this hook fired on every Grep, Bash and
# TodoWrite, spending an interpreter start and an import chain to ask capability() a question whose
# answer was 'not a write' (0.222 s per ungated tool call, measured 2026-09-05; see
# core/experiments/hook-latency.md).
#
# A SUPERSET TEST, NEVER THE ANSWER. capability() stays the one definition of what a write is; this
# only refuses payloads that cannot possibly be one, by looking for the keys that make a call a
# write in the raw JSON. It can admit a non-write -- the real check below still runs and still
# decides -- and it can never turn a write away, which is the only direction that would be a bug.
case "$input_json" in
	*'"content"'*|*'"new_string"'*|*'"new_source"'*|*'"edits"'*) ;;
	*) exit 0 ;;
esac

# THE INTERPRETER IS ASKED FOR, NEVER SPELLED. This line read `python3` until 2026-08-29, and on a
# Windows clone that word resolves to a Microsoft Store execution alias which prints an advert and
# produces no output. `$file` came back empty, the `exit 0` below fired, and this hook -- with every
# stage it sources -- had never once run here. It failed green, behind the `2>/dev/null` that was
# there to swallow a malformed payload. Nothing downstream could tell the two apart.
PY="$(sh "$RUN" --python)" || exit 0
# Capability, not tool name (b20260901): registered on every tool, so a harness that adds one gets
# the same treatment. `capability` is imported rather than restated -- one definition, in
# hook_input.py, or this file becomes the copy of the law the law modules exist to prevent.
meta=$(echo "$input_json" | "$PY" -c \
	"import sys,json; sys.path.insert(0,'$HOOKS_DIR'); from hook_input import capability; d=json.load(sys.stdin); ti=d.get('tool_input'); ti=ti if isinstance(ti,dict) else d; print(capability(d.get('tool_name',''), ti)); print(ti.get('file_path',''))" 2>/dev/null)
cap=$(printf '%s' "$meta" | sed -n 1p)
file=$(printf '%s' "$meta" | sed -n 2p)

[ "$cap" = "write" ] || exit 0
[ -z "$file" ] || [ ! -f "$file" ] && exit 0

dir=$(dirname "$file")

# Locate tsc (PATH or ~/.local/bin fallback)
TSC=""; command -v tsc &>/dev/null && TSC="tsc"
[ -z "$TSC" ] && [ -x "$HOME/.local/bin/tsc" ] && TSC="$HOME/.local/bin/tsc"

# Walk up to nearest tsconfig.json, stopping at git root
find_tsconfig() {
	local d="$1"
	while [ "$d" != "/" ]; do
		[ -f "$d/tsconfig.json" ] && echo "$d/tsconfig.json" && return
		{ [ -f "$d/.git" ] || [ -d "$d/.git" ]; } && return
		d=$(dirname "$d")
	done
}

# Split 2026-07-31 at 208 lines (the cap is 200). It was never blocked because the
# line-count gate could not see .sh files until file_law.py landed. Parts are SOURCED —
# they share $file, $dir, $TSC, $RUN, $PY and find_tsconfig. Order preserved: lint runs
# last, after interfaces.sh has written the .d.ts it needs.
for part in interfaces reminders sync lint; do
  # shellcheck source=/dev/null
  source "$HOOKS_DIR/postedit/$part.sh"
done
