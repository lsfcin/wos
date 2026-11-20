# docs
> Long-form documents, read and edited in place. Provider leaves: `gdocs` (Google Docs API), `docx` (local .docx form tables).

```bash
core/run tools/docs/gdocs list     --account personal --name "ementa"
core/run tools/docs/gdocs read     --account personal <document_id>            # the doc as markdown
core/run tools/docs/gdocs read     --account personal --outline <document_id>  # body indices to edit by
core/run tools/docs/gdocs new      --account personal "Ata" --from draft.md
core/run tools/docs/gdocs push     --account personal <document_id> draft.md   # replace the whole body
core/run tools/docs/gdocs apply    --account personal <document_id> requests.json
core/run tools/docs/gdocs comments --account personal <document_id>
```

**Two ways in, and the choice is whole-document versus surgical.** `read`/`push` carry Markdown, so a `.md` in this repo and the live Doc are the same document — Drive converts both directions and a `push` keeps the id, URL and sharing. `apply` is the real boundary for anything smaller; `text` and `replace` are conveniences over it.

**`read --outline` prints body indices on purpose** — they are what a `batchUpdate` request needs, so reading a document hands back the handles for editing it. Unlike a Slides object id, **an index goes stale the moment anything is inserted or deleted before it**, so a batch is built highest index first and `apply` refuses one that is not. Pass the revision back and a document someone else moved rejects the batch instead of misplacing the edit.

`core/run tools/docs/docx fill|read|text` is the local third way in, for a labelled `.docx` form table: [`SPECS.md`](SPECS.md) § docx.

Why `push` can orphan comments, what Markdown loses in the round trip, the index algebra, and the two auth grants (the same split as [`../files/`](../files/CONTEXT.md)): [`SPECS.md`](SPECS.md).

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What the Docs API actually returns, and how a .docx form is filled without it — learned the expensive way; read alongside `CONTEXT.md`. |
| [`docs_core.py`](docs_core.py) | [`docs_core.pyi`](docs_core.pyi) | `IndexOrderError`, `get_service`, `get_document`, `create`, `request_index` | docs_core.py — Google Docs read+write boundary (account-agnostic) for Core/tools/docs/gdocs |
| [`docs_drive.py`](docs_drive.py) | [`docs_drive.pyi`](docs_drive.pyi) | `list_documents`, `export_md`, `push_md`, `create_from_md`, `comments` | docs_drive.py — the half of a Google Doc that the Docs API cannot reach: listing, markdown, comments |
| [`docs_outline.py`](docs_outline.py) | [`docs_outline.pyi`](docs_outline.pyi) | `paragraph_text`, `style`, `outline` | docs_outline.py — a document as navigable text: body indices, structure, and the words on them |
| [`docx`](docx) | — | — | fill a labelled .docx form table from JSON keeping its formatting, read one back to JSON, or print body text with list numbers |
| [`docx_template.py`](docx_template.py) | [`docx_template.pyi`](docx_template.pyi) | `uniq_cells`, `match_label`, `set_font`, `fill_cell`, `from_template` | docx_template.py — fill a labelled .docx form table keeping its formatting, and read it back the same way |
| [`gdocs`](gdocs) | — | — | Google Docs CLI: auth, list, read, new, push, apply, text, replace, comments |
<!-- routing:end -->
