# Tools
> CLI tools callable via bash, one directory per family; routing block auto-synced on save.

**A family directory is the feature; the tool inside it is the provider.** `mail/gmail`,
`calendar/gcalendar`, `files/gdrive` — swapping a provider changes a leaf, never a family.

Naming rules, the auth-failure protocol, how to add a tool, and the one capability here with no CLI
wrapper: [`SPECS.md`](SPECS.md).

Call any tool via bash — `core/run tools/<family>/<provider> <args>`:
```
core/run tools/files/gdrive search --account personal "aula"
```

<!-- routing:start -->
## Routing

| Subdirectory | Description |
|--------------|-------------|
| [`assets/`](assets/CONTEXT.md) | Interface stubs for non-code assets (.imgif / .csvif), one file or a whole paper. |
| [`audio/`](audio/CONTEXT.md) | Speech to text. Backend leaf: `faster-whisper large-v3-turbo`, local, no network. |
| [`calendar/`](calendar/CONTEXT.md) | Read what is scheduled. Provider leaf: `gcalendar`. Auth: [`../auth/gauth.py`](calendar/../auth/gauth.py). |
| [`chat/`](chat/CONTEXT.md) | Exported conversation to navigable text — voice notes transcribed inline, bot noise dropped, secrets redacted. Provider leaf: `wazip` (WhatsApp). |
| [`docs/`](docs/CONTEXT.md) | Long-form documents, read and edited in place. Provider leaf: `gdocs` (Google Docs API). |
| [`files/`](files/CONTEXT.md) | Remote file storage: list, search, download, upload. Provider leaf: `gdrive`. |
| [`forms/`](forms/CONTEXT.md) | Surveys and their answers: a form written as a versioned spec, applied in one call. Provider leaf: `gforms`. |
| [`links/`](links/CONTEXT.md) | A link gets a name a room can be told out loud. Provider leaf: `cfpages` (Cloudflare Pages). |
| [`mail/`](mail/CONTEXT.md) | Read a mailbox and triage it. Provider leaf: `gmail`. Auth: [`../auth/gauth.py`](mail/../auth/gauth.py). |
| [`notes/`](notes/CONTEXT.md) | Pages and note databases, read as navigable text. Provider leaf: `notion` (Notion REST API). |
| [`paper/`](paper/CONTEXT.md) | Academic sources and text: search papers, extract text, annotate, check terminology. |
| [`slides/`](slides/CONTEXT.md) | Presentations, read and edited in place. Provider leaf: `gslides` (Google Slides API). |
| [`test/`](test/CONTEXT.md) | The verify-fast suite: every Level 0 check plus the tool unit tests. Zero-token, no network. |
| [`verify/`](verify/CONTEXT.md) | Verification contract + patterns for all code projects: levels T0-T3, script names, dump-oracle rules. Reference |
| [`video/`](video/CONTEXT.md) | Link to navigable text — metadata, captions, transcript, OCR, VLM caption. |
| [`web/`](web/CONTEXT.md) | Reach the open web: search, fetch a page as text, browse and search code hosts. |
| [`wos/`](wos/CONTEXT.md) | Tools that act on the workspace itself: spec list, contract check, skill mirrors. |

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`SPECS.md`](SPECS.md) | — | — | What must be true of a `core/tools/` feature, and why: how a family is named, what a failure has to hand back, and what work is the agent's rather than Lucas's. |
| [`attachments_util.py`](attachments_util.py) | [`attachments_util.pyi`](attachments_util.pyi) | `safe_name`, `month_dir`, `unique_path`, `prune_old_attachments` | attachments_util.py — shared filename/dir helpers for Core/tools attachment downloaders (gmail, telegram) |
| [`auth/gauth.py`](auth/gauth.py) | [`auth/gauth.pyi`](auth/gauth.pyi) | `config_dir`, `get_accounts`, `primary_aliases`, `resolve_alias`, `AuthExpired` | gauth.py — Google's leaf of the auth family: shared OAuth2 for every Google-backed tool |
| [`deps.txt`](deps.txt) | — | — | Every external dependency the core/tools surface needs, declared: what installs it, what checks it, and what its absence breaks. Read by core/tools/wos/deps (the check runner) and by core/tools/test/wos/test_deps.py (the class check). |
| [`gcli.py`](gcli.py) | [`gcli.pyi`](gcli.pyi) | `run`, `aliases`, `auth_command` | gcli.py — the two things every Google-backed CLI does identically: consent, and fan out over accounts |
| [`notify/telegram`](notify/telegram) | — | — | tell Lucas, on the chat he already reads |
| [`secret_law.py`](secret_law.py) | [`secret_law.pyi`](secret_law.pyi) | `redact_line`, `redact`, `Finding`, `scan_text`, `scan` | secret_law.py — the one definition of what counts as a secret: the patterns, the redaction a transcript needs, and the scan that REFUSES a file rather than cleaning it. |
| [`short_name.py`](short_name.py) | [`short_name.pyi`](short_name.pyi) | `mint` | short_name.py — the one line a tool spends on offering `--short-name`: mint a short link for what it created |
| [`tool_law.py`](tool_law.py) | [`tool_law.pyi`](tool_law.pyi) | `require` | tool_law.py — the feature switch for core/tools features: the one guard every CLI entrypoint calls |
<!-- routing:end -->
