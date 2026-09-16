# gmail_triage.py — Claude API email classification for Core/tools/mail/gmail
import json, anthropic

_SYSTEM = """You are triaging emails for Lucas, a CS professor in Brazil. Classify each email.

Routes:
- "task:today"   — urgent, deadline within 1-2 days
- "task:week"    — action needed, no hard deadline
- "task:month"   — important but not pressing
- "task:backlog" — newsletter, reading material, low priority
- "delete"       — noise: notifications, automated alerts, receipts

For each email return a JSON object:
{
  "index": <int>,
  "route": "<route>",
  "goal_hint": "<relevant goal area, e.g. career/papers, or null>",
  "urgency": "high|medium|low",
  "needs_reply": true|false,
  "summary_pt": "<1-sentence summary in Portuguese>",
  "inbox_entry": "<complete Brain/INBOX.md entry text, see format below>"
}

INBOX entry format (copy exactly, adapt content):
[src: gmail:<sender-email>]
[gmail/<alias>] <concise subject in Portuguese>
from: <sender-email> · <date as YYYY-MM-DD>
<route signal, e.g. "task: week">
[goal: <hint> — include only if goal_hint is set]
[attachment: Brain/attachments/YYYY-MM/<filename> — include only if has_attachment is true]

The [src: gmail:<sender-email>] line is mandatory on every entry — it marks the content as
non-Lucas-authored, so triage never promotes it verbatim into a trusted file (quote it instead).

Return only a valid JSON array of objects, one per email. No prose outside the JSON."""


def classify(emails: list) -> list:
    """Classify emails via Claude Haiku. Returns enriched list with route metadata."""
    if not emails:
        return []

    client = anthropic.Anthropic()

    payload = [
        {
            "index": i,
            "alias": e["alias"],
            "from": e["from"],
            "subject": e["subject"],
            "date": e["date"],
            "snippet": e["snippet"],
            "body_preview": e["body_preview"],
            "has_attachment": bool(e.get("attachments")),
            "attachment_names": [a["filename"] for a in e.get("attachments", [])],
        }
        for i, e in enumerate(emails)
    ]

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        system=_SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )

    results = json.loads(msg.content[0].text)
    return [{**emails[r["index"]], **r} for r in results]
