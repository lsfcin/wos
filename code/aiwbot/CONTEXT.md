# aiwbot
> Provider-agnostic bot: control swappable coding agents (claude·opencode·copilot) from chat.
> goal: [workspace-os](../../brain/goals/workspace-os.md)
> spec: none

## Overview
One `AgentBackend` interface normalizes every coding-agent CLI into a stream of `AgentEvent`s, so the frontend (Telegram) never knows which provider runs underneath — provider is data, not code.
Phase A (current) proves the boundary against claude + opencode with a bare harness + free fixture tests, before any Telegram wiring.

`make test` runs the free fixture tests; `make smoke` runs one live prompt through each backend (~$0.20). Installing and operating the systemd service is [`SETUP-telegram.md`](../../SETUP-telegram.md); the token and the chat pairing are an account, and live with every other one.

This tree is the `bot` feature of the workspace registry, and the only project under `code/` that crosses into the public repo — the switch is read at `main()` and again at the INBOX write.

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`backend/`](backend/CONTEXT.md) | Provider-agnostic boundary: each coding-agent CLI → normalized AgentEvent stream; one class per provider. |
| [`frontend/`](frontend/CONTEXT.md) | Telegram frontend on the AgentBackend boundary — /new + reply-to-continue + INBOX capture. |
| [`tests/`](tests/CONTEXT.md) | Free unit tests — pure-logic fixtures/parsers/formatting, no network or cost. |

| File | Interface | Description |
|------|-----------|-------------|
| [`ISSUES.md`](ISSUES.md) | — | aiwbot — Issues |
| [`REFS.md`](REFS.md) | — | aiwbot — References |
| [`ROADMAP-p2.md`](ROADMAP-p2.md) | — | aiwbot — P2: backend + model + effort selection |
| [`ROADMAP-p3.md`](ROADMAP-p3.md) | — | aiwbot — P3: Telegram output fidelity + `/resume` stability |
| [`ROADMAP.md`](ROADMAP.md) | — | aiwbot — Roadmap |
| [`SPECS-boundary.md`](SPECS-boundary.md) | — | The one interface every coding-agent CLI becomes, and what it must pin. |
| [`SPECS-capability.md`](SPECS-capability.md) | — | What a backend declares it can do, and how mode, model and effort are offered. |
| [`SPECS-questions.md`](SPECS-questions.md) | — | An agent that asks: how the question is carried, positioned, and answered. |
| [`SPECS-sessions.md`](SPECS-sessions.md) | — | Where a session lives, who can see it, and how a resume keeps one lineage. |
| [`SPECS-streaming.md`](SPECS-streaming.md) | — | How an answer arrives bubble by bubble, what is sealed, and what spend means. |
| [`SPECS-telegram.md`](SPECS-telegram.md) | — | Panels, buttons, tables and speech-to-text: what the chat client can render. |
| [`SPECS.md`](SPECS.md) | — | aiwbot — Specs |
| [`conftest.py`](conftest.py) | [`conftest.pyi`](conftest.pyi) | conftest.py — pytest anchor: puts the project root on sys.path so `backend` imports resolve. |
| [`proto.py`](proto.py) | [`proto.pyi`](proto.pyi) | proto.py — live smoke: run one prompt through each backend + prove single-lineage resume. ~$0.10/run. |
| [`requirements.txt`](requirements.txt) | — | requirements.txt — aiwbot's extra runtime deps, installed into the shared workspace venv. |
<!-- routing:end -->
