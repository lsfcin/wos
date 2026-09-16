# gcli.py — the two things every Google-backed CLI does identically: consent, and fan out over accounts
#
# Shares the tools root with gauth's callers for the reason core/tools/SPECS.md gives: a module
# imported by more than one family belongs here. `cmd_auth` had been copy-pasted into gslides,
# gdrive, gcalendar and gforms with only the grant name changing, and the fifth copy was about to
# arrive with gdocs — at which point the duplication gate would have rejected it. mail/gmail is
# deliberately NOT a caller: it keeps its own credentials.json and predates gauth.config_dir.
import pathlib as _pathlib
import sys as _sys

_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent / 'auth'))
import gauth  # noqa: E402


def run(main_fn, *refusals) -> None:
    """`gauth.run`, plus this CLI's own refusals printed as their message.

    gauth already converts a dead token and a rejected API call into one readable line,
    on the principle that a message naming its own fix is worth nothing inside a
    traceback. A tool that refuses work *before* the network — gdocs rejecting a batch
    whose indices run the wrong way — produces exactly that kind of message and had
    exactly that problem, so it takes the same exit.
    """
    try:
        gauth.run(main_fn)
    except refusals as exc:
        _sys.exit(str(exc))


def aliases(account: str) -> list:
    """Which aliases a command runs over: one named account, or every configured one."""
    return gauth.primary_aliases() if account == "all" else [gauth.resolve_alias(account)]


def auth_command(kind: str, alias: str, connect, reauth: bool = False) -> None:
    """Run one OAuth consent for a grant, and print where the token actually landed.

    `kind` is the grant name, which IS the config directory suffix — `slides` and
    `slides-write` are two directories, and inferring the second from the first is the
    failure slides/SPECS.md records costing a session. So the last line prints the real
    path rather than leaving the caller to reconstruct it.

    `connect` is the tool's own `get_service`-shaped callable, taking the resolved primary
    alias. It is passed in rather than looked up because that call is the only part of
    consent a family does differently.
    """
    primary = gauth.resolve_alias(alias)
    token = gauth.config_dir(kind) / f"{primary}.token.json"
    if reauth and token.exists():
        # drop the stale token so a revoked/expired one can't dead-end on refresh
        token.unlink()
        print(f"Removed stale token: {token}")
    print(f"Opening browser for OAuth — {kind} ({primary})...")
    connect(primary)
    print(f"Done. Token saved: {token}")
