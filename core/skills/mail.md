---
name: gmail
description: >
  Triage Gmail across all configured accounts — classify, confirm routes, write to brain/INBOX.md.
---

Triage Gmail across all configured accounts — classify, confirm routes, write to brain/INBOX.md.

Arguments: $ARGUMENTS

## Overview

Pull recent unread emails, classify via AI, present to Lucas for confirmation, then write confirmed entries to
`brain/INBOX.md`. Downloads attachments and scaffolds draft replies when needed.

## Protocol

### Step 1 — Fetch & Classify

Run:
```
core/run tools/mail/gmail sync [--since 7] [--account all]
```

Output will show emails grouped by route. Read it carefully before presenting.

### Step 2 — Present Grouped

Show each email with its proposed route, summary, and INBOX entry preview. Group by:

1. **Urgency** (`task:today`)
2. **Actionable** (`task:week`, `task:month`, needs_reply)
3. **Goal context** (goal_hint set)
4. **Reading/backlog** (`task:backlog`)
5. **Delete** (noise, notifications)

For each email:
```
[route] [alias] Subject
from: sender@email.com · YYYY-MM-DD
summary: ...
📎 attachments: file.pdf (if any)
INBOX preview:
  [gmail/alias] Subject summary
  from: sender · date
  task: week
```

### Step 3 — Get Confirmation

Present all routes first. Wait for Lucas to confirm, override, or skip each.

Accepted inputs per email:
- `y` or enter — confirm as proposed
- `task:today` / `task:week` / `task:month` / `task:backlog` / `goal` / `draft` / `delete` — override route
- `skip` — leave in Gmail, don't write to INBOX

Confirm in batches if many emails — don't ask one by one for large sets; group delete candidates together.

### Step 4 — Write Confirmed Entries

For each confirmed email:

1. **Write INBOX entry** — prepend to `brain/INBOX.md` after the header block, before existing entries
2. **Attachments** — if `has_attachment`, run:
   ```
   core/run tools/mail/gmail attachments --id <message_id>
   ```
   Then update the INBOX entry to include the `attachment:` line with the saved path.
3. **Draft reply** — if route is `draft` or `needs_reply` is true and Lucas wants to draft, create:
   ```
   branches/writing/drafts/email/YYYY-MM-DD-<alias>-<name>.md
   ```
   with format:
   ```markdown
   # Draft: Re: <subject>
   to: <sender-email>
   subject: Re: <original subject>
   account: <alias>
   original-date: YYYY-MM-DD
   status: draft

   ---

   <!-- original: <summary_pt> -->

   [body]
   ```

### Step 5 — Offer Chain

After all writes:
> "N entries added to brain/INBOX.md. Run /inbox to route them now?"

Lucas can confirm or handle later.

## Notes

- Never sends email — read-only Gmail access throughout
- All writes require Lucas confirmation — no silent auto-routing
- Attachments saved to `brain/attachments/YYYY-MM/` with `.summary.md` companion
- Cache is at `~/.config/workspace-gmail/fetch_cache.json` — if < 1h old, offer to skip re-fetch
- If Gmail auth is missing for an account, direct Lucas to run `core/tools/mail/gmail auth <alias>`
