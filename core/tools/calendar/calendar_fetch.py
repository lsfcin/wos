# calendar_fetch.py — Google Calendar API auth and event fetch for Core/tools/calendar/gcalendar
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[2]))
import gauth

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

EVENT_FIELDS = "items(id,summary,description,start,end,location,status,htmlLink)"


def get_service(alias: str):
    return build("calendar", "v3", credentials=gauth.auth(alias, "calendar", SCOPES))


def list_calendars(alias: str) -> list:
    svc = get_service(alias)
    res = svc.calendarList().list().execute()
    return res.get("items", [])


def upcoming_events(alias: str, days: int = 7, cal_id: str = "primary", max_results: int = 20) -> list:
    svc = get_service(alias)
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days)
    res = svc.events().list(
        calendarId=cal_id,
        timeMin=now.isoformat(),
        timeMax=end.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy="startTime",
        fields=EVENT_FIELDS,
    ).execute()
    return res.get("items", [])


def events_in_range(alias: str, date_from: str, date_to: str, cal_id: str = "primary") -> list:
    """date_from/date_to: ISO 8601 strings (e.g. '2026-06-01T00:00:00Z')."""
    svc = get_service(alias)
    res = svc.events().list(
        calendarId=cal_id,
        timeMin=date_from,
        timeMax=date_to,
        singleEvents=True,
        orderBy="startTime",
        fields=EVENT_FIELDS,
    ).execute()
    return res.get("items", [])


def _fmt_event(e: dict) -> dict:
    start = e.get("start", {})
    end = e.get("end", {})
    return {
        "id": e.get("id"),
        "title": e.get("summary", "(sem título)"),
        "start": start.get("dateTime", start.get("date", "")),
        "end": end.get("dateTime", end.get("date", "")),
        "location": e.get("location", ""),
        "description": (e.get("description") or "")[:200],
        "link": e.get("htmlLink", ""),
    }


def fmt_events(events: list) -> list:
    return [_fmt_event(e) for e in events]
