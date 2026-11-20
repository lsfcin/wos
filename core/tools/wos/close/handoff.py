# Repository handoffs: names and edit counts come from local records, never a model.
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'hooks'))
from platform_law import locked  # noqa: E402


def name_of(value: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', value.lower()).strip('-')[:64] or 'workspace'


def identity(session: str = '', agent: str = '') -> tuple[str, str]:
    """Never infer the active session from the newest transcript in a shared directory."""
    if not session:
        if os.environ.get('CODEX_THREAD_ID') or os.environ.get('CODEX_SESSION_ID'):
            session = os.environ.get('CODEX_THREAD_ID') or os.environ['CODEX_SESSION_ID']
            agent = agent or 'chatgpt'
        elif os.environ.get('CLAUDE_CODE_SESSION_ID') or os.environ.get('CLAUDE_SESSION_ID'):
            session = os.environ.get('CLAUDE_CODE_SESSION_ID') or os.environ['CLAUDE_SESSION_ID']
            agent = agent or 'claude'
    if not session or not agent:
        raise ValueError('No session identity: pass --session and --agent from the native session metadata.')
    return session, name_of(agent)


def records(path: Path):
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue  # a live transcript can end with an unfinished record
            if isinstance(row, dict):
                yield row


def started(path: Path | None) -> float:
    """Epoch seconds of a transcript's first timestamp; 0.0 when there is none to read."""
    from datetime import datetime
    for row in records(path) if path and path.is_file() else ():
        stamp = row.get('timestamp')
        if isinstance(stamp, str):
            return datetime.fromisoformat(stamp.replace('Z', '+00:00')).timestamp()
    return 0.0


def transcript(session: str, agent: str, cwd: Path, given: str = '') -> Path | None:
    if given:
        path = Path(given)
        # Supplied Claude logs name the session on each record; Codex names it in session_meta.
        owned = any(row.get('sessionId') == session or
                    (row.get('type') == 'session_meta' and row.get('payload', {}).get('id') == session)
                    for row in records(path))
        if not owned:
            raise ValueError('Transcript does not identify the requested session.')
        return path
    if agent == 'chatgpt':
        home = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex')))
        matches = list((home / 'sessions').glob(f'**/*-{session}.jsonl'))
    elif agent == 'claude':
        project = re.sub(r'[^A-Za-z0-9]', '-', str(cwd))
        matches = list((Path.home() / '.claude' / 'projects' / project).glob(f'{session}.jsonl'))
    else:
        matches = []
    if len(matches) > 1:
        raise ValueError('Multiple transcripts for this session; pass --transcript explicitly.')
    return matches[0] if matches else None


def patch_lines(text: str) -> Counter:
    """Count recorded additions + removals; headers and hunk context are not edits."""
    counts, path = Counter(), ''
    for line in text.splitlines():
        if line.startswith(('*** Add File: ', '*** Update File: ', '*** Delete File: ')):
            path = line.split(': ', 1)[1]
        elif line.startswith('*** Move to: '):
            path = line.split(': ', 1)[1]
        elif line.startswith('*** '):
            path = ''
        elif path and line.startswith(('+', '-')):
            counts[path] += 1
    return counts


def successful(output) -> bool:
    """Codex patch results need a positive success marker, not merely an absence of errors."""
    text = json.dumps(output) if not isinstance(output, str) else output
    return 'Success. Updated the following files:' in text and not any(
        word in text for word in ('"isError": true', 'Failed to', 'patch verification failed'))


def edits(path: Path, cwd: Path) -> Counter:
    counts, pending = Counter(), {}
    for row in records(path):
        if row.get('isSidechain'):
            continue
        if row.get('type') == 'turn_context':
            cwd = Path(row.get('payload', {}).get('cwd', cwd))
        payload = row.get('payload', {})
        if row.get('type') == 'response_item':
            kind = payload.get('type')
            if kind in ('custom_tool_call', 'function_call') and payload.get('name', '').split('.')[-1] == 'apply_patch':
                patch = payload.get('input', payload.get('arguments', ''))
                pending[payload.get('call_id')] = (patch_lines(patch), cwd)
            elif kind in ('custom_tool_call_output', 'function_call_output'):
                call = pending.pop(payload.get('call_id'), None)
                if call and successful(payload.get('output')):
                    changes, base = call
                    counts.update({str((base / name).resolve()): n for name, n in changes.items()})
        content = row.get('message', {}).get('content', [])
        for block in content if isinstance(content, list) else []:
            if block.get('type') == 'tool_use' and block.get('name') == 'Edit':
                args = block.get('input', {})
                name = args.get('file_path', '')
                n = len(args.get('old_string', '').splitlines()) + len(args.get('new_string', '').splitlines())
                pending[block.get('id')] = (Counter({name: n}), cwd)
            elif block.get('type') == 'tool_result':
                call = pending.pop(block.get('tool_use_id'), None)
                if call and not block.get('is_error'):
                    changes, base = call
                    counts.update({str((base / name).resolve()): n for name, n in changes.items() if name})
    return counts


def repository(path: Path) -> Path | None:
    while not path.is_dir() and path != path.parent:
        path = path.parent
    result = subprocess.run(['git', '-C', str(path), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        return None
    common = subprocess.run(['git', '-C', str(path), 'rev-parse', '--path-format=absolute', '--git-common-dir'],
                            capture_output=True, text=True, encoding='utf-8')
    git_dir = Path(common.stdout.strip())
    # Worktrees share a repository; aggregate their lines under the primary checkout.
    return git_dir.parent if common.returncode == 0 and git_dir.name == '.git' else Path(result.stdout.strip())


def choose(root: Path, cwd: Path, session: str, agent: str, log: Path | None) -> dict:
    """Git's shared dirty tree is never evidence of what one session changed."""
    totals, roots = Counter(), {}
    for name, n in edits(log, cwd).items() if log else []:
        path = Path(name)
        parent = path.parent
        if parent not in roots:
            roots[parent] = repository(parent)
        repo = roots[parent]
        # outputs/ is the workspace's scratch, handoffs included; a repo nested there is real work.
        if path.is_relative_to(root / 'outputs') and repo == root:
            continue
        if repo and n:
            totals[str(repo)] += n
    ranked = sorted(totals, key=lambda p: (-totals[p], p)) or [str(repository(cwd) or cwd)]
    repos = [{'repository': r, 'key': key_of(root, Path(r)), 'lines': totals.get(r, 0)} for r in ranked]
    for entry in repos:
        entry['path'] = str(path_for(root, entry['key']))
    return {**repos[0], 'repos': repos, 'agent': agent, 'session': session,
            'lines': dict(totals), 'basis': 'confirmed Edit/patch lines' if totals else 'working repository fallback',
            'limitation': 'Shell/script writes, full-file replacements and implicit deletions are not measurable from these records.'}


# ONE HANDOFF PER REPOSITORY, A MAILBOX (Lucas, 2026-11-10). A session writes one section into each
# repository it worked in; sections from sessions that never met pile up until one session TAKES the
# file, which hands it every pending thread and deletes it. One file per repository and environment,
# latest wins, silently destroyed a parallel session's handoff — the defect this replaced.
MARKER = re.compile(r'^<!-- handoff-session: (\[.*?\]) -->\n', re.M)
TAKEN = ('— Taken: this file is deleted, and every thread above is now yours. Finish it, move it to its '
         'ROADMAP or ISSUES, or carry it into your own handoff.')


def key_of(root: Path, repo: Path) -> str:
    """The repository's path under the workspace, so two repositories never share a handoff."""
    try:
        part = Path(repo).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        part = Path(repo).name
    return 'workspace' if part == '.' else name_of(part)


def path_for(root: Path, key: str) -> Path:
    return Path(root) / 'outputs' / f'handoff-{key}.md'


def lock_for(path: Path) -> Path:
    return path.with_name(f'.{path.stem}.lock')


def _sections(text: str) -> list[tuple[str, str]]:
    """(owner, section) pairs, owner being the marker's JSON; text before any marker is kept."""
    starts = [m.start() for m in MARKER.finditer(text)]
    head = text[:starts[0]] if starts else text
    out = [('', head)] if head.strip() else []
    for begin, end in zip(starts, starts[1:] + [len(text)]):
        out.append((MARKER.match(text, begin).group(1), text[begin:end]))
    return out


def write(path: Path, agent: str, session: str, text: str) -> None:
    """Add this session's section; a section it wrote earlier is replaced, never another's."""
    owner = json.dumps([agent, session])
    section = f'<!-- handoff-session: {owner} -->\n' + text.strip('\n') + '\n'
    with locked(lock_for(path)):
        pending = _sections(path.read_text(encoding='utf-8')) if path.exists() else []
        kept = [s.strip('\n') + '\n' for o, s in pending if o != owner]
        temp = path.with_suffix('.tmp')
        temp.write_text('\n'.join(kept + [section]), encoding='utf-8', newline='\n')
        temp.replace(path)


def take(path: Path) -> str | None:
    """Every pending section, handed to one taker and deleted; None when nothing is pending."""
    if not path.exists():
        return None   # asked before locking, so a mistyped key leaves no lock file behind
    with locked(lock_for(path)):
        if not path.exists():
            return None
        text = path.read_text(encoding='utf-8')
        path.unlink()
    return text.rstrip('\n') + '\n\n' + TAKEN + '\n'
