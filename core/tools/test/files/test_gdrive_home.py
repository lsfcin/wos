# T1 home account: a one-account Google command without --account lands on the workspace's own account (the first configured), never asks.
import importlib.machinery
import importlib.util
import sys

from conftest import WORKSPACE_ROOT

sys.path.insert(0, str(WORKSPACE_ROOT / "core/tools/auth"))
import gauth  # noqa: E402

ACCOUNTS = [{"aliases": ["personal", "pessoal"]}, {"aliases": ["ufrpe", "rural"]}]


def load(relative: str):
    loader = importlib.machinery.SourceFileLoader(relative.replace("/", "_"), str(WORKSPACE_ROOT / relative))
    module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
    loader.exec_module(module)
    return module


def test_no_alias_resolves_to_the_first_account_and_a_named_one_still_wins(monkeypatch) -> None:
    monkeypatch.setattr(gauth, "get_accounts", lambda: ACCOUNTS)
    assert gauth.resolve_alias(None) == "personal"
    assert gauth.resolve_alias("rural") == "ufrpe"


def test_put_without_account_goes_home_and_explicit_account_wins(monkeypatch) -> None:
    gdrive = load("core/tools/files/gdrive")
    monkeypatch.setattr(gdrive.gauth, "get_accounts", lambda: ACCOUNTS)
    seen = []
    monkeypatch.setattr(gdrive.drive_core, "get_service", lambda alias, write=False: seen.append(alias))
    monkeypatch.setattr(gdrive.drive_core, "upload_local", lambda *a, **k: {"name": "x", "id": "1"})
    for argv in (["gdrive", "put", "x.pdf"], ["gdrive", "put", "--account", "ufrpe", "x.pdf"]):
        monkeypatch.setattr(sys, "argv", argv)
        gdrive.main()
    assert seen == ["personal", "ufrpe"]


def test_every_google_cli_lets_account_default() -> None:
    for relative in ("core/tools/files/gdrive", "core/tools/docs/gdocs", "core/tools/slides/gslides", "core/tools/forms/gforms"):
        text = (WORKSPACE_ROOT / relative).read_text(encoding="utf-8")
        assert '"--account", required=True' not in text, relative
