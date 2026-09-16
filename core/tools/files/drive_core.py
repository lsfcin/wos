# drive_core.py — Google Drive read+write boundary (account-agnostic) for Core/tools/files/gdrive
import pathlib
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parents[2]))
import gauth

SCOPES_READ  = ["https://www.googleapis.com/auth/drive.readonly"]
SCOPES_WRITE = ["https://www.googleapis.com/auth/drive"]

EXPORT_MIME = {
    "application/vnd.google-apps.document":     "application/pdf",
    "application/vnd.google-apps.spreadsheet":  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.google-apps.presentation": "application/pdf",
}

# (gdoc mimeType, requested format) -> export mimeType, for callers that need
# an editable format instead of the PDF default (e.g. reading tables verbatim).
EXPORT_MIME_OVERRIDES = {
    ("application/vnd.google-apps.document", "docx"): "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    # Markdown is the format an agent can actually read, and Drive converts it back on
    # upload — so this row is what makes a repo .md and a live Doc the same document.
    ("application/vnd.google-apps.document", "md"): "text/markdown",
}

EXPORT_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/markdown": ".md",
}

FILE_FIELDS = "id,name,mimeType,modifiedTime,size,parents,webViewLink"

GDOC_MIME = "application/vnd.google-apps.document"


def get_service(alias: str, write: bool = False):
    """Build a Drive service for alias. Read uses the `drive` token (readonly);
    write uses a separate `drive-write` token (full scope) so it never clobbers
    the readonly one."""
    service, scopes = ("drive-write", SCOPES_WRITE) if write else ("drive", SCOPES_READ)
    return build("drive", "v3", credentials=gauth.auth(alias, service, scopes))


# ── Reads (per-alias; build their own readonly service) ────────────────────────

def list_files(alias: str, folder_id: str = "root", page_size: int = 50) -> list:
    svc = get_service(alias)
    q = f"'{folder_id}' in parents and trashed=false"
    res = svc.files().list(q=q, pageSize=page_size, fields=f"files({FILE_FIELDS})").execute()
    return res.get("files", [])


def search_files(alias: str, query: str, page_size: int = 20) -> list:
    svc = get_service(alias)
    q = f"fullText contains '{query}' and trashed=false"
    res = svc.files().list(q=q, pageSize=page_size, fields=f"files({FILE_FIELDS})").execute()
    return res.get("files", [])


def recent_files(alias: str, page_size: int = 30) -> list:
    svc = get_service(alias)
    res = svc.files().list(
        pageSize=page_size,
        orderBy="modifiedTime desc",
        fields=f"files({FILE_FIELDS})",
        q="trashed=false",
    ).execute()
    return res.get("files", [])


def download_file(alias: str, file_id: str, dest_dir: pathlib.Path, export_as: str = None) -> pathlib.Path:
    """Download or export file. `export_as` (e.g. "docx") overrides the default
    export mimeType for Google-native files. Returns saved path."""
    svc = get_service(alias)
    meta = svc.files().get(fileId=file_id, fields="name,mimeType").execute()
    name, mime = meta["name"], meta["mimeType"]

    dest_dir.mkdir(parents=True, exist_ok=True)

    if mime in EXPORT_MIME:
        export_mime = EXPORT_MIME_OVERRIDES.get((mime, export_as), EXPORT_MIME[mime])
        ext = EXPORT_EXT.get(export_mime, "")
        req = svc.files().export_media(fileId=file_id, mimeType=export_mime)
        name = name + ext
    else:
        req = svc.files().get_media(fileId=file_id)

    path = dest_dir / name
    with open(path, "wb") as fh:
        dl = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            _, done = dl.next_chunk()

    return path


# ── Writes (take an explicit write service so callers reuse one across ops) ─────

def list_folder(svc, folder_id: str) -> list:
    items, page_token = [], None
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
            pageSize=1000,
        ).execute()
        items.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return items


def find_or_create_folder(svc, name: str, parent_id: str, dry_run: bool = False) -> str:
    if dry_run:
        return f"[dry-run-folder:{name}]"
    resp = svc.files().list(
        q=(f"'{parent_id}' in parents"
           f" and name='{name.replace(chr(39), chr(39)+chr(39))}'"
           f" and mimeType='application/vnd.google-apps.folder'"
           f" and trashed=false"),
        fields="files(id, name)",
    ).execute()
    existing = resp.get("files", [])
    if existing:
        return existing[0]["id"]
    folder = svc.files().create(
        body={
            "name": name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        },
        fields="id",
    ).execute()
    return folder["id"]


def copy_file(svc, file_id: str, name: str, parent_id: str) -> dict:
    return svc.files().copy(
        fileId=file_id,
        body={"name": name, "parents": [parent_id]},
        fields="id, webViewLink",
    ).execute()


def list_permissions(svc, file_id: str) -> list:
    """Who can reach this file, and how. Read before copying anything someone else edits —
    a copy starts private, so the other person silently loses the file unless this is replayed."""
    res = svc.permissions().list(
        fileId=file_id, fields="permissions(id, type, role, emailAddress, domain)").execute()
    return res.get("permissions", [])


def grant_permission(svc, file_id: str, email: str = None, role: str = "writer",
                     kind: str = "user", notify: bool = False) -> dict:
    """`notify=False` on purpose: the point is to keep access someone already had, and a mail
    saying a file was shared with them is confusing when nothing changed for them.
    `kind="anyone"` restores link access — the thing a CSV export URL depends on, and the one
    permission a copy silently drops."""
    body = {"type": kind, "role": role}
    if kind == "user":
        body["emailAddress"] = email
    return svc.permissions().create(
        fileId=file_id, sendNotificationEmail=notify, body=body, fields="id").execute()


def trash_file(svc, file_id: str) -> dict:
    """Trash, never `files().delete()`. The bin is recoverable for 30 days and a permanent delete
    of someone else's live document has no undo at all."""
    return svc.files().update(fileId=file_id, body={"trashed": True}, fields="id, name").execute()


def upload_local(svc, path: pathlib.Path, parent_id: str, as_gdoc: bool = False,
                 name: str = None) -> dict:
    """Upload a local file to parent_id. When as_gdoc, the target mimeType is a
    Google Doc so Drive converts (e.g. .docx→Google Doc) on import. Returns the
    created file's {id, name, webViewLink}."""
    path = pathlib.Path(path)
    media = MediaFileUpload(str(path), resumable=True)
    body = {"name": name or path.name, "parents": [parent_id]}
    if as_gdoc:
        body["mimeType"] = GDOC_MIME
    return svc.files().create(
        body=body, media_body=media, fields="id,webViewLink,name"
    ).execute()
