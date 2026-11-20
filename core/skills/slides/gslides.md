# gslides — the Google Slides leaf of /slides
> Provider hand: read, preview and edit decks through the API. The craft is in [`../slides.md`](../slides.md).

## Commands

```
core/run tools/slides/gslides list    --account personal --name "AI4Good"
core/run tools/slides/gslides read    --account personal <presentation_id>   # deck as navigable text
core/run tools/slides/gslides new     --account personal "Aula 3"
core/run tools/slides/gslides text    --account personal --slide <slide_id> <id> "título"
core/run tools/slides/gslides preview --account personal --sheet <presentation_id>   # slide PNGs + contact sheets
core/run tools/slides/gslides stats   --account personal <presentation_id>   # style numbers + slide archetypes
core/run tools/slides/gslides lint    --account personal <presentation_id>   # what a room cannot read
core/run tools/slides/gslides apply   --account personal <presentation_id> requests.json
```

## How to edit

1. `read` first — it prints element ids on purpose; those ids are exactly what a `batchUpdate` request needs, so one read hands back the handles for the edit.
2. Build the request list as a JSON file. `apply` is the real boundary — every other write command is a convenience over it, and the API's own shape (a list of typed requests) is the format. `read --json` shows the input side of the same shape.
3. `apply`, then `read` again to verify, and `preview` when the question is visual (layout, overlap, glyph density) rather than textual.

## Notes

- Two auth grants per account (read, write) — on a dead token the CLI names the exact command:
  `core/run tools/slides/gslides auth <alias> --reauth` (add `--write` for the write grant)
- A layout cannot be created or duplicated: a template is a deck you copy, a new look an edit to its master/layouts
- Per-frame motion goes through `batchUpdate`; there is no animation convenience
- Rendering facts the API does not document (fonts, transforms, export quirks):
  `core/tools/slides/SPECS.md`
