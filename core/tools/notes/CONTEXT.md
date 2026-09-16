# notes
> Pages and note databases, read as navigable text. Provider leaf: `notion` (Notion REST API).

```bash
core/run tools/notes/notion auth personal                    # prompts for the secret, stores it 600
core/run tools/notes/notion whoami --account personal        # proves the token is alive
core/run tools/notes/notion list --account personal --name "Computação"
core/run tools/notes/notion read --account personal <page-id-or-pasted-URL>
core/run tools/notes/notion search --account personal "aula 3"
core/run tools/notes/notion apply --account personal ops.json          # update / append / delete
core/run tools/notes/notion text --account personal <block-id> mes.md  # rewrite one block's text
```

**`apply` is the boundary; `text` is the convenience over it** — the same split as
[`../docs/`](../docs/CONTEXT.md). The contrast with `gdocs` is the part worth knowing: **Notion
addresses a block by id, and an id does not shift when a neighbour changes.** So a batch has no
index algebra and no highest-first rule — order matters only between `append`s. What `apply` does
guarantee is that **every call is built before the first one is sent**, so a typo in operation 9
cannot land operations 1 through 8.

`text` reads a file written with `**bold**` and `[label](url)` and rewrites one block from it.
Named inline links are the house format for a class calendar — a bare `mention/link_preview` chip
renders without a label, so it cannot say which deck it points at.

**`read` prints block ids on purpose** — every write in the Notion API addresses a block by id, so
reading a page hands back the handles for editing it, the same contract as
[`../slides/`](../slides/CONTEXT.md) `read`. It takes a page or a database, since Notion has no
single endpoint for either.

Notion has no headless consent flow — the secret is minted inside Lucas's account at
[my-integrations](https://www.notion.so/my-integrations) and a page is connected to it one at a
time, his only two clicks. Auth recovery, the builtin-pipe storage rule, and the family-wide
protocol: [`../SPECS.md`](../SPECS.md).

**A 404 is a sharing failure until proven otherwise.** Notion returns the same code for "not
connected to this integration" and "no such id," and the first is by far the more common cause:
content stays invisible to an integration it hasn't been shared with. `not_shared_text` leads
with that reading on purpose.

Notion has no read/write token split (AD-11's exception, [`core/SPECS.md`](../../SPECS.md)):
capabilities are chosen when the integration is created, so one secret already carries the
strongest grant.

`VERSION` in `notion_core.py` pins the API contract — Notion breaks by version, not by date, and a
bump can change the shape of a database response.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | Notion API gotchas and the auth mechanics specific to this tool. |
| [`notion`](notion) | — | — | Notion CLI: auth, whoami, list, search, read, apply, text |
| [`notion_auth.py`](notion_auth.py) | [`notion_auth.pyi`](notion_auth.pyi) | `AuthMissing`, `NotShared`, `config_dir`, `token_path`, `save_token` | notion_auth.py — Notion's integration-token store, and the instructions a failure prints |
| [`notion_core.py`](notion_core.py) | [`notion_core.pyi`](notion_core.pyi) | `ApiRefused`, `normalize_id`, `url`, `request`, `paged` | notion_core.py — Notion REST boundary (workspace-agnostic) for Core/tools/notes/notion |
| [`notion_lines.py`](notion_lines.py) | [`notion_lines.pyi`](notion_lines.pyi) | `run`, `runs`, `paragraph` | notion_lines.py — compact text (**bold**, [label](url)) to the rich_text runs Notion stores |
| [`notion_outline.py`](notion_outline.py) | [`notion_outline.pyi`](notion_outline.pyi) | `rich_text`, `block_text`, `marker`, `prop_value`, `title_of` | notion_outline.py — a page as navigable text: block ids, structure, and the words on them |
| [`notion_write.py`](notion_write.py) | [`notion_write.pyi`](notion_write.pyi) | `OpRefused`, `plan`, `apply`, `load`, `text_op` | notion_write.py — the three writes the Notion API has, planned in full before any one is sent |
<!-- routing:end -->
