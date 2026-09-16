# gmail_fetch.py — Gmail API auth, fetch, and MIME parse for Core/tools/mail/gmail
import json, pathlib, base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

CONFIG_DIR = pathlib.Path.home() / ".config" / "workspace-gmail"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def auth(alias: str) -> Credentials:
    """Run OAuth2 flow for alias, persist token, return credentials."""
    token_path = CONFIG_DIR / f"{alias}.token.json"
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds_file = CONFIG_DIR / "credentials.json"
            if not creds_file.exists():
                raise FileNotFoundError(f"credentials.json not found at {creds_file}")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding='utf-8', newline='\n')

    return creds


def get_service(alias: str):
    """Return authenticated Gmail API service for alias."""
    return build("gmail", "v1", credentials=auth(alias))


def _decode_body(data: str) -> str:
    try:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_parts(payload: dict) -> tuple:
    """Return (body_text, attachments_list) from MIME payload."""
    body, attachments = "", []
    parts = payload.get("parts", [])

    if not parts:
        if payload.get("mimeType") == "text/plain":
            body = _decode_body(payload.get("body", {}).get("data", ""))
        return body, attachments

    for part in parts:
        mime = part.get("mimeType", "")
        filename = part.get("filename", "")

        if mime == "text/plain" and not filename:
            body = body or _decode_body(part.get("body", {}).get("data", ""))
        elif filename:
            attachments.append({
                "filename": filename,
                "mime": mime,
                "attachment_id": part.get("body", {}).get("attachmentId"),
                "size": part.get("body", {}).get("size", 0),
            })
        elif mime.startswith("multipart/"):
            sub_body, sub_att = _extract_parts(part)
            body = body or sub_body
            attachments.extend(sub_att)

    return body, attachments


def _header(headers: list, name: str) -> str:
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def fetch(alias: str, since_days: int = 7, max_results: int = 50) -> list:
    """Fetch recent unread emails for alias. Returns structured list."""
    service = get_service(alias)
    result = service.users().messages().list(
        userId="me", q=f"is:unread newer_than:{since_days}d", maxResults=max_results
    ).execute()

    emails = []
    for msg in result.get("messages", []):
        raw = service.users().messages().get(
            userId="me", id=msg["id"], format="full"
        ).execute()
        headers = raw.get("payload", {}).get("headers", [])
        body, attachments = _extract_parts(raw.get("payload", {}))
        emails.append({
            "id": msg["id"],
            "alias": alias,
            "from": _header(headers, "from"),
            "to": _header(headers, "to"),
            "subject": _header(headers, "subject"),
            "date": _header(headers, "date"),
            "snippet": raw.get("snippet", ""),
            "body_preview": body[:500],
            "attachments": attachments,
        })

    return emails


def fetch_all(aliases: list, since_days: int = 7) -> list:
    """Fetch from all aliases, merge and return."""
    all_emails = []
    for alias in aliases:
        try:
            emails = fetch(alias, since_days)
            all_emails.extend(emails)
            print(f"  {alias}: {len(emails)} emails", flush=True)
        except Exception as e:
            print(f"  {alias}: ERROR — {e}", flush=True)
    return all_emails
