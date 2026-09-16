# gmail_attachments.py — download and summarize Gmail attachments for Core/tools/mail/gmail
import base64, pathlib, subprocess
import anthropic
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[1]))  # tools root
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[2] / 'hooks'))
import attachments_util
from platform_law import WORKSPACE_ROOT, interpreter

BRAIN_ATTACHMENTS = WORKSPACE_ROOT / "brain/attachments"


def _extract_text(filepath: pathlib.Path) -> str:
    """Try to extract text from file using Core/tools/parse."""
    try:
        # Spawned through interpreter(), never by its own path: `parse` is an extensionless script
        # whose shebang only means anything on POSIX, so naming it alone fails with WinError 193
        # here -- and this arm swallows every exception, so the summary would just come back empty.
        result = subprocess.run(
            [interpreter(), str(WORKSPACE_ROOT / "core/tools/paper/parse"), str(filepath)],
            capture_output=True, text=True, timeout=30, encoding='utf-8'
        )
        return result.stdout[:3000] if result.returncode == 0 else ""
    except Exception:
        return ""


def _summarize(filepath: pathlib.Path, email_meta: dict) -> str:
    """Generate AI summary of attachment, return markdown text."""
    text = _extract_text(filepath)
    date_raw = email_meta.get("date", "")
    # Try to shorten date to YYYY-MM-DD
    date_short = date_raw[:10] if date_raw else "unknown"

    client = anthropic.Anthropic()
    prompt = (
        f"Summarize this email attachment for a personal knowledge base.\n\n"
        f"File: {filepath.name}\n"
        f"From: {email_meta.get('from', 'unknown')}\n"
        f"Date: {date_short}\n"
        f"Subject: {email_meta.get('subject', 'unknown')}\n\n"
        f"Content:\n{text or '[binary or unreadable file]'}\n\n"
        f"Return exactly this markdown format:\n"
        f"# {filepath.name}\n"
        f"from: <sender-email> | account: {email_meta.get('alias', '?')} | date: {date_short}\n"
        f"type: <document type in 2-3 words>\n"
        f"summary: <2-3 sentences in Portuguese>\n"
        f"key-fields: <comma-separated key items, deadlines, names>"
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


def download(service, alias: str, email_id: str, attachment: dict, email_meta: dict) -> pathlib.Path | None:
    """Download attachment from Gmail API, save + summarize. Returns saved path or None."""
    att_id = attachment.get("attachment_id")
    if not att_id:
        return None

    try:
        raw = service.users().messages().attachments().get(
            userId="me", messageId=email_id, id=att_id
        ).execute()
        data = base64.urlsafe_b64decode(raw["data"] + "==")
    except Exception as e:
        print(f"  Failed to download {attachment['filename']}: {e}")
        return None

    month_dir = attachments_util.month_dir(BRAIN_ATTACHMENTS)
    filepath = attachments_util.unique_path(month_dir / attachments_util.safe_name(attachment["filename"]))
    filepath.write_bytes(data)

    summary = _summarize(filepath, {**email_meta, "alias": alias})
    (filepath.parent / f"{filepath.stem}.summary.md").write_text(summary, encoding='utf-8', newline='\n')

    return filepath
