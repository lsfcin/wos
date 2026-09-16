// Helpers for the workspace-policy opencode plugin.
// Lives OUTSIDE .opencode/plugins/ so opencode does not auto-load it as a
// plugin (opencode scans only .opencode/plugins/*). Imported by
// .opencode/plugins/workspace-policy.js.
//
// These are the translation layer between opencode's tool.execute.before
// /after events and the stdin-JSON + CLAUDE_TOOL_NAME/CLAUDE_TOOL_INPUT env
// schema that the existing core/hooks/* scripts already expect (see
// .claude/settings.json and core/hooks/copilot/copilot-pre-tool.py for the prior art).

import { spawnSync } from "node:child_process"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

// Derived, never spelled. This was one machine's absolute path until 2026-08-30 — a directory only
// the authoring machine has, so on any other clone every hook path this module builds pointed at
// nothing and the whole opencode policy plugin was inert. The file sits at <root>/.opencode/, so
// the root is two levels up from its own URL, which is true wherever the repo is cloned.
export const WORKSPACE = resolve(dirname(fileURLToPath(import.meta.url)), "..")
export const HOOKS = `${WORKSPACE}/core/hooks`

// Session-stable id, the Copilot `copilot<host-pid>` pattern (core/hooks/SPECS.md § The contract
// a new agent's shim must satisfy). This module is imported in-process, so process.pid IS the
// opencode host process: unique per session, stable for its whole life. Without it the markers
// dedupe on hook_input.py's ppid fallback — the terminal, shared by every session the terminal
// ever ran — and the CONTEXT.md chain leaks "already seen" across sessions.
export const SESSION_ID = `opencode${process.pid}`

// The interpreter, asked never spelled. The bare word `python3` is the one spelling this
// workspace bans (core/run header): on a Windows clone it reaches the Microsoft Store alias,
// which prints an advert and exits 9009 — every gate after it dies while the plugin reads as
// green. `core/run --python` prints this clone's venv interpreter; cached once per process.
// Empty string means no venv is installed, and the plugin registers no hooks (there is
// nothing for them to run).
let _python = null
export function python() {
  if (_python !== null) return _python
  const r = spawnSync("sh", [`${WORKSPACE}/core/run`, "--python"], { encoding: "utf8" })
  _python = r.status === 0 ? r.stdout.trim() : ""
  return _python
}

// opencode tool names -> Claude canonical env value + matcher group.
//   read             -> Read  (pre-read.py, facade-tracker)
//   edit, apply_patch-> Edit  (pre-edit + facade-scan + facade-gate, post-edit.sh)
//   write            -> Write (same scripts; pre-edit.py Write branch + facade-scan)
export const TOOL_MAP = {
  read:        { canonical: "Read",  group: "read" },
  edit:        { canonical: "Edit",  group: "edit" },
  write:       { canonical: "Write", group: "edit" },
  apply_patch: { canonical: "Edit",  group: "edit" }, // edit-permission; paths in patchText
}

// Reusable key lists — same as copilot-pre-tool.py (camelCase + snake_case).
const PATH_KEYS = ["filePath", "file_path", "path", "file", "filepath", "targetPath", "target_path"]
const CONTENT_KEYS = ["content", "text", "newCode", "new_code"]
const OLD_KEYS = ["oldString", "old_string", "oldText", "old_text"]
const NEW_KEYS = ["newString", "new_string", "newText", "new_text"]

// apply_patch markers embedded in patchText (per opencode docs).
const APPLY_PATCH_RE = /^\*\*\*\s+(?:Add File|Update File|Move to|Delete File):\s+(.+)$/gm

function firstString(obj, keys) {
  if (!obj || typeof obj !== "object") return ""
  for (const k of keys) if (typeof obj[k] === "string" && obj[k]) return obj[k]
  return ""
}

// Resolve a possibly-relative path against the workspace root.
function normalizePath(raw) {
  if (!raw || typeof raw !== "string" || !raw.trim()) return ""
  return resolve(WORKSPACE, raw)
}

// Build the Claude-shape payload(s) from opencode's args. For apply_patch
// there is no filePath; paths are embedded in patchText markers — extract them
// and return one payload per path (caller iterates). Every payload carries the
// session-stable id (SESSION_ID) so the canonical scripts dedupe their markers.
//
// AN EMPTY FIELD IS OMITTED, NOT SENT EMPTY, and since 2026-09-05 that is load-bearing.
// hook_input.capability() asks whether a content key is PRESENT, not whether it holds anything, so
// a read payload carrying `content: ""` reads as a write and core/hooks/dispatch.py would run the
// write gates on a file nobody is writing. apply_patch keeps a pair of empty edit fields on
// purpose: it IS a write, its body is a patch nothing here can measure, and the empty pair puts it
// on pre-edit.py's patch branch — which blocks a file already past the cap and cannot mistake a
// patched-in file for a new one with no first-line comment.
/**
 * @param {Record<string, any>} args opencode tool args
 * @param {string} toolName opencode tool name
 * @returns {Array<Record<string, any>>}
 */
