# docs_drive.py — the half of a Google Doc that the Docs API cannot reach: listing, markdown, comments
import html, pathlib, sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent / 'auth'))
sys.path.insert(0, str(_HERE.parent / 'files'))
from googleapiclient.http import MediaFileUpload
import drive_core
import gauth

GDOC_MIME = drive_core.GDOC_MIME
MD_MIME = "text/markdown"

# Everything here rides the tokens files/gdrive already owns. A `docs-drive` grant would
# be a third and fourth config directory holding consents the account has twice over.
COMMENT_FIELDS = ("comments(id,content,resolved,createdTime,author/displayName,"
                  "quotedFileContent/value,replies(content,createdTime,author/displayName))")


def list_documents(alias: str, name: str = "") -> list:
    """List documents from Drive. Optionally filter by name substring.

    The Docs API has no list endpoint at all — it only answers about a document you can
    already name — so discovery is Drive's job, exactly as it is for slides.
    """
    svc = drive_core.get_service(alias)
    q = f"mimeType='{GDOC_MIME}' and trashed=false"
    if name:
        q += f" and name contains '{name}'"
    res = svc.files().list(
        q=q,
        pageSize=100,
        fields="files(id,name,modifiedTime,webViewLink)",
        orderBy="modifiedTime desc",
    ).execute()
    return res.get("files", [])


def export_md(alias: str, document_id: str) -> str:
    """The document as Markdown — headings, bold, lists, tables and links intact.

    This is the read an agent actually wants. `documents.get` returns the same words
    wrapped in several kilobytes of style objects per paragraph; Drive's own exporter
    already knows how to render them, so asking it costs one call and no parser.
    """
    svc = drive_core.get_service(alias)
    return svc.files().export_media(
        fileId=document_id, mimeType=MD_MIME
    ).execute().decode("utf-8")


def push_md(alias: str, document_id: str, md_path) -> dict:
    """Replace the whole body of an existing document from a Markdown file.

    Drive re-converts on update and, in Google's words, "the full contents of the
    document are replaced" — the file id, URL and sharing all survive, which is what
    makes this a sync rather than a re-upload. What does NOT survive is anything anchored
    to the text that goes away: see SPECS.md before pushing over a reviewed document.
    """
    svc = drive_core.get_service(alias, write=True)
    media = MediaFileUpload(str(md_path), mimetype=MD_MIME, resumable=True)
    return svc.files().update(
        fileId=document_id, media_body=media, fields="id,name,webViewLink"
    ).execute()


def create_from_md(alias: str, title: str, md_path, folder_id: str = "") -> dict:
    """Create a document whose content is a Markdown file, converted by Drive on import."""
    svc = drive_core.get_service(alias, write=True)
    body = {"name": title, "mimeType": GDOC_MIME}
    if folder_id:
        body["parents"] = [folder_id]
    media = MediaFileUpload(str(md_path), mimetype=MD_MIME, resumable=True)
    return svc.files().create(
        body=body, media_body=media, fields="id,name,webViewLink"
    ).execute()


def comments(alias: str, document_id: str, include_resolved: bool = False) -> list:
    """Comment threads on the document, newest first, each with the text it is anchored to.

    Comments live in Drive, not in Docs — a `documents.get` never mentions them, which is
    why a document can read as finished while carrying twenty open objections.
    """
    svc = drive_core.get_service(alias)
    found, token = [], None
    while True:
        res = svc.comments().list(
            fileId=document_id, pageSize=100, pageToken=token,
            fields=f"nextPageToken,{COMMENT_FIELDS}",
        ).execute()
        found.extend(res.get("comments", []))
        token = res.get("nextPageToken")
        if not token:
            break
    if not include_resolved:
        found = [c for c in found if not c.get("resolved")]
    return [_unescaped(c) for c in found]


def _unescaped(comment: dict) -> dict:
    """Drive returns comment text HTML-escaped, anchors included.

    Confirmed 2026-08-26: a thread anchored to "Seção dois" comes back as
    "Se&#231;&#227;o dois". Left alone it reaches the agent as mojibake, and any quote of
    it back to Lucas is wrong — so the decoding happens here, once, rather than at each
    of the places that render a comment.
    """
    comment["content"] = html.unescape(comment.get("content", ""))
    anchor = comment.get("quotedFileContent")
    if anchor:
        anchor["value"] = html.unescape(anchor.get("value", ""))
    for reply in comment.get("replies", []):
        reply["content"] = html.unescape(reply.get("content", ""))
    return comment
