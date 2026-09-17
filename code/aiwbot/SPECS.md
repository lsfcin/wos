# aiwbot — Specs

## Conventions
- Style R1–R6 (see code/CONTEXT.md). Files under the line cap. Facade imports only via `backend/__init__.py`.
- Free tests must stay green to commit; live smoke (`make smoke`) is manual and costs money.

<!-- routing:start -->
## Routing

| Part | Description | Governs |
|------|-------------|---------|
| [`SPECS-boundary.md`](SPECS-boundary.md) | The one interface every coding-agent CLI becomes, and what it must pin. | backend/ |
| [`SPECS-capability.md`](SPECS-capability.md) | What a backend declares it can do, and how mode, model and effort are offered. | backend/ capability declaration, frontend/ pickers |
| [`SPECS-questions.md`](SPECS-questions.md) | An agent that asks: how the question is carried, positioned, and answered. | frontend/ question handling |
| [`SPECS-sessions.md`](SPECS-sessions.md) | Where a session lives, who can see it, and how a resume keeps one lineage. | backend/, frontend/ session listing |
| [`SPECS-streaming.md`](SPECS-streaming.md) | How an answer arrives bubble by bubble, what is sealed, and what spend means. | frontend/ streaming |
| [`SPECS-telegram.md`](SPECS-telegram.md) | Panels, buttons, tables and speech-to-text: what the chat client can render. | frontend/ |
<!-- routing:end -->
