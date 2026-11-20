# T1 auth recovery: a dead Google token must hand Lucas a runnable fix, not a traceback.
import os
import pathlib
import subprocess
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import gauth
from platform_law import interpreter


ACCOUNTS = [
    {"aliases": ["personal", "pessoal"], "email": "lsf.cin@gmail.com"},
    {"aliases": ["cin", "voxar"], "email": "lsf@cin.ufpe.br"},
]


@pytest.fixture
def accounts(monkeypatch):
    monkeypatch.setattr(gauth, "get_accounts", lambda: ACCOUNTS)


def test_secondary_alias_resolves_to_its_account_address(accounts):
    """Lucas types 'pessoal'; the consent screen still has to name the primary address."""
    assert gauth.account_email("pessoal") == "lsf.cin@gmail.com"
    assert gauth.account_email("voxar") == "lsf@cin.ufpe.br"


def test_unknown_alias_says_where_to_look_rather_than_guessing(accounts):
    email = gauth.account_email("nope")
    assert "accounts.json" in email


def test_recovery_names_the_command_and_the_account(accounts):
    """The two things the message exists to carry. Four accounts make the address load-bearing."""
    text = gauth.recovery_text("personal", "drive", pathlib.Path("/tmp/t.json"))
    assert "core/run tools/files/gdrive auth personal --reauth" in text
    assert "lsf.cin@gmail.com" in text


def test_drive_write_recovers_with_the_write_flag(accounts):
    """A read re-consent leaves the write token dead, so the flag cannot be dropped."""
    text = gauth.recovery_text("cin", "drive-write", pathlib.Path("/tmp/t.json"))
    assert "--write --reauth" in text


def test_service_without_a_reauth_flag_still_gets_a_runnable_step(accounts):
    """A service outside the table falls back to naming the real token path."""
    token = pathlib.Path("/home/x/.config/workspace-sheets/cin.token.json")
    text = gauth.recovery_text("cin", "sheets", token)
    assert str(token) in text
    assert "lsf@cin.ufpe.br" in text


def test_run_prints_the_instruction_instead_of_raising(accounts, capsys):
    """Entrypoints wrap main() in run(); a traceback here is the bug this guards."""
    def boom():
        raise gauth.AuthExpired("SIGN IN AS: lsf.cin@gmail.com")

    with pytest.raises(SystemExit) as exit_info:
        gauth.run(boom)
    assert "lsf.cin@gmail.com" in str(exit_info.value)


TOOLS_ROOT = pathlib.Path(__file__).resolve().parents[1]


def _gauth_clis():
    """Every CLI that authenticates through gauth — found by scan, never by list.

    The list form went stale the moment the tools moved onto the feature axis, which is
    exactly the move this guard has to survive.
    """
    for path in sorted(TOOLS_ROOT.rglob("*")):
        if not path.is_file() or path.suffix or path.name.startswith("."):
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        if "import" in body and "gauth" in body:
            yield path, body


def _run_check_shim(tmp_path, module: str, attr: str = "run"):
    """A sitecustomize that replaces the entrypoint wrapper with a recorder.

    Loaded before the CLI's own code, so `<module>.<attr>` is already the recorder by the
    time the CLI reaches it. The recorder raises SystemExit(0) immediately: nothing after
    the wrapper runs, so no network and no consent flow is ever reached.
    """
    shim = tmp_path / "shim"
    shim.mkdir(parents=True)
    check = tmp_path / "check.txt"
    (shim / "sitecustomize.py").write_text(
        "import os, pathlib, sys\n"
        f"sys.path.insert(0, {str(TOOLS_ROOT / 'auth')!r})\n"
        f"sys.path.insert(0, {str(TOOLS_ROOT / 'notes')!r})\n"
        f"import {module}\n"
        "def _rec(main_fn):\n"
        "    pathlib.Path(os.environ['RUN_CHECK']).write_text('called')\n"
        "    raise SystemExit(0)\n"
        f"{module}.{attr} = _rec\n", encoding="utf-8", newline='\n')
    return shim, check


def _reaches_wrapper(cli, tmp_path, module: str) -> bool:
    shim, check = _run_check_shim(tmp_path, module)
    subprocess.run([interpreter(), str(cli)], capture_output=True, text=True, timeout=60,
                   env={**os.environ, "PYTHONPATH": str(shim), "RUN_CHECK": str(check)}, encoding='utf-8')
    return check.exists()


def test_every_google_cli_routes_its_entrypoint_through_run(tmp_path):
    """Run each CLI and watch the wrapper actually get called.

    This replaced `"gauth.run(main)" in body` on 2026-08-24. A CLI calling main() directly
    would print a traceback and lose the instruction — and the substring could not tell the
    difference between the call and the same characters in a comment.
    """
    found = list(_gauth_clis())
    assert found, "no gauth-backed CLI found — the scan is looking in the wrong place"
    bypassed = [cli.name for cli, _ in found
                if not _reaches_wrapper(cli, tmp_path / cli.name, "gauth")]
    assert not bypassed, f"these CLIs never reach gauth.run: {bypassed}"


def test_every_reauth_command_names_a_tool_that_exists():
    """The recovery message is only runnable while its path is real, and only through core/run:
    the tools carry no shebang, so a bare path dies in the shell. Renames rot it silently."""
    workspace_root = TOOLS_ROOT.parents[1]
    for service, template in gauth._REAUTH_CMD.items():
        runner, rel = template.format(alias="personal").split()[:2]
        assert runner == "core/run", f"recovery for '{service}' skips core/run: {template}"
        tool = workspace_root / "core" / rel
        assert tool.is_file(), f"recovery for '{service}' points at a missing tool: {tool}"
