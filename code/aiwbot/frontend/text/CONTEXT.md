# text
> Agent markdown becomes Telegram HTML: blocks, inline spans, tables, and chunks that never break a tag.
> spec: ../SPECS.md

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`__init__.py`](__init__.py) | [`__init__.pyi`](__init__.pyi) | — | **facade** — __init__.py — facade: agent markdown becomes Telegram HTML. Import text only through here. |
| [`format.py`](format.py) | [`format.pyi`](format.pyi) | `relative_time`, `plain`, `clip_chars`, `title_words`, `title_from_prompt` | format.py — pure text formatting: markdown/tables -> Telegram HTML, session headers. No I/O. |
| [`htmlsplit.py`](htmlsplit.py) | [`htmlsplit.pyi`](htmlsplit.pyi) | `split_html`, `strip_tags` | htmlsplit.py — split Telegram HTML into sendable chunks without ever breaking a tag. |
| [`inline.py`](inline.py) | [`inline.pyi`](inline.pyi) | `convert` | inline.py — markdown inline spans -> Telegram HTML (bold, strike, code, links, italic). |
| [`markdown.py`](markdown.py) | [`markdown.pyi`](markdown.pyi) | `stable_prefix`, `format_body` | markdown.py — agent markdown -> Telegram HTML: block level (fences, tables, headings, lists). |
| [`table.py`](table.py) | [`table.pyi`](table.pyi) | `is_row`, `is_separator`, `render` | table.py — pipe-tables -> Telegram row blocks: rows become labelled text, never a <pre> box. |
<!-- routing:end -->
