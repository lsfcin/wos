# Agents — Specs
> How a worker runs on another harness, and the traps each call has.

**A worker can run on another harness, from any harness, through bash: prompt in, one file out, read-only.** An outside panel is one call, `core/run tools/panel/ask --out <file> <prompt>`, which runs the Codex and agy rows below in that order and skips a model out of quota. Lucas prefers GPT and spends `gpt-6.1-sol` before any other worker (2026-10-19), because it does not spend the Claude quota; the spawner writes files from the output, never the worker.

| Harness | Call (verified 2026-10-19) | Traps |
|---|---|---|
| Codex (GPT) | `codex exec -s read-only -m gpt-6.1-sol -C <workspace> --ephemeral -o <out> "<prompt>" < /dev/null` | the binary ships inside the ChatGPT desktop app's `resources/`, off PATH; without `< /dev/null` it waits on stdin; `-s read-only` reads the tree and writes nothing; refuses to generate or rank political persuasion aimed at a voter group (6 of 9 generators and the judge, 2026-10-19), and offers source, clarity and feasibility checks instead; `-c tools.web_search=true` makes it a working fact-checker with primary URLs |
| Codex with Google auth | same call with `-s workspace-write -c sandbox_workspace_write.network_access=true --add-dir ~/.config/workspace-<service>` in place of `-s read-only` (verified 2026-10-26) | `read-only` cuts the network and the token refresh's write; a token expired outside the sandbox still needs `auth <alias> --reauth` from the spawner |
| agy (Gemini) | `agy --disable-slash-commands --model <id> -p "<prompt with the files inlined>"` | model before prompt; headless needs no tools; `--dangerously-skip-permissions` is refused by Claude Code's auto-mode classifier; `agy models` lists ids and says whether it is logged in |
| Claude Code | `claude -p "<prompt>"` | not run on 2026-10-19; spends Claude quota, the one these calls exist to save |
