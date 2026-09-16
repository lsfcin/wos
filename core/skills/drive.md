---
name: drive
description: >
  List, search, and download files from Google Drive across all configured accounts (personal, cin, ufrpe).
---

# Drive skill

Arguments: $ARGUMENTS

---

## Overview

Access Google Drive across 3 accounts via `core/tools/files/gdrive` — read *and* write. Reads use the
`drive` token, `mkdir`/`put` use a separate `drive-write` one, so a read re-consent leaves the write
token dead: `gdrive auth <alias> --write --reauth` is a different command.

## Commands

```bash
core/run tools/files/gdrive recent [--account all|personal|cin|ufrpe] [--limit 20]
core/run tools/files/gdrive list   [--account ...] [--folder <id>]
core/run tools/files/gdrive search [--account ...] <query>
core/run tools/files/gdrive download --account <alias> <file_id>
core/run tools/files/gdrive mkdir   --account <alias> [--parent <id>] <name>
core/run tools/files/gdrive put     --account <alias> [--parent <id>] [--gdoc] <path>
core/run tools/files/gdrive auth <alias>   # first-time per account
```

## Auth (first-time setup)

Tokens stored at `~/.config/workspace-drive/{alias}.token.json`. Run once per account:

```bash
core/run tools/files/gdrive auth personal
core/run tools/files/gdrive auth cin
core/run tools/files/gdrive auth ufrpe
```

## Workflow

1. User asks about a Drive file → run `search` or `recent`.
2. Found file → show name, date, link. Ask if should download.
3. Download → file lands in `Downloads/workspace-drive/` at the workspace root.
   Google Docs/Slides exported as PDF; Sheets as .xlsx.
   To **read** a Google Doc as text, use `core/tools/docs/gdocs read` instead —
   a PDF of a document is a worse read than its markdown.
4. If file needs processing (PDF, text) → read and summarize.

## Accounts

Same aliases as Gmail: `personal` (lsf.cin@gmail.com), `cin` (lsf@cin.ufpe.br), `ufrpe` (lucas.sfigueiredo@ufrpe.br).
