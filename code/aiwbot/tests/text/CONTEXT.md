# text
> Agent markdown becomes Telegram HTML: blocks, inline spans, tables, chunking, button labels.
> spec: none

<!-- routing:start -->
## Routing

| File | Interface | Description |
|------|-----------|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | **facade** — __init__.py — marks tests/text as a package. |
| [`test_b1_table_bold.py`](test_b1_table_bold.py) | [`test_b1_table_bold.pyi`](test_b1_table_bold.pyi) | test_b1_table_bold.py — regression spec for [b1]: tables and bold not rendering in Telegram. |
| [`test_format.py`](test_format.py) | [`test_format.pyi`](test_format.pyi) | test_format.py — free unit test: markdown/table -> Telegram HTML conversion. |
| [`test_htmlsplit.py`](test_htmlsplit.py) | [`test_htmlsplit.pyi`](test_htmlsplit.pyi) | test_htmlsplit.py — free unit test: chunking formatted HTML without breaking a tag. |
| [`test_labels.py`](test_labels.py) | [`test_labels.pyi`](test_labels.pyi) | test_labels.py — free unit test: fitting a model id into a button label. |
| [`test_markdown.py`](test_markdown.py) | [`test_markdown.pyi`](test_markdown.pyi) | test_markdown.py — free unit test: block + inline markdown -> Telegram HTML. |
<!-- routing:end -->
