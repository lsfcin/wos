# store
> What a provider already wrote: its session store, its transcript, its model catalogue.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | **facade** — __init__.py — marks tests/store as a package. |
| [`test_b3_context_pct.py`](test_b3_context_pct.py) | [`test_b3_context_pct.pyi`](test_b3_context_pct.pyi) | test_b3_context_pct.py — regression spec for [b3]: context occupancy over 100% (even 200%). |
| [`test_catalog.py`](test_catalog.py) | [`test_catalog.pyi`](test_catalog.pyi) | test_catalog.py — free unit test: opencode catalogue — effort vocabularies, groups, favourites. |
| [`test_f8_footer_model.py`](test_f8_footer_model.py) | [`test_f8_footer_model.pyi`](test_f8_footer_model.pyi) | test_f8_footer_model.py — Lucas, live 2026-07-29: an opencode answer's footer named no model. Not a parser bug: opencode's JSONL never says which model ran. So the model is read from its own store after the turn, exactly as occupancy already is (b3/AD-24). |
| [`test_ocstore.py`](test_ocstore.py) | [`test_ocstore.pyi`](test_ocstore.pyi) | test_ocstore.py — free unit test: opencode sqlite reads — last assistant turn + occupancy. |
| [`test_transcript.py`](test_transcript.py) | [`test_transcript.pyi`](test_transcript.pyi) | test_transcript.py — free unit test: tail-scan a claude .jsonl for title/preview/model. |
<!-- routing:end -->
