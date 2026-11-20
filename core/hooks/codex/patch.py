# Translate Codex apply_patch into complete file contents without writing anything.
from pathlib import Path


def locate(lines: list[str], wanted: list[str], start: int, eof: bool = False) -> int:
    """Codex matches exact context first, then tolerates whitespace differences."""
    if not wanted:
        return len(lines) if eof else start
    positions = [len(lines) - len(wanted)] if eof else range(start, len(lines) - len(wanted) + 1)
    for normalise in (lambda s: s, str.rstrip, str.strip):
        expected = list(map(normalise, wanted))
        for i in positions:
            if i >= start and list(map(normalise, lines[i:i + len(wanted)])) == expected:
                return i
    raise ValueError('Patch context does not match the current file')


def updated(content: str, body: list[str]) -> str:
    if body and not body[0].startswith('@@'):
        body = ['@@', *body]
    lines, cursor, index = content.splitlines(), 0, 0
    while index < len(body):
        header = body[index]
        if not header.startswith('@@'):
            raise ValueError('Expected a patch hunk header')
        anchor = header[3:] if header.startswith('@@ ') else ''
        if anchor:
            cursor = locate(lines, [anchor], cursor) + 1
        index += 1
        before, after, eof = [], [], False
        while index < len(body) and not body[index].startswith('@@'):
            line = body[index]
            index += 1
            if line == '*** End of File':
                eof = True
                break
            if not line:
                line = ' '
            if line[0] not in ' +-':
                raise ValueError('Invalid patch hunk line')
            if line[0] != '+':
                before.append(line[1:])
            if line[0] != '-':
                after.append(line[1:])
        position = locate(lines, before, cursor, eof)
        lines[position:position + len(before)] = after
        cursor = position + len(after)
    return '\n'.join(lines) + ('\n' if lines else '')


def changes(command: str, cwd: str, after: bool = False) -> list[dict]:
    """All sources and destinations, including deletes and moves; never modifies disk.

    After the patch ran only target paths matter. Its old hunks cannot be replayed then.
    """
    rows = command.strip().splitlines()
    if not rows or rows[0] != '*** Begin Patch' or rows[-1] != '*** End Patch':
        raise ValueError('Expected a complete Codex patch')
    result, virtual, i = [], {}, 1
    while i < len(rows) - 1:
        header = rows[i]
        i += 1
        kind = next((k for k in ('Add', 'Update', 'Delete') if header.startswith(f'*** {k} File: ')), None)
        if kind is None:
            raise ValueError('Unknown patch operation')
        path = (Path(cwd) / header.split(': ', 1)[1]).resolve()
        destination = path
        if i < len(rows) - 1 and rows[i].startswith('*** Move to: '):
            destination = (Path(cwd) / rows[i].split(': ', 1)[1]).resolve()
            i += 1
        body = []
        while i < len(rows) - 1 and not rows[i].startswith(('*** Add File:', '*** Update File:', '*** Delete File:')):
            body.append(rows[i])
            i += 1
        if kind == 'Delete' or destination != path:
            result.append({'file_path': str(path), 'edits': [], 'operation': 'delete'})
        if kind == 'Delete':
            virtual[path] = None
            continue
        if after:
            content = destination.read_text(encoding='utf-8') if destination.is_file() else ''
        elif kind == 'Add':
            if any(not row.startswith('+') for row in body):
                raise ValueError('Invalid added file content')
            content = '\n'.join(row[1:] for row in body) + ('\n' if body else '')
        else:
            previous = virtual[path] if path in virtual else path.read_text(encoding='utf-8')
            if previous is None:
                raise ValueError('Patch updates a deleted file')
            content = updated(previous, body)
        result.append({'file_path': str(destination), 'content': content, 'operation': 'write'})
        if destination != path:
            virtual[path] = None
        virtual[destination] = content
    return result
