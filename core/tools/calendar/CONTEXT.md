# calendar
> Read what is scheduled. Provider leaf: `gcalendar`. Auth: [`../auth/gauth.py`](../auth/gauth.py).

Read-only by design — nothing here writes an event. `--account all` fans out over every alias in
`accounts.json`, which is the normal case: Lucas's teaching, research and personal calendars are
three separate Google accounts.

<!-- routing:start -->
## Routing

| File | Interface | API | Description |
|------|-----------|-----|-------------|
| [`calendar_fetch.py`](calendar_fetch.py) | [`calendar_fetch.pyi`](calendar_fetch.pyi) | `get_service`, `list_calendars`, `upcoming_events`, `events_in_range`, `fmt_events` | calendar_fetch.py — Google Calendar API auth and event fetch for Core/tools/calendar/gcalendar |
| [`gcalendar`](gcalendar) | — | — | Google Calendar read-only CLI for workspace OS — commands: auth, upcoming, range, calendars |
<!-- routing:end -->
