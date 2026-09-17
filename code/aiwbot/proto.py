# proto.py — live smoke: run one prompt through each backend + prove single-lineage resume. ~$0.10/run.
import asyncio
import pathlib
import sys
from backend import get_backend
from backend.base import check_contract

# The workspace root, found from where this file sits rather than named — same reason as
# frontend/config.py: two machines share this tree and neither path is the other's.
_CWD = str(pathlib.Path(__file__).resolve().parents[2])
_PROMPT = "reply with exactly: PONG"
_RESUME = "what single word did you just reply? one word only."


async def _collect(name: str, prompt: str, session_id: str | None) -> list:
    backend = get_backend(name)
    events = []
    async for event in backend.send(prompt, session_id=session_id, cwd=_CWD):
        events.append(event)
    return events


def _session_of(events: list) -> str | None:
    sid = None
    for event in events:
        if event.session_id:
            sid = event.session_id
    return sid


def _print_events(label: str, events: list) -> None:
    print(f"--- {label} ---")
    for event in events:
        clipped = event.text[:60]
        snippet = clipped.replace("\n", " ")
        short_sid = str(event.session_id)[:12]
        print(f"  {event.kind:8} sid={short_sid:12} cost={event.cost_usd} {snippet}")


async def _run_backend(name: str) -> bool:
    turn1 = await _collect(name, _PROMPT, None)
    _print_events(name, turn1)
    ok1, r1 = check_contract(turn1)
    sid = _session_of(turn1)
    turn2 = await _collect(name, _RESUME, sid)
    short = str(sid)[:8]
    _print_events(f"{name} resume {short}", turn2)
    ok2, r2 = check_contract(turn2)
    passed = ok1 and ok2
    print(f"  => {name}: turn1={r1} turn2={r2} PASS={passed}\n")
    return passed


async def _main() -> None:
    args = sys.argv[1:]
    names = args or ["claude", "opencode"]
    results = []
    for name in names:
        passed = await _run_backend(name)
        results.append(passed)
    allpass = all(results)
    verdict = "ALL PASS" if allpass else "SOME FAILED"
    print(verdict)
    code = 0 if allpass else 1
    sys.exit(code)


if __name__ == "__main__":
    asyncio.run(_main())
