# Setup — context compaction
> The two halves of what shrinks a session: rtk compresses tool output before it reaches the
> context, caveman compresses the agent's own writing. Each needs a binary and a registration, and in
> both cases the registration is the part that silently reverts.
> feature: rtk-compaction, caveman
> enforced-by: core/tools/test/workspace/test_setup_executable.py

The five-part contract: [`SETUP.md`](SETUP.md). Both features are optional and cost only tokens when
skipped. Read the ⚠ blocks first — each names a command that undoes a step in this file.

<!-- steps:start -->

## RTK
> feature: `rtk-compaction` · agent: yes

[rtk-ai/rtk](https://github.com/rtk-ai/rtk) — a Rust proxy that compresses dev-command output before
it reaches the context.

⚠ **Name collision.** If `rtk gain` reports an unknown subcommand, the installed binary is
reachingforthejack/rtk, a different tool with the same name. Check `which rtk`.

**Precondition** `rtk --version && rtk gain --help >/dev/null && echo "rtk present"`

**Install**
```bash
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/master/install.sh | sh   # → ~/.local/bin/rtk
```

**Verify** `rtk gain` — a savings table, not an error.

## RTK — Claude Code registration
> feature: `rtk-compaction` · agent: yes

**One registration, and it must be the shim** — registered **globally**, so it also covers sessions
started inside nested `code/*` repos. Why a shim rather than `rtk hook`, which rewrites line 1 only:
[`core/hooks/compact/SPECS.md`](core/hooks/compact/SPECS.md).

⚠ **Never run `rtk init --global --auto-patch` here.** It reverts the entry to `rtk hook claude`,
silently dropping multi-line compaction, and `rtk init --show` reports both wirings as configured.

**Precondition** `grep -c bash-compact-rewrite ~/.claude/settings.json` — one match when done.

**Install** — idempotent; replaces any existing `Bash` entry rather than appending:
```bash
"$(sh core/run --python)" - <<'PATCH'
import json, pathlib
p = pathlib.Path.home() / '.claude' / 'settings.json'
d = json.loads(p.read_text())
shim = f'sh {pathlib.Path.cwd()}/core/run hooks/compact/bash-compact-rewrite.py'
pre = d.setdefault('hooks', {}).setdefault('PreToolUse', [])
entry = next((e for e in pre if e.get('matcher') == 'Bash'), None)
if entry is None:
    pre.append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': shim}]})
else:
    entry['hooks'] = [{'type': 'command', 'command': shim}]
p.write_text(json.dumps(d, indent=2) + '\n')
PATCH
```

**Verify** — end to end. **Config alone proves nothing.**
```bash
printf '%s' '{"hook_event_name":"PreToolUse","tool_name":"Bash","session_id":"check",
"tool_input":{"command":"cd core\ngit status\nls -la"}}' \
  | sh core/run hooks/compact/bash-compact-rewrite.py
# expect: cd core / rtk git status / rtk ls -la  — lines 2 and 3 are what raw rtk drops
```

## RTK — ZCode registration
> feature: `rtk-compaction` · agent: yes

Same shim, same exactly-once rule, ZCode's **user scope** (`~/.zcode/cli/config.json` → `hooks`).
User scope, not the workspace's `.zcode/config.json`: project-scope ZCode hooks stay inert until the
workspace is trusted (`core/experiments/zcode-hook-protocol.md`), while user-scope ones run — and the
exactly-once rule from [`core/hooks/compact/SPECS.md`](core/hooks/compact/SPECS.md) is about scope
merging, not about Claude.

**Precondition** `grep -c bash-compact-rewrite ~/.zcode/cli/config.json` — one match when done.

**Install** — idempotent; creates the file if absent, replaces the `Bash` entry rather than appending:
```bash
"$(sh core/run --python)" - <<'PATCH'
import json, pathlib
p = pathlib.Path.home() / '.zcode' / 'cli' / 'config.json'
d = json.loads(p.read_text()) if p.exists() else {}
shim = f'sh {pathlib.Path.cwd()}/core/run hooks/compact/bash-compact-rewrite.py'
hooks = d.setdefault('hooks', {})
hooks['enabled'] = True
pre = hooks.setdefault('PreToolUse', [])
entry = next((e for e in pre if e.get('matcher') == 'Bash'), None)
if entry is None:
    pre.append({'matcher': 'Bash', 'hooks': [{'type': 'command', 'command': shim}]})
else:
    entry['hooks'] = [{'type': 'command', 'command': shim}]
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(d, indent=2) + '\n')
PATCH
```

**Verify** — the same end-to-end check as the Claude section; expect `split-rewrote` in the
`/tmp/claude_rtk_compact_check.tsv` counter. Config alone proves nothing.

## RTK — other agents
> feature: `rtk-compaction` · agent: yes

Skip whichever you do not use. Pi and Feynman need the local `package.json`: their loader resolves
the generated `rtk.ts`'s import as a real `require()`, relative to the extension's own directory.

**Precondition** `ls ~/.config/opencode/plugins/rtk.ts ~/.pi/agent/extensions/rtk.ts 2>/dev/null`

**Install**
```bash
rtk init --global --opencode        # writes ~/.config/opencode/plugins/rtk.ts
rtk init --agent pi --global
mkdir -p ~/.pi/agent/extensions && cd ~/.pi/agent/extensions
echo '{"name":"pi-extensions-peer-deps","private":true}' > package.json
npm install @earendil-works/pi-coding-agent
mkdir -p ~/.feynman/agent/extensions && cp ~/.pi/agent/extensions/rtk.ts ~/.feynman/agent/extensions/
cd ~/.feynman/agent/extensions && cp ~/.pi/agent/extensions/package.json .
npm install @earendil-works/pi-coding-agent
```

**Verify** `pi -e ~/.pi/agent/extensions/rtk.ts --no-session` — silence and exit 0 means loaded.
Feynman has no dry-run flag, so treat it as unverified. Uninstall any target:
`rtk init --uninstall [--global] [--copilot|--opencode|--agent pi]`.

## Caveman
> feature: `caveman` · agent: yes

Output compression, ~65% of the agent's own output. **Vendored** — source of truth
[`core/skills/caveman/`](core/skills/caveman/CONTEXT.md), upstream credit
[JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman). ⚠ **Do not run the upstream
installer**: it replaces the links with copies and re-forks both installs. Needs Node ≥ 18.

**Precondition** `core/run tools/wos/sync-global-skills --check`

**Install** — the links, then the config every agent reads:
```bash
core/run tools/wos/sync-global-skills        # links ~/.agents/skills/caveman + ~/.claude/hooks/caveman-*
mkdir -p ~/.config/caveman && echo '{"defaultMode": "full"}' > ~/.config/caveman/config.json
```
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.config\caveman" | Out-Null
'{"defaultMode": "full"}' | Set-Content "$env:USERPROFILE\.config\caveman\config.json"
```

If `~/.claude/settings.json` did not come across from the old machine, add its three entries:
`SessionStart` → `caveman-activate.js`, `UserPromptSubmit` → `caveman-mode-tracker.js`,
`statusLine` → `caveman-statusline.sh`. Modes: `lite`, `full`, `ultra`, `off`.

**Verify** — open a Claude Code session; the `[CAVEMAN] ⛏` badge appears in the statusline.

## Caveman shell helper
> feature: `caveman` · agent: yes

**Precondition** `grep -q "caveman-compress()" ~/.bashrc && echo "already appended"`

**Install** — guarded by the precondition; appending twice defines the function twice.
```bash
cat >> ~/.bashrc << EOF

# caveman-compress shortcut. The root is baked in at install time because ~/.bashrc lives
# outside the repo; the interpreter is asked for, never spelled `python3`.
caveman-compress() {
  local CLAUDE_BIN
  CLAUDE_BIN="\$(dirname "\$CLAUDE_CODE_EXECPATH")"
  (cd $PWD/core/skills/caveman && PATH="\$CLAUDE_BIN:\$PATH" "\$(sh $PWD/core/run --python)" -m scripts "\$1")
}
EOF
source ~/.bashrc
```
```powershell
Add-Content $PROFILE @'
function caveman-compress {
    param([string]$File)
    $claudeBin = Split-Path $env:CLAUDE_CODE_EXECPATH
    Push-Location "$env:USERPROFILE\.claude\skills\caveman"
    $env:PATH = "$claudeBin;$env:PATH"
    python3 -m scripts $File
    Pop-Location
}
'@
```

**Verify** `type caveman-compress` — expected: "caveman-compress is a function".

<!-- steps:end -->
