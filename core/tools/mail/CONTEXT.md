# mail
> Read a mailbox and triage it. Provider leaf: `gmail`. Auth: [`../auth/gauth.py`](../auth/gauth.py).

Fetch caches to `~/.config/workspace-gmail/fetch_cache.json`, so `triage` re-runs without
re-fetching. `attachments` writes through the shared `attachments_util.py` at the tools root —
the one module `video/` also imports, which is why it stays there and not here.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`gmail`](gmail) | — | — | read-only Gmail integration for workspace OS Commands: auth <alias> [--reauth], fetch [--since N] [--account A], triage, sync, attachments [--id ID] |
| [`gmail_attachments.py`](gmail_attachments.py) | [`gmail_attachments.pyi`](gmail_attachments.pyi) | `download` | gmail_attachments.py — download and summarize Gmail attachments for Core/tools/mail/gmail |
| [`gmail_fetch.py`](gmail_fetch.py) | [`gmail_fetch.pyi`](gmail_fetch.pyi) | `auth`, `get_service`, `fetch`, `fetch_all` | gmail_fetch.py — Gmail API auth, fetch, and MIME parse for Core/tools/mail/gmail |
| [`gmail_triage.py`](gmail_triage.py) | [`gmail_triage.pyi`](gmail_triage.pyi) | `classify` | gmail_triage.py — Claude API email classification for Core/tools/mail/gmail |
<!-- routing:end -->
