# interview
> The agent asking Lucas a question mid-turn: the broker, the transport, and the bubble it draws.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | **facade** — __init__.py — marks tests/interview as a package. |
| [`test_f4_ask.py`](test_f4_ask.py) | [`test_f4_ask.pyi`](test_f4_ask.pyi) | test_f4_ask.py — F4 Stage 4: the broker. One asyncio.Future per question, the chat UX that resolves it (tap or reply), and the rule Lucas set — a wait always ends in TEXT the agent can act on, never in an MCP error, because an error aborts the turn and loses its work. |
| [`test_f4_ask_wiring.py`](test_f4_ask_wiring.py) | [`test_f4_ask_wiring.pyi`](test_f4_ask_wiring.pyi) | test_f4_ask_wiring.py — F4 Stage 4: the transport and the CLI wiring around the broker. |
| [`test_f6_interview_shape.py`](test_f6_interview_shape.py) | [`test_f6_interview_shape.pyi`](test_f6_interview_shape.pyi) | test_f6_interview_shape.py — what the chat looks like when the agent interviews Lucas mid-turn |
| [`test_f7_opencode_ask.py`](test_f7_opencode_ask.py) | [`test_f7_opencode_ask.pyi`](test_f7_opencode_ask.pyi) | test_f7_opencode_ask.py — opencode parity: the ask transport and the retry vocabulary. |
| [`test_f8_ask_answer_shape.py`](test_f8_ask_answer_shape.py) | [`test_f8_ask_answer_shape.pyi`](test_f8_ask_answer_shape.pyi) | test_f8_ask_answer_shape.py — what an interview looks like in the chat, read on a phone. |
<!-- routing:end -->
