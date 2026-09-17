# interview
> The agent asking Lucas a question mid-turn: the broker, its transport, and the bubble it draws.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: the agent asking Lucas a question mid-turn: the broker, its transport, and the bubble it draws. |
| [`ask.py`](ask.py) | [`ask.pyi`](ask.pyi) | `new_token`, `register`, `unregister`, `question_of`, `answer` | ask.py — the bot side of ask_user: hold a running turn open on a question until Lucas answers. The agent's tool call blocks inside the daemon (askserver hands it here), so an answer resumes the SAME turn rather than starting a new one — that is the whole point of the MCP round trip. |
| [`askserver.py`](askserver.py) | [`askserver.pyi`](askserver.pyi) | `url`, `port`, `handle_rpc`, `start` | askserver.py — the daemon's own MCP server: one HTTP endpoint per live turn, JSON-RPC by hand. |
| [`askshape.py`](askshape.py) | [`askshape.pyi`](askshape.pyi) | `markup`, `bubble_text`, `answer_note`, `close` | askshape.py — what a question LOOKS like in the chat: its bubble, its keys, and how it closes. |
<!-- routing:end -->
