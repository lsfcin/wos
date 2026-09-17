# stream
> The answer arriving live: deltas, repaint rate, and bubbles sealed as they are born.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — marks tests/stream as a package. |
| [`test_f4_frames.py`](test_f4_frames.py) | [`test_f4_frames.pyi`](test_f4_frames.pyi) | — | test_f4_frames.py — F4 Stage 2: what may be RENDERED mid-stream, and the guarantee that a streamed turn still ends as byte-for-byte the answer today's code ships. |
| [`test_f4_sealing.py`](test_f4_sealing.py) | [`test_f4_sealing.pyi`](test_f4_sealing.pyi) | — | test_f4_sealing.py — F4 Stage 3: bubbles sealed as they are born, and the property that makes that safe. If the first test here fails, Stage 3 is wrong and Stage 2 still ships. |
| [`test_f4_streaming.py`](test_f4_streaming.py) | [`test_f4_streaming.pyi`](test_f4_streaming.pyi) | `send_action`, `edit_text` | test_f4_streaming.py — F4 Stage 2: the live bubble. Throttle mechanics, the pin, and the guarantee that a streamed turn still ends as byte-for-byte today's answer. |
| [`test_f5_answer_shape.py`](test_f5_answer_shape.py) | [`test_f5_answer_shape.pyi`](test_f5_answer_shape.pyi) | `reply_text` | test_f5_answer_shape.py — F5: a long answer arrives as several repliable bubbles. Lucas, INBOX 2026-07-26: "partir a resposta em várias mensagens pra parecer mais como uma conversação, desde que me permitisse, respondendo qualquer uma delas, continuar na mesma sessão." |
| [`test_f6_bubble_shape.py`](test_f6_bubble_shape.py) | [`test_f6_bubble_shape.pyi`](test_f6_bubble_shape.pyi) | — | test_f6_bubble_shape.py — the furniture on a bubble, decided by Lucas on 2026-07-28: the voice transcript quoted INSIDE every bubble instead of in one of its own, a position marker at the end of each, and `·` never opening a line. What a bubble is made of, not how it is split. |
| [`test_f6_pacing.py`](test_f6_pacing.py) | [`test_f6_pacing.pyi`](test_f6_pacing.pyi) | — | test_f6_pacing.py — the pause BETWEEN bubbles (Lucas, 2026-07-28). Distinct from the repaint floor in test_f4_streaming.py, and that distinction is the whole point: MIN_INTERVAL paces edits to the live bubble, BUBBLE_GAP paces the conversation. Confusing the two is why the cadence looked like it did nothing — "o tempo entre bubbles não funcionou". |
| [`test_stream_parse.py`](test_stream_parse.py) | [`test_stream_parse.pyi`](test_stream_parse.pyi) | — | test_stream_parse.py — F4 Stage 1: claude's stream-json becomes deltas, and the turn still reassembles into exactly the answer the batch path would have produced. |
<!-- routing:end -->