export function buildPayloads(args, toolName) {
  if (toolName === "apply_patch") {
    const patchText = args.patchText || ""
    const paths = [...patchText.matchAll(APPLY_PATCH_RE)].map(m => normalizePath(m[1].trim()))
    return paths.filter(Boolean).map(p => ({
      file_path: p, old_string: "", new_string: "", session_id: SESSION_ID,
    }))
  }
  const fp = normalizePath(firstString(args, PATH_KEYS))
  if (!fp) return []
  const payload = { file_path: fp, session_id: SESSION_ID }
  for (const [key, keys] of [["content", CONTENT_KEYS], ["old_string", OLD_KEYS],
                             ["new_string", NEW_KEYS]]) {
    const value = firstString(args, keys)
    if (value) payload[key] = value
  }
  return [payload]
}

// Grep is gated by context-gate.py only (Claude parity: matcher Grep sits on the context gate,
// never on pre-read.py). Its target is a `path` key, not `file_path` — context-gate.py's
// target_path() reads `path` when CLAUDE_TOOL_NAME is "Grep".
/**
 * @param {Record<string, any>} args opencode grep args
 * @returns {Record<string, any> | null}
 */
export function buildGrepPayload(args) {
  const raw = firstString(args, PATH_KEYS)
  if (!raw) return null
  return { path: normalizePath(raw), session_id: SESSION_ID }
}

// Spawn a hook script with the Claude Code stdin-JSON + env schema.
// `stdin:true`  -> pre-hook: feed JSON on stdin.
// `stdin:false` -> post-hook: feed JSON via CLAUDE_TOOL_INPUT env var.
// Always sets CLAUDE_TOOL_NAME = canonical ("Read"/"Edit"/"Write"/"Grep"/"Bash").
/**
 * @param {string} script absolute path to the hook script
 * @param {Record<string, any>} payload Claude-shape hook payload
 * @param {string} canonical value for the CLAUDE_TOOL_NAME env var
 * @param {{stdin?: boolean}} [opts] stdin true = pre-hook (stdin JSON), false = post-hook (env JSON)
 * @returns {import("node:child_process").SpawnSyncReturns<string>}
 */
export function run(script, payload, canonical, { stdin } = {}) {
  const env = { ...process.env, CLAUDE_TOOL_NAME: canonical }
  const json = JSON.stringify(payload)
  const py = python()
  if (!py) return { status: 1, stdout: "", stderr: "workspace-policy: no venv interpreter — run /install" }
  const argv = script.endsWith(".sh") ? ["bash", script] : [py, script]
  if (stdin) {
    return spawnSync(argv[0], argv.slice(1), {
      input: json, env, cwd: WORKSPACE, encoding: "utf8",
    })
  }
  env.CLAUDE_TOOL_INPUT = json
  return spawnSync(argv[0], argv.slice(1), {
    env, cwd: WORKSPACE, encoding: "utf8",
  })
}

// Non-blocking warning surfacing. opencode has no inline-tool-warning API on
// `tool.execute.before`, so pre-hook warnings go to two channels: a server log
// entry + a TUI toast. The LLM does NOT see these; only the user does. Blocking
// messages use throw (separate code path) which the LLM DOES see.
//
// THE PAYLOAD IS UNWRAPPED FIRST, because a warning is read by a person. A gate
// speaks in hookSpecificOutput.additionalContext (core/hooks/SPECS.md), which is
// the only exit-0 channel that reaches an LLM; putting that JSON in a toast shows
// the envelope instead of the sentence. Verified 2026-09-05 by driving the plugin
// with a synthetic client: every toast was a JSON document.
export async function warn(client, msg) {
  let text = (msg || "").trim()
  if (!text) return
  try {
    const said = JSON.parse(text)?.hookSpecificOutput?.additionalContext
    if (typeof said === "string" && said.trim()) text = said.trim()
  } catch {}
  try {
    await client.app.log({ body: { service: "workspace-policy", level: "warn", message: text } })
  } catch {}
  try {
    await client.tui.showToast({ body: { message: text, variant: "warning", title: "workspace-policy" } })
  } catch {}
}
