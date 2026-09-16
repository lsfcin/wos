---
name: gdocs
description: >
  Read and edit Google Docs in place across all configured accounts — markdown round trip or
  surgical batchUpdate, comments included.
---

Read and edit Google Docs in place across all configured accounts (personal, cin, ufrpe).

Arguments: $ARGUMENTS

## Commands

```
core/run tools/docs/gdocs list     --account personal --name "ementa"
core/run tools/docs/gdocs read     --account personal <document_id>             # doc as markdown
core/run tools/docs/gdocs read     --account personal --outline <document_id>   # body indices to edit by
core/run tools/docs/gdocs new      --account personal "Ata" --from draft.md
core/run tools/docs/gdocs push     --account personal <document_id> draft.md    # replace the whole body
core/run tools/docs/gdocs apply    --account personal <document_id> requests.json
core/run tools/docs/gdocs comments --account personal <document_id>
```

## Two ways in — choose whole-document or surgical

- **Whole document:** `read`/`push` carry Markdown, so a `.md` in this repo and the live Doc are the
  same document; `push` keeps the id, URL and sharing. Caution: `push` can orphan comments.
- **Surgical:** `read --outline` prints body indices on purpose — they are what a `batchUpdate`
  needs. An index goes stale the moment anything is inserted or deleted before it, so build the
  batch highest index first; `apply` refuses one that is not, and a passed revision id makes an
  edit reject instead of misplace when someone else moved the document.

## Notes

- Two auth grants per account — on a dead token the CLI names the fix:
  `core/run tools/docs/gdocs auth <alias> --reauth` (add `--write` for the write grant)
- Markdown loses some structure in the round trip (what exactly: `core/tools/docs/SPECS.md`)
- `comments` is read-only; replying happens in the UI
