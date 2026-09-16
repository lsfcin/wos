# audio
> Speech to text. Backend leaf: `faster-whisper large-v3-turbo`, local, no network.

The wrapper is domain-free on purpose: `run` takes the conditioning prompt as an argument, so
the vocabulary lives with whoever owns it — aiwbot primes for workspace jargon, `code/obra`
primes for construction and cartório terms. A bare word list ANYWHERE in that prompt suppresses
punctuation; write it as writing someone could have said.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`stt.py`](stt.py) | [`stt.pyi`](stt.pyi) | `model`, `confident`, `run` | stt.py — speech-to-text boundary: faster-whisper large-v3-turbo, lazy-loaded; fails safe to "" . Priming is the CALLER's data — a domain passes its own carrier prose to `run`, because the prompt is what buys both vocabulary and punctuation, and no two domains share one. |
<!-- routing:end -->
