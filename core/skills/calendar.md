---
name: calendar
description: >
  List upcoming events and query date ranges from Google Calendar across all configured accounts (personal, cin, ufrpe).
---

# Calendar skill

Arguments: $ARGUMENTS

---

## Overview

Access Google Calendar (read-only) across 3 accounts via `core/tools/calendar/gcalendar`.

## Commands

```bash
core/run tools/calendar/gcalendar upcoming  [--account all|personal|cin|ufrpe] [--days 7]
core/run tools/calendar/gcalendar range     [--account ...] <from_date> <to_date>   # YYYY-MM-DD
core/run tools/calendar/gcalendar calendars [--account ...]
core/run tools/calendar/gcalendar auth <alias>   # first-time per account
```

## Auth (first-time setup)

Tokens stored at `~/.config/workspace-calendar/{alias}.token.json`. Run once per account:

```bash
core/run tools/calendar/gcalendar auth personal
core/run tools/calendar/gcalendar auth cin
core/run tools/calendar/gcalendar auth ufrpe
```

## Workflow

1. User asks what's on calendar / free slots / upcoming deadlines → run `upcoming`.
2. Specific date range → run `range`.
3. Multiple accounts → use `--account all` (default).
4. Summarize events, flag conflicts or deadlines relevant to current task.

## Accounts

Same aliases as Gmail: `personal` (lsf.cin@gmail.com), `cin` (lsf@cin.ufpe.br), `ufrpe` (lucas.sfigueiredo@ufrpe.br).
