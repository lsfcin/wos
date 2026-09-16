// Workspace policy plugin for opencode.
// Runs the SAME workspace behavioral policies as every other harness, through the same three
// entrypoints:
//   - dispatch.py         : every PreToolUse gate, selected by capability (core/hooks/gates.txt)
//   - post-edit.sh, facade-tracker.py, context-tracker.py : the PostToolUse trackers
//   - precompact-wipe.py  : wipe seen-markers on experimental.session.compacting
//
// The core/hooks/* scripts remain the single source of truth. This plugin only TRANSLATES
// opencode's tool.execute.before/after events into the stdin-JSON + CLAUDE_TOOL_NAME/
// CLAUDE_TOOL_INPUT env schema the scripts already expect, and maps Claude exit-2 to opencode
// throw. It used to translate the gate LIST as well — six numbered steps keyed on opencode's tool
// names, one of five such copies across the harnesses — until core/hooks/dispatch.py made the
// capability the only question (b20260905). Translation helpers live in ../wp-helpers.js (kept
// out of plugins/ so opencode does not auto-load them as a plugin).
//
// Every payload carries a session-stable id (`opencode<host-pid>`, the Copilot
// pattern) and every spawn asks core/run for the interpreter — the platform boundary —
// never the bare word python3. Full event->script mapping, stdin-vs-env schema,
// and the warning-surfacing limitation are documented in ../CONTEXT.md.

import { spawnSync } from "node:child_process"
import {
  HOOKS, TOOL_MAP, SESSION_ID, WORKSPACE,
  python, buildPayloads, buildGrepPayload, run, warn,
} from "../index.js"

function blockMsg(r, fallback) {
  return `${r.stdout || ""}${r.stderr || ""}`.trim() || fallback
}

export const WorkspacePolicy = async ({ client }) => {
  // The `opencode-plugin` switch (core/SPECS.md § AD-14). Asked through
  // feature_law.py's --enabled arm, which exists so a second harness reaches the same
  // registry without a second implementation of it. Off = register no hooks at all,
  // which is the honest observable: opencode runs with none of the canonical gates.
  // The interpreter comes from core/run --python (the platform boundary): the bare word
  // `python3` is the spelling that silently disables the whole plugin on a Windows
  // clone — the Store alias prints an advert, exits 9009, and the check reads as "off".
  const py = python()
  if (!py) return {}
  const on = spawnSync(py, [`${HOOKS}/feature_law.py`, "--enabled", "opencode-plugin"], {
    encoding: "utf8",
  })
  if (on.status !== 0) return {}
  return {
    // TRANSLATE, THEN HAND OVER. Which gates run, in what order, was spelled out here in six
    // numbered steps — a hand-copy of core/hooks/gates.txt keyed on opencode's tool NAMES, which
    // is the whitelist b20260901 retired. This handler now does only what a shim is for: turn
    // opencode's args into a canonical payload and let core/hooks/dispatch.py read the capability
    // off it. bash and grep still need their own branch because their target is a `command` and a
    // `path` rather than a `file_path`, which is a translation, not a policy.
    "tool.execute.before": async (input, output) => {
      const args = output.args || {}
      let payloads = []
      let canonical = ""

      if (input.tool === "bash") {
        const command = args.command || args.cmd || ""
        if (!command) return
        payloads = [{ command, session_id: SESSION_ID }]
        canonical = "Bash"
      } else if (input.tool === "grep") {
        const p = buildGrepPayload(args)
        if (!p) return
        payloads = [p]
        canonical = "Grep"
      } else {
        const m = TOOL_MAP[input.tool]
        if (!m) return
        payloads = buildPayloads(args, input.tool)
        canonical = m.canonical
      }

      for (const p of payloads) {
        const r = run(`${HOOKS}/dispatch.py`, p, canonical, { stdin: true })
        if (r.status === 2) throw new Error(blockMsg(r, "blocked by a workspace gate"))
        if (r.stdout && r.stdout.trim()) await warn(client, r.stdout)
      }
    },

    "tool.execute.after": async (input, output) => {
      const m = TOOL_MAP[input.tool]
      if (!m) return
      // `after` carries args on `input.args` (per @opencode-ai/plugin types).
      const payloads = buildPayloads(input.args || output.args || {}, input.tool)
      if (payloads.length === 0) return

      // WHICH GATES RUN IS NOT DECIDED HERE — the same rule the `before` handler already follows.
      // This branch named facade-tracker.py and context-tracker.py itself until 2026-09-06: a
      // hand-copy of the two `post read` rows in core/hooks/gates.txt, keyed on the group, drifting
      // the moment either side changed (b20260905). dispatch.py reads the moment off the payload.
      // post-edit.sh cannot join that table — its rows are imported into the dispatcher's own
      // process and post-edit.sh is bash — so it keeps this spawn.
      const msgs = []
      for (const p of payloads) {
        const d = run(`${HOOKS}/dispatch.py`, { ...p, hook_event_name: "PostToolUse" },
                      m.canonical, { stdin: false })
        if (d.stdout && d.stdout.trim()) msgs.push(d.stdout.trim())
        if (m.group === "read") continue
        const r = run(`${HOOKS}/post-edit.sh`, p, m.canonical, { stdin: false })
        if (r.stdout && r.stdout.trim()) msgs.push(r.stdout.trim())
        if (r.stderr && r.stderr.trim()) msgs.push(r.stderr.trim())
      }

      const text = msgs.join("\n\n").trim()
      if (!text) return
      // Append post-hook output (✓ .pyi regenerated, 💬 FIRST-LINE MISSING, …)
      // to the tool result so the LLM sees it — output.output is opencode's
      // only inline channel for after-hooks.
      if (typeof output.output === "string") {
        output.output = `${output.output}\n\n--- workspace-policy ---\n${text}`
      } else {
        output.output = `\n--- workspace-policy ---\n${text}`
      }
      try {
        await client.app.log({ body: { service: "workspace-policy", level: "info", message: text } })
      } catch {}
    },

    // PreCompact equivalent — wipe this session's CONTEXT.md seen-markers so the
    // chain is re-read after compaction (injected context may be summarized away).
    // Same script Claude Code runs; it reads the session id from stdin JSON and
    // consults feature_law itself, so an off switch stays in one registry.
    "experimental.session.compacting": async () => {
      spawnSync(python(), [`${HOOKS}/session/precompact-wipe.py`], {
        input: JSON.stringify({ session_id: SESSION_ID }),
        cwd: WORKSPACE, encoding: "utf8",
      })
    },
  }
}
